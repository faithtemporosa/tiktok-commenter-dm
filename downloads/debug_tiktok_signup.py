#!/usr/bin/env python3
"""
Debug TikTok signup form to understand select options
"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"

def find_browser_802():
    """Find browser with serial 802"""
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
        if str(profile.get('serial_number', '')) == '802':
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

def debug_signup_form():
    """Debug the signup form"""
    print("Finding browser 802...")
    profile = find_browser_802()
    if not profile:
        print("Browser 802 not found!")
        return

    user_id = profile.get('user_id')
    print(f"Opening browser {profile.get('name')}...")

    browser_info = open_browser(user_id)
    if not browser_info:
        print("Failed to open browser!")
        return

    time.sleep(2)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            print("Navigating to TikTok signup...")
            page.goto("https://www.tiktok.com/signup", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Click "Use phone or email"
            try:
                page.click("text=Use phone or email", timeout=5000)
                time.sleep(2)
            except:
                pass

            # Click "Email" tab
            try:
                page.click("text=Email", timeout=5000)
                time.sleep(2)
            except:
                pass

            # Take a screenshot
            screenshot_path = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_signup_debug.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"\nScreenshot saved to: {screenshot_path}\n")

            # Find birthdate dropdown elements by text
            print("Looking for birthdate dropdown elements...\n")

            # Try to find Month dropdown
            try:
                month_elem = page.locator("text=Month").first
                print("Month element found:")
                print(f"  Tag: {month_elem.evaluate('el => el.tagName')}")
                print(f"  Type: {month_elem.evaluate('el => el.type')}")
                print(f"  Class: {month_elem.get_attribute('class')}")
                print(f"  Role: {month_elem.get_attribute('role')}")

                # Click it and see what happens
                month_elem.click()
                time.sleep(1)
                page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/month_dropdown_open.png")
                print("  Clicked Month dropdown, screenshot saved")

                # Look for the dropdown menu that appears
                dropdown_items = page.locator("[role='option']").all()
                print(f"\n  Found {len(dropdown_items)} dropdown items")
                if dropdown_items:
                    print("  First 5 items:")
                    for i, item in enumerate(dropdown_items[:5]):
                        text = item.inner_text()
                        print(f"    [{i}] {text}")

            except Exception as e:
                print(f"Error finding Month: {e}")

            # Try alternative selectors
            print("\nTrying to find custom select elements...")
            custom_selects = page.locator("[role='combobox']").all()
            print(f"Found {len(custom_selects)} combobox elements")

            for i, elem in enumerate(custom_selects[:3]):
                aria_label = elem.get_attribute('aria-label')
                print(f"  Combobox {i}: aria-label='{aria_label}'")

            print("\n\nWaiting 30 seconds before closing...")
            time.sleep(30)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing browser...")
        close_browser(user_id)

if __name__ == "__main__":
    debug_signup_form()
