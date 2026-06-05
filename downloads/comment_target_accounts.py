#!/usr/bin/env python3
"""
Comment on specific target accounts - Separate from main commenter
Comment on latest 1 video per account (likes disabled - TikTok blocks them)
Each browser can only comment on each target account ONCE per day
Auto-signup for logged out browsers

Usage: python3 comment_target_accounts.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import time
import random
import json
import re
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build

# STEALTH MODE - Hide automation detection
from stealth_browsing import (
    inject_stealth,
    natural_scroll,
    natural_mouse_movement,
    watch_video_naturally,
    random_pause,
    click_naturally,
    type_naturally
)

# Supabase for cloud sync to Vercel dashboard
try:
    from supabase import create_client
    SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Warning: supabase not installed, stats won't sync to cloud")

# Comment functions are now inline - no need to import from main commenter

ADSPOWER_API = 'http://local.adspower.net:50325'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'
TARGET_STATS_PATH = 'target_accounts_stats.json'
COMMENTED_VIDEOS_PATH = 'target_commented_videos.json'
ACCOUNT_CREATION_DATES_PATH = 'account_creation_dates.json'
DAILY_ACTIVITY_PATH = 'daily_activity_tracker.json'
DAILY_TARGET_COMMENTS_PATH = 'daily_target_comments.json'  # Track comments per target per day
WEEKLY_TARGET_COMMENTS_PATH = 'weekly_target_comments.json'  # Track comments per target per week

# Keep Playwright instances alive to prevent auto-close
PLAYWRIGHT_INSTANCES = []

# KEEP BROWSERS OPEN MODE - Set to True to just open browsers without automation
KEEP_OPEN_MODE = True  # Set to False to run automation

# New account limits
NEW_ACCOUNT_DAYS = 30  # Consider account "new" for first 30 days
NEW_ACCOUNT_DAILY_FOLLOWS = 2
NEW_ACCOUNT_DAILY_COMMENTS = 5  # Max 5 comments per browser per day
WEEKLY_VIDEOS_PER_ACCOUNT = 2  # Max 2 videos per target account per week per browser

def normalize_video_url(video_url):
    """Extract just the video ID from a TikTok URL to ensure consistent tracking.
    e.g. https://www.tiktok.com/@user/video/123456?q=1 -> 123456
    """
    if '/video/' in video_url:
        # Extract video ID (the number after /video/)
        video_id = video_url.split('/video/')[1].split('?')[0].split('/')[0]
        return video_id
    return video_url

def like_video(page):
    """Like a video"""
    try:
        # Try to find and click the like button
        liked = page.evaluate('''() => {
            const likeBtn = document.querySelector('[data-e2e="like-icon"], [data-e2e="browse-like-icon"]');
            if (likeBtn && !likeBtn.closest('button').classList.contains('liked')) {
                likeBtn.closest('button').click();
                return true;
            }
            return false;
        }''')

        if liked:
            time.sleep(1)
            return True
        return False
    except:
        return False

def load_commented_videos(browser_name=None):
    """Load set of already commented video IDs for a specific browser.
    Each browser tracks its own commented videos independently."""
    try:
        with open(COMMENTED_VIDEOS_PATH, 'r') as f:
            data = json.load(f)
            # Handle both old format (list) and new format (dict per browser)
            if isinstance(data, list):
                # Old global format - return empty for per-browser queries
                return set()
            elif browser_name and browser_name in data:
                return set(data[browser_name])
            return set()
    except:
        return set()

def save_commented_video(video_url, browser_name):
    """Save a video ID as commented for a specific browser"""
    video_id = normalize_video_url(video_url)
    try:
        with open(COMMENTED_VIDEOS_PATH, 'r') as f:
            data = json.load(f)
            # Convert old format to new if needed
            if isinstance(data, list):
                data = {}
    except:
        data = {}

    if browser_name not in data:
        data[browser_name] = []

    if video_id not in data[browser_name]:
        data[browser_name].append(video_id)

    # Keep only last 100 videos per browser
    if len(data[browser_name]) > 100:
        data[browser_name] = data[browser_name][-100:]

    with open(COMMENTED_VIDEOS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_account_creation_dates():
    """Load account creation dates"""
    try:
        with open(ACCOUNT_CREATION_DATES_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_account_creation_date(browser_name):
    """Save when an account was created"""
    from datetime import datetime
    dates = load_account_creation_dates()
    if browser_name not in dates:
        dates[browser_name] = datetime.now().strftime('%Y-%m-%d')
        with open(ACCOUNT_CREATION_DATES_PATH, 'w') as f:
            json.dump(dates, f, indent=2)

def is_new_account(browser_name):
    """Check if account is new (within NEW_ACCOUNT_DAYS days)"""
    from datetime import datetime, timedelta
    dates = load_account_creation_dates()
    if browser_name not in dates:
        return False

    creation_date = datetime.strptime(dates[browser_name], '%Y-%m-%d')
    days_old = (datetime.now() - creation_date).days
    return days_old <= NEW_ACCOUNT_DAYS

def load_daily_activity():
    """Load daily activity tracker"""
    try:
        with open(DAILY_ACTIVITY_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def get_today_activity(browser_name):
    """Get today's follow and comment count for a browser"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    activity = load_daily_activity()

    if browser_name not in activity:
        return {'follows': 0, 'comments': 0}

    if today not in activity[browser_name]:
        return {'follows': 0, 'comments': 0}

    return activity[browser_name][today]

def record_follow(browser_name):
    """Record a follow action for today"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    activity = load_daily_activity()

    if browser_name not in activity:
        activity[browser_name] = {}

    if today not in activity[browser_name]:
        activity[browser_name][today] = {'follows': 0, 'comments': 0}

    activity[browser_name][today]['follows'] += 1

    with open(DAILY_ACTIVITY_PATH, 'w') as f:
        json.dump(activity, f, indent=2)

def record_comment(browser_name):
    """Record a comment action for today"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    activity = load_daily_activity()

    if browser_name not in activity:
        activity[browser_name] = {}

    if today not in activity[browser_name]:
        activity[browser_name][today] = {'follows': 0, 'comments': 0}

    activity[browser_name][today]['comments'] += 1

    with open(DAILY_ACTIVITY_PATH, 'w') as f:
        json.dump(activity, f, indent=2)

def can_follow_today(browser_name):
    """Check if account can follow more accounts today"""
    if not is_new_account(browser_name):
        return True  # No limit for established accounts

    today_activity = get_today_activity(browser_name)
    return today_activity['follows'] < NEW_ACCOUNT_DAILY_FOLLOWS

def can_comment_today(browser_name):
    """Check if account can comment more today"""
    if not is_new_account(browser_name):
        return True  # No limit for established accounts

    today_activity = get_today_activity(browser_name)
    return today_activity['comments'] < NEW_ACCOUNT_DAILY_COMMENTS

