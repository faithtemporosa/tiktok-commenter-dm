#!/usr/bin/env python3
"""
Warmup accounts with STEALTH natural browsing behavior
Fixes: New IP warmup + CDP detection + Unnatural behavior

NO reposting (causes server errors)
ONLY natural viewing with stealth mode
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import time
import random
from playwright.sync_api import sync_playwright
import json
from datetime import datetime
from stealth_browsing import inject_stealth, browse_for_you_page, random_pause

ADSPOWER_API = 'http://local.adspower.net:50325'
WARMUP_LOG_PATH = 'warmup_log.json'

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def load_warmup_log():
    """Load warmup activity log"""
    try:
        with open(WARMUP_LOG_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_warmup_log(log):
    """Save warmup activity log"""
    with open(WARMUP_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)

def record_warmup_session(browser_name, num_videos):
    """Record warmup session"""
    log = load_warmup_log()
    today = datetime.now().strftime('%Y-%m-%d')

    if browser_name not in log:
        log[browser_name] = {'sessions': [], 'total_videos': 0}

    log[browser_name]['sessions'].append({
        'date': today,
        'videos_watched': num_videos
    })
    log[browser_name]['total_videos'] += num_videos

    save_warmup_log(log)

def warmup_browser(browser_name, user_id, num_videos=10):
    """Warmup a single browser with STEALTH natural browsing"""

    print(f"[{browser_name}] Starting warmup session...")

    debug_url = open_browser(user_id)
    if not debug_url:
        print(f"[{browser_name}] ✗ Failed to open browser")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            # Close extra pages
            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            # ===== FIX #1: INJECT STEALTH - Hide CDP automation =====
            inject_stealth(page)
            print(f"[{browser_name}] ✓ Stealth mode enabled (CDP hidden)")

            # Check login status
            print(f"[{browser_name}] Checking login status...")
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=60000)
            random_pause(3, 5)

            is_logged_in = True
            is_logged_out = False

            # Check for login button by getting all buttons and checking their text
            try:
                buttons = page.locator('button').all()
                for btn in buttons:
                    try:
                        text = btn.inner_text(timeout=500)
                        if text and 'log in' in text.lower():
                            is_logged_out = True
                            print(f"[{browser_name}] Found login button: '{text}'")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"[{browser_name}] Login check error: {str(e)[:40]}")

            if is_logged_out:
                print(f"[{browser_name}] ⚠ Account is logged out")
                print(f"[{browser_name}] → Running auto-signup...")

                # Import auto-signup from comment script
                import sys
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from comment_target_accounts import auto_signup

                signup_success, username = auto_signup(page, browser_name)

                if signup_success:
                    print(f"[{browser_name}] ✓ Auto-signup successful! Username: @{username}")
                    is_logged_in = True
                else:
                    print(f"[{browser_name}] ✗ Auto-signup failed, skipping warmup")
                    return False
            else:
                is_logged_in = True

            if is_logged_in:
                print(f"[{browser_name}] ✓ Logged in, starting warmup...")

            # ===== FIX #2: NATURAL BROWSING BEHAVIOR =====
            # Scroll, mouse movements, watch full videos, random pauses
            browse_for_you_page(page, num_videos=num_videos)

            # Random additional natural actions
            if random.random() < 0.3:
                # Sometimes visit trending page (natural behavior)
                print(f"[{browser_name}] Visiting trending...")
                page.goto("https://www.tiktok.com/trending", wait_until="networkidle", timeout=30000)
                random_pause(2, 4)

            # Record session for tracking
            record_warmup_session(browser_name, num_videos)

            print(f"[{browser_name}] ✓ Warmup complete ({num_videos} videos)")
            return True

    except Exception as e:
        print(f"[{browser_name}] ✗ Error: {str(e)[:60]}")
        return False

    finally:
        close_browser(user_id)
        # ===== FIX #3: IP WARMUP - Longer pauses between browsers =====
        random_pause(5, 10)

def get_all_browsers():
    """Get all browsers from AdsPower"""
    all_browsers = []
    page = 1

    while True:
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100},
                timeout=10
            )
            data = response.json()

            if data['code'] != 0:
                break

            browsers = data['data']['list']
            if not browsers:
                break

            all_browsers.extend(browsers)
            page += 1

        except Exception as e:
            break

    return all_browsers

def main():
    print("=" * 70)
    print("STEALTH ACCOUNT WARMUP - Natural Browsing for IP Trust")
    print("=" * 70)
    print()
    print("FIXES:")
    print("  ✓ CDP detection hidden (stealth mode)")
    print("  ✓ Natural behavior (scrolling, mouse movement, full video watch)")
    print("  ✓ IP warmup (gradual activity over multiple days)")
    print()
    print("Run daily for 3-7 days before commenting automation.")
    print()

    # Get all browsers
    print("Loading browsers...")
    browsers = get_all_browsers()
    print(f"Found {len(browsers)} browsers")
    print()

    # How many to warm up per session
    default_num = min(20, len(browsers))
    num_input = input(f"How many browsers to warm up? (default {default_num}, max {len(browsers)}): ").strip()
    num_browsers = int(num_input) if num_input else default_num
    num_browsers = min(num_browsers, len(browsers))

    videos_input = input("Videos to watch per browser? (default 10, range 5-20): ").strip()
    videos_per_browser = int(videos_input) if videos_input else 10
    videos_per_browser = max(5, min(20, videos_per_browser))

    print()
    print(f"Will warm up {num_browsers} browsers, {videos_per_browser} videos each")
    print()

    # Select random browsers for variety
    selected = random.sample(browsers, num_browsers)

    success = 0
    failed = 0

    for i, browser in enumerate(selected, 1):
        print(f"\n[{i}/{num_browsers}] " + "=" * 60)

        browser_name = browser.get('name', 'Unknown')
        user_id = browser.get('user_id')

        if warmup_browser(browser_name, user_id, num_videos=videos_per_browser):
            success += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print(f"WARMUP SESSION COMPLETE")
    print(f"  Success: {success}")
    print(f"  Failed:  {failed}")
    print()
    print("NEXT STEPS:")
    print("  1. Run this script daily for 3-7 days")
    print("  2. After warmup period, accounts are ready for light automation")
    print("  3. Start with 1 comment every 2-3 days per account")
    print("=" * 70)

if __name__ == "__main__":
    main()
