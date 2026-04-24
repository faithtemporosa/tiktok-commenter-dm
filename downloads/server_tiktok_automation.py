#!/usr/bin/env python3
"""
Server TikTok Automation - Android Emulators
=============================================
Runs on Ubuntu server with 10 Android emulators.
Uses Appium for TikTok app automation.

Features:
- Comment on target accounts
- View videos naturally
- Track activity in Supabase
- Run multiple emulators in parallel

Requirements:
- Appium running: appium
- ADB connected: adb devices
- TikTok installed and logged in on each emulator

Usage:
    python3 server_tiktok_automation.py
"""

import time
import random
import json
import subprocess
import requests
from datetime import datetime
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
    print("ERROR: Install Appium: pip3 install appium-python-client selenium --break-system-packages")

# Supabase
try:
    from supabase import create_client
    SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    HAS_SUPABASE = True
except:
    HAS_SUPABASE = False
    print("Warning: Supabase not available")

# =============================================================================
# CONFIGURATION
# =============================================================================
ADB_PATH = "/root/android-sdk/platform-tools/adb"
APPIUM_SERVER = "http://localhost:4723"
PARALLEL_EMULATORS = 3
COMMENTS_PER_ACCOUNT = 2

# All 10 emulators
EMULATORS = [
    {"name": "Emulator-1", "udid": "emulator-5554"},
    {"name": "Emulator-2", "udid": "emulator-5556"},
    {"name": "Emulator-3", "udid": "emulator-5558"},
    {"name": "Emulator-4", "udid": "emulator-5560"},
    {"name": "Emulator-5", "udid": "emulator-5562"},
    {"name": "Emulator-6", "udid": "emulator-5564"},
    {"name": "Emulator-7", "udid": "emulator-5566"},
    {"name": "Emulator-8", "udid": "emulator-5568"},
    {"name": "Emulator-9", "udid": "emulator-5570"},
    {"name": "Emulator-10", "udid": "emulator-5572"},
]

# Target accounts to comment on
TARGET_ACCOUNTS = [
    'flockboynation',
    'happyandyaya',
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]

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

# =============================================================================
# HELPERS
# =============================================================================
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def natural_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def get_adb_devices():
    """Get list of connected emulators"""
    try:
        result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = []
        for line in lines:
            if '\tdevice' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return devices
    except Exception as e:
        log(f"Error getting ADB devices: {e}")
        return []

def check_appium():
    """Check if Appium server is running"""
    try:
        resp = requests.get(f"{APPIUM_SERVER}/status", timeout=3)
        return resp.status_code == 200
    except:
        return False

def create_driver(udid, device_name='Android Emulator'):
    """Create Appium driver for emulator"""
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = device_name
    options.udid = udid
    options.app_package = 'com.zhiliaoapp.musically'
    options.app_activity = 'com.ss.android.ugc.aweme.splash.SplashActivity'
    options.no_reset = True
    options.full_reset = False
    options.automation_name = 'UiAutomator2'
    options.new_command_timeout = 300

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
    """Tap element with delay"""
    natural_delay(0.3, 0.8)
    element.click()
    natural_delay(0.5, 1)

def human_swipe(driver, start_x, start_y, end_x, end_y, duration=800):
    """Human-like swipe"""
    start_x += random.randint(-20, 20)
    start_y += random.randint(-20, 20)
    end_x += random.randint(-20, 20)
    end_y += random.randint(-20, 20)
    duration += random.randint(-100, 100)
    driver.swipe(start_x, start_y, end_x, end_y, duration)
    natural_delay(0.5, 1)

