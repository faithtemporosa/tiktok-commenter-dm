#!/usr/bin/env python3
"""
View target accounts - VIEW ONLY mode (no commenting)
For new accounts (first 3 days): only scroll and view videos (no commenting or following)
For older accounts: view videos and can follow (no commenting)
Auto-signup for logged out browsers starting from tt3

Usage: python3 targeted_accounts_view.py
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
from datetime import datetime, timedelta

ADSPOWER_API = 'http://local.adspower.net:50325'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'
TARGET_STATS_PATH = 'target_accounts_view_stats.json'
ACCOUNT_CREATION_DATES_PATH = 'account_creation_dates.json'
DAILY_ACTIVITY_PATH = 'daily_activity_tracker.json'

# New account limits - first 3 days is view-only
VIEW_ONLY_DAYS = 3  # First 3 days: only view, no commenting or following
MAX_VIDEOS_TO_VIEW = 10  # Max videos to view per target account
PARALLEL_BROWSERS = 3

# Target accounts to view
TARGET_ACCOUNTS = [
    'flockboynation',
    'happyandyaya',
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]

# ============ UTILITY FUNCTIONS ============

def load_account_creation_dates():
    """Load account creation dates"""
    try:
        with open(ACCOUNT_CREATION_DATES_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_account_creation_date(browser_name):
    """Save when an account was created"""
    dates = load_account_creation_dates()
    if browser_name not in dates:
        dates[browser_name] = datetime.now().strftime('%Y-%m-%d')
        with open(ACCOUNT_CREATION_DATES_PATH, 'w') as f:
            json.dump(dates, f, indent=2)

def get_account_age_days(browser_name):
    """Get how many days old an account is. Returns None if creation date unknown."""
    dates = load_account_creation_dates()
    if browser_name not in dates:
        return None

    creation_date = datetime.strptime(dates[browser_name], '%Y-%m-%d')
    days_old = (datetime.now() - creation_date).days
    return days_old

def is_view_only_account(browser_name):
    """Check if account is in view-only period (first VIEW_ONLY_DAYS days)"""
    days_old = get_account_age_days(browser_name)
    if days_old is None:
        return False  # Unknown age, allow normal behavior
    return days_old <= VIEW_ONLY_DAYS

def load_daily_activity():
    """Load daily activity tracker"""
    try:
        with open(DAILY_ACTIVITY_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def record_view(browser_name):
    """Record a video view action for today"""
    today = datetime.now().strftime('%Y-%m-%d')
    activity = load_daily_activity()

    if browser_name not in activity:
        activity[browser_name] = {}

    if today not in activity[browser_name]:
        activity[browser_name][today] = {'follows': 0, 'comments': 0, 'views': 0}

    if 'views' not in activity[browser_name][today]:
        activity[browser_name][today]['views'] = 0

    activity[browser_name][today]['views'] += 1

    with open(DAILY_ACTIVITY_PATH, 'w') as f:
        json.dump(activity, f, indent=2)

def get_browser_list():
    """Get list of browsers from AdsPower"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=100', timeout=30)
    return resp.json().get('data', {}).get('list', [])

def get_all_browsers():
    """Get all browsers from AdsPower (handles pagination)"""
    all_browsers = []
    page = 1
    while True:
        resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100', timeout=30)
        data = resp.json().get('data', {})
        browsers = data.get('list', [])
        if not browsers:
            break
        all_browsers.extend(browsers)
        page += 1
        if page > 20:  # Safety limit
            break
    return all_browsers

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
                    print(f"    ✓ Found code in subject: {code_match.group(1)}")
                    return code_match.group(1)

                # Try to find code in body
                body = ''
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if part.get('mimeType') == 'text/html':
                            import base64
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                        elif part.get('mimeType') == 'text/plain':
                            import base64
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'body' in msg['payload'] and msg['payload']['body'].get('data'):
                    import base64
                    body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

                if body:
                    code_match = re.search(r'(\d{6})', body)
                    if code_match:
                        print(f"    ✓ Found code in body: {code_match.group(1)}")
                        return code_match.group(1)

            if attempt < max_attempts - 1:
                time.sleep(3)

        print(f"    No verification code found after {max_attempts} attempts")
        return None
    except Exception as e:
        print(f"    Gmail error: {e}")
        return None

