#!/usr/bin/env python3
"""
View target accounts - TIKTOK APP VERSION (iOS Mobile App Automation)
Uses Appium to control the actual TikTok app on a real iPhone or simulator
For new accounts (first 3 days): only scroll and view videos

Requirements:
    pip install Appium-Python-Client
    - Appium server running (appium or appium server)
    - TikTok app installed on iOS device/simulator
    - Xcode installed (for iOS)
    - WebDriverAgent set up (for real device)

Usage: python3 targeted_accounts_view_app.py
"""

import time
import random
import json
from datetime import datetime
from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============ CONFIGURATION ============

# Target accounts to view
TARGET_ACCOUNTS = [
    'flockboynation',
    'happyandyaya',
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]

# Settings
MAX_VIDEOS_TO_VIEW = 10  # Max videos to view per target account
STATS_PATH = 'target_accounts_view_stats_app.json'

# Appium settings for iOS (update these based on your setup)
APPIUM_SERVER = 'http://localhost:4723'
DEVICE_NAME = 'iPhone1'  # Your iPhone name
PLATFORM_VERSION = '18.3'  # Your iOS version (iOS 18.3.1)
TIKTOK_BUNDLE_ID = 'com.zhiliaoapp.musically'  # TikTok bundle ID
UDID = '00008110-00082A1343B601E'  # Your iPhone's UDID

# ============ HELPER FUNCTIONS ============

def load_stats():
    """Load viewing statistics"""
    try:
        with open(STATS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    """Save viewing statistics"""
    with open(STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)

def update_stats(account, videos_viewed):
    """Update statistics for a target account"""
    stats = load_stats()

    if account not in stats:
        stats[account] = {
            'total_views': 0,
            'sessions': [],
            'last_viewed': None
        }

    stats[account]['total_views'] += videos_viewed
    stats[account]['sessions'].append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'videos_viewed': videos_viewed
    })
    stats[account]['last_viewed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    save_stats(stats)

def setup_driver():
    """Initialize Appium driver for TikTok app (iOS)"""
    print('Connecting to TikTok app on iOS...')

    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.device_name = DEVICE_NAME
    options.platform_version = PLATFORM_VERSION
    options.bundle_id = TIKTOK_BUNDLE_ID
    options.no_reset = True  # Don't reset app state
    options.auto_accept_alerts = True  # Auto accept permission alerts

    if UDID:
        options.udid = UDID  # For real device

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    time.sleep(5)  # Wait for app to load

    print('✓ Connected to TikTok app on iOS')
    return driver

def search_account(driver, account):
    """Search for a TikTok account in the app (iOS)"""
    print(f'  Searching for @{account}...', flush=True)

    try:
        # Tap on search/discover icon (usually at the bottom)
        # iOS TikTok uses accessibility labels
        try:
            search_button = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID,
                'Discover'
            )
        except:
            # Try XPath if accessibility ID doesn't work
            search_button = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeButton[@name="Discover"] | //XCUIElementTypeButton[@label="Discover"]'
            )
        search_button.click()
        time.sleep(2)

        # Tap on search box
        try:
            search_box = driver.find_element(
                AppiumBy.CLASS_NAME,
                'XCUIElementTypeSearchField'
            )
        except:
            search_box = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeSearchField | //XCUIElementTypeTextField'
            )
        search_box.click()
        time.sleep(1)

        # Clear any existing text and type the account name
        search_box.clear()
        search_box.send_keys(account)
        time.sleep(2)

        # Tap on "Users" tab to see user results
        try:
            users_tab = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeButton[@name="Users"] | //XCUIElementTypeStaticText[@name="Users"]'
            )
            users_tab.click()
            time.sleep(1)
        except:
            print('  Users tab not found, continuing...', flush=True)

        # Tap on the account in search results
        try:
            account_result = driver.find_element(
                AppiumBy.XPATH,
                f'//XCUIElementTypeStaticText[contains(@name, "@{account}")] | //XCUIElementTypeStaticText[contains(@label, "@{account}")]'
            )
            account_result.click()
        except:
            # Try tapping on the first result
            first_result = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeCell[1]'
            )
            first_result.click()

        time.sleep(3)

        print(f'  ✓ Navigated to @{account}', flush=True)
        return True

    except Exception as e:
        print(f'  ✗ Failed to search for @{account}: {str(e)[:100]}', flush=True)
        return False

