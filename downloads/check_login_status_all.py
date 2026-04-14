#!/usr/bin/env python3
"""
Check TikTok login status for all browsers
"""
import requests
import re
from playwright.sync_api import sync_playwright
import time

ADSPOWER_API = "http://local.adspower.net:50325"

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def check_tiktok_login(profile_id, profile_name):
    """Check if browser is logged into TikTok"""
    try:
        debug_url = open_browser(profile_id)
        if not debug_url:
            return False, "Failed to open"

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            # Keep only 1 tab
            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to TikTok
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Check if logged in by looking for profile button or login button
            current_url = page.url
            is_logged_in = False

            try:
                # Look for login button (means not logged in)
                login_btn = page.locator('button:has-text("Log in")').first
                if login_btn.is_visible(timeout=2000):
                    is_logged_in = False
                else:
                    # No login button visible, probably logged in
                    is_logged_in = True
            except:
                # If we can't find login button, check URL
                is_logged_in = 'foryou' in current_url or 'following' in current_url or '@' in current_url

            close_browser(profile_id)
            return is_logged_in, "Logged in" if is_logged_in else "Logged out"

    except Exception as e:
        close_browser(profile_id)
        return False, str(e)[:50]

def main():
    print("="*60)
    print("  CHECKING TIKTOK LOGIN STATUS FOR ALL BROWSERS")
    print("="*60)

    # Get all profiles
    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    print(f"\nFound {len(profiles)} total browsers")

    # Sort by browser number
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))

    logged_in = []
    logged_out = []
    errors = []

    for i, profile in enumerate(profiles, 1):
        profile_id = profile.get("user_id")
        profile_name = profile.get("name", profile_id)

        print(f"\n[{i}/{len(profiles)}] Checking {profile_name}...", end=" ")

        is_logged_in, status = check_tiktok_login(profile_id, profile_name)

        if is_logged_in:
            print("✓ Logged in")
            logged_in.append(profile_name)
        elif "Failed" in status or "Error" in status:
            print(f"✗ Error: {status}")
            errors.append((profile_name, status))
        else:
            print("✗ Logged out")
            logged_out.append(profile_name)

        time.sleep(1)  # Brief delay between checks

    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"  Logged in: {len(logged_in)}")
    print(f"  Logged out: {len(logged_out)}")
    print(f"  Errors: {len(errors)}")

    if logged_out:
        print(f"\n  Logged out browsers ({len(logged_out)}):")
        for name in logged_out[:20]:
            print(f"    - {name}")
        if len(logged_out) > 20:
            print(f"    ... and {len(logged_out) - 20} more")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for name, err in errors[:10]:
            print(f"    - {name}: {err}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
