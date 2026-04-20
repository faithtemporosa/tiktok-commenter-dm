#!/usr/bin/env python3
"""
Android Emulator TikTok Commenter - Target Accounts

Comment on specific target accounts using Android emulators (BlueStacks, NOX, etc.)
Uses Appium for mobile automation with stealth features

Requirements:
- Android emulator (BlueStacks, NOX, or Android Studio AVD)
- Appium server running: npm install -g appium
- TikTok app installed on emulator(s)
- ADB enabled on emulators

Usage: python3 comment_target_emulator.py

Install dependencies:
pip install appium-python-client selenium requests
"""

import time
import random
import json
import subprocess
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Appium imports
try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_APPIUM = True
except ImportError:
    HAS_APPIUM = False
    print("ERROR: Appium not installed. Run: pip install appium-python-client selenium")
    exit(1)

# Supabase for cloud sync
try:
    from supabase import create_client
    SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Warning: supabase not installed, stats won't sync to cloud")

# Configuration
EMULATOR_CONFIGS_PATH = 'emulator_configs.json'
TARGET_STATS_PATH = 'target_accounts_stats.json'
COMMENTED_VIDEOS_PATH = 'emulator_commented_videos.json'
DAILY_ACTIVITY_PATH = 'emulator_daily_activity.json'

# Target accounts
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
COMMENTS_PER_ACCOUNT = 2  # Comment on 2 videos per account
PARALLEL_EMULATORS = 2    # Run 2 emulators simultaneously
APPIUM_SERVER = 'http://localhost:4723'  # Appium server address

# Comments by niche
NICHE_COMMENTS = {
    'fitness': [
        'Love the gains content!',
        'Great tips! Been looking for this',
        'This is exactly what I needed to see',
        'Solid advice right here',
        'Thanks for sharing this!'
    ],
    'adventure': [
        'What an amazing journey!',
        'This is so inspiring!',
        'Living the dream! Love it',
        'Wow, this looks incredible',
        'Adding this to my bucket list'
    ],
    'tech': [
        'The future is here!',
        'This is incredible tech!',
        'Mind blown by this',
        'Game changer right here',
        'This is next level'
    ],
    'lifestyle': [
        'Beautiful content!',
        'So elegant!',
        'Love the aesthetic!',
        'This is goals',
        'Absolutely stunning'
    ],
    'default': [
        'This is fire!',
        'Love this vibe!',
        'Keep creating!',
        'Amazing work!',
        'Love this!'
    ]
}

def natural_delay(min_sec=1, max_sec=3):
    """Random delay to simulate human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_swipe(driver, start_x, start_y, end_x, end_y, duration=800):
    """Perform human-like swipe with variations"""
    # Add slight randomness to coordinates
    start_x += random.randint(-20, 20)
    start_y += random.randint(-20, 20)
    end_x += random.randint(-20, 20)
    end_y += random.randint(-20, 20)

    # Vary duration slightly
    duration += random.randint(-100, 100)

    driver.swipe(start_x, start_y, end_x, end_y, duration)
    natural_delay(0.5, 1.5)

def get_adb_devices():
    """Get list of connected Android devices/emulators"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        devices = []
        for line in lines:
            if '\tdevice' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return devices
    except Exception as e:
        print(f"Error getting ADB devices: {e}")
        return []

