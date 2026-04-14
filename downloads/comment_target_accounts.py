#!/usr/bin/env python3
"""
Comment on specific target accounts - Separate from main commenter
All browsers view all videos per account, comment on 2 videos per account
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

# Comment functions are now inline - no need to import from main commenter

ADSPOWER_API = 'http://local.adspower.net:50325'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'
TARGET_STATS_PATH = 'target_accounts_stats.json'
COMMENTED_VIDEOS_PATH = 'target_commented_videos.json'

def normalize_video_url(video_url):
    """Extract just the video ID from a TikTok URL to ensure consistent tracking.
    e.g. https://www.tiktok.com/@user/video/123456?q=1 -> 123456
    """
    if '/video/' in video_url:
        # Extract video ID (the number after /video/)
        video_id = video_url.split('/video/')[1].split('?')[0].split('/')[0]
        return video_id
    return video_url

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
COMMENTS_PER_ACCOUNT = 2  # Comment on 2 videos per account
VIEW_ALL_VIDEOS = True     # View all videos before commenting
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
    """Close AdsPower browser"""
    requests.get(f'{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}')

# ============ AUTO-SIGNUP FUNCTIONS ============

# Name generators for signup
ADJECTIVES = ['swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean', 'forest',
              'digital', 'cyber', 'tech', 'smart', 'neon', 'atomic', 'vivid', 'prism',
              'flux', 'zen', 'drift', 'echo', 'nova', 'pixel', 'quantum', 'stellar']
NOUNS = ['phoenix', 'dragon', 'falcon', 'eagle', 'wolf', 'tiger', 'star', 'moon',
         'wave', 'flame', 'pixel', 'pulse', 'echo', 'spark', 'glow', 'path',
         'stream', 'verse', 'core', 'field', 'track', 'scope', 'grid', 'focus']

def generate_email():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(100, 999)
    return f"{adj}{noun}{num}@automateyourbizz.xyz"

def generate_password():
    adj = random.choice(ADJECTIVES).capitalize()
    noun = random.choice(NOUNS).capitalize()
    num = random.randint(10, 99)
    return f"{adj}{noun}.{num}"

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

        # Click send code
        try:
            send_btn = page.locator('button:has-text("Send code"), button:has-text("Envoyer")').first
            send_btn.click(timeout=10000)
            print(f'    [{browser_name}] Send code button clicked', flush=True)
            time.sleep(2)

            # Verify code was sent by looking for "Resend code" button
            try:
                resend_btn = page.locator('button:has-text("Resend"), button:has-text("Resend code"), button:has-text("Renvoyer")').first
                if resend_btn.is_visible(timeout=3000):
                    print(f'    [{browser_name}] ✓ Code sent successfully (Resend button visible)', flush=True)
                else:
                    print(f'    [{browser_name}] ⚠ Resend button not found - code may not have sent', flush=True)
            except:
                print(f'    [{browser_name}] ⚠ Could not verify if code was sent', flush=True)

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
        time.sleep(5)

        # Set username - TikTok prompts for username after email verification
        try:
            # Generate username from email (e.g., forestcore740@... -> forestcore740)
            username_base = email.split('@')[0]

            # Look for username input field
            username_input = page.locator('input[name="uniqueId"], input[placeholder*="username"], input[placeholder*="Username"]').first
            if username_input.is_visible(timeout=5000):
                username_input.fill(username_base)
                time.sleep(1)
                print(f'    [{browser_name}] Username set to: {username_base}', flush=True)

                # Click next/submit button to continue
                page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Suivant"), button:has-text("Sign up")').first.click(timeout=10000)
                time.sleep(3)
            else:
                print(f'    [{browser_name}] No username input found, may be auto-assigned', flush=True)
        except Exception as username_err:
            print(f'    [{browser_name}] Username setup: {str(username_err)[:50]}', flush=True)

        # Check if signup succeeded
        page.goto('https://www.tiktok.com/profile', timeout=15000)
        time.sleep(2)

        if '/@' in page.url:
            username = page.url.split('/@')[1].split('?')[0].split('/')[0]
            print(f'    [{browser_name}] ✓ Signup success! @{username}', flush=True)

            # Save to profile mapping
            try:
                with open(PROFILE_MAPPING_PATH, 'r') as f:
                    mapping = json.load(f)
            except:
                mapping = {}
            mapping[browser_name] = username
            with open(PROFILE_MAPPING_PATH, 'w') as f:
                json.dump(mapping, f, indent=2)

            return True, username

        return False, None

    except Exception as e:
        print(f'    [{browser_name}] Signup error: {str(e)[:50]}', flush=True)
        return False, None

# ============ END AUTO-SIGNUP FUNCTIONS ============

def view_and_comment_on_profile(page, account, browser_name):
    """Visit a profile, view ALL videos, and comment on 2 videos"""
    print(f'    Visiting @{account}...', flush=True)

    videos_viewed = 0
    comments_made = 0

    # Load already commented videos to avoid re-commenting
    already_commented = load_commented_videos()

    try:
        page.goto(f'https://www.tiktok.com/@{account}', timeout=30000)
        time.sleep(4)

        # Scroll to load more videos
        for _ in range(3):
            page.evaluate('window.scrollBy(0, 1000)')
            time.sleep(1)

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

        print(f'    Found {len(videos)} videos to view', flush=True)

        # Get niche-appropriate comments
        niche = get_niche(account)
        comments_pool = NICHE_COMMENTS.get(niche, NICHE_COMMENTS['default'])

        # Find videos we haven't commented on yet (normalize URLs to video IDs for comparison)
        uncommented_indices = [i for i, v in enumerate(videos) if normalize_video_url(v) not in already_commented]

        if uncommented_indices:
            # Select which videos to comment on (2 random ones from uncommented)
            comment_indices = set(random.sample(uncommented_indices, min(COMMENTS_PER_ACCOUNT, len(uncommented_indices))))
            print(f'    {len(uncommented_indices)} videos available for commenting (skipping {len(videos) - len(uncommented_indices)} already commented)', flush=True)
        else:
            # All videos already commented on
            comment_indices = set()
            print(f'    All {len(videos)} videos already commented on, will only view', flush=True)

        # View ALL videos, comment on selected ones
        for idx, video_url in enumerate(videos):
            try:
                page.goto(video_url, timeout=30000)
                time.sleep(random.randint(5, 23))  # Watch for a bit
                videos_viewed += 1

                # Comment only on selected videos
                if idx in comment_indices:
                    comment = random.choice(comments_pool)
                    commented = False

                    # Wait for page to fully load
                    time.sleep(3)

                    # Close any popups first
                    page.keyboard.press('Escape')
                    time.sleep(0.5)

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
                        time.sleep(2)  # Wait for comment section to expand

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
                            time.sleep(0.5)

                            # Type the comment
                            page.keyboard.type(comment, delay=random.randint(25, 50))
                            time.sleep(1)

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
                        else:
                            print(f'    ✗ Could not find comment input on video {idx+1}', flush=True)
                    else:
                        print(f'    ✗ Could not click comment icon on video {idx+1}', flush=True)

                    time.sleep(random.randint(5, 23))

            except Exception as e:
                print(f'    Video {idx+1} error: {str(e)[:40]}', flush=True)

        print(f'    Viewed {videos_viewed} videos, made {comments_made} comments', flush=True)
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

            # CHECK LOGIN STATUS FIRST
            print(f'  Checking login status...', flush=True)
            is_logged_in, username = check_login_status(page)

            if not is_logged_in:
                print(f'  ⚠ {browser_name} NOT logged in - running auto-signup...', flush=True)
                signup_success, new_username = auto_signup(page, browser_name)

                if not signup_success:
                    print(f'  ✗ Signup failed for {browser_name}, skipping...', flush=True)
                    browser_conn.close()
                    close_browser(user_id)
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

                # Wait between accounts
                if acc_idx < len(TARGET_ACCOUNTS) - 1:
                    time.sleep(random.randint(5, 23))

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
    print(f'  - View all videos per account: {VIEW_ALL_VIDEOS}')
    print(f'  - Comments per account: {COMMENTS_PER_ACCOUNT}')
    print(f'  - Parallel browsers: {PARALLEL_BROWSERS}')
    print()

    # Get ALL browsers
    print('Loading all browsers from AdsPower...')
    browsers = get_all_browsers()
    if not browsers:
        print('No browsers found in AdsPower!')
        return

    # Filter browsers by serial number (500-806)
    browsers = [b for b in browsers if 500 <= int(b.get('serial_number', 0)) <= 806]
    print(f'Filtered to browsers with serial numbers 500-806: {len(browsers)} browsers')

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

    # Process browsers in parallel
    with ThreadPoolExecutor(max_workers=PARALLEL_BROWSERS) as executor:
        # Submit all browser tasks
        future_to_browser = {}
        for idx, browser in enumerate(browsers):
            future = executor.submit(process_browser, browser, idx, len(browsers))
            future_to_browser[future] = browser

        # Collect results as they complete
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

                # Progress update
                completed = browsers_completed + browsers_failed
                if completed % 10 == 0:
                    print(f'\n  === Progress: {completed}/{len(browsers)} browsers, {total_comments} total comments ===\n', flush=True)

            except Exception as e:
                print(f'  Error processing browser {browser["name"]}: {e}', flush=True)
                browsers_failed += 1

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
