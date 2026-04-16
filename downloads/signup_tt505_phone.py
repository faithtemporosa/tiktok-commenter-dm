#!/usr/bin/env python3
"""
Sign up browser tt505 with US phone number
"""
import requests
import time
import random
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
        webdriver_path = data['data'].get('webdriver')

        return debug_port, webdriver_path
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

def signup_with_phone(page):
    """Sign up with US phone number"""
    try:
        # Go to phone signup page
        print("Opening TikTok signup page...")
        page.goto('https://www.tiktok.com/signup', timeout=30000)
        time.sleep(3)

        # Take screenshot of initial page
        page.screenshot(path='downloads/tt505_step1_initial.png')
        print("Screenshot saved: tt505_step1_initial.png")

        # Click "Use phone or email" button
        print("\nClicking 'Use phone or email' button...")
        try:
            page.locator('div:has-text("Use phone or email")').first.click(timeout=5000)
            time.sleep(2)
            print("✓ Clicked 'Use phone or email'")
        except Exception as e:
            print(f"Could not click button: {e}")
            # Try alternate text
            try:
                page.locator('button:has-text("Use phone or email"), a:has-text("Use phone or email")').first.click(timeout=5000)
                time.sleep(2)
            except:
                pass

        page.screenshot(path='downloads/tt505_step1b_phone_or_email.png')
        print("Screenshot saved: tt505_step1b_phone_or_email.png")

        # Fill birthdate - random age between 25-35
        print("\nFilling birthdate...")
        try:
            # Month
            page.locator('[role="combobox"]').nth(0).click(timeout=5000)
            time.sleep(0.3)
            month_clicks = random.randint(1, 6)
            for _ in range(month_clicks):
                page.keyboard.press('ArrowDown')
                time.sleep(0.05)
            page.keyboard.press('Enter')
            time.sleep(0.3)

            # Day
            page.locator('[role="combobox"]').nth(1).click(timeout=5000)
            time.sleep(0.3)
            day_clicks = random.randint(1, 15)
            for _ in range(day_clicks):
                page.keyboard.press('ArrowDown')
                time.sleep(0.05)
            page.keyboard.press('Enter')
            time.sleep(0.3)

            # Year - 28+ years old
            page.locator('[role="combobox"]').nth(2).click(timeout=5000)
            time.sleep(0.3)
            for _ in range(28):
                page.keyboard.press('ArrowDown')
                time.sleep(0.05)
            page.keyboard.press('Enter')
            time.sleep(0.3)

            print("✓ Birthdate filled")
        except Exception as e:
            print(f"Birthdate error: {e}")
            return False

        page.screenshot(path='downloads/tt505_step2_birthdate.png')
        print("Screenshot saved: tt505_step2_birthdate.png")

        # Make sure we're on phone signup (not email)
        # The page should already show "Phone" input, but let's verify
        print("\n===========================================")
        print("MANUAL STEP 1: Enter your US phone number")
        print("===========================================")
        print("1. Look at the TikTok window")
        print("2. Make sure 'US +1' is selected in the country code dropdown")
        print("3. Enter your US phone number in the 'Phone number' field")
        print("4. Click 'Send code' button")
        print("")
        input("Press ENTER after you've clicked 'Send code'...")

        # Take screenshot after code is sent
        page.screenshot(path='downloads/tt505_step3_after_send.png')
        print("Screenshot saved: tt505_step3_after_send.png")

        print("\n===========================================")
        print("MANUAL STEP 2: Enter verification code")
        print("===========================================")
        print("1. Check your phone for the 6-digit code")
        print("2. Enter the code in the 'Enter 6-digit code' field")
        print("")
        code = input("Enter the 6-digit code you received: ")

        # Enter the verification code
        try:
            code_input = page.locator('input[placeholder*="code"], input[name="verifyCode"]').first
            code_input.fill(code)
            time.sleep(1)
            print(f"✓ Code entered: {code}")
        except Exception as e:
            print(f"Error entering code: {e}")
            return False

        # Click Next/Submit
        try:
            page.locator('button:has-text("Next"), button[type="submit"]').first.click(timeout=5000)
            print("✓ Clicked Next button")
            time.sleep(5)
        except Exception as e:
            print(f"Error clicking Next: {e}")

        page.screenshot(path='downloads/tt505_step4_after_code.png')
        print("Screenshot saved: tt505_step4_after_code.png")

        # Set username if prompted
        print("\n===========================================")
        print("MANUAL STEP 3: Set username (if needed)")
        print("===========================================")
        print("If TikTok asks for a username:")
        print("1. Enter a unique username")
        print("2. Click Next/Sign up")
        print("")
        input("Press ENTER after username is set (or if no username prompt appears)...")

        page.screenshot(path='downloads/tt505_step5_after_username.png')
        print("Screenshot saved: tt505_step5_after_username.png")

        # Check if signup succeeded
        time.sleep(3)
        page.goto('https://www.tiktok.com/profile', timeout=15000)
        time.sleep(2)

        if '/@' in page.url:
            username = page.url.split('/@')[1].split('?')[0].split('/')[0]
            print(f"\n✓✓✓ SIGNUP SUCCESS! ✓✓✓")
            print(f"Username: @{username}")
            print(f"Browser: tt505")
            return True
        else:
            print("\n⚠ Could not verify signup. Current URL:", page.url)
            return False

    except Exception as e:
        print(f"Signup error: {e}")
        page.screenshot(path='downloads/tt505_error.png')
        return False

def main():
    browser_serial = 505

    print("=" * 60)
    print(f"  Signing up browser tt505 (serial {browser_serial})")
    print("  Using US phone number verification")
    print("=" * 60)
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

            # Run signup process
            success = signup_with_phone(page)

            if success:
                print("\n" + "=" * 60)
                print("  SIGNUP COMPLETED SUCCESSFULLY!")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("  SIGNUP INCOMPLETE - Please check manually")
                print("=" * 60)

            print("\nBrowser will remain open for you to verify.")
            print("Press ENTER to close the browser...")
            input()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_browser(browser_serial)
        print("Browser closed")

if __name__ == '__main__':
    main()