def view_videos_on_profile(driver, account):
    """View videos from a profile in the TikTok app (iOS)"""
    print(f'  Viewing videos from @{account}...', flush=True)

    videos_viewed = 0

    try:
        # Get screen size for swipe calculations
        size = driver.get_window_size()
        width = size['width']
        height = size['height']

        # Scroll down to load videos
        print('  Loading videos on profile...', flush=True)
        for _ in range(3):
            # Swipe up to load more videos
            driver.swipe(width // 2, height * 0.7, width // 2, height * 0.3, 800)
            time.sleep(1)

        # Find video thumbnails and tap the first one
        # TikTok shows videos in a grid on profile
        try:
            # Try to find first video thumbnail using iOS elements
            first_video = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeCell[1] | //XCUIElementTypeCollectionView//XCUIElementTypeCell[1]'
            )
            first_video.click()
            time.sleep(2)

            print(f'  Opened first video', flush=True)

            # Now we're in the video player - watch and swipe through videos
            for i in range(min(MAX_VIDEOS_TO_VIEW, 15)):
                # Watch video for random duration
                view_duration = random.randint(8, 18)
                print(f'  Watching video {i+1}/{MAX_VIDEOS_TO_VIEW}... ({view_duration}s)', flush=True)

                # Simulate watching behavior
                time.sleep(view_duration // 2)

                # Small scroll (like checking comments)
                driver.swipe(width // 2, height * 0.8, width // 2, height * 0.6, 300)
                time.sleep(1)

                # Scroll back up
                driver.swipe(width // 2, height * 0.6, width // 2, height * 0.8, 300)
                time.sleep(view_duration // 2)

                videos_viewed += 1

                # Swipe up to next video (standard TikTok navigation)
                if i < MAX_VIDEOS_TO_VIEW - 1:
                    driver.swipe(width // 2, height * 0.8, width // 2, height * 0.2, 400)
                    time.sleep(1.5)

            # Go back using iOS back gesture or button
            try:
                # Try to find back button
                back_button = driver.find_element(
                    AppiumBy.XPATH,
                    '//XCUIElementTypeButton[@name="Back"] | //XCUIElementTypeButton[@name="back"]'
                )
                back_button.click()
            except:
                # Use swipe from left edge (iOS back gesture)
                driver.swipe(10, height // 2, width // 2, height // 2, 300)

            time.sleep(2)

        except Exception as video_err:
            print(f'  ✗ Could not find videos: {str(video_err)[:100]}', flush=True)
            return videos_viewed

        return videos_viewed

    except Exception as e:
        print(f'  ✗ Error viewing videos: {str(e)[:100]}', flush=True)
        return videos_viewed

def go_to_home(driver):
    """Navigate back to TikTok home feed (iOS)"""
    try:
        # Tap home icon (usually bottom left)
        try:
            home_button = driver.find_element(
                AppiumBy.ACCESSIBILITY_ID,
                'Home'
            )
        except:
            home_button = driver.find_element(
                AppiumBy.XPATH,
                '//XCUIElementTypeButton[@name="Home"] | //XCUIElementTypeButton[@label="Home"]'
            )
        home_button.click()
        time.sleep(2)
        return True
    except:
        # If home button not found, try back gesture
        try:
            size = driver.get_window_size()
            # Swipe from left edge (iOS back gesture)
            for _ in range(3):
                driver.swipe(10, size['height'] // 2, size['width'] // 2, size['height'] // 2, 300)
                time.sleep(1)
        except:
            pass
        return False

def process_account(driver, account):
    """Process one target account - search and view videos"""
    print(f'\n[Processing @{account}]', flush=True)

    # Go to home first
    go_to_home(driver)

    # Search for the account
    if not search_account(driver, account):
        return 0

    # View videos on their profile
    videos_viewed = view_videos_on_profile(driver, account)

    # Update stats
    update_stats(account, videos_viewed)

    print(f'✓ @{account} complete: {videos_viewed} videos viewed', flush=True)

    # Wait before next account
    wait_time = random.randint(10, 20)
    print(f'  Waiting {wait_time}s before next account...', flush=True)
    time.sleep(wait_time)

    return videos_viewed

def main():
    print('=' * 60)
    print('  Target Accounts Viewer - TIKTOK APP (iOS)')
    print('=' * 60)
    print(f'\nTarget accounts: {len(TARGET_ACCOUNTS)}')
    for acc in TARGET_ACCOUNTS:
        print(f'  - @{acc}')
    print(f'\nSettings:')
    print(f'  - Max videos to view per account: {MAX_VIDEOS_TO_VIEW}')
    print(f'  - Appium server: {APPIUM_SERVER}')
    print(f'  - Device: {DEVICE_NAME}')
    print(f'  - iOS version: {PLATFORM_VERSION}')
    print()

    input('Make sure:\n  1. Appium server is running with xcuitest driver\n  2. iPhone/Simulator is connected\n  3. TikTok app is installed\n  4. You are logged into TikTok\n  5. WebDriverAgent is set up (for real device)\n\nPress ENTER to continue...')

    # Setup driver
    try:
        driver = setup_driver()
    except Exception as e:
        print(f'\n✗ Failed to connect to TikTok app: {e}')
        print('\nTroubleshooting:')
        print('  1. Make sure Appium server is running: appium')
        print('  2. Install xcuitest driver: appium driver install xcuitest')
        print('  3. Check device is connected: xcrun xctrace list devices')
        print('  4. For real device, set up WebDriverAgent in Xcode')
        print('  5. Make sure TikTok is installed on the device')
        return

    total_videos = 0
    accounts_completed = 0

    try:
        # Process each target account
        for idx, account in enumerate(TARGET_ACCOUNTS):
            print(f'\n[Account {idx+1}/{len(TARGET_ACCOUNTS)}]', flush=True)

            videos = process_account(driver, account)
            total_videos += videos

            if videos > 0:
                accounts_completed += 1

    except KeyboardInterrupt:
        print('\n\n⚠ Interrupted by user')
    except Exception as e:
        print(f'\n✗ Error: {e}')
    finally:
        print('\nClosing connection...')
        driver.quit()

    # Final summary
    print('\n' + '=' * 60)
    print('  FINAL SUMMARY - TIKTOK APP (iOS)')
    print('=' * 60)
    print(f'Accounts processed: {accounts_completed}/{len(TARGET_ACCOUNTS)}')
    print(f'Total videos viewed: {total_videos}')
    print()

if __name__ == '__main__':
    main()
