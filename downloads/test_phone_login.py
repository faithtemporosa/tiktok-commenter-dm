#!/usr/bin/env python3
"""
Test TikTok phone login to diagnose blocking issues
"""
from playwright.sync_api import sync_playwright
import time

def test_phone_login():
    print("=" * 80)
    print("  TIKTOK PHONE LOGIN DIAGNOSTIC")
    print("=" * 80)
    print()

    with sync_playwright() as p:
        print("Step 1: Opening Chrome browser...")
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
            ]
        )

        # Use desktop context (not mobile)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # Remove automation indicators
        page = context.new_page()

        print("Step 2: Navigating to TikTok login...")
        page.goto('https://www.tiktok.com/login/phone-or-email/phone')
        time.sleep(3)

        print()
        print("=" * 80)
        print("MANUAL TEST INSTRUCTIONS")
        print("=" * 80)
        print()
        print("A browser window should now be open. Please try to:")
        print()
        print("1. Select your country code (e.g., +1 for US)")
        print("2. Enter a phone number")
        print("3. Click 'Send code'")
        print()
        print("=" * 80)
        print("WHAT TO LOOK FOR:")
        print("=" * 80)
        print()
        print("Error 1: 'Too many attempts'")
        print("  → TikTok has temporarily blocked your IP")
        print("  → Solution: Wait 24 hours OR use different IP/proxy")
        print()
        print("Error 2: 'This phone number is invalid'")
        print("  → Phone number format wrong OR already used")
        print("  → Solution: Try different number format or new number")
        print()
        print("Error 3: 'Verification code not sent'")
        print("  → TikTok suspects automation/VoIP number")
        print("  → Solution: Use real mobile number (not VoIP/virtual)")
        print()
        print("Error 4: 'Captcha/Puzzle slider'")
        print("  → TikTok wants to verify you're human")
        print("  → Solution: Complete the puzzle (normal behavior)")
        print()
        print("Error 5: Page keeps refreshing/redirecting")
        print("  → TikTok detected automation")
        print("  → Solution: Use real mobile device instead of browser")
        print()
        print("=" * 80)
        print()
        input("Press Enter when you've finished testing or seen an error...")

        # Take screenshot of current state
        screenshot_path = 'downloads/phone_login_error.png'
        page.screenshot(path=screenshot_path)
        print(f"\n✓ Screenshot saved: {screenshot_path}")
        print()

        # Check for common error messages
        print("Checking for error messages...")
        print()

        errors_to_check = [
            ('Too many attempts', 'text=/too many/i'),
            ('Invalid phone', 'text=/invalid/i'),
            ('Suspicious activity', 'text=/suspicious/i'),
            ('Rate limit', 'text=/rate limit/i'),
            ('Try again later', 'text=/try again later/i'),
        ]

        found_errors = []
        for error_name, selector in errors_to_check:
            try:
                if page.locator(selector).count() > 0:
                    found_errors.append(error_name)
                    print(f"  ✗ Found: {error_name}")
            except:
                pass

        if not found_errors:
            print("  ✓ No obvious error messages detected")
            print("    (This doesn't mean it's working - check browser manually)")

        print()
        print("=" * 80)
        print("DIAGNOSIS & SOLUTIONS")
        print("=" * 80)
        print()

        if 'Too many attempts' in found_errors or 'Try again later' in found_errors:
            print("ISSUE DETECTED: Rate Limited / Too Many Attempts")
            print()
            print("Cause:")
            print("  • You've tried logging in too many times from this IP")
            print("  • TikTok blocked your IP temporarily (usually 24 hours)")
            print()
            print("Solutions:")
            print("  1. Wait 24 hours and try again")
            print("  2. Use a different IP address/proxy")
            print("  3. Try from mobile device (4G/5G, not WiFi)")
            print("  4. Use VPN to change your IP")
            print()

        elif 'Invalid phone' in found_errors:
            print("ISSUE DETECTED: Invalid Phone Number")
            print()
            print("Possible Causes:")
            print("  • Phone number already registered to another TikTok account")
            print("  • VoIP/virtual number (TikTok blocks these)")
            print("  • Wrong format (need country code, e.g., +1 555-123-4567)")
            print()
            print("Solutions:")
            print("  1. Use a real mobile number (not Google Voice, etc.)")
            print("  2. Use SMS verification service (SMS-Activate, 5SIM)")
            print("  3. Try different phone number that hasn't been used")
            print()

        else:
            print("GENERAL DIAGNOSIS:")
            print()
            print("Why phone login might fail in browsers:")
            print()
            print("1. TikTok Anti-Automation Detection")
            print("   • TikTok can detect Playwright/Selenium")
            print("   • Even normal Chrome might be flagged if too many attempts")
            print("   • AdsPower browsers are even more detectable")
            print()
            print("2. IP Reputation")
            print("   • If your IP/proxy was used for automation before")
            print("   • Data center IPs are more suspicious than residential")
            print("   • Shared proxies have bad reputation")
            print()
            print("3. Browser Fingerprinting")
            print("   • TikTok checks browser fingerprint consistency")
            print("   • Inconsistent fingerprints = Suspicious")
            print("   • AdsPower modifies fingerprints (can be detected)")
            print()
            print("=" * 80)
            print("RECOMMENDED SOLUTION")
            print("=" * 80)
            print()
            print("Best approach: Use REAL MOBILE DEVICE")
            print()
            print("Why mobile works better:")
            print("  ✓ TikTok trusts mobile app more than web browsers")
            print("  ✓ Uses mobile IP (harder to detect)")
            print("  ✓ Natural device fingerprint")
            print("  ✓ No automation detection")
            print()
            print("Options:")
            print()
            print("Option 1: Android Emulator (NoxPlayer)")
            print("  • Emulates real Android device")
            print("  • TikTok app thinks it's real phone")
            print("  • Can run multiple instances")
            print("  • Free and works on Mac")
            print()
            print("Option 2: Real Physical Phone")
            print("  • Use your Android phone")
            print("  • Most reliable method")
            print("  • Can only do 1 account at a time")
            print()
            print("Option 3: Wait 24-48 Hours")
            print("  • Sometimes TikTok blocks are temporary")
            print("  • Try again from different network")
            print("  • Use mobile data instead of WiFi")
            print()

        browser.close()

if __name__ == '__main__':
    test_phone_login()
