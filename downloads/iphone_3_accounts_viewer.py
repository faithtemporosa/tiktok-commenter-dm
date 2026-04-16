#!/usr/bin/env python3
"""
iPhone TikTok Automation - 3 Account Rotation
Automates viewing with your 3 existing TikTok accounts on iPhone

Strategy:
- Account 1: View 30 videos
- Switch to Account 2: View 30 videos
- Switch to Account 3: View 30 videos
- Total: 90 views per target account
- Spread across 3 accounts = More natural, less likely to be rate-limited
"""

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
import time
import sys
import subprocess
import json

# Configuration
TARGET_ACCOUNTS = [
    'charlidamelio',
    'addisonre',
    'bellapoarch',
]

VIDEOS_PER_ACCOUNT_PER_TIKTOK = 30  # Each TikTok account views 30 videos
WATCH_TIME_SECONDS = 15
BREAK_BETWEEN_ACCOUNTS = 30  # Seconds to wait before switching TikTok accounts

# Your 3 TikTok account usernames (for tracking)
TIKTOK_ACCOUNTS = [
    'Account 1',  # Replace with actual username
    'Account 2',  # Replace with actual username
    'Account 3',  # Replace with actual username
]

def check_iphone():
    """Check if iPhone is connected"""
    try:
        result = subprocess.run(['idevice_id', '-l'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print("✗ iPhone not connected")
            return None
    except FileNotFoundError:
        print("✗ Run setup first: bash downloads/setup_iphone_automation.sh")
        return None

def create_driver(udid):
    """Create Appium driver"""
    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.device_name = 'iPhone'
    options.udid = udid
    options.bundle_id = 'com.zhiliaoapp.musically'
    options.automation_name = 'XCUITest'
    options.no_reset = True

    try:
        driver = webdriver.Remote('http://localhost:4723', options=options)
        return driver
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Make sure Appium server is running:")
        print("  appium")
        return None

def view_videos_from_fyp(driver, num_videos, account_name):
    """
    View videos from For You Page
    Simpler than searching - just swipe and watch

    Args:
        driver: Appium driver
        num_videos: Number of videos to watch
        account_name: Which TikTok account is viewing (for logging)
    """
    print()
    print(f"Viewing {num_videos} videos with {account_name}...")
    print()

    try:
        # Make sure we're on For You page (home)
        driver.activate_app('com.zhiliaoapp.musically')
        time.sleep(2)

        # Tap home button to ensure we're on FYP
        try:
            home_btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, 'Home')
            home_btn.click()
            time.sleep(2)
        except:
            # Already on home, continue
            pass

        # Watch videos
        for i in range(num_videos):
            print(f"  Video {i+1}/{num_videos}: Watching ({WATCH_TIME_SECONDS}s)...", end='', flush=True)
            time.sleep(WATCH_TIME_SECONDS)
            print(" ✓")

            # Swipe up to next video
            if i < num_videos - 1:
                print(f"    → Next video")
                driver.swipe(200, 600, 200, 200, 500)
                time.sleep(2)

        print()
        print(f"✓ {account_name} watched {num_videos} videos")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def view_specific_account(driver, target_username, num_videos, viewing_account_name):
    """
    View videos from a specific account

    Args:
        driver: Appium driver
        target_username: TikTok account to view (e.g., 'charlidamelio')
        num_videos: Number of videos to watch
        viewing_account_name: Your TikTok account doing the viewing
    """
    print()
    print(f"{viewing_account_name} viewing @{target_username}...")
    print()

    try:
        # Activate TikTok
        driver.activate_app('com.zhiliaoapp.musically')
        time.sleep(2)

        # Open search
        print("  Opening search...")
        try:
            search_btn = driver.find_element(AppiumBy.ACCESSIBILITY_ID, 'Search')
            search_btn.click()
        except:
            driver.tap([(150, 800)])  # Tap search icon location
        time.sleep(2)

        # Search for account
        print(f"  Searching @{target_username}...")
        try:
            search_field = driver.find_element(AppiumBy.CLASS_NAME, 'XCUIElementTypeSearchField')
            search_field.click()
            time.sleep(1)
            search_field.send_keys(target_username)
            time.sleep(2)
        except Exception as e:
            print(f"  ✗ Search failed: {e}")
            return False

        # Click account
        print("  Opening account...")
        try:
            account = driver.find_element(AppiumBy.XPATH, f"//*[contains(@name, '@{target_username}')]")
            account.click()
            time.sleep(3)
        except:
            print(f"  ✗ Account not found")
            return False

        # Click first video
        print("  Opening videos...")
        driver.tap([(200, 400)])  # First video location
        time.sleep(3)

        # Watch videos
        for i in range(num_videos):
            print(f"  Video {i+1}/{num_videos}: Watching ({WATCH_TIME_SECONDS}s)...", end='', flush=True)
            time.sleep(WATCH_TIME_SECONDS)
            print(" ✓")

            if i < num_videos - 1:
                print(f"    → Next video")
                driver.swipe(200, 600, 200, 200, 500)
                time.sleep(2)

        print()
        print(f"✓ {viewing_account_name} watched {num_videos} videos from @{target_username}")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def switch_account_manual(current_account_num):
    """
    Prompt user to manually switch to next account
    (TikTok doesn't allow programmatic account switching for security)
    """
    next_account = (current_account_num % 3) + 1
    next_account_name = TIKTOK_ACCOUNTS[next_account - 1]

    print()
    print("=" * 80)
    print(f"TIME TO SWITCH TO {next_account_name}")
    print("=" * 80)
    print()
    print("Please manually switch TikTok accounts on your iPhone:")
    print()
    print(f"1. Tap 'Profile' (bottom right)")
    print(f"2. Tap your username at top")
    print(f"3. Select '{next_account_name}'")
    print(f"4. Press Enter here when ready...")
    print()
    input("Press Enter when you've switched accounts...")
    print()
    print(f"✓ Now using {next_account_name}")
    return next_account

def main():
    print("=" * 80)
    print("  IPHONE TIKTOK AUTOMATION - 3 Account Rotation")
    print("=" * 80)
    print()
    print("Strategy:")
    print(f"  • Each of your 3 TikTok accounts views {VIDEOS_PER_ACCOUNT_PER_TIKTOK} videos")
    print(f"  • Target accounts: {', '.join(['@' + acc for acc in TARGET_ACCOUNTS])}")
    print(f"  • Total views per target: {VIDEOS_PER_ACCOUNT_PER_TIKTOK * 3}")
    print()
    print("Your 3 TikTok accounts:")
    for i, acc in enumerate(TIKTOK_ACCOUNTS, 1):
        print(f"  {i}. {acc}")
    print()
    print("Note: You'll need to manually switch accounts when prompted")
    print("      (TikTok doesn't allow automated account switching)")
    print()
    print("=" * 80)
    print()

    # Check iPhone
    udid = check_iphone()
    if not udid:
        sys.exit(1)

    print("✓ iPhone connected")
    print()
    print("Make sure Appium is running in another terminal: appium")
    print()
    input("Press Enter to start...")

    # Create driver
    driver = create_driver(udid)
    if not driver:
        sys.exit(1)

    print("✓ Connected!")

    try:
        total_views = 0
        current_account = 1

        # For each target account
        for target_username in TARGET_ACCOUNTS:
            print()
            print("=" * 80)
            print(f"TARGET: @{target_username}")
            print("=" * 80)

            # Each of your 3 TikTok accounts will view this target
            for tiktok_account_num in range(1, 4):
                account_name = TIKTOK_ACCOUNTS[tiktok_account_num - 1]

                # View videos
                success = view_specific_account(
                    driver,
                    target_username,
                    VIDEOS_PER_ACCOUNT_PER_TIKTOK,
                    account_name
                )

                if success:
                    total_views += VIDEOS_PER_ACCOUNT_PER_TIKTOK

                # Switch to next account (if not last)
                if tiktok_account_num < 3:
                    print()
                    print(f"Taking {BREAK_BETWEEN_ACCOUNTS}s break before switching accounts...")
                    time.sleep(BREAK_BETWEEN_ACCOUNTS)
                    current_account = switch_account_manual(current_account)

            # Break between target accounts
            if target_username != TARGET_ACCOUNTS[-1]:
                print()
                print(f"✓ Finished @{target_username}")
                print(f"Taking 60s break before next target account...")
                time.sleep(60)

        # Summary
        print()
        print("=" * 80)
        print("SESSION COMPLETE!")
        print("=" * 80)
        print()
        print(f"Total views generated: ~{total_views}")
        print(f"Targets viewed: {len(TARGET_ACCOUNTS)}")
        print(f"Accounts used: 3")
        print()
        print("Breakdown:")
        for target in TARGET_ACCOUNTS:
            views_per_target = VIDEOS_PER_ACCOUNT_PER_TIKTOK * 3
            print(f"  @{target}: {views_per_target} views")
        print()

    except KeyboardInterrupt:
        print()
        print("Interrupted by user")

    finally:
        driver.quit()
        print("Done!")

if __name__ == '__main__':
    main()