def check_login_status(page):
    """Check if user is logged in to TikTok. Returns (is_logged_in, username)"""
    try:
        page.goto('https://www.tiktok.com/profile', timeout=15000)
        time.sleep(2)

        # If URL contains /@username, user is logged in
        if '/@' in page.url:
            username = page.url.split('/@')[1].split('?')[0].split('/')[0]
            return True, username

        return False, None
    except:
        return False, None

def auto_signup(page, browser_name):
    """Automatically sign up a TikTok account. Returns (success, username)"""
    print(f'    [{browser_name}] Starting auto-signup...', flush=True)

    try:
        # Generate credentials
        email = generate_email()
        password = generate_password()

        print(f'    [{browser_name}] Email: {email}', flush=True)
        print(f'    [{browser_name}] Password: {password}', flush=True)

        # Go to TikTok login page
        page.goto('https://www.tiktok.com/login/phone-or-email/email', timeout=30000)
        time.sleep(3)

        # Fill email and password
        page.locator('input[name="email"], input[type="text"]').first.fill(email)
        time.sleep(1)
        page.locator('input[name="password"], input[type="password"]').first.fill(password)
        time.sleep(1)

        # Take screenshot before clicking send code
        page.screenshot(path=f'downloads/before_send_code_{browser_name}.png')

        # Click send code - click twice until "Resend code" appears
        try:
            for attempt in range(2):
                send_btn = page.locator('button:has-text("Send code"), button:has-text("Envoyer")').first
                if send_btn.is_visible(timeout=3000):
                    send_btn.click()
                    print(f'    [{browser_name}] Send code button clicked (attempt {attempt + 1})', flush=True)
                    time.sleep(3)
                else:
                    break

            # Verify code was sent by looking for "Resend code" button
            resend_visible = False
            try:
                resend_btn = page.locator('button:has-text("Resend"), button:has-text("Resend code"), button:has-text("Renvoyer")').first
                if resend_btn.is_visible(timeout=3000):
                    print(f'    [{browser_name}] ✓ Code sent successfully (Resend button visible)', flush=True)
                    resend_visible = True
            except:
                print(f'    [{browser_name}] ⚠ Could not verify if code was sent - continuing', flush=True)

            # Take screenshot after clicking send code
            page.screenshot(path=f'downloads/after_send_code_{browser_name}.png')
        except Exception as send_err:
            print(f'    [{browser_name}] Send code error: {send_err}', flush=True)
            page.screenshot(path=f'downloads/send_code_error_{browser_name}.png')

        # Fetch verification code from Gmail
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
        time.sleep(8)

        # Take screenshot after code submission to see current state
        page.screenshot(path=f'downloads/after_code_submit_{browser_name}.png')

        # Set username - TikTok prompts for username after email verification
        try:
            # Generate username from email (e.g., forestcore740@... -> forestcore740)
            username_base = email.split('@')[0]
            print(f'    [{browser_name}] Looking for username input field...', flush=True)

            # Wait for username input field to appear - try multiple times
            username_filled = False
            for attempt in range(3):
                try:
                    # Look for username input field with longer timeout
                    username_input = page.locator('input[name="uniqueId"], input[placeholder*="username"], input[placeholder*="Username"], input[placeholder*="nom"], input[data-e2e="username-input"]').first

                    # Wait for it to be visible and editable
                    username_input.wait_for(state='visible', timeout=10000)
                    time.sleep(2)

                    # Clear and fill the username
                    username_input.click()
                    time.sleep(0.5)
                    username_input.fill('')
                    time.sleep(0.5)
                    username_input.fill(username_base)
                    time.sleep(1)

                    print(f'    [{browser_name}] ✓ Username set to: {username_base}', flush=True)
                    username_filled = True

                    # Take screenshot after filling username
                    page.screenshot(path=f'downloads/after_username_{browser_name}.png')

                    # Click next/submit button to continue
                    page.locator('button[type="submit"], button:has-text("Next"), button:has-text("Suivant"), button:has-text("Sign up"), button:has-text("S\'inscrire")').first.click(timeout=10000)
                    time.sleep(3)
                    break
                except Exception as retry_err:
                    if attempt < 2:
                        print(f'    [{browser_name}] Username attempt {attempt + 1} failed, retrying...', flush=True)
                        time.sleep(3)
                    else:
                        raise retry_err

            if not username_filled:
                print(f'    [{browser_name}] No username input found after 3 attempts, may be auto-assigned', flush=True)

        except Exception as username_err:
            print(f'    [{browser_name}] Username setup error: {str(username_err)[:100]}', flush=True)
            # Take screenshot on error
            page.screenshot(path=f'downloads/username_error_{browser_name}.png')
            print(f'    [{browser_name}] Screenshot saved to username_error_{browser_name}.png', flush=True)

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

            # Save credentials to a file
            try:
                creds_file = 'tiktok_accounts_credentials.json'
                try:
                    with open(creds_file, 'r') as f:
                        creds = json.load(f)
                except:
                    creds = {}

                creds[browser_name] = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                with open(creds_file, 'w') as f:
                    json.dump(creds, f, indent=2)
                print(f'    [{browser_name}] ✓ Credentials saved to {creds_file}', flush=True)
            except Exception as creds_err:
                print(f'    [{browser_name}] ⚠ Failed to save credentials: {creds_err}', flush=True)

            # Save account creation date
            save_account_creation_date(browser_name)

            return True, username
        else:
            print(f'    [{browser_name}] ✗ Signup failed - not logged in', flush=True)
            return False, None

    except Exception as e:
        print(f'    [{browser_name}] Signup error: {e}', flush=True)
        return False, None