def load_emulator_configs():
    """Load emulator configurations"""
    try:
        with open(EMULATOR_CONFIGS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config
        configs = {
            'emulators': [
                {
                    'name': 'Emulator-1',
                    'udid': 'emulator-5554',
                    'tiktok_account': 'account1',
                    'device_name': 'Android Emulator'
                }
            ]
        }
        with open(EMULATOR_CONFIGS_PATH, 'w') as f:
            json.dump(configs, f, indent=2)
        return configs

def save_emulator_configs(configs):
    """Save emulator configurations"""
    with open(EMULATOR_CONFIGS_PATH, 'w') as f:
        json.dump(configs, f, indent=2)

def load_commented_videos(emulator_name=None):
    """Load commented videos for specific emulator"""
    try:
        with open(COMMENTED_VIDEOS_PATH, 'r') as f:
            data = json.load(f)
            if emulator_name:
                return set(data.get(emulator_name, []))
            return data
    except FileNotFoundError:
        return set() if emulator_name else {}

def save_commented_videos(emulator_name, video_id):
    """Save commented video for emulator"""
    try:
        with open(COMMENTED_VIDEOS_PATH, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    if emulator_name not in data:
        data[emulator_name] = []

    if video_id not in data[emulator_name]:
        data[emulator_name].append(video_id)

    with open(COMMENTED_VIDEOS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def create_driver(udid, device_name='Android Emulator'):
    """Create Appium driver for emulator"""
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = device_name
    options.udid = udid
    options.app_package = 'com.zhiliaoapp.musically'  # TikTok package
    options.app_activity = 'com.ss.android.ugc.aweme.splash.SplashActivity'
    options.no_reset = True  # Keep app data
    options.full_reset = False
    options.automation_name = 'UiAutomator2'

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    return driver

def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present"""
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except:
        return None

def tap_element(driver, element):
    """Tap element with human-like delay"""
    natural_delay(0.5, 1)
    element.click()
    natural_delay(0.5, 1.5)

def search_account(driver, account_name):
    """Search for TikTok account"""
    try:
        print(f"  Searching for @{account_name}...")

        # Tap search icon
        search_btn = wait_for_element(driver, AppiumBy.ANDROID_UIAUTOMATOR,
                                      'new UiSelector().resourceId("com.zhiliaoapp.musically:id/bgw")')
        if search_btn:
            tap_element(driver, search_btn)
        else:
            # Try alternative search button
            search_btn = driver.find_element(AppiumBy.XPATH,
                                            '//*[@content-desc="Search"]')
            tap_element(driver, search_btn)

        natural_delay(1, 2)

        # Type account name
        search_input = wait_for_element(driver, AppiumBy.CLASS_NAME, 'android.widget.EditText')
        if search_input:
            search_input.click()
            natural_delay(0.5, 1)

            # Type with human-like delays
            for char in account_name:
                search_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

            natural_delay(1, 2)

            # Tap first result (the account)
            try:
                first_result = driver.find_element(AppiumBy.XPATH,
                                                  '//*[@resource-id="com.zhiliaoapp.musically:id/title"]')
                tap_element(driver, first_result)
                return True
            except:
                print(f"  Could not find account @{account_name}")
                return False

        return False
    except Exception as e:
        print(f"  Error searching account: {e}")
        return False

def get_latest_videos(driver, count=2):
    """Get latest videos from profile"""
    try:
        natural_delay(2, 3)

        # Find video grid
        videos = []
        video_elements = driver.find_elements(AppiumBy.XPATH,
                                             '//*[@resource-id="com.zhiliaoapp.musically:id/video_cover"]')

        # Get first N videos
        for i, video_elem in enumerate(video_elements[:count]):
            videos.append({
                'element': video_elem,
                'index': i
            })

        return videos
    except Exception as e:
        print(f"  Error getting videos: {e}")
        return []

def open_video(driver, video_info):
    """Open video from profile grid"""
    try:
        tap_element(driver, video_info['element'])
        natural_delay(2, 3)
        return True
    except Exception as e:
        print(f"  Error opening video: {e}")
        return False

def watch_video_naturally(driver, duration=5):
    """Watch video with natural behavior"""
    print(f"  Watching video for {duration}s...")

    # Occasional scroll to see comments
    if random.random() < 0.3:
        size = driver.get_window_size()
        start_y = int(size['height'] * 0.8)
        end_y = int(size['height'] * 0.4)
        human_swipe(driver, size['width']//2, start_y, size['width']//2, end_y)
        time.sleep(1)
        # Swipe back
        human_swipe(driver, size['width']//2, end_y, size['width']//2, start_y)

    time.sleep(duration)

def post_comment(driver, comment_text):
    """Post comment on video"""
    try:
        print(f"  Posting comment: '{comment_text}'")

        # Tap comment button
        comment_btn = wait_for_element(driver, AppiumBy.ANDROID_UIAUTOMATOR,
                                       'new UiSelector().description("Comment")')
        if not comment_btn:
            comment_btn = driver.find_element(AppiumBy.XPATH,
                                             '//*[@content-desc="Comment"]')

        tap_element(driver, comment_btn)
        natural_delay(1, 2)

        # Find comment input
        comment_input = wait_for_element(driver, AppiumBy.CLASS_NAME,
                                        'android.widget.EditText')
        if comment_input:
            comment_input.click()
            natural_delay(0.5, 1)

            # Type comment with human-like speed
            for char in comment_text:
                comment_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            natural_delay(1, 2)

            # Tap post button
            post_btn = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
                                          'new UiSelector().text("Post")')
            tap_element(driver, post_btn)

            natural_delay(2, 3)

            # Close comment sheet (back button)
            driver.back()
            natural_delay(1, 2)

            print("  ✓ Comment posted")
            return True

        return False
    except Exception as e:
        print(f"  Error posting comment: {e}")
        return False

def go_back_to_profile(driver):
    """Go back to profile from video"""
    try:
        driver.back()
        natural_delay(1, 2)
    except:
        pass

def process_emulator(emulator_config):
    """Process one emulator - comment on target accounts"""
    emulator_name = emulator_config['name']
    udid = emulator_config['udid']

    print(f"\n{'='*60}")
    print(f"Emulator: {emulator_name} ({udid})")
    print(f"{'='*60}")

    driver = None
    try:
        # Create driver
        print(f"Connecting to {emulator_name}...")
        driver = create_driver(udid, emulator_config.get('device_name', 'Android'))

        natural_delay(2, 3)

        commented_videos = load_commented_videos(emulator_name)
        total_comments = 0

        # Process each target account
        for acc_idx, account in enumerate(TARGET_ACCOUNTS):
            print(f"\n[{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}")

            if not search_account(driver, account):
                continue

            # Get latest videos
            videos = get_latest_videos(driver, COMMENTS_PER_ACCOUNT)
            print(f"  Found {len(videos)} videos")

            for video_idx, video_info in enumerate(videos):
                # Check if already commented
                video_id = f"{account}_video_{video_info['index']}"
                if video_id in commented_videos:
                    print(f"  Video {video_idx+1}: Already commented - skipping")
                    continue

                # Open video
                if not open_video(driver, video_info):
                    continue

                # Watch naturally
                watch_duration = random.randint(3, 7)
                watch_video_naturally(driver, watch_duration)

                # Select random comment
                niche = 'default'
                if 'catalyst' in account or 'flock' in account:
                    niche = 'fitness'
                elif 'adventure' in account or 'ventur' in account:
                    niche = 'adventure'
                elif 'aisoiq' in account:
                    niche = 'tech'
                else:
                    niche = 'lifestyle'

                comment = random.choice(NICHE_COMMENTS.get(niche, NICHE_COMMENTS['default']))

                # Post comment
                if post_comment(driver, comment):
                    save_commented_videos(emulator_name, video_id)
                    total_comments += 1

                # Go back to profile
                go_back_to_profile(driver)
                natural_delay(2, 3)

            # Go back to home before next account
            driver.press_keycode(3)  # Home key
            natural_delay(2, 3)

            # Open TikTok again
            driver.activate_app('com.zhiliaoapp.musically')
            natural_delay(2, 3)

        print(f"\n{emulator_name} Summary:")
        print(f"  Total comments: {total_comments}")

        return {
            'emulator': emulator_name,
            'comments': total_comments,
            'status': 'completed'
        }

    except Exception as e:
        print(f"\nError with {emulator_name}: {e}")
        return {
            'emulator': emulator_name,
            'comments': 0,
            'status': 'failed',
            'error': str(e)
        }
    finally:
        if driver:
            driver.quit()

def main():
    """Main function"""
    print("="*60)
    print("Android Emulator TikTok Commenter")
    print("="*60)

    # Check Appium server
    try:
        resp = requests.get(f"{APPIUM_SERVER}/status", timeout=3)
        print(f"✓ Appium server running at {APPIUM_SERVER}")
    except:
        print(f"✗ Appium server not running at {APPIUM_SERVER}")
        print("Start Appium: appium")
        return

    # Get available devices
    devices = get_adb_devices()
    print(f"\nConnected devices: {len(devices)}")
    for device in devices:
        print(f"  - {device}")

    if not devices:
        print("\n✗ No emulators connected")
        print("Start your emulator (BlueStacks, NOX, etc.) and try again")
        return

    # Load configs
    configs = load_emulator_configs()
    emulators = configs['emulators']

    print(f"\nConfigured emulators: {len(emulators)}")
    print(f"Target accounts: {len(TARGET_ACCOUNTS)}")
    for acc in TARGET_ACCOUNTS:
        print(f"  - @{acc}")

    print(f"\nParallel emulators: {PARALLEL_EMULATORS}")
    print(f"Comments per account: {COMMENTS_PER_ACCOUNT}")

    # Process emulators in parallel
    results = []
    with ThreadPoolExecutor(max_workers=PARALLEL_EMULATORS) as executor:
        futures = {executor.submit(process_emulator, emu): emu for emu in emulators}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # Print summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    total_comments = sum(r['comments'] for r in results)
    successful = sum(1 for r in results if r['status'] == 'completed')

    print(f"Emulators processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total comments: {total_comments}")

    for result in results:
        status_icon = "✓" if result['status'] == 'completed' else "✗"
        print(f"  {status_icon} {result['emulator']}: {result['comments']} comments")

if __name__ == "__main__":
    if not HAS_APPIUM:
        print("Install Appium: pip install appium-python-client selenium")
    else:
        main()
