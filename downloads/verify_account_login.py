#!/usr/bin/env python3
"""
Verify that a TikTok account is logged in
"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"

def find_browser_by_serial(serial_num):
    """Find browser by serial number"""
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
        if page > 10:
            break

    for profile in profiles:
        if str(profile.get('serial_number', '')) == str(serial_num):
            return profile
    return None

def open_browser(user_id):
    """Open browser"""
    resp = requests.get(
        f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0",
        timeout=60
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("data", {})
    return None

def close_browser(user_id):
    """Close browser"""
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass

def verify_login(serial_num):
    """Verify if account is logged in"""
    print(f"Verifying browser with serial #{serial_num}...")

    profile = find_browser_by_serial(serial_num)
    if not profile:
        print(f"Browser {serial_num} not found!")
        return False

    user_id = profile.get('user_id')
    profile_name = profile.get('name')
    print(f"Found profile: {profile_name}")

    print("Opening browser...")
    browser_info = open_browser(user_id)
    if not browser_info:
        print("Failed to open browser!")
        return False

    time.sleep(2)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            print("Navigating to TikTok...")
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            current_url = page.url
            print(f"Current URL: {current_url}")

            # Check if logged in
            is_logged_in = ('foryou' in current_url or
                           'following' in current_url or
                           '@' in current_url)

            if is_logged_in:
                print("✓ ACCOUNT IS LOGGED IN!")

                # Try to get the username
                try:
                    # Look for profile link or username
                    profile_link = page.locator("a[href*='/@']").first
                    if profile_link:
                        href = profile_link.get_attribute('href')
                        username = href.split('/@')[-1].split('?')[0]
                        print(f"  Username: @{username}")
                except:
                    print("  Could not extract username")

                # Take screenshot
                screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/verify_browser_{serial_num}.png"
                page.screenshot(path=screenshot_path)
                print(f"  Screenshot saved: {screenshot_path}")

                return True
            else:
                print("✗ ACCOUNT IS NOT LOGGED IN")
                print(f"  Current URL: {current_url}")

                # Take screenshot
                screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/verify_browser_{serial_num}_notloggedin.png"
                page.screenshot(path=screenshot_path)
                print(f"  Screenshot saved: {screenshot_path}")

                return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        print("Closing browser...")
        close_browser(user_id)

if __name__ == "__main__":
    # Verify browser 802 (should be account #6)
    print("=" * 60)
    print("Verifying Account #6 - Browser 802")
    print("=" * 60)
    verify_login(802)

    print("\n" + "=" * 60)
    print("Verifying Account #7 - Browser 801")
    print("=" * 60)
    verify_login(801)

    print("\n" + "=" * 60)
    print("Verifying Account #8 - Browser 800")
    print("=" * 60)
    verify_login(800)
