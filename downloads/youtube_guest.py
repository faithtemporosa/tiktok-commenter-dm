#!/usr/bin/env python3
"""
Watch YouTube videos as guest (no login required)
"""

import requests
import time
from playwright.sync_api import sync_playwright
import random
import re

ADSPOWER_API = "http://local.adspower.net:50325"

VIDEOS_TO_WATCH = [
    "https://www.youtube.com/watch?v=kpLgGkYTcag",
    "https://www.youtube.com/watch?v=s4XUJlNnHtU",
    "https://www.youtube.com/watch?v=5o3f1yE9N1E",
    "https://www.youtube.com/watch?v=XkokY3AVUKE",
]

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def watch_videos(page, profile_name):
    print(f"  [{profile_name}] Watching {len(VIDEOS_TO_WATCH)} videos as guest...")

    for i, video_url in enumerate(VIDEOS_TO_WATCH, 1):
        try:
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Opening video...")
            page.goto(video_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            # Click play if video is paused
            try:
                play_btn = page.locator('button.ytp-play-button[aria-label*="Play"]').first
                if play_btn.is_visible(timeout=2000):
                    play_btn.click()
                    print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Clicked play")
            except:
                pass

            # Watch for 30-45 seconds (YouTube needs 30s for view)
            watch_time = random.randint(30, 45)
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Watching {watch_time}s...")
            time.sleep(watch_time)

        except Exception as e:
            print(f"    [{i}/{len(VIDEOS_TO_WATCH)}] Error: {str(e)[:50]}")

    print(f"  [{profile_name}] Done watching videos")

def process_profile(profile_id, profile_name):
    print(f"\n{'='*60}")
    print(f"Processing {profile_name} (Guest mode)")
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

            watch_videos(page, profile_name)
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

        if process_profile(profile_id, profile_name):
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
