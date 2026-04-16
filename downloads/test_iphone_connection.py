#!/usr/bin/env python3
"""
Test iPhone connection with Appium
"""
from appium import webdriver
from appium.options.ios import XCUITestOptions
import sys

# Your iPhone details
UDID = "00008110-000828A1343B601E"
DEVICE_NAME = "iPhone1"

def test_connection():
    print("=" * 80)
    print("  iPhone Connection Test")
    print("=" * 80)
    print()
    print(f"Device: {DEVICE_NAME}")
    print(f"UDID: {UDID}")
    print()
    print("Attempting to connect...")
    print()

    # Configure connection options
    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.device_name = DEVICE_NAME
    options.udid = UDID
    options.automation_name = 'XCUITest'
    options.no_reset = True
    options.new_command_timeout = 300

    try:
        # Connect to iPhone via Appium
        print("Connecting to Appium server...")
        driver = webdriver.Remote('http://localhost:4723', options=options)

        print()
        print("✓ SUCCESS! iPhone connected!")
        print()
        print("Connection details:")
        print(f"  • Session ID: {driver.session_id}")
        print(f"  • Platform: {driver.capabilities.get('platformName')}")
        print(f"  • OS Version: {driver.capabilities.get('platformVersion')}")
        print(f"  • Device: {driver.capabilities.get('deviceName')}")
        print()

        # Close connection
        driver.quit()

        print("=" * 80)
        print("  Test Complete - Ready for Automation!")
        print("=" * 80)
        print()
        print("Next step: Run the TikTok automation script")
        print()
        print("  python3 downloads/iphone_3_accounts_viewer.py")
        print()

        return True

    except Exception as e:
        print()
        print("✗ Connection failed!")
        print()
        print(f"Error: {e}")
        print()
        print("=" * 80)
        print("Troubleshooting:")
        print("=" * 80)
        print()
        print("1. Make sure Appium server is running:")
        print("   /Users/faithtemporosa/.npm-global/bin/appium")
        print()
        print("2. Make sure iPhone is unlocked")
        print()
        print("3. Make sure iPhone is connected via USB cable")
        print()
        print("4. Check if WebDriverAgent needs to be installed:")
        print("   This may require Xcode to be installed")
        print()

        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