# ============ VIEWING FUNCTIONS ============

def view_profile_videos(page, account, browser_name):
    """Visit a profile and view videos (no commenting)"""
    print(f'    Visiting @{account}...', flush=True)

    videos_viewed = 0
    account_age_days = get_account_age_days(browser_name)
    is_view_only = is_view_only_account(browser_name)

    if is_view_only:
        print(f'    Account is {account_age_days} days old - VIEW ONLY mode (no following)', flush=True)
    elif account_age_days is not None:
        print(f'    Account is {account_age_days} days old - normal viewing mode', flush=True)

    try:
        page.goto(f'https://www.tiktok.com/@{account}', timeout=30000)
        time.sleep(4)

        # Scroll to load more videos
        for _ in range(3):
            page.evaluate('window.scrollBy(0, 1000)')
            time.sleep(1)

        # Get video links from profile
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
            return 0

        # Limit to MAX_VIDEOS_TO_VIEW videos
        videos_to_view = videos[:MAX_VIDEOS_TO_VIEW]
        print(f'    Found {len(videos)} videos, will view {len(videos_to_view)}', flush=True)

        # View videos
        for idx, video_url in enumerate(videos_to_view):
            try:
                page.goto(video_url, timeout=30000)
                view_duration = random.randint(5, 15)  # Watch for 5-15 seconds

                # Scroll down a bit while viewing (simulate real viewing behavior)
                time.sleep(view_duration / 2)
                page.evaluate('window.scrollBy(0, 200)')
                time.sleep(view_duration / 2)

                videos_viewed += 1
                record_view(browser_name)
                print(f'    ✓ Viewed video {idx + 1}/{len(videos_to_view)}', flush=True)

                # Wait between videos
                if idx < len(videos_to_view) - 1:
                    time.sleep(random.randint(2, 5))

            except Exception as video_err:
                print(f'    ⚠ Failed to view video {idx + 1}: {str(video_err)[:50]}', flush=True)
                continue

        return videos_viewed

    except Exception as e:
        print(f'    Error viewing @{account}: {str(e)[:100]}', flush=True)
        return videos_viewed

