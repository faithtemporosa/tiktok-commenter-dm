#!/usr/bin/env python3
"""
Sign up browser tt505 with US phone number - Manual assisted
Browser stays open, you manually complete the signup
"""
import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = 'http://local.adspower.net:50325'

def open_browser(browser_serial):
    """Open AdsPower browser"""
    try:
        response = requests.get(f'{ADSPOWER_API}/api/v1/browser/start',
                              params={'serial_number': browser_serial})
        data = response.json()

        if data['code'] != 0:
            print(f"Failed to start browser: {data.get('msg', 'Unknown error')}")
            return None, None

        debug_port = data['data']['ws']['puppeteer']
        return debug_port, None
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None, None

def close_browser(browser_serial):
    """Close AdsPower browser"""
    try:
        requests.get(f'{ADSPOWER_API}/api/v1/browser/stop',
                    params={'serial_number': browser_serial})
    except Exception as e:
        print(f"Error closing browser: {e}")

def main():
    browser_serial = 505

    print("=" * 70)
    print(f"  Browser tt505 (serial {browser_serial}) - Manual Phone Signup")
    print("=" * 70)
    print()

    # Open browser
    debug_port, _ = open_browser(browser_serial)
    if not debug_port:
        print("Failed to open browser")
        return

    print(f"✓ Browser opened on port {debug_port}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_port)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to TikTok signup page
            print("\nNavigating to TikTok signup page...")
            page.goto('https://www.tiktok.com/signup/phone-or-email/phone', timeout=30000)
            time.sleep(3)

            print("\n" + "=" * 70)
            print("  MANUAL SIGNUP INSTRUCTIONS")
            print("=" * 70)
            print()
            print("The TikTok signup page is now open in the browser.")
            print()
            print("STEP 1: Fill in your birthdate")
            print("  - Select month, day, and year (make sure you're 18+)")
            print()
            print("STEP 2: Enter US phone number")
            print("  - Make sure 'US +1' is selected in the country dropdown")
            print("  - Enter your US phone number")
            print("  - Click 'Send code'")
            print()
            print("STEP 3: Enter verification code")
            print("  - Check your phone for the 6-digit code")
            print("  - Enter it in the TikTok form")
            print("  - Click 'Next'")
            print()
            print("STEP 4: Set username (if prompted)")
            print("  - Enter a unique username")
            print("  - Click 'Sign up' or 'Next'")
            print()
            print("=" * 70)
            print()

            # Wait for user to complete signup
            print("Complete the signup in the browser window.")
            print("Press ENTER here when signup is complete...")
            input()

            # Check if signup succeeded
            print("\nChecking signup status...")
            try:
                page.goto('https://www.tiktok.com/profile', timeout=15000)
                time.sleep(2)

                if '/@' in page.url:
                    username = page.url.split('/@')[1].split('?')[0].split('/')[0]
                    print(f"\n✓✓✓ SIGNUP SUCCESS! ✓✓✓")
                    print(f"Username: @{username}")
                    print(f"Browser: tt505")

                    # Save to CSV
                    print("\nDo you want to save this account to tiktok_accounts.csv?")
                    save = input("Enter 'y' to save, or press ENTER to skip: ")

                    if save.lower() == 'y':
                        import csv
                        import os
                        csv_path = '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_accounts.csv'

                        # Get phone number from user
                        phone = input("Enter the phone number used (for records): ")

                        file_exists = os.path.exists(csv_path)
                        with open(csv_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(['browser_id', 'serial', 'username', 'phone', 'password'])
                            writer.writerow(['tt505', '505', username, phone, 'Spectrum.01'])

                        print(f"✓ Saved to {csv_path}")
                else:
                    print("\n⚠ Could not verify signup")
                    print(f"Current URL: {page.url}")
                    print("Please check manually in the browser")
            except Exception as e:
                print(f"Error checking signup: {e}")

            print("\nBrowser will remain open.")
            print("Press ENTER to close the browser...")
            input()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        close_browser(browser_serial)
        print("Browser closed")

if __name__ == '__main__':
    main()
