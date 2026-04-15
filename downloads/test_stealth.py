#!/usr/bin/env python3
"""
Test stealth mode - Check if CDP is hidden
"""

import requests
from playwright.sync_api import sync_playwright
import time
from stealth_browsing import inject_stealth

ADSPOWER_API = 'http://local.adspower.net:50325'

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

# Get first browser
response = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=1')
browser = response.json()['data']['list'][0]
user_id = browser['user_id']
name = browser['name']

print(f"Testing stealth mode on browser: {name}")
print("=" * 60)

debug_url = open_browser(user_id)

try:
    with sync_playwright() as p:
        browser_conn = p.chromium.connect_over_cdp(debug_url)
        context = browser_conn.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        # INJECT STEALTH
        inject_stealth(page)
        print("✓ Stealth mode injected")

        # Test on bot detection site
        print("\nTesting on bot detection site...")
        page.goto("https://bot.sannysoft.com/", timeout=30000)
        time.sleep(5)

        # Check webdriver detection
        result = page.evaluate("navigator.webdriver")
        print(f"\nnavigator.webdriver: {result}")

        if result is None or result == False:
            print("✓ STEALTH WORKING - webdriver is hidden!")
        else:
            print("✗ STEALTH FAILED - webdriver is detected")

        # Check CDP
        cdp_result = page.evaluate("window.chrome && window.chrome.runtime")
        print(f"window.chrome.runtime: {cdp_result}")

        print("\nCheck the browser window for red vs green indicators.")
        print("Green = not detected, Red = detected as bot")
        input("\nPress Enter to close...")

except Exception as e:
    print(f"Error: {e}")

finally:
    close_browser(user_id)
    print("Browser closed")
