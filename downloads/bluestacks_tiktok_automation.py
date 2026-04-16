#!/usr/bin/env python3
"""
Automate TikTok viewing in Bluestacks using ADB
Generates views and follows for target accounts
"""
import subprocess
import time
import random

# Configuration
TIKTOK_PACKAGE = "com.zhiliaoapp.musically"
TIKTOK_ACTIVITY = "com.ss.android.ugc.aweme.splash.SplashActivity"
ADB_HOST = "127.0.0.1:5555"

# Target accounts to view and follow
TARGET_ACCOUNTS = [
    "charlidamelio",
    "khaby.lame",
    "bellapoarch"
]

# Settings
VIDEOS_PER_ACCOUNT = 20  # Watch 20 videos per account
WATCH_TIME_MIN = 8  # Minimum seconds to watch
WATCH_TIME_MAX = 20  # Maximum seconds to watch

def run_adb(command):
    """Run ADB command"""
    try:
        result = subprocess.run(
            f"adb -s {ADB_HOST} {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"ADB error: {e}")
        return False, ""

def tap(x, y):
    """Tap at coordinates"""
    run_adb(f"shell input tap {x} {y}")
    time.sleep(0.5)

def swipe(x1, y1, x2, y2, duration=300):
    """Swipe gesture"""
    run_adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
    time.sleep(0.5)

def type_text(text):
    """Type text"""
    # Escape special characters
    text = text.replace(" ", "%s")
    run_adb(f"shell input text {text}")
    time.sleep(0.5)

def press_key(key):
    """Press a key (KEYCODE_BACK, KEYCODE_HOME, etc.)"""
    run_adb(f"shell input keyevent {key}")
    time.sleep(0.5)

def launch_tiktok():
    """Launch TikTok app"""
    print("Launching TikTok...")
    success, _ = run_adb(f"shell am start -n {TIKTOK_PACKAGE}/{TIKTOK_ACTIVITY}")
    if success:
        print("✓ TikTok launched")
        time.sleep(5)  # Wait for app to load
        return True
    else:
        print("✗ Failed to launch TikTok")
        return False

def search_account(username):
    """Search for a TikTok account"""
    print(f"\nSearching for @{username}...")

    # Tap search icon (top right, approximate coordinates)
    # Note: These coordinates are for standard Bluestacks resolution
    # You may need to adjust based on your screen
    tap(950, 150)  # Search button
    time.sleep(2)

    # Clear search field and type username
    tap(500, 200)  # Search field
    time.sleep(1)

    # Type username
    type_text(username)
    time.sleep(2)

    # Tap first result (the account)
    tap(500, 400)  # First search result
    time.sleep(3)

    print(f"✓ Opened @{username} profile")

def follow_account():
    """Follow the currently opened account"""
    print("Following account...")
    tap(900, 250)  # Follow button location (approximate)
    time.sleep(2)
    print("✓ Followed")

def watch_videos(count):
    """Watch multiple videos"""
    print(f"Watching {count} videos...")

    for i in range(count):
        # Random watch time
        watch_time = random.randint(WATCH_TIME_MIN, WATCH_TIME_MAX)
        print(f"  Video {i+1}/{count}: Watching for {watch_time}s...")
        time.sleep(watch_time)

        # Swipe up to next video
        swipe(500, 800, 500, 200, 300)
        time.sleep(1)

    print(f"✓ Watched {count} videos")

def go_home():
    """Return to For You page"""
    print("Returning to For You page...")
    press_key("KEYCODE_BACK")
    time.sleep(2)
    press_key("KEYCODE_BACK")
    time.sleep(2)

def check_connection():
    """Check if ADB is connected to Bluestacks"""
    print("Checking ADB connection...")
    success, output = run_adb("devices")

    if ADB_HOST in output:
        print(f"✓ Connected to Bluestacks ({ADB_HOST})")
        return True
    else:
        print(f"✗ Not connected to Bluestacks")
        print("\nTrying to connect...")
        subprocess.run(f"adb connect {ADB_HOST}", shell=True)
        time.sleep(2)

        success, output = run_adb("devices")
        if ADB_HOST in output:
            print(f"✓ Connected!")
            return True
        else:
            print("✗ Connection failed")
            print("\nMake sure:")
            print("  1. Bluestacks is running")
            print("  2. ADB is enabled in Bluestacks settings")
            print("  3. Run: adb connect 127.0.0.1:5555")
            return False

def main():
    print("=" * 70)
    print("  TikTok Bluestacks Automation - Views & Follows")
    print("=" * 70)
    print()
    print(f"Target accounts: {', '.join(TARGET_ACCOUNTS)}")
    print(f"Videos per account: {VIDEOS_PER_ACCOUNT}")
    print()
    print("=" * 70)
    print()

    # Check connection
    if not check_connection():
        return

    # Launch TikTok
    if not launch_tiktok():
        return

    # Process each target account
    for account in TARGET_ACCOUNTS:
        print()
        print("=" * 70)
        print(f"  Processing @{account}")
        print("=" * 70)

        try:
            # Search and open account
            search_account(account)

            # Follow account
            follow_account()

            # Tap on first video to start watching
            tap(500, 500)  # First video
            time.sleep(3)

            # Watch videos
            watch_videos(VIDEOS_PER_ACCOUNT)

            # Go back to home
            go_home()

            print(f"✓ Completed @{account}")
            print()

        except Exception as e:
            print(f"✗ Error processing @{account}: {e}")
            go_home()
            continue

    print()
    print("=" * 70)
    print("  AUTOMATION COMPLETE!")
    print("=" * 70)
    print()
    total_views = len(TARGET_ACCOUNTS) * VIDEOS_PER_ACCOUNT
    print(f"Generated approximately {total_views} views")
    print(f"Followed {len(TARGET_ACCOUNTS)} accounts")
    print()
    print("Check TikTok analytics to verify views registered.")

if __name__ == '__main__':
    main()
