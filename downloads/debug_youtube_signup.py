#!/usr/bin/env python3
"""Debug YouTube signup flow to find correct selectors"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://local.adspower.net:50325"

# Get profiles
response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=100", timeout=10)
profiles = response.json().get("data", {}).get("list", [])

# Sort and get tt11
import re
profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))
profile = profiles[10] if len(profiles) > 10 else profiles[0]  # tt11 or first

profile_id = profile.get("user_id")
profile_name = profile.get("name")

print(f"Opening {profile_name}...")

# Open browser
response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=30)
debug_url = response.json()["data"]["ws"]["puppeteer"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(debug_url)
    context = browser.contexts[0]

    # Close extra tabs
    while len(context.pages) > 1:
        context.pages[-1].close()

    page = context.pages[0] if context.pages else context.new_page()

    print("Going to YouTube...")
    page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)

    print("Clicking Sign In...")
    page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first.click()
    time.sleep(3)

    print("Clicking Create account...")
    page.locator('button:has-text("Create account"), span:has-text("Create account")').first.click()
    time.sleep(2)

    print("Clicking For personal use...")
    try:
        page.locator('li:has-text("For my personal use")').first.click()
        time.sleep(2)
    except:
        pass

    print("Filling name...")
    page.locator('input[name="firstName"]').first.fill("Test")
    page.locator('input[name="lastName"]').first.fill("User")
    time.sleep(1)

    print("Clicking Next...")
    page.locator('button:has-text("Next")').first.click()
    time.sleep(3)

    print("Filling birthdate...")
    try:
        page.locator('select#month').first.select_option(label="January")
    except:
        pass
    page.locator('input#day').first.fill("15")
    page.locator('input#year').first.fill("2000")
    try:
        page.locator('select#gender').first.select_option(label="Rather not say")
    except:
        pass
    time.sleep(1)

    print("Clicking Next...")
    page.locator('button:has-text("Next")').first.click()
    time.sleep(3)

    # Take screenshot of current page
    screenshot_path = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/debug_youtube_step.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # Print all visible text
    print("\n--- Current page content ---")
    print(page.content()[:3000])

    print("\n\nBrowser is open. Check the screenshot and browser manually.")
    print("Press Enter to close...")
    input()

# Close browser
requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile_id}")
print("Done!")
