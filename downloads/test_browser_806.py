#!/usr/bin/env python3
"""
Test browser 806 with TikTok signup
"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"

def open_browser(user_id):
    """Open an AdsPower browser"""
    try:
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0",
            timeout=60
        )
        data = resp.json()
        if data.get("code") == 0:
            debug_info = data.get("data", {})
            return debug_info
        else:
            print(f"Error opening browser: {data}")
        return None
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None

def close_browser(user_id):
    """Close an AdsPower browser"""
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass

def find_browser_806():
    """Find browser profile with serial number 806"""
    profiles = []
    page = 1
    while True:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100", timeout=10)
        data = resp.json()
        if data.get("code") != 0:
            break
        batch = data.get("data", {}).get("list", [])
        if not batch:
            break
        profiles.extend(batch)
        page += 1
        if page > 10:  # safety limit
            break

    # Find profile with serial number 806
    for profile in profiles:
        serial = str(profile.get('serial_number', ''))
        if serial == '806':
            return profile

    return None

def test_tiktok_signup():
    """Test TikTok signup flow"""

    print("=" * 60)
    print("  Testing Browser 806 - TikTok Signup")
    print("=" * 60)
    print()

    # Find browser 806
    print("Finding browser profile with 806...")
    profile = find_browser_806()

    if not profile:
        print("✗ Browser 806 not found!")
        return

    user_id = profile.get('user_id')
    profile_name = profile.get('name', '')
    print(f"✓ Found profile: {profile_name} (ID: {user_id})")
    print()

    # Open browser
    print("Opening browser...")
    browser_info = open_browser(user_id)

    if not browser_info:
        print("✗ Failed to open browser")
        return

    print(f"✓ Browser opened")
    print(f"  Debug info: {browser_info}")
    print()

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print("✗ No WebSocket endpoint found")
        close_browser(user_id)
        return

    print(f"✓ WebSocket endpoint: {ws_endpoint}")
    print()

    time.sleep(3)

    # Connect with Playwright
    print("Connecting to browser with Playwright...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            print(f"✓ Connected to browser")
            print(f"  Current URL: {page.url}")
            print()

            # Navigate to TikTok signup
            print("Navigating to TikTok signup page...")
            page.goto("https://www.tiktok.com/signup", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            print(f"✓ Loaded TikTok signup")
            print(f"  Current URL: {page.url}")
            print()

            # Take screenshot
            screenshot_path = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_signup_test.png"
            page.screenshot(path=screenshot_path)
            print(f"✓ Screenshot saved: {screenshot_path}")
            print()

            # Try to find elements
            print("Checking page elements...")

            # Check for common selectors
            selectors_to_check = [
                "text=Use phone or email",
                "text=Email",
                "select",
                "input[type='text']",
                "input[type='password']",
                "button:has-text('Send code')",
                "button:has-text('Next')",
            ]

            for selector in selectors_to_check:
                try:
                    count = page.locator(selector).count()
                    print(f"  '{selector}': {count} found")
                except Exception as e:
                    print(f"  '{selector}': Error - {e}")

            print()
            print("Waiting 10 seconds for you to inspect the browser...")
            time.sleep(10)

            print("✓ Test complete!")

    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()

    # Close browser
    print()
    print("Closing browser...")
    close_browser(user_id)
    print("✓ Browser closed")
    print()
    print("=" * 60)

if __name__ == "__main__":
    test_tiktok_signup()
