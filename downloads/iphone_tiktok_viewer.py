#!/usr/bin/env python3
"""
iPhone TikTok Automation - Views & Follows
Control your iPhone from Mac via USB to automate TikTok viewing

Requirements:
- iPhone connected via USB
- Appium installed: npm install -g appium
- XCUITest driver: appium driver install xcuitest
- Python packages: pip3 install appium-python-client
"""

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
import time
import sys
import subprocess

# Configuration
TARGET_ACCOUNTS = [
    'charlidamelio',
    'addisonre',
    'bellapoarch',
]

VIDEOS_PER_ACCOUNT = 20
WATCH_TIME_SECONDS = 15  # Watch each video for 15 seconds
FOLLOW_ACCOUNTS = True  # Set to True to follow accounts

def check_prerequisites():
    """Check if Appium and iPhone are ready"""
    print("Checking prerequisites...")
    print()

    # Check if Appium is installed
    try:
        result = subprocess.run(['appium', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Appium installed: {result.stdout.strip()}")
        else:
            print("✗ Appium not found. Install with: npm install -g appium")
            return False
    except FileNotFoundError:
        print("✗ Appium not found. Install with: npm install -g appium")
        return False

    # Check if iPhone is connected
    try:
        result = subprocess.run(['idevice_id', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            udid = result.stdout.strip()
            print(f"✓ iPhone connected: {udid}")
            return udid
        else:
            print("✗ iPhone not connected. Connect via USB and trust this computer.")
            return False
    except FileNotFoundError:
        print("✗ idevice_id not found. Install with: brew install libimobiledevice")
        return False

def get_iphone_name():
    """Get iPhone name"""
    try:
        result = subprocess.run(['ideviceinfo', '-k', 'DeviceName'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return "iPhone"
    except:
        return "iPhone"

def start_appium_server():
    """Start Appium server in background"""
    print()
    print("=" * 80)
    print("IMPORTANT: Start Appium Server First")
    print("=" * 80)
    print()
    print("In a separate terminal window, run:")
    print()
    print("  appium")
    print()
    print("Then press Enter here to continue...")
    input()

def create_driver(udid):
    """Create Appium driver for iPhone"""
    print()
    print("Connecting to iPhone...")

    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.device_name = get_iphone_name()
    options.udid = udid
    options.bundle_id = 'com.zhiliaoapp.musically'  # TikTok bundle ID
    options.automation_name = 'XCUITest'
    options.no_reset = True  # Don't reset app state
    options.new_command_timeout = 300

    try:
        driver = webdriver.Remote('http://localhost:4723', options=options)
        print("✓ Connected to iPhone")
        return driver
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Appium server is running (appium)")
        print("  2. Make sure iPhone is unlocked")
        print("  3. Make sure TikTok app is installed")
        print("  4. Make sure Developer Mode is enabled on iPhone")
        return None

def wait_and_log(seconds, message):
    """Wait with progress indicator"""
    print(f"{message} ({seconds}s)", end='', flush=True)
    for i in range(seconds):
        time.sleep(1)
        print('.', end='', flush=True)
    print(' Done!')

def view_account_videos(driver, username, num_videos=20, follow=False):
    """
    View videos from a specific TikTok account

    Args:
        driver: Appium driver instance
        username: TikTok username (without @)
        num_videos: Number of videos to watch
        follow: Whether to follow the account
    """
    print()
    print("=" * 80)
    print(f"Viewing @{username}")
    print("=" * 80)
    print()

    try:
        # Make sure TikTok is active
        driver.activate_app('com.zhiliaoapp.musically')
        time.sleep(2)

        # Tap search (bottom navigation)
        print("Step 1: Opening search...")
        try:
            # Try to find search button by accessibility ID
            search_btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, 'Search')
            search_btn.click()
        except:
            # Fallback: tap approximate location (adjust if needed)
            driver.tap([(150, 800)])  # Approximate search button location
        time.sleep(2)

        # Tap search field and enter username
        print(f"Step 2: Searching for @{username}...")
        try:
            search_field = driver.find_element(AppiumBy.CLASS_NAME, 'XCUIElementTypeSearchField')
            search_field.click()
            time.sleep(1)
            search_field.send_keys(username)
            time.sleep(2)
        except Exception as e:
            print(f"  Could not find search field: {e}")
            print("  Make sure you're on the Search screen")
            return False

        # Tap on the user account in search results
        print("Step 3: Opening account...")
        try:
            # Look for the username in results
            account = driver.find_element(AppiumBy.XPATH, f"//*[contains(@name, '@{username}')]")
            account.click()
            time.sleep(3)
        except:
            print(f"  Could not find @{username} in search results")
            return False

        # Follow the account if requested
        if follow:
            print("Step 4: Following account...")
            try:
                follow_btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, 'Follow')
                follow_btn.click()
                time.sleep(1)
                print("  ✓ Followed!")
            except:
                print("  Already following or button not found")

        # Click first video
        print("Step 5: Opening first video...")
        try:
            # Tap approximate location of first video (adjust if needed)
            driver.tap([(200, 400)])
            time.sleep(3)
        except:
            print("  Could not open video")
            return False

        # Watch videos
        print(f"Step 6: Watching {num_videos} videos...")
        print()

        for i in range(num_videos):
            print(f"  Video {i+1}/{num_videos}:", end=' ')
            wait_and_log(WATCH_TIME_SECONDS, "Watching")

            # Swipe up to next video
            if i < num_videos - 1:  # Don't swipe after last video
                print("    Swiping to next video...")
                driver.swipe(200, 600, 200, 200, 500)  # Swipe up
                time.sleep(2)

        print()
        print(f"✓ Finished watching {num_videos} videos from @{username}")
        return True

    except Exception as e:
        print(f"✗ Error while viewing @{username}: {e}")
        return False

def go_home(driver):
    """Return to TikTok home screen"""
    print()
    print("Returning to home...")
    try:
        # Press home button in TikTok (bottom left)
        driver.tap([(50, 800)])
        time.sleep(2)
    except:
        pass

def main():
    print("=" * 80)
    print("  IPHONE TIKTOK AUTOMATION - Views & Follows")
    print("=" * 80)
    print()
    print("This script will:")
    print(f"  • View {VIDEOS_PER_ACCOUNT} videos from each target account")
    print(f"  • Watch each video for {WATCH_TIME_SECONDS} seconds")
    if FOLLOW_ACCOUNTS:
        print(f"  • Follow each account")
    print()
    print(f"Target accounts: {', '.join(['@' + acc for acc in TARGET_ACCOUNTS])}")
    print()
    print("=" * 80)
    print()

    # Check prerequisites
    udid = check_prerequisites()
    if not udid:
        print()
        print("Please install missing prerequisites and try again.")
        sys.exit(1)

    print()
    print("✓ All prerequisites met!")

    # Start Appium server prompt
    start_appium_server()

    # Create driver
    driver = create_driver(udid)
    if not driver:
        sys.exit(1)

    try:
        # Process each target account
        success_count = 0
        fail_count = 0

        for username in TARGET_ACCOUNTS:
            success = view_account_videos(
                driver,
                username,
                num_videos=VIDEOS_PER_ACCOUNT,
                follow=FOLLOW_ACCOUNTS
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

            # Go back to home between accounts
            if username != TARGET_ACCOUNTS[-1]:  # Not last account
                go_home(driver)
                time.sleep(3)

        # Summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"  ✓ Successful: {success_count} accounts")
        print(f"  ✗ Failed: {fail_count} accounts")
        print(f"  Total videos watched: ~{success_count * VIDEOS_PER_ACCOUNT}")
        print()

    except KeyboardInterrupt:
        print()
        print("Interrupted by user")

    finally:
        print()
        print("Closing connection...")
        driver.quit()
        print("Done!")

if __name__ == '__main__':
    main()
