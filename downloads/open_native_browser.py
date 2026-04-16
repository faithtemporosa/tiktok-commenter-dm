#!/usr/bin/env python3
"""
Open native Mac browser for TikTok testing
Browser stays open until you manually close it
"""
import time
from playwright.sync_api import sync_playwright

print("=" * 70)
print("  Native Mac Browser - Manual TikTok Test")
print("=" * 70)
print()
print("This will open a clean Mac browser (no AdsPower, no proxy)")
print("You can manually test if views/follows register.")
print()
print("Steps:")
print("1. Browser will open in mobile mode (iPhone)")
print("2. Log in to TikTok manually")
print("3. Watch some videos")
print("4. Check if views register in analytics")
print("5. Close this terminal when done to close browser")
print()
print("=" * 70)
print()

with sync_playwright() as p:
    # Launch with iPhone device emulation
    device = p.devices['iPhone 13 Pro']
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(**device)
    page = context.new_page()

    print("✓ Browser launched (iPhone 13 Pro)")
    print("✓ Clean environment - no AdsPower, no proxy")
    print()

    # Go to TikTok
    page.goto('https://www.tiktok.com', timeout=60000)
    print("✓ TikTok opened")
    print()

    print("=" * 70)
    print("  BROWSER IS READY!")
    print("=" * 70)
    print()
    print("Now test manually:")
    print("  1. Log in to TikTok in the browser window")
    print("  2. Watch videos from a target account")
    print("  3. Check TikTok analytics to see if views counted")
    print()
    print("Compare results with AdsPower browsers to see if:")
    print("  - Native browser works → AdsPower is being detected")
    print("  - Native browser fails → IP/account issue")
    print()
    print("Browser will stay open. Press Ctrl+C here to close it.")
    print()

    try:
        # Keep browser open indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing browser...")
        browser.close()
        print("Done!")
