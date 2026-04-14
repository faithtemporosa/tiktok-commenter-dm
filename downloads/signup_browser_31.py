#!/usr/bin/env python3
"""Sign up YouTube for browser 31 (tt9)"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://local.adspower.net:50325"

# Browser 31 (tt9) credentials
profile_id = "k19g7nx5"
email = "techdew618@automateyourbizz.xyz"
password = "Urbanwave46!2026"
username = "urbanwave46"

print("Opening browser 31 (tt9)...")
response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=30)
debug_url = response.json()["data"]["ws"]["puppeteer"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(debug_url)
    context = browser.contexts[0]

    # Open YouTube in new tab
    print("Opening YouTube...")
    page = context.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)

    print("\n" + "="*60)
    print("YouTube opened in browser 31 (tt9)")
    print("="*60)
    print(f"\nCredentials:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print(f"  Username: {username}")
    print("\nThe browser is now open. To sign up:")
    print("  1. Click 'Sign in' button (top right)")
    print("  2. Click 'Create account'")
    print("  3. Fill in the form with the credentials above")
    print("  4. Complete phone/captcha verification")

    print("\nBrowser will stay open. Press Ctrl+C when done.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDone!")