# =============================================================================
# TIKTOK ACTIONS
# =============================================================================
def search_account(driver, account_name):
    """Search for TikTok account"""
    try:
        log(f"  Searching for @{account_name}...")

        # Tap search icon
        search_btn = wait_for_element(driver, AppiumBy.XPATH, '//*[@content-desc="Search"]', timeout=5)
        if not search_btn:
            search_btn = wait_for_element(driver, AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().resourceId("com.zhiliaoapp.musically:id/bgw")')

        if search_btn:
            tap_element(driver, search_btn)
        else:
            log(f"  Could not find search button")
            return False

        natural_delay(1, 2)

        # Type account name
        search_input = wait_for_element(driver, AppiumBy.CLASS_NAME, 'android.widget.EditText')
        if search_input:
            search_input.click()
            natural_delay(0.5, 1)

            # Type naturally
            for char in account_name:
                search_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            natural_delay(1, 2)

            # Press enter/search
            driver.press_keycode(66)  # Enter key
            natural_delay(2, 3)

            # Click on Users tab
            try:
                users_tab = driver.find_element(AppiumBy.XPATH, '//*[contains(@text, "Users") or contains(@text, "Accounts")]')
                tap_element(driver, users_tab)
                natural_delay(1, 2)
            except:
                pass

            # Tap first result
            try:
                first_result = wait_for_element(driver, AppiumBy.XPATH,
                    f'//*[contains(@text, "{account_name}")]', timeout=5)
                if first_result:
                    tap_element(driver, first_result)
                    natural_delay(2, 3)
                    return True
            except:
                pass

        log(f"  Could not find @{account_name}")
        return False
    except Exception as e:
        log(f"  Error searching: {e}")
        return False

def get_latest_videos(driver, count=2):
    """Get latest videos from profile"""
    try:
        natural_delay(2, 3)

        # Find video thumbnails
        videos = []
        video_elements = driver.find_elements(AppiumBy.XPATH,
            '//*[@resource-id="com.zhiliaoapp.musically:id/cover"]')

        if not video_elements:
            video_elements = driver.find_elements(AppiumBy.XPATH,
                '//*[contains(@resource-id, "video") or contains(@resource-id, "cover")]')

        for i, elem in enumerate(video_elements[:count]):
            videos.append({'element': elem, 'index': i})

        return videos
    except Exception as e:
        log(f"  Error getting videos: {e}")
        return []

def watch_video(driver, duration=5):
    """Watch video naturally"""
    log(f"  Watching for {duration}s...")

    # Occasional interaction
    if random.random() < 0.3:
        size = driver.get_window_size()
        start_y = int(size['height'] * 0.7)
        end_y = int(size['height'] * 0.5)
        human_swipe(driver, size['width']//2, start_y, size['width']//2, end_y)
        time.sleep(1)
        human_swipe(driver, size['width']//2, end_y, size['width']//2, start_y)

    time.sleep(duration)

def post_comment(driver, comment_text):
    """Post comment on video"""
    try:
        log(f"  Posting: '{comment_text}'")

        # Tap comment button
        comment_btn = wait_for_element(driver, AppiumBy.XPATH, '//*[@content-desc="Comment"]')
        if not comment_btn:
            comment_btn = wait_for_element(driver, AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().description("Comment")')

        if not comment_btn:
            log(f"  Could not find comment button")
            return False

        tap_element(driver, comment_btn)
        natural_delay(1, 2)

        # Find comment input
        comment_input = wait_for_element(driver, AppiumBy.CLASS_NAME, 'android.widget.EditText')
        if comment_input:
            comment_input.click()
            natural_delay(0.5, 1)

            # Type comment naturally
            for char in comment_text:
                comment_input.send_keys(char)
                time.sleep(random.uniform(0.03, 0.1))

            natural_delay(1, 2)

            # Tap Post button
            try:
                post_btn = driver.find_element(AppiumBy.XPATH, '//*[contains(@text, "Post")]')
                tap_element(driver, post_btn)
                natural_delay(2, 3)

                # Close comment sheet
                driver.back()
                natural_delay(1, 2)

                log(f"  Comment posted!")
                return True
            except:
                log(f"  Could not find Post button")

        return False
    except Exception as e:
        log(f"  Error posting comment: {e}")
        return False

def get_niche_comment(account_name):
    """Get comment based on account niche"""
    if 'catalyst' in account_name or 'flock' in account_name:
        niche = 'fitness'
    elif 'adventure' in account_name or 'ventur' in account_name:
        niche = 'adventure'
    elif 'aisoiq' in account_name:
        niche = 'tech'
    elif 'grace' in account_name or 'happy' in account_name:
        niche = 'lifestyle'
    else:
        niche = 'default'

    return random.choice(NICHE_COMMENTS.get(niche, NICHE_COMMENTS['default']))

# =============================================================================
# MAIN PROCESSING
# =============================================================================
def process_emulator(emulator):
    """Process one emulator - comment on target accounts"""
    name = emulator['name']
    udid = emulator['udid']

    log(f"\n{'='*50}")
    log(f"Starting {name} ({udid})")
    log(f"{'='*50}")

    driver = None
    total_comments = 0

    try:
        log(f"Connecting to {name}...")
        driver = create_driver(udid)
        natural_delay(3, 5)

        for acc_idx, account in enumerate(TARGET_ACCOUNTS):
            log(f"\n[{acc_idx+1}/{len(TARGET_ACCOUNTS)}] @{account}")

            if not search_account(driver, account):
                # Go back to home
                driver.press_keycode(3)
                natural_delay(2, 3)
                driver.activate_app('com.zhiliaoapp.musically')
                natural_delay(2, 3)
                continue

            videos = get_latest_videos(driver, COMMENTS_PER_ACCOUNT)
            log(f"  Found {len(videos)} videos")

            for video_idx, video_info in enumerate(videos):
                try:
                    # Open video
                    tap_element(driver, video_info['element'])
                    natural_delay(2, 3)

                    # Watch naturally
                    watch_duration = random.randint(4, 8)
                    watch_video(driver, watch_duration)

                    # Post comment
                    comment = get_niche_comment(account)
                    if post_comment(driver, comment):
                        total_comments += 1

                    # Go back to profile
                    driver.back()
                    natural_delay(2, 3)

                except Exception as e:
                    log(f"  Error on video {video_idx}: {e}")
                    driver.back()
                    natural_delay(1, 2)

            # Go home before next account
            driver.press_keycode(3)
            natural_delay(2, 3)
            driver.activate_app('com.zhiliaoapp.musically')
            natural_delay(3, 5)

        log(f"\n{name} completed: {total_comments} comments")
        return {'emulator': name, 'comments': total_comments, 'status': 'completed'}

    except Exception as e:
        log(f"Error with {name}: {e}")
        return {'emulator': name, 'comments': total_comments, 'status': 'failed', 'error': str(e)}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    log("="*60)
    log("Server TikTok Automation - Android Emulators")
    log("="*60)

    # Check Appium
    if not check_appium():
        log("ERROR: Appium not running!")
        log("Start Appium: appium")
        return
    log("Appium server running")

    # Get connected devices
    devices = get_adb_devices()
    log(f"Connected emulators: {len(devices)}")
    for d in devices:
        log(f"  - {d}")

    if not devices:
        log("ERROR: No emulators connected")
        return

    # Filter to only connected emulators
    active_emulators = [e for e in EMULATORS if e['udid'] in devices]
    log(f"Active emulators: {len(active_emulators)}")

    if not active_emulators:
        log("ERROR: No matching emulators")
        return

    log(f"Target accounts: {len(TARGET_ACCOUNTS)}")
    log(f"Parallel emulators: {PARALLEL_EMULATORS}")

    # Process emulators in parallel
    results = []
    with ThreadPoolExecutor(max_workers=PARALLEL_EMULATORS) as executor:
        futures = {executor.submit(process_emulator, emu): emu for emu in active_emulators}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # Summary
    log("\n" + "="*60)
    log("FINAL SUMMARY")
    log("="*60)

    total_comments = sum(r['comments'] for r in results)
    successful = sum(1 for r in results if r['status'] == 'completed')

    log(f"Emulators processed: {len(results)}")
    log(f"Successful: {successful}")
    log(f"Total comments: {total_comments}")

    for r in results:
        icon = "OK" if r['status'] == 'completed' else "FAIL"
        log(f"  [{icon}] {r['emulator']}: {r['comments']} comments")

    # Save to Supabase
    if HAS_SUPABASE:
        try:
            supabase.table('automation_runs').insert({
                'run_type': 'server_emulator',
                'emulators': len(results),
                'total_comments': total_comments,
                'results': json.dumps(results),
                'created_at': datetime.now().isoformat()
            }).execute()
            log("Results saved to Supabase")
        except Exception as e:
            log(f"Supabase error: {e}")

if __name__ == "__main__":
    if not HAS_APPIUM:
        print("Install Appium: pip3 install appium-python-client selenium --break-system-packages")
    else:
        main()
