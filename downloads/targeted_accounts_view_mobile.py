#!/usr/bin/env python3
"""
View target accounts - MOBILE VERSION - VIEW ONLY mode (no commenting)
For new accounts (first 3 days): only scroll and view videos (no commenting or following)
For older accounts: view videos and can follow (no commenting)
Auto-signup for logged out browsers starting from tt3

Usage: python3 targeted_accounts_view_mobile.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import random
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

# Import ALL signup/browser functions from comment_target_accounts.py
# This ensures we use the SAME working signup process
from comment_target_accounts import (
    auto_signup,
    check_login_status,
    get_all_browsers,
    open_browser,
    close_browser,
    load_account_creation_dates,
    save_account_creation_date,
    ADSPOWER_API,
    PROFILE_MAPPING_PATH,
    ACCOUNT_CREATION_DATES_PATH,
    DAILY_ACTIVITY_PATH
)

# View-only specific settings
TARGET_STATS_PATH = 'target_accounts_view_stats_mobile.json'
VIEW_ONLY_DAYS = 3  # First 3 days: only view, no commenting or following
MAX_VIDEOS_TO_VIEW = 10  # Max videos to view per target account

# Mobile-specific settings
MOBILE_USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
]

MOBILE_VIEWPORTS = [
    {'width': 390, 'height': 844},  # iPhone 14 Pro
    {'width': 393, 'height': 852},  # iPhone 14 Pro Max
    {'width': 412, 'height': 915},  # Pixel 7
    {'width': 360, 'height': 800},  # Galaxy S21
]

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

# ============ VIEW-ONLY SPECIFIC FUNCTIONS ============

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

def setup_mobile_context(page):
    """Configure page for mobile browsing"""
    # Set mobile viewport
    viewport = random.choice(MOBILE_VIEWPORTS)
    page.set_viewport_size(viewport)

    # Set mobile user agent
    user_agent = random.choice(MOBILE_USER_AGENTS)
    page.context.set_extra_http_headers({
        'User-Agent': user_agent
    })

    print(f'    Mobile setup: {viewport["width"]}x{viewport["height"]}', flush=True)

def mobile_scroll(page, distance=500):
    """Simulate mobile scrolling with touch gestures"""
    # Simulate touch scroll
    page.evaluate(f'''() => {{
        window.scrollBy({{
            top: {distance},
            behavior: 'smooth'
        }});
    }}''')
    time.sleep(random.uniform(0.5, 1.5))

def view_profile_videos_mobile(page, account, browser_name):
    """Visit a profile and view videos (no commenting) - MOBILE VERSION"""
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

        # Mobile scrolling to load more videos
        for _ in range(3):
            mobile_scroll(page, 800)
            time.sleep(1.5)

        # Get video links from profile (mobile selectors)
        videos = page.evaluate('''() => {
            const links = [];
            // Mobile TikTok uses different selectors
            document.querySelectorAll('a[href*="/video/"]').forEach(a => {
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
                view_duration = random.randint(8, 20)  # Watch for 8-20 seconds (mobile users watch longer)

                # Simulate mobile viewing behavior
                # Watch first half
                time.sleep(view_duration / 3)

                # Small scroll (like reading comments)
                mobile_scroll(page, 150)
                time.sleep(view_duration / 3)

                # Scroll back up
                mobile_scroll(page, -100)
                time.sleep(view_duration / 3)

                videos_viewed += 1
                record_view(browser_name)
                print(f'    ✓ Viewed video {idx + 1}/{len(videos_to_view)} (mobile)', flush=True)

                # Wait between videos (slightly longer on mobile)
                if idx < len(videos_to_view) - 1:
                    time.sleep(random.randint(3, 7))

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

def process_browser(browser, browser_idx, total_browsers):
    """Process one browser - view target accounts - MOBILE VERSION"""
    user_id = browser.get('user_id')
    browser_name = browser.get('name', f'browser_{user_id}')

    print(f'\n[{browser_idx+1}/{total_browsers}] {browser_name} - Processing {len(TARGET_ACCOUNTS)} accounts (MOBILE)', flush=True)

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

            # SETUP MOBILE MODE
            setup_mobile_context(page)

            # CHECK LOGIN STATUS FIRST
            print(f'  Checking login status...', flush=True)
            is_logged_in, username = check_login_status(page)

            if not is_logged_in:
                print(f'  Not logged in - attempting auto-signup...', flush=True)
                signup_success, username = auto_signup(page, browser_name)

                if not signup_success:
                    print(f'  ✗ Auto-signup failed for {browser_name} - leaving browser open for manual signup', flush=True)
                    browser_conn.close()
                    # DON'T close the browser - leave it open for manual signup
                    # close_browser(user_id)
                    return {'success': False, 'videos': 0}

                print(f'  ✓ Auto-signup successful! @{username}', flush=True)
            else:
                print(f'  ✓ Logged in as @{username}', flush=True)

            # Process each target account
            for acc_idx, account in enumerate(TARGET_ACCOUNTS):
                print(f'  [{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}', flush=True)

                videos = view_profile_videos_mobile(page, account, browser_name)
                browser_videos += videos

                # Update stats for this target account
                update_account_stats(account, videos, browser_name)

                # Wait between accounts (slightly longer on mobile for natural behavior)
                if acc_idx < len(TARGET_ACCOUNTS) - 1:
                    time.sleep(random.randint(7, 18))

            browser_conn.close()

    except Exception as e:
        print(f'  Browser error: {e}', flush=True)
        close_browser(user_id)
        return {'success': False, 'videos': browser_videos}

    close_browser(user_id)
    print(f'  {browser_name} done: {browser_videos} videos viewed (mobile)', flush=True)

    return {'success': True, 'videos': browser_videos}

def main():
    print('=' * 60)
    print('  Target Accounts Viewer - MOBILE VERSION (Single Browser)')
    print('=' * 60)

    # Ask user for browser name
    browser_name = input('\nEnter browser name to use (e.g., tt1, tt208): ').strip()

    if not browser_name:
        print('Error: Browser name is required!')
        return

    print(f'\nTarget accounts: {len(TARGET_ACCOUNTS)}')
    for acc in TARGET_ACCOUNTS:
        print(f'  - @{acc}')
    print(f'\nSettings:')
    print(f'  - Mode: MOBILE (random viewport & user agent)')
    print(f'  - Max videos to view per account: {MAX_VIDEOS_TO_VIEW}')
    print(f'  - View-only period for new accounts: {VIEW_ONLY_DAYS} days')
    print(f'  - Browser: {browser_name}')
    print()

    # Get ALL browsers and find the requested one
    print(f'Loading browser {browser_name} from AdsPower...')
    browsers = get_all_browsers()
    if not browsers:
        print('No browsers found in AdsPower!')
        return

    # Find the specific browser
    browser = None
    for b in browsers:
        if b.get('name') == browser_name:
            browser = b
            break

    if not browser:
        print(f'Error: Browser {browser_name} not found!')
        print(f'Available browsers: {[b.get("name") for b in browsers[:10]]}...')
        return

    print(f'Found browser: {browser.get("name")} (serial {browser.get("serial_number")})')
    print(f'\nTotal work: {len(TARGET_ACCOUNTS)} accounts to visit')
    print(f'Expected views: ~{len(TARGET_ACCOUNTS) * MAX_VIDEOS_TO_VIEW} videos')
    print()

    # Process the single browser
    result = process_browser(browser, 0, 1)

    # Final summary
    print('\n' + '=' * 60)
    print('  FINAL SUMMARY - MOBILE VERSION')
    print('=' * 60)
    if result['success']:
        print(f'Status: ✓ COMPLETED')
    else:
        print(f'Status: ✗ FAILED')
    print(f'Total videos viewed: {result["videos"]}')
    print()

if __name__ == '__main__':
    main()
