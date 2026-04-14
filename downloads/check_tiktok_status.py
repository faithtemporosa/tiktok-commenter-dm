#!/usr/bin/env python3
"""
Just check TikTok login status - no login attempts
"""

import requests
import time
from playwright.sync_api import sync_playwright
import re

ADSPOWER_API = "http://local.adspower.net:50325"

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def check_tiktok_status(profile_id, profile_name):
    """Check if logged into TikTok"""
    debug_url = open_browser(profile_id)
    if not debug_url:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            # Keep only 1 tab
            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=60000)

            # Wait for cookies to load and TikTok to process session (10-15 seconds)
            print(f"  Waiting for session to restore from cookies...")
            time.sleep(12)

            # Check if logged in by looking for logged-in UI elements
            is_logged_in = False

            # Check URL first
            final_url = page.url
            if 'foryou' in final_url or 'following' in final_url or '@' in final_url:
                is_logged_in = True
            else:
                # Check for logged-in UI elements (Profile, Upload, Messages, etc.)
                try:
                    # Look for Upload button or Profile section - these only appear when logged in
                    upload_btn = page.locator('a:has-text("Upload"), [href*="/upload"]').first
                    if upload_btn.is_visible(timeout=2000):
                        is_logged_in = True
                except:
                    pass

                if not is_logged_in:
                    try:
                        # Look for Profile link with avatar
                        profile_link = page.locator('a:has-text("Profile")').first
                        if profile_link.is_visible(timeout=2000):
                            is_logged_in = True
                    except:
                        pass

            return is_logged_in

    except Exception as e:
        print(f"  Error: {str(e)[:60]}")
        return None
    finally:
        close_browser(profile_id)

def main():
    import sys

    num_to_check = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))
    profiles_to_check = profiles[start_index:start_index + num_to_check]

    print(f"Checking {len(profiles_to_check)} profiles (from index {start_index})")
    print("=" * 60)

    logged_in = []
    logged_out = []
    errors = []

    for i, profile in enumerate(profiles_to_check, 1):
        profile_id = profile.get("user_id")
        profile_name = profile.get("name", profile_id)

        print(f"[{i}/{len(profiles_to_check)}] {profile_name}...", end=" ", flush=True)

        status = check_tiktok_status(profile_id, profile_name)

        if status is True:
            print("✓ LOGGED IN")
            logged_in.append(profile_name)
        elif status is False:
            print("✗ LOGGED OUT")
            logged_out.append(profile_name)
        else:
            print("? ERROR")
            errors.append(profile_name)

        time.sleep(1)

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  ✓ Logged in: {len(logged_in)}")
    print(f"  ✗ Logged out: {len(logged_out)}")
    print(f"  ? Errors: {len(errors)}")

    if logged_out:
        print(f"\nLogged out browsers: {', '.join(logged_out)}")

    if errors:
        print(f"\nError browsers: {', '.join(errors)}")

    print("=" * 60)

if __name__ == "__main__":
    main()