def update_account_stats(account, videos_viewed, browser_name):
    """Update statistics for a target account"""
    try:
        with open(TARGET_STATS_PATH, 'r') as f:
            stats = json.load(f)
    except:
        stats = {}

    if account not in stats:
        stats[account] = {
            'total_views': 0,
            'browsers': [],
            'last_viewed': None
        }

    stats[account]['total_views'] += videos_viewed
    if browser_name not in stats[account]['browsers']:
        stats[account]['browsers'].append(browser_name)
    stats[account]['last_viewed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(TARGET_STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)

# ============ MAIN PROCESSING ============

def process_browser(browser, browser_idx, total_browsers):
    """Process one browser - view target accounts"""
    user_id = browser.get('user_id')
    browser_name = browser.get('name', f'browser_{user_id}')

    print(f'\n[{browser_idx+1}/{total_browsers}] {browser_name} - Processing {len(TARGET_ACCOUNTS)} accounts', flush=True)

    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'  Failed to open browser', flush=True)
        return {'success': False, 'videos': 0}

    browser_videos = 0

    try:
        with sync_playwright() as p:
            browser_conn = p.chromium.connect_over_cdp(ws_url)
            context = browser_conn.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # CHECK LOGIN STATUS FIRST
            print(f'  Checking login status...', flush=True)
            is_logged_in, username = check_login_status(page)

            if not is_logged_in:
                print(f'  Not logged in - attempting auto-signup...', flush=True)
                signup_success, username = auto_signup(page, browser_name)

                if not signup_success:
                    print(f'  ✗ Auto-signup failed for {browser_name}', flush=True)
                    browser_conn.close()
                    close_browser(user_id)
                    return {'success': False, 'videos': 0}

                print(f'  ✓ Auto-signup successful! @{username}', flush=True)
            else:
                print(f'  ✓ Logged in as @{username}', flush=True)

            # Process each target account
            for acc_idx, account in enumerate(TARGET_ACCOUNTS):
                print(f'  [{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}', flush=True)

                videos = view_profile_videos(page, account, browser_name)
                browser_videos += videos

                # Update stats for this target account
                update_account_stats(account, videos, browser_name)

                # Wait between accounts
                if acc_idx < len(TARGET_ACCOUNTS) - 1:
                    time.sleep(random.randint(5, 15))

            browser_conn.close()

    except Exception as e:
        print(f'  Browser error: {e}', flush=True)
        close_browser(user_id)
        return {'success': False, 'videos': browser_videos}

    close_browser(user_id)
    print(f'  {browser_name} done: {browser_videos} videos viewed', flush=True)

    return {'success': True, 'videos': browser_videos}

def main():
    print('=' * 60)
    print('  Target Accounts Viewer - VIEW ONLY MODE')
    print('=' * 60)
    print(f'\nTarget accounts: {len(TARGET_ACCOUNTS)}')
    for acc in TARGET_ACCOUNTS:
        print(f'  - @{acc}')
    print(f'\nSettings:')
    print(f'  - Max videos to view per account: {MAX_VIDEOS_TO_VIEW}')
    print(f'  - View-only period for new accounts: {VIEW_ONLY_DAYS} days')
    print(f'  - Parallel browsers: {PARALLEL_BROWSERS}')
    print(f'  - Starting from: tt3')
    print()

    # Get ALL browsers
    print('Loading all browsers from AdsPower...')
    browsers = get_all_browsers()
    if not browsers:
        print('No browsers found in AdsPower!')
        return

    # Filter browsers: serial number 500-806 AND starting from tt3
    # Extract number from browser name (e.g., "tt3" -> 3, "tt42" -> 42)
    def get_browser_number(browser):
        match = re.search(r'tt(\d+)', browser.get('name', ''))
        return int(match.group(1)) if match else 0

    # Filter by serial number and starting from tt3
    browsers = [b for b in browsers
                if 500 <= int(b.get('serial_number', 0)) <= 806
                and get_browser_number(b) >= 3]

    print(f'Filtered to browsers starting from tt3 (serial 500-806): {len(browsers)} browsers')

    # Sort by browser number for consistent ordering
    browsers.sort(key=get_browser_number)

    # Show first few browsers
    print(f'\nFirst 5 browsers to process:')
    for b in browsers[:5]:
        print(f'  - {b.get("name")} (serial {b.get("serial_number")})')

    print(f'\nTotal work: {len(browsers)} browsers x {len(TARGET_ACCOUNTS)} accounts = {len(browsers) * len(TARGET_ACCOUNTS)} profile visits')
    print(f'Expected views: ~{len(browsers) * len(TARGET_ACCOUNTS) * MAX_VIDEOS_TO_VIEW}')
    print()

    total_videos_viewed = 0
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
                if result['success']:
                    browsers_completed += 1
                else:
                    browsers_failed += 1
                total_videos_viewed += result['videos']
            except Exception as e:
                browsers_failed += 1
                print(f'Error processing browser: {e}')

    # Final summary
    print('\n' + '=' * 60)
    print('  FINAL SUMMARY')
    print('=' * 60)
    print(f'Browsers completed: {browsers_completed}')
    print(f'Browsers failed: {browsers_failed}')
    print(f'Total videos viewed: {total_videos_viewed}')
    print()

if __name__ == '__main__':
    main()
