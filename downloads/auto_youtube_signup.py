#!/usr/bin/env python3
"""
Automatically sign up for YouTube in the currently open browser
"""

from playwright.sync_api import sync_playwright
import time

# Credentials for browser 797
email = "firelion847@automateyourbizz.xyz"
password = "Novaspark39!2026"
first_name = "Nova"
last_name = "Spark"
birthdate_month = "January"
birthdate_day = "1"
birthdate_year = "2001"

print("Connecting to browser 797...")

# The browser should already be open, connect to it
debug_url = "ws://127.0.0.1:54525/devtools/browser"  # You'll need to get this from AdsPower

with sync_playwright() as p:
    # Connect to the already open browser
    try:
        browser = p.chromium.connect_over_cdp(debug_url)
        context = browser.contexts[0]

        # Find the YouTube tab
        youtube_page = None
        for page in context.pages:
            if "youtube.com" in page.url:
                youtube_page = page
                break

        if not youtube_page:
            print("YouTube tab not found! Opening new tab...")
            youtube_page = context.new_page()
            youtube_page.goto("https://www.youtube.com", timeout=60000)
            time.sleep(3)

        print("Found YouTube page, starting signup...")

        # Click Sign in button
        print("Step 1: Clicking Sign in...")
        try:
            youtube_page.click('a:has-text("Sign in")', timeout=10000)
            time.sleep(3)
        except:
            print("Already on sign in page or button not found")

        # Click Create account
        print("Step 2: Looking for Create account...")
        try:
            # Wait for and click "Create account"
            youtube_page.click('span:has-text("Create account")', timeout=10000)
            time.sleep(2)

            # Click "For my personal use"
            youtube_page.click('li:has-text("For my personal use")', timeout=5000)
            time.sleep(2)
        except Exception as e:
            print(f"Create account step error: {e}")

        # Fill in name
        print("Step 3: Filling in name...")
        try:
            youtube_page.fill('input[name="firstName"]', first_name)
            time.sleep(0.5)
            youtube_page.fill('input[name="lastName"]', last_name)
            time.sleep(0.5)

            # Click Next
            youtube_page.click('button:has-text("Next")', timeout=5000)
            time.sleep(3)
        except Exception as e:
            print(f"Name fill error: {e}")

        # Fill in birthday and gender
        print("Step 4: Filling in birthday...")
        try:
            # Month dropdown
            youtube_page.select_option('select#month', label=birthdate_month)
            time.sleep(0.5)

            # Day
            youtube_page.fill('input#day', birthdate_day)
            time.sleep(0.5)

            # Year
            youtube_page.fill('input#year', birthdate_year)
            time.sleep(0.5)

            # Gender - select "Rather not say"
            try:
                youtube_page.select_option('select#gender', label="Rather not say")
            except:
                try:
                    youtube_page.select_option('select#gender', label="Prefer not to say")
                except:
                    print("Could not select gender option")
            time.sleep(1)

            # Click Next
            youtube_page.click('button:has-text("Next")', timeout=5000)
            time.sleep(3)
        except Exception as e:
            print(f"Birthday fill error: {e}")

        # Choose email option
        print("Step 5: Setting up email...")
        try:
            # Try to click "Use my current email address instead" if available
            try:
                youtube_page.click('div:has-text("Use my current email")', timeout=3000)
                time.sleep(2)
            except:
                print("No email option found, continuing...")

            # Enter email
            youtube_page.fill('input[type="email"]', email)
            time.sleep(1)

            # Click Next
            youtube_page.click('button:has-text("Next")', timeout=5000)
            time.sleep(5)
        except Exception as e:
            print(f"Email fill error: {e}")

        # Enter password
        print("Step 6: Setting password...")
        try:
            youtube_page.fill('input[name="Passwd"]', password)
            time.sleep(1)

            # Confirm password if needed
            try:
                youtube_page.fill('input[name="PasswdAgain"]', password)
                time.sleep(1)
            except:
                print("No password confirmation field")

            # Click Next
            youtube_page.click('button:has-text("Next")', timeout=5000)
            time.sleep(5)
        except Exception as e:
            print(f"Password fill error: {e}")

        print("\n" + "="*60)
        print("Signup form submitted!")
        print("="*60)
        print("\nPlease check the browser for:")
        print("  - Phone verification (if required)")
        print("  - Captcha verification")
        print("  - Terms of service acceptance")
        print("\nBrowser will stay open for manual completion.")

        # Keep browser open
        input("\nPress Enter when done...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

print("Done!")
