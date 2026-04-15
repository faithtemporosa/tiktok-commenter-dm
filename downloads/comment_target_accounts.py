#!/usr/bin/env python3
"""
Comment on specific target accounts - Separate from main commenter
Comment on latest 1 video per account (likes disabled - TikTok blocks them)
Each browser can only comment on each target account ONCE per day
Auto-signup for logged out browsers

Usage: python3 comment_target_accounts.py
"""

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

# Comment functions are now inline - no need to import from main commenter

ADSPOWER_API = 'http://local.adspower.net:50325'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'
TARGET_STATS_PATH = 'target_accounts_stats.json'
COMMENTED_VIDEOS_PATH = 'target_commented_videos.json'
ACCOUNT_CREATION_DATES_PATH = 'account_creation_dates.json'
DAILY_ACTIVITY_PATH = 'daily_activity_tracker.json'
DAILY_TARGET_COMMENTS_PATH = 'daily_target_comments.json'  # Track comments per target per day

# New account limits
NEW_ACCOUNT_DAYS = 30  # Consider account "new" for first 30 days
NEW_ACCOUNT_DAILY_FOLLOWS = 2
NEW_ACCOUNT_DAILY_COMMENTS = 2

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

def load_commented_videos():
    """Load set of already commented video IDs"""
    try:
        with open(COMMENTED_VIDEOS_PATH, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_commented_video(video_url):
    """Save a video ID as commented"""
    video_id = normalize_video_url(video_url)
    commented = load_commented_videos()
    commented.add(video_id)
    # Keep only last 10000 videos to prevent file from growing too large
    if len(commented) > 10000:
        commented = set(list(commented)[-10000:])
    with open(COMMENTED_VIDEOS_PATH, 'w') as f:
        json.dump(list(commented), f)

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

def load_target_stats():
    """Load existing target account stats from JSON"""
    try:
        with open(TARGET_STATS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_target_stats(stats):
    """Save target account stats to JSON"""
    with open(TARGET_STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)

def update_account_stats(account, videos_viewed, comments_made, browser_name):
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

    # Keep last 100 sessions
    stats[account]['sessions'].append({
        'browser': browser_name,
        'views': videos_viewed,
        'comments': comments_made,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    stats[account]['sessions'] = stats[account]['sessions'][-100:]

    save_target_stats(stats)

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
COMMENTS_PER_ACCOUNT = 1  # Comment on 1 video per account (latest only)
LIKES_PER_ACCOUNT = 0      # Disabled - TikTok blocks automated likes
VIEW_ALL_VIDEOS = False    # Skip viewing - just comment
PARALLEL_BROWSERS = 3      # Number of browsers to run in parallel

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

def fetch_verification_code(email, max_attempts=30):
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
    base_path = '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads'
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

        # Click "Edit profile" button
        try:
            edit_btn = page.locator('button:has-text("Edit profile")').first
            edit_btn.wait_for(state='visible', timeout=5000)
            edit_btn.click()
            time.sleep(3)
            print(f'    [{browser_name}] ✓ Edit profile opened', flush=True)
        except Exception as e:
            print(f'    [{browser_name}] ⚠ Could not open Edit profile: {str(e)[:50]}', flush=True)
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
        page.goto('https://www.tiktok.com/signup/phone-or-email/email', timeout=30000)
        time.sleep(3)

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

        # Enter email
        page.locator('input[name="email"]').fill(email)
        time.sleep(0.5)

        # Enter password
        page.locator('input[type="password"]').fill(password)
        time.sleep(0.5)

        # Click send code - click twice with proper waiting
        try:
            # First click
            send_btn = page.locator('button:has-text("Send code"), button:has-text("Envoyer")').first
            if send_btn.is_visible(timeout=3000):
                send_btn.click()
                print(f'    [{browser_name}] Send code clicked (1st time)', flush=True)
                time.sleep(5)  # Wait longer after first click

            # Second click (TikTok requires two clicks)
            send_btn = page.locator('button:has-text("Send code"), button:has-text("Envoyer")').first
            if send_btn.is_visible(timeout=3000):
                send_btn.click()
                print(f'    [{browser_name}] Send code clicked (2nd time)', flush=True)
                time.sleep(8)  # Wait longer after second click for UI to update

            # Verify code was sent by looking for "Resend code" button
            resend_visible = False
            try:
                # Try multiple selectors for Resend button
                resend_selectors = [
                    'button:has-text("Resend code")',
                    'button:has-text("Resend")',
                    'button:has-text("Renvoyer")',
                    'div:has-text("Resend code")',
                    '[data-e2e*="resend"]'
                ]

                for selector in resend_selectors:
                    try:
                        resend_btn = page.locator(selector).first
                        if resend_btn.is_visible(timeout=2000):
                            print(f'    [{browser_name}] ✓ Code sent (Resend button found)', flush=True)
                            resend_visible = True
                            break
                    except:
                        continue

                if not resend_visible:
                    print(f'    [{browser_name}] ⚠ Resend button not visible - continuing anyway', flush=True)
            except:
                print(f'    [{browser_name}] ⚠ Could not verify if code was sent - continuing', flush=True)

            # Take screenshot to verify current state
            screenshot_path = f'/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/signup_{browser_name}_after_send.png'
            page.screenshot(path=screenshot_path)
            print(f'    [{browser_name}] Screenshot saved: {screenshot_path}', flush=True)
            time.sleep(1)
        except Exception as e:
            print(f'    [{browser_name}] Error clicking send code: {str(e)[:60]}', flush=True)
            return False, None

        # Get verification code
        code = fetch_verification_code(email)
        if not code:
            print(f'    [{browser_name}] No verification code received', flush=True)
            return False, None

        print(f'    [{browser_name}] Got code: {code}', flush=True)

        # Enter code
        page.locator('input[placeholder*="code"], input[name="code"]').fill(code)
        time.sleep(1)

        # Submit
        page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Suivant")').click(timeout=10000)
        print(f'    [{browser_name}] Verification code submitted, waiting for username page...', flush=True)

        # Wait longer for page to navigate after code submission
        print(f'    [{browser_name}] Waiting for page to load...', flush=True)
        time.sleep(10)

        # Set username - TikTok prompts for username after email verification
        # Generate username from email (e.g., forestcore740@... -> forestcore740)
        username_base = email.split('@')[0]
        username_set = False

        try:
            print(f'    [{browser_name}] Looking for username input field...', flush=True)

            # Try to find username input with multiple selectors
            username_input = page.locator('input[name="uniqueId"], input[placeholder*="username"], input[placeholder*="Username"], input[data-e2e="username-input"]').first

            if username_input.is_visible(timeout=5000):
                username_input.click()
                time.sleep(1)
                username_input.fill(username_base)
                time.sleep(1)
                print(f'    [{browser_name}] ✓ Username set to: {username_base}', flush=True)
                username_set = True

                # Click next/submit button
                try:
                    page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Sign up")').first.click(timeout=5000)
                    time.sleep(3)
                except:
                    # Maybe no next button, already on profile
                    pass
            else:
                print(f'    [{browser_name}] No username input visible - TikTok may auto-assign', flush=True)

        except Exception as e:
            print(f'    [{browser_name}] Username setup skipped - checking if auto-assigned', flush=True)

        # Wait for signup to complete
        time.sleep(5)

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
                print(f'    [{browser_name}] ✗ Signup failed - not logged in after process', flush=True)
                return False, None

        except Exception as verify_err:
            print(f'    [{browser_name}] ✗ Signup verification error: {str(verify_err)[:100]}', flush=True)
            return False, None

    except Exception as e:
        print(f'    [{browser_name}] Signup error: {str(e)[:50]}', flush=True)
        return False, None

# ============ END AUTO-SIGNUP FUNCTIONS ============

def view_and_comment_on_profile(page, account, browser_name):
    """Visit a profile and comment on latest 1 video (once per day per target)"""
    print(f'    Visiting @{account}...', flush=True)

    # CHECK: Has this browser already commented on this target account today?
    if has_commented_on_target_today(browser_name, account):
        print(f'    ⏭  Already commented on @{account} today - skipping', flush=True)
        return 0, 0

    videos_viewed = 0
    comments_made = 0
    followed = False

    # Load already commented videos to avoid re-commenting
    already_commented = load_commented_videos()

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

        # Select latest 1 video to comment on (first video in the list)
        # TikTok videos are typically ordered with newest first
        if len(videos) == 0:
            print(f'    No videos to process on @{account}', flush=True)
            return 0, 0

        # Check if the latest video has already been commented on
        latest_video_id = normalize_video_url(videos[0])
        if latest_video_id in already_commented:
            print(f'    Latest video already commented on - skipping', flush=True)
            return 0, 0

        # Check if we can comment today (for new accounts)
        if not can_comment_today(browser_name):
            print(f'    Daily comment limit reached, will skip comments', flush=True)
            return 0, 0

        # Process ONLY the latest video (index 0)
        print(f'    Will comment on latest video', flush=True)

        # Process only the latest 1 video
        for idx in [0]:
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

                            time.sleep(2)
                            print(f'    ✓ Commented: "{comment}"', flush=True)
                            commented = True
                            comments_made += 1

                            # Save this video as commented to prevent re-commenting
                            save_commented_video(video_url)

                            # Record comment for daily limit tracking
                            record_comment(browser_name)

                            # Record that we commented on this target account today
                            record_target_comment(browser_name, account)
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

    print(f'\n[{browser_idx+1}/{total_browsers}] {browser_name} - Processing {len(TARGET_ACCOUNTS)} accounts', flush=True)

    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'  Failed to open browser', flush=True)
        return {'success': False, 'videos': 0, 'comments': 0}

    browser_videos = 0
    browser_comments = 0

    try:
        with sync_playwright() as p:
            browser_conn = p.chromium.connect_over_cdp(ws_url)
            context = browser_conn.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # ===== INJECT STEALTH MODE - Hide CDP/automation detection =====
            inject_stealth(page)

            # CHECK LOGIN STATUS FIRST
            print(f'  Checking login status...', flush=True)
            is_logged_in, username = check_login_status(page)

            if not is_logged_in:
                print(f'  ⚠ {browser_name} NOT logged in - running auto-signup...', flush=True)
                signup_success, new_username = auto_signup(page, browser_name)

                if not signup_success:
                    print(f'  ✗ Signup failed for {browser_name} - leaving browser open for manual signup', flush=True)
                    browser_conn.close()
                    # DON'T close the browser - leave it open for manual signup
                    # close_browser(user_id)
                    return {'success': False, 'videos': 0, 'comments': 0}

                username = new_username
                print(f'  ✓ {browser_name} now logged in as @{username}', flush=True)
            else:
                print(f'  ✓ {browser_name} logged in as @{username}', flush=True)

            # Process ALL target accounts with this browser
            for acc_idx, account in enumerate(TARGET_ACCOUNTS):
                print(f'  [{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}', flush=True)

                videos, comments = view_and_comment_on_profile(page, account, browser_name)
                browser_videos += videos
                browser_comments += comments

                # Update stats for this target account
                update_account_stats(account, videos, comments, browser_name)

                # Natural pause between accounts
                if acc_idx < len(TARGET_ACCOUNTS) - 1:
                    random_pause(5, 23)

            browser_conn.close()

    except Exception as e:
        print(f'  Browser error: {e}', flush=True)
        close_browser(user_id)
        return {'success': False, 'videos': browser_videos, 'comments': browser_comments}

    close_browser(user_id)
    print(f'  {browser_name} done: {browser_videos} videos viewed, {browser_comments} comments', flush=True)

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
