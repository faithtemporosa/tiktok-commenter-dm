#!/usr/bin/env python3
"""
Check all 505 browsers one by one to verify TikTok login status
"""

import requests
import time
from playwright.sync_api import sync_playwright
import re
import json

ADSPOWER_API = "http://local.adspower.net:50325"
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def check_login(profile_id, profile_name):
    """Check if browser is logged into TikTok"""
    print(f"Checking {profile_name}...", end=" ", flush=True)

    debug_url = open_browser(profile_id)
    if not debug_url:
        print("✗ Failed to open")
        return False, None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            # Go to TikTok
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=60000)
            time.sleep(12)  # Wait for session cookies to load

            # Close any popups
            try:
                close_btn = page.locator('[aria-label="Close"]').first
                if close_btn.is_visible(timeout=1000):
                    close_btn.click()
                    time.sleep(1)
            except:
                pass

            current_url = page.url
            is_logged_in = False
            tiktok_username = None

            # MAIN RULE: Check if red "Log in" button is visible
            # If "Log in" button is NOT visible, user is logged in
            try:
                login_btn = page.get_by_role("link", name="Log in").first
                is_login_btn_visible = login_btn.is_visible(timeout=2000)

                if is_login_btn_visible:
                    # Login button is visible = user is NOT logged in
                    is_logged_in = False
                else:
                    # Login button is NOT visible = user IS logged in
                    is_logged_in = True
            except:
                # If we can't find the login button, assume logged in
                is_logged_in = True

            # If logged in, try to get username from URL
            if is_logged_in and '@' in current_url:
                tiktok_username = current_url.split('@')[1].split('/')[0].split('?')[0]

            # Try to get username if logged in
            if is_logged_in and not tiktok_username:
                try:
                    # Navigate to profile to get username
                    page.goto("https://www.tiktok.com/foryou", timeout=30000)
                    time.sleep(3)

                    # Try to click profile
                    try:
                        profile_btn = page.locator('a:has-text("Profile")').first
                        if profile_btn.is_visible(timeout=2000):
                            profile_btn.click()
                            time.sleep(3)

                            final_url = page.url
                            if '@' in final_url:
                                tiktok_username = final_url.split('@')[1].split('/')[0].split('?')[0]
                    except:
                        pass
                except:
                    pass

            if is_logged_in:
                print(f"✓ Logged in{' as @' + tiktok_username if tiktok_username else ''}")
                return True, tiktok_username
            else:
                print("✗ Logged out")
                return False, None

    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return False, None

    finally:
        close_browser(profile_id)

def main():
    print("Fetching all browsers...")
    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    profiles = response.json()['data']['list']
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))

    print(f"Found {len(profiles)} profiles\n")
    print("="*60)
    print("Checking all browsers one by one...")
    print("="*60 + "\n")

    logged_in = 0
    logged_out = 0
    errors = 0

    # Load existing mapping
    try:
        with open(PROFILE_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)
    except:
        mapping = {}

    for i, profile in enumerate(profiles, 1):
        profile_id = profile['user_id']
        profile_name = profile['name']

        print(f"[{i}/{len(profiles)}] ", end="")

        success, username = check_login(profile_id, profile_name)

        if success:
            logged_in += 1
            # Update mapping if we got a username
            if username and profile_name not in mapping:
                mapping[profile_name] = username
        elif username is None and success is False:
            errors += 1
        else:
            logged_out += 1

        # Small delay between checks
        time.sleep(2)

    # Save updated mapping
    with open(PROFILE_MAPPING_PATH, 'w') as f:
        json.dump(mapping, f, indent=2)

    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total profiles: {len(profiles)}")
    print(f"✓ Logged in: {logged_in}")
    print(f"✗ Logged out: {logged_out}")
    print(f"⚠ Errors: {errors}")
    print("="*60)

if __name__ == "__main__":
    main()
