#!/usr/bin/env python3
"""
Warm up accounts before targeted viewing:
1. Repost 1-2 videos from For You page
2. View 5-10 videos from For You page
3. This makes accounts look natural before doing targeted viewing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

from comment_target_accounts import (
    auto_signup,
    check_login_status,
    get_all_browsers,
    open_browser,
    close_browser,
    ADSPOWER_API
)

PARALLEL_BROWSERS = 2  # Run 2 browsers at a time, wait for both to finish before starting next batch
VIDEOS_TO_REPOST = 2  # Repost 1-2 videos
VIDEOS_TO_VIEW = random.randint(5, 10)  # View 5-10 videos

def repost_video(page, video_index):
    """Repost a video from the For You page"""
    try:
        # Find share button
        share_btn = page.locator('button[aria-label*="Share"], [data-e2e="browse-share"]').first
        share_btn.click(timeout=5000)
        time.sleep(2)

        # Click repost option
        repost_btn = page.locator('div:has-text("Repost"), button:has-text("Repost")').first
        repost_btn.click(timeout=5000)
        time.sleep(2)

        print(f'    ✓ Reposted video {video_index}')
        return True
    except Exception as e:
        print(f'    ⚠ Failed to repost video {video_index}: {str(e)[:50]}')
        return False

def scroll_to_next_video(page):
    """Scroll to next video in For You page"""
    try:
        # Try pressing Arrow Down key
        page.keyboard.press('ArrowDown')
        time.sleep(2)
        return True
    except:
        try:
            # Alternative: scroll by pixel amount
            page.evaluate('window.scrollBy(0, window.innerHeight)')
            time.sleep(2)
            return True
        except:
            return False

def warmup_browser(browser, browser_idx, total_browsers):
    """Warm up one browser with natural activity"""
    user_id = browser.get('user_id')
    browser_name = browser.get('name', f'browser_{user_id}')

    print(f'\n[{browser_idx+1}/{total_browsers}] {browser_name} - Warming up account', flush=True)

    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'  ✗ Failed to open browser', flush=True)
        return {'success': False}

    try:
        with sync_playwright() as p:
            browser_conn = p.chromium.connect_over_cdp(ws_url)
            context = browser_conn.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Check login status
            print(f'  Checking login status...', flush=True)
            is_logged_in, username = check_login_status(page)

            if not is_logged_in:
                print(f'  Not logged in - attempting auto-signup...', flush=True)
                signup_success, username = auto_signup(page, browser_name)

                if not signup_success:
                    print(f'  ✗ Auto-signup failed - skipping warmup', flush=True)
                    browser_conn.close()
                    return {'success': False}

                print(f'  ✓ Auto-signup successful! @{username}', flush=True)
            else:
                print(f'  ✓ Logged in as @{username}', flush=True)

            # Go to For You page (TikTok home)
            print(f'  Opening For You page...', flush=True)
            page.goto('https://www.tiktok.com/foryou', timeout=30000)
            time.sleep(5)

            # Phase 1: Repost 1-2 videos
            videos_reposted = 0
            num_to_repost = random.randint(1, VIDEOS_TO_REPOST)
            print(f'  Phase 1: Reposting {num_to_repost} videos...', flush=True)

            for i in range(num_to_repost):
                # Watch for a few seconds before reposting
                watch_time = random.randint(3, 8)
                time.sleep(watch_time)

                # Try to repost
                if repost_video(page, i + 1):
                    videos_reposted += 1

                # Scroll to next video
                scroll_to_next_video(page)
                time.sleep(random.randint(2, 4))

            # Phase 2: View 5-10 videos from For You
            videos_to_view = random.randint(5, 10)
            print(f'  Phase 2: Viewing {videos_to_view} videos...', flush=True)

            for i in range(videos_to_view):
                # Watch video for random duration
                watch_time = random.randint(5, 15)
                print(f'    Watching video {i+1}/{videos_to_view} for {watch_time}s...', flush=True)

                # Scroll while watching (simulate real behavior)
                time.sleep(watch_time / 2)
                page.evaluate('window.scrollBy(0, 100)')
                time.sleep(watch_time / 2)

                # Scroll to next video
                scroll_to_next_video(page)
                time.sleep(random.randint(2, 5))

            print(f'  ✓ Warmup complete: {videos_reposted} reposts, {videos_to_view} views', flush=True)

            browser_conn.close()

    except Exception as e:
        print(f'  ✗ Error during warmup: {str(e)[:100]}', flush=True)
        close_browser(user_id)
        return {'success': False}

    close_browser(user_id)
    return {'success': True}

def main():
    print('=' * 60)
    print('  Account Warmup - Repost & View For You Videos')
    print('=' * 60)
    print(f'\nSettings:')
    print(f'  - Videos to repost per account: 1-{VIDEOS_TO_REPOST}')
    print(f'  - Videos to view per account: 5-10')
    print(f'  - Parallel browsers: {PARALLEL_BROWSERS}')
    print(f'  - Browsers to process: tt1 - tt23')
    print()

    # Get ALL browsers
    print('Loading all browsers from AdsPower...')
    browsers = get_all_browsers()
    if not browsers:
        print('No browsers found in AdsPower!')
        return

    # Filter browsers: tt1 to tt23 by name
    def get_browser_number(browser):
        match = re.search(r'tt(\d+)', browser.get('name', ''))
        return int(match.group(1)) if match else 0

    browsers = [b for b in browsers
                if 1 <= get_browser_number(b) <= 23]

    print(f'Filtered to browsers tt1-tt23: {len(browsers)} browsers')

    # Sort by browser number
    browsers.sort(key=get_browser_number)

    # Show first few browsers
    print(f'\nFirst 5 browsers to warm up:')
    for b in browsers[:5]:
        print(f'  - {b.get("name")} (serial {b.get("serial_number")})')

    print(f'\nTotal browsers to warm up: {len(browsers)}')
    print()

    browsers_completed = 0
    browsers_failed = 0

    # Process browsers in batches - wait for entire batch to complete before starting next
    batch_size = PARALLEL_BROWSERS
    for batch_start in range(0, len(browsers), batch_size):
        batch_browsers = browsers[batch_start:batch_start + batch_size]

        print(f'\n--- Processing batch {batch_start//batch_size + 1} ({len(batch_browsers)} browsers) ---', flush=True)

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit browsers in this batch
            future_to_browser = {}
            for idx_in_batch, browser in enumerate(batch_browsers):
                global_idx = batch_start + idx_in_batch
                future = executor.submit(warmup_browser, browser, global_idx, len(browsers))
                future_to_browser[future] = browser

            # Wait for all browsers in batch to complete
            for future in as_completed(future_to_browser):
                browser = future_to_browser[future]
                try:
                    result = future.result()
                    if result['success']:
                        browsers_completed += 1
                    else:
                        browsers_failed += 1
                except Exception as e:
                    browsers_failed += 1
                    print(f'Error processing browser: {e}')

        # Batch complete - wait a bit before starting next batch
        if batch_start + batch_size < len(browsers):
            print(f'\n✓ Batch complete. Waiting 5 seconds before next batch...', flush=True)
            time.sleep(5)

    # Final summary
    print('\n' + '=' * 60)
    print('  WARMUP SUMMARY')
    print('=' * 60)
    print(f'Browsers completed: {browsers_completed}')
    print(f'Browsers failed: {browsers_failed}')
    print()
    print('Accounts are now warmed up!')
    print('You can now run targeted_accounts_view.py')
    print()

if __name__ == '__main__':
    main()