def load_daily_target_comments():
    """Load daily per-target-account comment tracking"""
    try:
        with open(DAILY_TARGET_COMMENTS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def has_commented_on_target_today(browser_name, target_account):
    """Check if browser has already commented on this target account today"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    data = load_daily_target_comments()

    # Structure: {browser_name: {date: [target_accounts_commented]}}
    if browser_name not in data:
        return False
    if today not in data[browser_name]:
        return False

    return target_account in data[browser_name][today]

def record_target_comment(browser_name, target_account):
    """Record that browser commented on target account today"""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    data = load_daily_target_comments()

    if browser_name not in data:
        data[browser_name] = {}
    if today not in data[browser_name]:
        data[browser_name][today] = []

    if target_account not in data[browser_name][today]:
        data[browser_name][today].append(target_account)

    # Clean up old dates (keep only last 7 days)
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    for browser in list(data.keys()):
        for date in list(data[browser].keys()):
            if date < cutoff:
                del data[browser][date]
        if not data[browser]:
            del data[browser]

    with open(DAILY_TARGET_COMMENTS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_weekly_target_comments():
    """Load weekly per-target-account comment tracking"""
    try:
        with open(WEEKLY_TARGET_COMMENTS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def get_current_week():
    """Get current week as YYYY-WW format"""
    from datetime import datetime
    return datetime.now().strftime('%Y-%W')

def get_weekly_comment_count(browser_name, target_account):
    """Get how many videos this browser has commented on for this target this week"""
    week = get_current_week()
    data = load_weekly_target_comments()

    if browser_name not in data:
        return 0
    if week not in data[browser_name]:
        return 0

    return data[browser_name][week].get(target_account, 0)

def can_comment_on_target_this_week(browser_name, target_account):
    """Check if browser can comment on more videos for this target this week"""
    count = get_weekly_comment_count(browser_name, target_account)
    return count < WEEKLY_VIDEOS_PER_ACCOUNT

def has_reached_weekly_quota_all_targets(browser_name):
    """Check if browser has reached weekly quota (2 videos) for ALL target accounts.
    Returns True if browser should be skipped entirely (no more targets to comment on)."""
    for account in TARGET_ACCOUNTS:
        if can_comment_on_target_this_week(browser_name, account):
            return False  # Can still comment on at least one target
    return True  # Reached quota for ALL targets

def record_weekly_target_comment(browser_name, target_account):
    """Record that browser commented on a video for target account this week"""
    week = get_current_week()
    data = load_weekly_target_comments()

    if browser_name not in data:
        data[browser_name] = {}
    if week not in data[browser_name]:
        data[browser_name][week] = {}

    current_count = data[browser_name][week].get(target_account, 0)
    data[browser_name][week][target_account] = current_count + 1

    # Clean up old weeks (keep only last 2 weeks)
    from datetime import datetime, timedelta
    current_week_num = int(datetime.now().strftime('%W'))
    current_year = int(datetime.now().strftime('%Y'))

    for browser in list(data.keys()):
        for week_str in list(data[browser].keys()):
            try:
                year, week_num = week_str.split('-')
                if int(year) < current_year or (int(year) == current_year and int(week_num) < current_week_num - 1):
                    del data[browser][week_str]
            except:
                pass
        if not data[browser]:
            del data[browser]

    with open(WEEKLY_TARGET_COMMENTS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_target_stats():
    """Load existing target account stats from JSON"""
    try:
        with open(TARGET_STATS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_target_stats(stats):
    """Save target account stats to JSON and sync to Supabase"""
    with open(TARGET_STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)

    # Sync to Supabase for Vercel dashboard
    if HAS_SUPABASE:
        try:
            for account, data in stats.items():
                supabase.table('target_account_stats').upsert({
                    'account': account,
                    'total_views': data.get('total_views', 0),
                    'total_comments': data.get('total_comments', 0),
                    'browsers_engaged': len(data.get('browsers_engaged', [])),
                    'last_updated': data.get('last_updated', '')
                }, on_conflict='account').execute()
        except Exception as e:
            print(f"    Warning: Failed to sync to Supabase: {e}")

def sync_account_to_supabase(browser_name, username, email=None, account_type='login', status='active'):
    """Sync TikTok account info to Supabase tiktok_account_history table.
    Records ALL accounts that have ever been used on each browser.

    Args:
        browser_name: Browser identifier (e.g., 'tt23')
        username: TikTok username
        email: Email used for signup (optional)
        account_type: 'signup' for new accounts, 'login' for existing
        status: 'active', 'logged_out', 'suspended'
    """
    if not HAS_SUPABASE or not username:
        return

    try:
        # Extract browser number from name (e.g., "tt23" -> 23)
        browser_num = int(re.search(r'\d+', browser_name).group()) if re.search(r'\d+', browser_name) else None
        now = time.strftime('%Y-%m-%d %H:%M:%S')

        # Record in history table (tracks ALL accounts per browser)
        history_record = {
            'browser_num': browser_num,
            'browser_name': browser_name,
            'username': username,
            'account_type': account_type,
            'status': status,
            'last_seen': now
        }

        if email:
            history_record['email'] = email

        # Upsert based on browser_num + username (composite key)
        # This creates new record for each unique browser+username combo
        supabase.table('tiktok_account_history').upsert(
            history_record,
            on_conflict='browser_num,username'
        ).execute()

        print(f'    ✓ Synced @{username} ({account_type}, {status}) to Supabase', flush=True)
    except Exception as e:
        # Don't fail the whole process if sync fails
        pass

def mark_previous_account_logged_out(browser_name):
    """Mark the previous account on this browser as logged out.
    Called when we detect a browser is no longer logged in."""
    try:
        # Load profile mapping to get the previous username
        with open(PROFILE_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)

        if browser_name in mapping:
            previous_username = mapping[browser_name]
            if previous_username:
                # Mark as logged out in Supabase
                sync_account_to_supabase(browser_name, previous_username, account_type='login', status='logged_out')
                print(f'    ⚠ Marked @{previous_username} as logged out', flush=True)
    except:
        pass

def update_account_stats(account, videos_viewed, comments_made, browser_name, tiktok_username=None):
    """Update stats for a target account"""
    stats = load_target_stats()

    if account not in stats:
        stats[account] = {
            'total_views': 0,
            'total_comments': 0,
            'browsers_engaged': [],
            'last_updated': None,
            'sessions': []
        }

    stats[account]['total_views'] += videos_viewed
    stats[account]['total_comments'] += comments_made
    if browser_name not in stats[account]['browsers_engaged']:
        stats[account]['browsers_engaged'].append(browser_name)
    stats[account]['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')

    # Keep last 100 sessions - now includes tiktok_username
    stats[account]['sessions'].append({
        'browser': browser_name,
        'tiktok_username': tiktok_username,
        'views': videos_viewed,
        'comments': comments_made,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    stats[account]['sessions'] = stats[account]['sessions'][-100:]

    save_target_stats(stats)

    # Sync comment activity to Supabase if any comments were made
    if comments_made > 0 and HAS_SUPABASE and tiktok_username:
        try:
            supabase.table('target_comment_history').insert({
                'browser_name': browser_name,
                'tiktok_username': tiktok_username,
                'target_account': account,
                'comments_made': comments_made,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }).execute()
        except:
            pass

# Target accounts to comment on (edit this list as needed)
TARGET_ACCOUNTS = [
    'flockboynation',
    'happyandyaya',
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]

# Settings
COMMENTS_PER_ACCOUNT = 2  # Comment on 2 videos per account (latest 2)
LIKES_PER_ACCOUNT = 0      # Disabled - TikTok blocks automated likes
VIEW_ALL_VIDEOS = False    # Skip viewing - just comment
PARALLEL_BROWSERS = 2      # Keep only 2 browsers open at a time

# Comments by niche - customize as needed
NICHE_COMMENTS = {
    'fitness': [
        'Love the gains content!',
        'Great tips! Been looking for this',
        'This is exactly what I needed to see',
        'Solid advice right here',
        'Thanks for sharing this!'
    ],
    'adventure': [
        'What an amazing journey!',
        'This is so inspiring!',
        'Living the dream! Love it',
        'Wow, this looks incredible',
        'Adding this to my bucket list'
    ],
    'tech': [
        'The future is here!',
        'This is incredible tech!',
        'Mind blown by this',
        'Game changer right here',
        'This is next level'
    ],
    'lifestyle': [
        'Beautiful content!',
        'So elegant!',
        'Love the aesthetic!',
        'This is goals',
        'Absolutely stunning'
    ],
    'default': [
        'This is fire!',
        'Love this vibe!',
        'Keep creating!',
        'Amazing content!',
        'This is great!'
    ]
}

def get_niche(account):
    """Determine niche based on account name"""
    account_lower = account.lower()
    if any(x in account_lower for x in ['supplement', 'supps', 'fit', 'gym', 'catalyst']):
        return 'fitness'
    elif any(x in account_lower for x in ['adventure', 'life', 'travel', 'explore']):
        return 'adventure'
    elif any(x in account_lower for x in ['ai', 'tech', 'digital', 'code']):
        return 'tech'
    elif any(x in account_lower for x in ['house', 'grace', 'style', 'fashion', 'beauty']):
        return 'lifestyle'
    return 'default'

def get_browser_list():
    """Get list of browsers from AdsPower"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=100', timeout=30)
    return resp.json().get('data', {}).get('list', [])

def open_browser(user_id):
    """Open AdsPower browser and return websocket URL"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}', timeout=60)
    data = resp.json()
    if data.get('code') == 0:
        return data['data']['ws']['puppeteer']
    return None

def close_browser(user_id):
    """Close AdsPower browser with retries"""
    for attempt in range(3):
        try:
            resp = requests.get(f'{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}', timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                time.sleep(1)  # Wait for browser to fully close
                return True
        except:
            pass
        time.sleep(1)
    return False

# ============ AUTO-SIGNUP FUNCTIONS ============

# Name generators for signup
ADJECTIVES = ['swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean', 'forest',
              'digital', 'cyber', 'tech', 'smart', 'neon', 'atomic', 'vivid', 'prism',
              'flux', 'zen', 'drift', 'echo', 'nova', 'pixel', 'quantum', 'stellar']
NOUNS = ['phoenix', 'dragon', 'falcon', 'eagle', 'wolf', 'tiger', 'star', 'moon',
         'wave', 'flame', 'pixel', 'pulse', 'echo', 'spark', 'glow', 'path',
         'stream', 'verse', 'core', 'field', 'track', 'scope', 'grid', 'focus']

def generate_email():
    """Generate email with rotating domains"""
    # Add your email domains here (all should forward to your Gmail)
    DOMAINS = [
        'automateyourbizz.xyz',  # Original domain
        # Add more domains below:
        # 'yourdomain1.com',
        # 'yourdomain2.com',
        # 'yourdomain3.com',
    ]

    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(100, 999)
    domain = random.choice(DOMAINS)  # Randomly select a domain
    return f"{adj}{noun}{num}@{domain}"

def generate_password():
    # Always use the same password for all signups
    return "Spectrum.01"

def get_gmail_service():
    """Get Gmail API service"""
    try:
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
        return build('gmail', 'v1', credentials=creds)
    except:
        return None

def fetch_verification_code(email, max_attempts=12):
    """Fetch TikTok verification code from Gmail"""
    try:
        service = get_gmail_service()
        if not service:
            print(f"    Gmail service unavailable")
            return None
        query = f'from:tiktok to:{email} subject:(verification OR code) is:unread newer_than:10m'
        print(f"    Searching for TikTok email to {email}...")

        for attempt in range(max_attempts):
            results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])

            if messages:
                print(f"    Found {len(messages)} email(s), extracting code...")
                msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

                print(f"    Email from: {from_header}")
                print(f"    Subject: {subject}")

                # Try to find code in subject
                code_match = re.search(r'(\d{6})', subject)
                if code_match:
                    code = code_match.group(1)
                    service.users().messages().modify(userId='me', id=messages[0]['id'],
                                                     body={'removeLabelIds': ['UNREAD']}).execute()
                    return code

                # Try to find code in email body if not in subject
                try:
                    if 'parts' in msg['payload']:
                        for part in msg['payload']['parts']:
                            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                                import base64
                                body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                                code_match = re.search(r'(\d{6})', body_text)
                                if code_match:
                                    code = code_match.group(1)
                                    print(f"    Found code in email body: {code}")
                                    service.users().messages().modify(userId='me', id=messages[0]['id'],
                                                                     body={'removeLabelIds': ['UNREAD']}).execute()
                                    return code
                except Exception as body_err:
                    print(f"    Could not parse email body: {str(body_err)[:40]}")

            if attempt < max_attempts - 1:
                if attempt % 6 == 0 and attempt > 0:  # Print status every 30 seconds
                    print(f"    Still waiting for code... ({attempt * 5}s elapsed)")
                time.sleep(5)

        print(f"    No verification email received after {max_attempts * 5} seconds")
        return None
    except Exception as e:
        print(f"    Error fetching code: {str(e)[:60]}")
        return None

def check_login_status(page):
    """Check if browser is logged into TikTok. Returns (is_logged_in, username)"""
    try:
        page.goto('https://www.tiktok.com/', timeout=30000)
        time.sleep(3)

        # Dismiss cookie consent banner if present
        try:
            cookie_btn = page.locator(
                'button:has-text("Permitir todas"), button:has-text("Allow all"), '
                'button:has-text("Accept all"), button:has-text("Accept"), '
                'button:has-text("Aceptar"), button:has-text("Akzeptieren")'
            ).first
            if cookie_btn.is_visible(timeout=1500):
                cookie_btn.click()
                time.sleep(1)
        except:
            pass

        # Check for login button (means NOT logged in)
        try:
            login_btn = page.locator('button:has-text("Log in"), [data-e2e="nav-login-button"]').first
            if login_btn.is_visible(timeout=3000):
                return False, None
        except:
            pass

        # Try to get username from profile
        try:
            page.goto('https://www.tiktok.com/profile', timeout=15000)
            time.sleep(2)
            url = page.url
            if '/@' in url:
                username = url.split('/@')[1].split('?')[0].split('/')[0]
                return True, username
        except:
            pass

        # Check for profile icon (means logged in)
        try:
            profile_icon = page.locator('[data-e2e="profile-icon"]').first
            if profile_icon.is_visible(timeout=2000):
                return True, None
        except:
            pass

        return False, None
    except:
        return False, None

def download_ai_profile_pic(save_path, browser_name):
    """Download AI-generated profile picture"""
    try:
        # Use random user API for realistic AI-generated photos
        response = requests.get('https://randomuser.me/api/?gender=female', timeout=30)
        data = response.json()

        # Get the large profile picture
        pic_url = data['results'][0]['picture']['large']

        # Download the image
        pic_response = requests.get(pic_url, timeout=30)
        with open(save_path, 'wb') as f:
            f.write(pic_response.content)

        print(f'    [{browser_name}] ✓ Downloaded profile picture', flush=True)
        return True
    except Exception as e:
        # Try alternative: thispersondoesnotexist.com
        try:
            print(f'    [{browser_name}] Trying alternative source...', flush=True)
            pic_url = f'https://thispersondoesnotexist.com/image?t={int(time.time())}'
            pic_response = requests.get(pic_url, timeout=30)
            with open(save_path, 'wb') as f:
                f.write(pic_response.content)
            print(f'    [{browser_name}] ✓ Downloaded profile picture (alternative)', flush=True)
            return True
        except Exception as e2:
            print(f'    [{browser_name}] ✗ Profile pic download failed', flush=True)
            return False

def generate_random_bio():
    """Generate a random bio for new account"""
    bios = [
        'Just vibing ✨ | Coffee enthusiast ☕',
        'Living life one day at a time 🌊 | Music lover 🎵',
        'Dreamer 💫 | Adventure seeker 🌍',
        'Creating my own sunshine ☀️ | Good vibes only ✌️',
        'Wanderlust & city dust 🏙️ | Always exploring 🗺️',
        'Making memories 📸 | Living in the moment 💭',
        'Chasing dreams 🌟 | Spread love ❤️',
        'Life is a journey 🚀 | Enjoy the ride 🎢',
        'Stay positive 😊 | Work hard, play harder 💪',
        'Just me being me 🙋 | Authenticity matters 💯'
    ]
    return random.choice(bios)

def setup_new_account_profile(page, browser_name):
    """Setup profile picture and bio for newly created account"""
    print(f'    [{browser_name}] Setting up profile...', flush=True)

    # Prepare profile picture
    import os as _os
    base_path = _os.path.dirname(_os.path.abspath(__file__))
    pic_dir = f'{base_path}/profile_pics'
    import os
    os.makedirs(pic_dir, exist_ok=True)
    pic_path = f'{pic_dir}/{browser_name}_profile.jpg'

    # Download profile picture
    if not download_ai_profile_pic(pic_path, browser_name):
        print(f'    [{browser_name}] ⚠ Skipping profile picture upload', flush=True)
        pic_path = None

    # Generate bio
    bio_text = generate_random_bio()

    try:
        # Navigate to profile page
        try:
            page.goto('https://www.tiktok.com/@me', timeout=30000)
            time.sleep(3)
        except:
            print(f'    [{browser_name}] ⚠ Could not navigate to profile', flush=True)
            return False

        # Dismiss any onboarding/intermediate screens before accessing profile
        for skip_label in ['Skip', 'Later', 'Not now', 'Done']:
            try:
                btn = page.locator(f'button:has-text("{skip_label}")').first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    print(f'    [{browser_name}] Dismissed screen before Edit profile ("{skip_label}")', flush=True)
                    time.sleep(2)
                    break
            except:
                pass

        # Click "Edit profile" button
        try:
            edit_btn = page.locator('button:has-text("Edit profile"), button:has-text("Edit Profile")').first
            edit_btn.wait_for(state='visible', timeout=8000)
            edit_btn.click()
            time.sleep(3)
            print(f'    [{browser_name}] ✓ Edit profile opened', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] ⚠ Could not open Edit profile: {str(e)[:50]}', flush=True)
            # Don't abort - the signup may have succeeded even if profile setup fails
            return False

        # Upload profile picture if we have one
        if pic_path:
            pic_uploaded = False

            # Method 1: Try clicking edit icons/buttons
            try:
                selectors = [
                    'button[aria-label*="photo"]',
                    'button[aria-label*="Upload"]',
                    'div[role="button"]:near(:text("Profile photo"))',
                ]

                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        element.wait_for(state='visible', timeout=2000)
                        element.click()
                        time.sleep(2)

                        file_input = page.locator('input[type="file"]').first
                        file_input.set_input_files(pic_path, timeout=5000)
                        time.sleep(3)

                        # Click Apply button
                        try:
                            apply_btn = page.locator('button:has-text("Apply")').first
                            apply_btn.wait_for(state='visible', timeout=5000)
                            apply_btn.click()
                            time.sleep(2)
                        except:
                            pass

                        pic_uploaded = True
                        print(f'    [{browser_name}] ✓ Profile picture uploaded', flush=True)
                        break
                    except:
                        continue
            except:
                pass

            # Method 2: Direct file input with JavaScript
            if not pic_uploaded:
                try:
                    page.evaluate("""() => {
                        const inputs = document.querySelectorAll('input[type="file"]');
                        if (inputs.length > 0) {
                            inputs[0].style.display = 'block';
                            inputs[0].style.visibility = 'visible';
                            inputs[0].style.opacity = '1';
                            inputs[0].style.position = 'relative';
                        }
                    }""")
                    time.sleep(1)

                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(pic_path, timeout=5000)
                    time.sleep(3)

                    # Click Apply button
                    try:
                        apply_btn = page.locator('button:has-text("Apply")').first
                        apply_btn.wait_for(state='visible', timeout=5000)
                        apply_btn.click()
                        time.sleep(2)
                    except:
                        pass

                    pic_uploaded = True
                    print(f'    [{browser_name}] ✓ Profile picture uploaded (direct)', flush=True)
                except:
                    print(f'    [{browser_name}] ⚠ Could not upload profile picture', flush=True)

        # Set bio
        try:
            bio_selectors = [
                'textarea[placeholder*="Bio"]',
                'div:has-text("Bio") ~ textarea',
                'textarea[name="bio"]',
            ]

            bio_set = False
            for selector in bio_selectors:
                try:
                    bio_input = page.locator(selector).first
                    bio_input.wait_for(state='visible', timeout=3000)
                    bio_input.click()
                    time.sleep(0.5)
                    bio_input.fill('')
                    time.sleep(0.5)
                    bio_input.fill(bio_text)
                    time.sleep(1)
                    print(f'    [{browser_name}] ✓ Bio set: {bio_text}', flush=True)
                    bio_set = True
                    break
                except:
                    continue

            if not bio_set:
                print(f'    [{browser_name}] ⚠ Could not set bio', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] ⚠ Bio update failed', flush=True)

        # Save changes
        try:
            save_btn = page.locator('button:has-text("Save")').first
            save_btn.wait_for(state='visible', timeout=5000)
            save_btn.click()
            time.sleep(3)
            print(f'    [{browser_name}] ✓ Profile saved!', flush=True)
            return True
        except Exception as e:
            print(f'    [{browser_name}] ⚠ Save button failed', flush=True)
            return False

    except Exception as e:
        print(f'    [{browser_name}] ✗ Profile setup error: {str(e)[:50]}', flush=True)
        return False

def auto_signup(page, browser_name):
    """Automatically signup a new TikTok account"""
    print(f'    [{browser_name}] Running auto-signup...', flush=True)

    email = generate_email()
    password = generate_password()
    print(f'    [{browser_name}] Email: {email}', flush=True)

    try:
        # Clear stale TikTok cookies/storage before signup — old session data
        # causes TikTok to show CAPTCHA or redirect to login instead of signup
        try:
            context = page.context
            context.clear_cookies()
            print(f'    [{browser_name}] Cleared cookies', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] Cookie clear skipped: {str(e)[:40]}', flush=True)

        page.goto(
            'https://www.tiktok.com/signup/phone-or-email/email',
            wait_until='domcontentloaded',
            timeout=15000,
        )
        time.sleep(1.5)

        # Dismiss cookie consent banner if present
        try:
            cookie_btn = page.locator(
                'button:has-text("Permitir todas"), button:has-text("Allow all"), '
                'button:has-text("Accept all"), button:has-text("Accept"), '
                'button:has-text("Aceptar"), button:has-text("Akzeptieren")'
            ).first
            if cookie_btn.is_visible(timeout=2000):
                cookie_btn.click()
                print(f'    [{browser_name}] Dismissed cookie banner', flush=True)
                time.sleep(1)
        except:
            pass

        # Fill birthdate using keyboard
        try:
            for i, count in enumerate([random.randint(1, 6), random.randint(1, 15), 28]):
                page.locator('[role="combobox"]').nth(i).click(timeout=5000)
                time.sleep(0.3)
                for _ in range(count):
                    page.keyboard.press('ArrowDown')
                    time.sleep(0.05)
                page.keyboard.press('Enter')
                time.sleep(0.3)
            print(f'    [{browser_name}] Birthdate filled', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] Birthdate error: {str(e)[:40]}', flush=True)
            return False, None

        # After birthdate, TikTok may need a moment or a "Next" click before email appears
        time.sleep(1)
        try:
            next_btn = page.locator('button:has-text("Next"), button:has-text("Continue"), button:has-text("Suivant")').first
            if next_btn.is_visible(timeout=2000):
                next_btn.click()
                print(f'    [{browser_name}] Clicked Next after birthdate', flush=True)
                time.sleep(1)
        except:
            pass

        # Enter email - type naturally to trigger React state updates
        # Use scroll_into_view + focus instead of click() to avoid actionability timeout
        try:
            email_input = page.locator('input[name="email"], input[type="email"]').first
            email_input.wait_for(state='visible', timeout=7000)
            email_input.scroll_into_view_if_needed()
            email_input.focus()
            time.sleep(0.3)
            email_input.fill('')
            for ch in email:
                email_input.type(ch)
                time.sleep(random.uniform(0.02, 0.05))
            time.sleep(0.25)
            print(f'    [{browser_name}] Email entered', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] Email input error: {str(e)[:60]}', flush=True)
            return False, None

        # Enter password - type naturally
        try:
            pw_input = page.locator('input[type="password"]').first
            pw_input.wait_for(state='visible', timeout=4000)
            pw_input.scroll_into_view_if_needed()
            pw_input.focus()
            time.sleep(0.3)
            pw_input.fill('')
            for ch in password:
                pw_input.type(ch)
                time.sleep(random.uniform(0.02, 0.05))
            time.sleep(0.35)
            print(f'    [{browser_name}] Password entered', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] Password input error: {str(e)[:60]}', flush=True)
            return False, None

        # Click Send code once, naturally. Force/retry clicks can cause TikTok
        # to count duplicate verification attempts and trigger max-attempt limits.
        try:
            code_sent = False

            send_btn = page.locator('button:has-text("Send code"), button:has-text("Envoyer")').first
            if send_btn.is_visible(timeout=5000):
                send_btn.scroll_into_view_if_needed()
                page.mouse.wheel(0, 250)

                enabled = False
                for _ in range(10):
                    disabled = send_btn.get_attribute('disabled')
                    aria_disabled = send_btn.get_attribute('aria-disabled')
                    class_name = send_btn.get_attribute('class') or ''
                    button_text = (send_btn.text_content() or '').strip()
                    if (
                        disabled is None
                        and aria_disabled not in ('true', '1')
                        and 'disabled' not in class_name.lower()
                        and button_text.lower() in ('send code', 'envoyer')
                    ):
                        enabled = True
                        break
                    time.sleep(0.3)

                if not enabled:
                    print(f'    [{browser_name}] Send code button not enabled - aborting this email', flush=True)
                    return False, None

                time.sleep(random.uniform(0.3, 0.7))
                send_btn.click()
                print(f'    [{browser_name}] Send code clicked', flush=True)

                # Wait for TikTok to process the request
                time.sleep(3)

                # Check for confirmation that code was sent
                for check in range(5):
                    # CAPTCHA detection - abort immediately if popup appears
                    try:
                        captcha_el = page.locator(
                            '[class*="captcha"], [id*="captcha"], iframe[src*="captcha"], '
                            '[class*="verify-wrap"], [data-e2e*="captcha"], '
                            '[class*="secsdk-captcha"], [class*="captcha-verify"], '
                            'text=Slide to verify, text=Hold and drag'
                        ).first
                        if captcha_el.is_visible(timeout=1500):
                            print(f'    [{browser_name}] ✗ CAPTCHA detected after Send code - aborting', flush=True)
                            return False, None
                    except:
                        pass

                    # Check for Resend button (most common indicator)
                    try:
                        resend_btn = page.locator(
                            'button:has-text("Resend code"), button:has-text("Resend"), '
                            'button:has-text("Renvoyer"), button:has-text("Send again"), '
                            '[data-e2e*="resend"]'
                        ).first
                        if resend_btn.is_visible(timeout=2000):
                            print(f'    [{browser_name}] ✓ Code sent! (Resend button visible)', flush=True)
                            code_sent = True
                            break
                    except:
                        pass

                    # Also check if the code input box became enabled (another sign code was sent)
                    try:
                        code_box = page.locator('input[placeholder*="code"], input[name="code"]').first
                        if code_box.is_visible(timeout=1000):
                            disabled_attr = code_box.get_attribute('disabled')
                            if disabled_attr is None:
                                print(f'    [{browser_name}] ✓ Code sent! (code input enabled)', flush=True)
                                code_sent = True
                                break
                    except:
                        pass

                    # Check for error messages from TikTok
                    try:
                        err_el = page.locator(
                            '[class*="error-text"], [class*="tip-error"], [class*="error-msg"], '
                            'text=/Maximum number of attempts|Too many attempts|Try again later/i'
                        ).first
                        if err_el.is_visible(timeout=500):
                            err_txt = (err_el.text_content() or '').strip()[:80]
                            print(f'    [{browser_name}] Send code error: {err_txt}', flush=True)
                            if re.search(r'maximum number of attempts|too many attempts|try again later', err_txt, re.I):
                                print(f'    [{browser_name}] TikTok rate-limited code sending - moving on', flush=True)
                                return False, None
                    except:
                        pass

                    time.sleep(1)

            # Double-check code was sent
            if not code_sent:
                # Check one more time for Resend button or code input field
                try:
                    resend_btn = page.locator('button:has-text("Resend"), div:has-text("Resend")').first
                    if resend_btn.is_visible(timeout=2000):
                        code_sent = True
                        print(f'    [{browser_name}] ✓ Code sent (verified)', flush=True)
                except:
                    # Check if code input field is visible (also means code was sent)
                    try:
                        code_input = page.locator('input[placeholder*="code"], input[name="code"]').first
                        if code_input.is_visible(timeout=2000):
                            code_sent = True
                            print(f'    [{browser_name}] ✓ Code input visible (code was sent)', flush=True)
                    except:
                        pass

            if not code_sent:
                # Take debug screenshot to see what's on screen
                import os as _os
                debug_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), f'debug_{browser_name}_send_failed.png')
                page.screenshot(path=debug_path)
                print(f'    [{browser_name}] Debug screenshot: {debug_path}', flush=True)
                print(f'    [{browser_name}] ✗ Could not verify code was sent - aborting', flush=True)
                return False, None

            # Take screenshot to verify current state
            import os as _os
            screenshot_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), f'signup_{browser_name}_after_send.png')
            page.screenshot(path=screenshot_path)
            print(f'    [{browser_name}] Screenshot saved: {screenshot_path}', flush=True)
            time.sleep(0.5)
        except Exception as e:
            print(f'    [{browser_name}] Error clicking send code: {str(e)[:60]}', flush=True)
            return False, None

        # Get verification code
        code = fetch_verification_code(email)
        if not code:
            print(f'    [{browser_name}] No verification code received', flush=True)
            return False, None

        print(f'    [{browser_name}] Got code: {code}', flush=True)

        # Enter code - type naturally one digit at a time
        code_input = page.locator('input[placeholder*="code"], input[name="code"]').first
        code_input.click()
        time.sleep(0.5)
        code_input.fill('')
        time.sleep(0.3)
        for digit in code:
            code_input.type(digit)
            time.sleep(random.uniform(0.08, 0.18))
        time.sleep(1)

        # Submit with a single natural click (no force/JS - those invalidate CSRF token)
        try:
            submit_btn = page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Suivant")').first
            submit_btn.wait_for(state='visible', timeout=5000)
            # Wait for button to become enabled (TikTok enables it once a valid code is typed)
            for _ in range(10):
                disabled = submit_btn.get_attribute('disabled')
                aria_disabled = submit_btn.get_attribute('aria-disabled')
                if disabled is None and aria_disabled not in ('true', '1'):
                    break
                time.sleep(0.5)
            submit_btn.scroll_into_view_if_needed()
            time.sleep(0.5)
            submit_btn.click()
            print(f'    [{browser_name}] Verification code submitted, waiting for page...', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] Submit click failed: {str(e)[:50]}', flush=True)
            return False, None

        # Wait for page to navigate after code submission (up to 15s)
        # TikTok redirects to username page on success - wait for URL to change
        try:
            page.wait_for_url(
                lambda url: 'signup/phone-or-email/email' not in url,
                timeout=15000
            )
            print(f'    [{browser_name}] Page navigated after code submission', flush=True)
        except:
            pass  # Timeout is OK - we'll detect the state below

        current_url = page.url
        print(f'    [{browser_name}] Post-code URL: {current_url[:80]}', flush=True)

        # Take screenshot so we can see exactly what TikTok is showing
        import os as _os
        post_code_shot = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), f'signup_{browser_name}_post_code.png')
        try:
            page.screenshot(path=post_code_shot)
        except:
            pass

        if 'login/download-app' in current_url:
            print(f'    [{browser_name}] TikTok redirected to app-download security page - fresh proxy/browser needed', flush=True)
            return False, None

        # Check for username page - this means signup succeeded
        try:
            username_input = page.locator('input[placeholder*="username"], input[name="nickname"]').first
            if username_input.is_visible(timeout=3000):
                print(f'    [{browser_name}] ✓ Reached username page - signup successful!', flush=True)
                # Fall through to username setup
        except:
            pass

        # Detect CAPTCHA (abort - cannot solve automatically)
        try:
            captcha_visible = page.locator(
                '[class*="captcha"], [id*="captcha"], iframe[src*="captcha"], '
                '[class*="verify-wrap"], [data-e2e*="captcha"], '
                '[class*="secsdk"], [class*="captcha-verify"]'
            ).first.is_visible(timeout=1500)
            if captcha_visible:
                print(f'    [{browser_name}] ✗ CAPTCHA detected after code submit', flush=True)
                return False, None
        except:
            pass

        # Detect visible error messages (invalid code, etc.) - only if still on signup page
        if 'signup' in current_url or 'login' in current_url:
            try:
                error_el = page.locator('[class*="error-text"], [data-e2e*="error"], [class*="tip-error"], [class*="error-msg"]').first
                if error_el.is_visible(timeout=1500):
                    err_msg = (error_el.text_content() or '').strip()[:80]
                    print(f'    [{browser_name}] ✗ Page error: {err_msg}', flush=True)
                    return False, None
            except:
                pass

            # Still on verification page with code input visible - code rejected
            try:
                code_input_still = page.locator('input[placeholder*="code"], input[name="code"]').first
                if code_input_still.is_visible(timeout=1500):
                    print(f'    [{browser_name}] ✗ Still on verification page - code rejected', flush=True)
                    return False, None
            except:
                pass

        # Dismiss common TikTok intermediate screens
        # "Skip" / "Later" / "Not now" buttons on interest/phone/onboarding pages
        for skip_label in ['Skip', 'Later', 'Not now', 'Continue', 'Next', 'Done']:
            try:
                skip_btn = page.locator(f'button:has-text("{skip_label}"), a:has-text("{skip_label}")').first
                if skip_btn.is_visible(timeout=1000):
                    skip_btn.click()
                    print(f'    [{browser_name}] Dismissed intermediate screen ("{skip_label}")', flush=True)
                    time.sleep(2)
                    break
            except:
                pass

        # Detect "Add phone number" prompt and dismiss
        try:
            phone_prompt = page.locator('text=Add phone number, text=phone number, text=Phone number').first
            if phone_prompt.is_visible(timeout=1000):
                print(f'    [{browser_name}] Phone prompt detected - trying to skip', flush=True)
                for skip_label in ['Skip', 'Later', 'Not now']:
                    try:
                        btn = page.locator(f'button:has-text("{skip_label}")').first
                        if btn.is_visible(timeout=1000):
                            btn.click()
                            time.sleep(2)
                            break
                    except:
                        pass
        except:
            pass

        # Set username - TikTok prompts for username after email verification
        username_base = email.split('@')[0]
        username_set = False

        try:
            print(f'    [{browser_name}] Looking for username input field...', flush=True)

            username_input = page.locator(
                'input[name="uniqueId"], input[placeholder*="username" i], '
                'input[data-e2e="username-input"]'
            ).first

            if username_input.is_visible(timeout=5000):
                username_input.click()
                time.sleep(1)
                username_input.fill(username_base)
                time.sleep(1)
                print(f'    [{browser_name}] ✓ Username set to: {username_base}', flush=True)
                username_set = True

                try:
                    page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Sign up")').first.click(timeout=5000)
                    time.sleep(3)
                except:
                    pass
            else:
                print(f'    [{browser_name}] No username input - checking if already past that step', flush=True)

        except Exception as e:
            print(f'    [{browser_name}] Username step skipped', flush=True)

        # Dismiss any onboarding/interests screens that appear after username
        time.sleep(3)
        for skip_label in ['Skip', 'Later', 'Not now']:
            try:
                btn = page.locator(f'button:has-text("{skip_label}")').first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    print(f'    [{browser_name}] Dismissed post-username screen ("{skip_label}")', flush=True)
                    time.sleep(2)
                    break
            except:
                pass

        # Wait for signup to fully complete
        time.sleep(4)

        # Setup profile picture and bio
        print(f'    [{browser_name}] Setting up profile...', flush=True)
        setup_new_account_profile(page, browser_name)

        # Check if signup succeeded by verifying we're logged in
        try:
            page.goto('https://www.tiktok.com/foryou', timeout=20000)
            time.sleep(3)

            # Check if we're on the For You page (means logged in)
            is_logged_in, username = check_login_status(page)

            if is_logged_in:
                final_username = username if username else username_base
                print(f'    [{browser_name}] ✓ Signup success! @{final_username}', flush=True)

                # Save to profile mapping
                try:
                    with open(PROFILE_MAPPING_PATH, 'r') as f:
                        mapping = json.load(f)
                except:
                    mapping = {}
                mapping[browser_name] = final_username
                with open(PROFILE_MAPPING_PATH, 'w') as f:
                    json.dump(mapping, f, indent=2)

                # Save account creation date for new account limits
                save_account_creation_date(browser_name)

                return True, final_username
            else:
                final_url = page.url
                print(f'    [{browser_name}] ✗ Signup failed - not logged in (landed on: {final_url[:70]})', flush=True)
                return False, None

        except Exception as verify_err:
            print(f'    [{browser_name}] ✗ Signup verification error: {str(verify_err)[:100]}', flush=True)
            return False, None

    except Exception as e:
        print(f'    [{browser_name}] Signup error: {str(e)[:50]}', flush=True)
        return False, None

# ============ END AUTO-SIGNUP FUNCTIONS ============

def view_and_comment_on_profile(page, account, browser_name, tiktok_username=None):
    """Visit a profile and comment on latest 1 video (once per day per target)"""
    print(f'    Visiting @{account}...', flush=True)

    # CHECK: Has this browser already commented on this target account today?
    if has_commented_on_target_today(browser_name, account):
        print(f'    ⏭  Already commented on @{account} today - skipping', flush=True)
        return 0, 0

    # CHECK: Has this browser reached weekly quota for this target? (2 videos per week per target)
    weekly_count = get_weekly_comment_count(browser_name, account)
    if not can_comment_on_target_this_week(browser_name, account):
        print(f'    ⏭  Weekly quota reached for @{account} ({weekly_count}/{WEEKLY_VIDEOS_PER_ACCOUNT} videos) - skipping', flush=True)
        return 0, 0

    videos_viewed = 0
    comments_made = 0
    followed = False

    # Load already commented videos for THIS browser (each browser tracks independently)
    already_commented = load_commented_videos(browser_name)

    # Check if this is a new account and what limits apply
    is_new = is_new_account(browser_name)
    if is_new:
        today_activity = get_today_activity(browser_name)
        print(f'    New account - Today: {today_activity["follows"]}/{NEW_ACCOUNT_DAILY_FOLLOWS} follows, {today_activity["comments"]}/{NEW_ACCOUNT_DAILY_COMMENTS} comments', flush=True)

    try:
        page.goto(f'https://www.tiktok.com/@{account}', timeout=30000)
        time.sleep(4)

        # Try to follow the account (if allowed)
        if can_follow_today(browser_name):
            try:
                # Look for follow button
                follow_btn = page.locator('button[data-e2e="follow-button"], button:has-text("Follow"), button:has-text("Suivre")').first
                if follow_btn.is_visible(timeout=3000):
                    follow_btn.click()
                    time.sleep(2)
                    record_follow(browser_name)
                    followed = True
                    print(f'    ✓ Followed @{account}', flush=True)
            except Exception as follow_err:
                pass  # Already following or button not found
        else:
            print(f'    ⚠ Daily follow limit reached for new account', flush=True)

        # Scroll to load more videos (NATURAL)
        for _ in range(3):
            natural_scroll(page, 'down', distance=random.randint(800, 1200))

        # Get ALL video links from profile
        videos = page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('[data-e2e="user-post-item"] a, [class*="DivItemContainer"] a, [class*="video-feed"] a').forEach(a => {
                if (a.href && a.href.includes('/video/')) {
                    links.push(a.href);
                }
            });
            return [...new Set(links)];
        }''')

        if not videos:
            print(f'    No videos found on @{account}', flush=True)
            return 0, 0

        print(f'    Found {len(videos)} videos', flush=True)

        # Get niche-appropriate comments
        niche = get_niche(account)
        comments_pool = NICHE_COMMENTS.get(niche, NICHE_COMMENTS['default'])

        # Select videos to comment on (newest first)
        if len(videos) == 0:
            print(f'    No videos to process on @{account}', flush=True)
            return 0, 0

        # Check if we can comment today (for new accounts)
        if not can_comment_today(browser_name):
            print(f'    Daily comment limit reached, will skip comments', flush=True)
            return 0, 0

        # Find the first video that hasn't been commented on yet
        video_to_comment = None
        for idx, video_url in enumerate(videos[:COMMENTS_PER_ACCOUNT + 5]):  # Check a few more in case some are already commented
            video_id = normalize_video_url(video_url)
            if video_id not in already_commented:
                video_to_comment = video_url
                print(f'    Found uncommented video (index {idx})', flush=True)
                break

        if video_to_comment is None:
            print(f'    All recent videos already commented on - skipping', flush=True)
            return 0, 0

        # Process the found video
        for video_url in [video_to_comment]:
            video_url = videos[idx]
            try:
                page.goto(video_url, timeout=30000)

                # ===== NATURAL VIDEO WATCHING with stealth =====
                watch_video_naturally(page, video_duration_seconds=random.randint(10, 25))
                videos_viewed += 1

                # Comment on the video (we already checked can_comment_today above)
                if True:
                    comment = random.choice(comments_pool)
                    commented = False

                    # Natural pause before commenting
                    random_pause(1, 2)

                    # Close any popups naturally
                    page.keyboard.press('Escape')
                    random_pause(0.3, 0.7)

                    # STEP 1: Click comment icon to expand comment section
                    clicked = page.evaluate('''() => {
                        const commentIcon = document.querySelector('[data-e2e="comment-icon"]');
                        if (commentIcon) {
                            commentIcon.click();
                            return true;
                        }
                        return false;
                    }''')

                    if clicked:
                        random_pause(1.5, 2.5)  # Wait for comment section to expand

                        # STEP 2: Click on the comment input area to focus it
                        input_found = page.evaluate('''() => {
                            // Try the DraftEditor content area
                            const draftEditor = document.querySelector('.public-DraftEditor-content, [data-e2e="comment-text"] [contenteditable="true"]');
                            if (draftEditor) {
                                draftEditor.click();
                                draftEditor.focus();
                                return {success: true, method: 'DraftEditor'};
                            }

                            // Try the comment-text container
                            const commentText = document.querySelector('[data-e2e="comment-text"]');
                            if (commentText) {
                                const editable = commentText.querySelector('[contenteditable="true"]');
                                if (editable) {
                                    editable.click();
                                    editable.focus();
                                    return {success: true, method: 'comment-text-editable'};
                                }
                                commentText.click();
                                return {success: true, method: 'comment-text-click'};
                            }

                            // Try comment-input container
                            const commentInput = document.querySelector('[data-e2e="comment-input"]');
                            if (commentInput) {
                                const editable = commentInput.querySelector('[contenteditable="true"]');
                                if (editable) {
                                    editable.click();
                                    editable.focus();
                                    return {success: true, method: 'comment-input-editable'};
                                }
                            }

                            return {success: false};
                        }''')

                        if input_found.get('success'):
                            random_pause(0.3, 0.8)

                            # ===== NATURAL TYPING with random delays =====
                            for char in comment:
                                page.keyboard.type(char)
                                time.sleep(random.uniform(0.05, 0.15))  # Human typing speed
                            random_pause(0.8, 1.5)

                            # STEP 3: Click post button
                            posted = page.evaluate('''() => {
                                const postBtn = document.querySelector('[data-e2e="comment-post"]');
                                if (postBtn) {
                                    postBtn.click();
                                    return {success: true};
                                }
                                return {success: false};
                            }''')

                            if not posted.get('success'):
                                page.keyboard.press('Enter')

                            time.sleep(3)

                            # Verify comment was actually posted by checking for our comment text
                            verify_result = page.evaluate('''(commentText) => {
                                const comments = document.querySelectorAll('[data-e2e="comment-item"], [class*="CommentItem"], [class*="comment-text"]');
                                for (const c of comments) {
                                    if (c.textContent.includes(commentText.substring(0, 20))) {
                                        return {verified: true};
                                    }
                                }
                                // Also check if there's an error message
                                const error = document.querySelector('[class*="error"], [class*="failed"], [class*="blocked"]');
                                if (error && error.textContent) {
                                    return {verified: false, error: error.textContent.substring(0, 50)};
                                }
                                return {verified: false};
                            }''', comment)

                            if verify_result.get('verified'):
                                print(f'    ✓ Commented: "{comment}"', flush=True)
                                commented = True
                                comments_made += 1

                                # Save this video as commented for THIS browser
                                save_commented_video(video_url, browser_name)

                                # Record comment for daily limit tracking
                                record_comment(browser_name)

                                # Record that we commented on this target account today
                                record_target_comment(browser_name, account)

                                # Record for weekly quota (2 videos per target per week)
                                record_weekly_target_comment(browser_name, account)
                            else:
                                error_msg = verify_result.get('error', 'Comment may not have posted')
                                print(f'    ⚠ Comment not verified: "{comment[:30]}..." - {error_msg}', flush=True)
                                # Take debug screenshot
                                import os as _os
                                debug_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), f'debug_{browser_name}_comment_failed.png')
                                page.screenshot(path=debug_path)
                                # Don't count as success
                                commented = False
                        else:
                            print(f'    ✗ Could not find comment input on video {idx+1}', flush=True)
                    else:
                        print(f'    ✗ Could not click comment icon on video {idx+1}', flush=True)

                    time.sleep(random.randint(2, 5))

            except Exception as e:
                print(f'    Video {idx+1} error: {str(e)[:40]}', flush=True)

        follow_status = f', followed @{account}' if followed else ''
        result_msg = f'    Viewed {videos_viewed} video, made {comments_made} comment{follow_status}' if videos_viewed == 1 else f'    Viewed {videos_viewed} videos, made {comments_made} comments{follow_status}'
        print(result_msg, flush=True)
        return videos_viewed, comments_made

    except Exception as e:
        print(f'    Profile error: {str(e)[:50]}', flush=True)
        return videos_viewed, comments_made

def get_all_browsers():
    """Get ALL browsers from AdsPower (paginated)"""
    browsers = []
    page_num = 1
    page_size = 100

    while True:
        try:
            for attempt in range(3):
                resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list', params={
                    'page': page_num,
                    'page_size': page_size
                }, timeout=30)
                data = resp.json()

                if data.get('code') == 0:
                    break
                elif 'Too many' in str(data.get('msg', '')):
                    print(f'  Rate limited, waiting...')
                    time.sleep(3)
                else:
                    break

            if data.get('code') != 0:
                break

            page_list = data.get('data', {}).get('list', [])
            if not page_list:
                break

            browsers.extend(page_list)
            print(f'  Loaded page {page_num}: {len(page_list)} browsers (total: {len(browsers)})')

            if len(page_list) < page_size:
                break

            page_num += 1
            time.sleep(1)  # Longer delay between pages

        except Exception as e:
            print(f'Error loading browsers: {e}')
            break

    return browsers

def process_browser(browser, browser_idx, total_browsers):
    """Process a single browser through all target accounts"""
    user_id = browser['user_id']
    browser_name = browser['name']

    print(f'\n{"=" * 60}', flush=True)
    print(f'[{browser_idx+1}/{total_browsers}] {browser_name}', flush=True)
    print(f'KEEP_OPEN_MODE = {KEEP_OPEN_MODE}', flush=True)
    print(f'{"=" * 60}', flush=True)

    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'  Failed to open browser', flush=True)
        return {'success': False, 'videos': 0, 'comments': 0}

    print(f'  ✓ Browser opened successfully', flush=True)
    print(f'  WebSocket URL: {ws_url[:50]}...', flush=True)

    # KEEP OPEN MODE - Just open browsers without connecting/automating
    if KEEP_OPEN_MODE:
        print(f'', flush=True)
        print(f'  *** KEEP_OPEN_MODE ACTIVE ***', flush=True)
        print(f'  Browser will stay open (no automation)', flush=True)
        print(f'  Returning without Playwright connection', flush=True)
        print(f'', flush=True)
        time.sleep(2)  # Small delay to ensure AdsPower registers the open
        return {'success': True, 'videos': 0, 'comments': 0}

    # Give browser time to fully initialize before connecting
    print(f'  Waiting for initialization...', flush=True)
    time.sleep(3)

    browser_videos = 0
    browser_comments = 0

    try:
        # Don't use 'with' statement - it auto-closes browsers when exiting the block
        # Store in global list to prevent garbage collection
        print(f'  Connecting via CDP...', flush=True)
        p = sync_playwright().start()
        PLAYWRIGHT_INSTANCES.append(p)  # Keep reference to prevent auto-close

        browser_conn = p.chromium.connect_over_cdp(ws_url)
        print(f'  Connected! Browser will stay open.', flush=True)
        context = browser_conn.contexts[0]

        # Close ALL extra tabs first - keep only 1 tab
        if len(context.pages) > 1:
            print(f'    Closing {len(context.pages) - 1} extra tabs...', flush=True)
            # Keep first tab, close all others
            for extra_page in context.pages[1:]:
                try:
                    extra_page.close()
                except:
                    pass

        page = context.pages[0] if context.pages else context.new_page()

        # ===== INJECT STEALTH MODE - Hide CDP/automation detection =====
        inject_stealth(page)

        # CHECK LOGIN STATUS FIRST
        print(f'  Checking login status...', flush=True)
        is_logged_in, username = check_login_status(page)

        if not is_logged_in:
            print(f'  ⚠ {browser_name} NOT logged in - skipping (manual signup required)', flush=True)
            # Don't auto-signup - user will do manual phone signup
            # Browser stays open - Playwright instance stored in global list
            return {'success': False, 'videos': 0, 'comments': 0, 'skipped': True}
        else:
            print(f'  ✓ {browser_name} logged in as @{username}', flush=True)
            # Sync existing login to Supabase history
            sync_account_to_supabase(browser_name, username, account_type='login')

        # Process ALL target accounts with this browser
        for acc_idx, account in enumerate(TARGET_ACCOUNTS):
            print(f'  [{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}', flush=True)

            videos, comments = view_and_comment_on_profile(page, account, browser_name, username)
            browser_videos += videos
            browser_comments += comments

            # Update stats for this target account (includes tiktok_username for history)
            update_account_stats(account, videos, comments, browser_name, username)

            # Natural pause between accounts
            if acc_idx < len(TARGET_ACCOUNTS) - 1:
                random_pause(5, 23)

        # DON'T close browser_conn or playwright - they're stored in PLAYWRIGHT_INSTANCES
        # browser_conn.close()
        # p.stop()

    except Exception as e:
        print(f'  Browser error: {e}', flush=True)
        # Don't close browser on error - leave it open for debugging
        # Playwright instance is stored in global list
        return {'success': False, 'videos': browser_videos, 'comments': browser_comments}

    # Don't close browser after processing - leave it open
    print(f'  {browser_name} done: {browser_videos} videos viewed, {browser_comments} comments', flush=True)

    # Sync account to Supabase with updated last_commented if any comments were made
    if browser_comments > 0 and username:
        sync_account_to_supabase(browser_name, username)

    return {'success': True, 'videos': browser_videos, 'comments': browser_comments}

def main():
    print('=' * 60)
    print('  Target Account Commenter - ALL BROWSERS')
    print('=' * 60)
    print(f'\nTarget accounts: {len(TARGET_ACCOUNTS)}')
    for acc in TARGET_ACCOUNTS:
        print(f'  - @{acc}')
    print(f'\nSettings:')
    print(f'  - Comments per account: {COMMENTS_PER_ACCOUNT}')
    print(f'  - Likes per account: {LIKES_PER_ACCOUNT}')
    print(f'  - Skip viewing: {not VIEW_ALL_VIDEOS}')
    print(f'  - Parallel browsers: {PARALLEL_BROWSERS}')
    print()

    # Get ALL browsers
    print('Loading all browsers from AdsPower...')
    browsers = get_all_browsers()
    if not browsers:
        print('No browsers found in AdsPower!')
        return

    # Filter browsers by serial number (starting from 23 = tt1)
    browsers = [b for b in browsers if int(b.get('serial_number', 0)) >= 23]
    print(f'Filtered to browsers with serial numbers 23+: {len(browsers)} browsers')

    # Sort by name for consistent ordering
    browsers.sort(key=lambda x: int(re.search(r'\d+', x.get('name', '0')).group()) if re.search(r'\d+', x.get('name', '0')) else 0)

    print(f'Found {len(browsers)} browsers')
    print(f'\nTotal work: {len(browsers)} browsers x {len(TARGET_ACCOUNTS)} accounts = {len(browsers) * len(TARGET_ACCOUNTS)} profile visits')
    print(f'Expected comments: ~{len(browsers) * len(TARGET_ACCOUNTS) * COMMENTS_PER_ACCOUNT}')
    print()

    total_videos_viewed = 0
    total_comments = 0
    browsers_completed = 0
    browsers_failed = 0

    # Process browsers in batches - wait for entire batch to complete before starting next
    batch_size = PARALLEL_BROWSERS
    for batch_start in range(0, len(browsers), batch_size):
        batch_browsers = browsers[batch_start:batch_start + batch_size]

        print(f'\n--- Processing batch {batch_start//batch_size + 1} ({len(batch_browsers)} browsers) ---', flush=True)

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit browsers in this batch only
            future_to_browser = {}
            for idx_in_batch, browser in enumerate(batch_browsers):
                global_idx = batch_start + idx_in_batch
                browser_name = browser.get('name', f'browser_{global_idx}')

                # Skip browsers that have already met daily quota
                if not can_comment_today(browser_name):
                    today_activity = get_today_activity(browser_name)
                    print(f'\n[{global_idx + 1}/{len(browsers)}] {browser_name} - SKIPPED (daily quota met: {today_activity["comments"]}/{NEW_ACCOUNT_DAILY_COMMENTS} comments)', flush=True)
                    browsers_completed += 1
                    continue

                # Skip browsers that have reached weekly quota for ALL target accounts
                if has_reached_weekly_quota_all_targets(browser_name):
                    print(f'\n[{global_idx + 1}/{len(browsers)}] {browser_name} - SKIPPED (weekly quota {WEEKLY_VIDEOS_PER_ACCOUNT}/{WEEKLY_VIDEOS_PER_ACCOUNT} reached for all {len(TARGET_ACCOUNTS)} targets)', flush=True)
                    browsers_completed += 1
                    continue

                future = executor.submit(process_browser, browser, global_idx, len(browsers))
                future_to_browser[future] = browser

            # Wait for all browsers in batch to complete
            for future in as_completed(future_to_browser):
                browser = future_to_browser[future]
                try:
                    result = future.result()
                    total_videos_viewed += result['videos']
                    total_comments += result['comments']
                    if result['success']:
                        browsers_completed += 1
                    else:
                        browsers_failed += 1
                except Exception as e:
                    print(f'  Error processing browser {browser["name"]}: {e}', flush=True)
                    browsers_failed += 1

        # Batch complete
        completed = browsers_completed + browsers_failed
        print(f'\n✓ Batch complete. Progress: {completed}/{len(browsers)} browsers, {total_comments} total comments', flush=True)

        # Wait before starting next batch
        if batch_start + batch_size < len(browsers):
            print(f'Waiting 5 seconds before next batch...', flush=True)
            time.sleep(5)

    # Final Summary
    print(f'\n{"=" * 60}')
    print('  FINAL SUMMARY')
    print(f'{"=" * 60}')
    print(f'Browsers completed: {browsers_completed}')
    print(f'Browsers failed: {browsers_failed}')
    print(f'Total videos viewed: {total_videos_viewed}')
    print(f'Total comments made: {total_comments}')
    print(f'{"=" * 60}')

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1].startswith('--parallel='):
        try:
            PARALLEL_BROWSERS = int(sys.argv[1].split('=')[1])
            PARALLEL_BROWSERS = max(1, min(10, PARALLEL_BROWSERS))  # Clamp between 1 and 10
        except:
            pass
    main()
