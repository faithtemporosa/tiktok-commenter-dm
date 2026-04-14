#!/usr/bin/env python3
"""
Login to YouTube using TikTok email credentials
Watch and like specified videos
"""

import requests
import time
from playwright.sync_api import sync_playwright
import random
import re
import csv
import os

ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = os.path.join(os.path.dirname(__file__), 'tiktok_accounts.csv')

VIDEOS_TO_WATCH = [
    "https://www.youtube.com/watch?v=kpLgGkYTcag",
    "https://www.youtube.com/watch?v=s4XUJlNnHtU",
    "https://www.youtube.com/watch?v=5o3f1yE9N1E",
    "https://www.youtube.com/watch?v=XkokY3AVUKE",
]

# Load credentials from CSV once (by Account #)
_credentials_cache = None

def load_credentials():
    global _credentials_cache
    if _credentials_cache is not None:
        return _credentials_cache

    _credentials_cache = {}
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            account_num = row.get('Account #', '')
            if account_num and account_num.isdigit():
                email = row.get('Email', '')
                # Only include accounts with valid emails
                if email and '@' in email:
                    _credentials_cache[int(account_num)] = {
                        'account_num': int(account_num),
                        'username': row.get('Username', ''),
                        'password': row.get('Password', ''),
                        'email': email,
                        'status': row.get('Status', ''),
                    }
    return _credentials_cache

def get_account_credentials(profile_num):
    """Get credentials by profile number (tt1 = 0, tt2 = 1, etc.)"""
    creds = load_credentials()
    # profile_num is 1-indexed (tt1, tt2...), Account # is 0-indexed
    account_num = profile_num - 1
    return creds.get(account_num)

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def watch_and_like_videos(page, profile_name):
    print(f"  [{profile_name}] Watching and liking {len(VIDEOS_TO_WATCH)} videos...")

    for i, video_url in enumerate(VIDEOS_TO_WATCH, 1):
        try:
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Opening video...")
            page.goto(video_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            # Try to like
            try:
                like_selectors = [
                    'like-button-view-model button',
                    '#segmented-like-button button',
                ]
                like_btn = None
                for selector in like_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            like_btn = btn
                            break
                    except:
                        continue

                if like_btn:
                    aria = like_btn.get_attribute("aria-pressed")
                    if aria != "true":
                        like_btn.click()
                        print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Liked!")
                        time.sleep(1)
                    else:
                        print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Already liked")
                else:
                    print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Like button not found")
            except:
                pass

            watch_time = random.randint(30, 45)
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Watching {watch_time}s...")
            time.sleep(watch_time)

        except Exception as e:
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Error: {str(e)[:50]}")

    print(f"  [{profile_name}] Done watching videos")

def process_youtube(profile_id, profile_name, email=None, password=None):
    print(f"\n{'='*60}")
    print(f"Processing {profile_name}")
    print(f"{'='*60}")

    debug_url = open_browser(profile_id)
    if not debug_url:
        print(f"  Failed to open browser")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            # Keep only 1 tab
            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            print(f"  Navigating to YouTube...")
            page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Check if already logged in
            is_logged_in = False
            try:
                page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first.wait_for(state="visible", timeout=5000)
                print(f"  Not logged in")
            except:
                print(f"  Already logged in!")
                is_logged_in = True

            if is_logged_in:
                # Logged in - watch and like videos
                watch_and_like_videos(page, profile_name)
                return True
            else:
                # Not logged in - try to sign in with email/password
                if email and password:
                    print(f"  [{profile_name}] Clicking Sign In...")
                    try:
                        sign_in_btn = page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first
                        sign_in_btn.click()
                        time.sleep(3)

                        # Enter email
                        print(f"  [{profile_name}] Entering email: {email}")
                        email_input = page.locator('input[type="email"]').first
                        email_input.wait_for(state="visible", timeout=10000)
                        email_input.fill(email)
                        time.sleep(1)

                        page.locator('button:has-text("Next")').first.click()
                        time.sleep(3)

                        # Check if account exists (password field appears)
                        try:
                            pwd_input = page.locator('input[type="password"], input[name="Passwd"]').first
                            pwd_input.wait_for(state="visible", timeout=5000)

                            # Account exists - enter password
                            print(f"  [{profile_name}] Entering password...")
                            pwd_input.fill(password)
                            time.sleep(1)

                            page.locator('button:has-text("Next")').first.click()
                            time.sleep(5)

                            # Check if logged in now
                            page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
                            time.sleep(3)

                            try:
                                page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first.wait_for(state="visible", timeout=3000)
                                print(f"  [{profile_name}] Login failed - still not signed in")
                            except:
                                print(f"  [{profile_name}] Login successful!")
                                watch_and_like_videos(page, profile_name)
                                return True

                        except:
                            # Password field didn't appear - account doesn't exist
                            print(f"  [{profile_name}] Google account doesn't exist for this email")

                    except Exception as e:
                        print(f"  [{profile_name}] Sign in error: {str(e)[:60]}")

                # Watch as guest (fallback)
                print(f"  [{profile_name}] Watching as guest...")
                page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
                time.sleep(2)

                for i, video_url in enumerate(VIDEOS_TO_WATCH, 1):
                    try:
                        print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Opening video...")
                        page.goto(video_url, wait_until="domcontentloaded", timeout=60000)
                        time.sleep(5)

                        # Click play if paused
                        try:
                            play_btn = page.locator('button.ytp-play-button[aria-label*="Play"]').first
                            if play_btn.is_visible(timeout=2000):
                                play_btn.click()
                        except:
                            pass

                        watch_time = random.randint(30, 45)
                        print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Watching {watch_time}s (guest)...")
                        time.sleep(watch_time)

                    except Exception as e:
                        print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Error: {str(e)[:50]}")

                print(f"  [{profile_name}] Done watching as guest")
                return True

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
        return False
    finally:
        print(f"  Closing browser...")
        close_browser(profile_id)

def main():
    import sys

    num_to_process = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    print(f"Found {len(profiles)} profiles")

    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))
    profiles_to_process = profiles[start_index:start_index + num_to_process]
    print(f"Processing {len(profiles_to_process)} profiles (from index {start_index})")

    success = 0
    failed = 0

    for profile in profiles_to_process:
        profile_id = profile.get("user_id")
        profile_name = profile.get("name", profile_id)

        # Get profile number from name (tt1 -> 1, tt2 -> 2)
        match = re.search(r'(\d+)', profile_name)
        profile_num = int(match.group(1)) if match else 0

        # Get credentials for this profile
        credentials = get_account_credentials(profile_num)
        email = credentials.get("email") if credentials else None
        password = credentials.get("password") if credentials else None

        if email:
            print(f"Email: {email}")

        if process_youtube(profile_id, profile_name, email, password):
            success += 1
        else:
            failed += 1

        # Wait between profiles
        time.sleep(random.randint(3, 6))

    print(f"\n{'='*60}")
    print(f"SUMMARY: Success={success}, Failed={failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
