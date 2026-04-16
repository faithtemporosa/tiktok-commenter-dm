#!/usr/bin/env python3
"""
Docker TikTok Automation
Controls 3 Docker Android containers for automated TikTok viewing
"""

import subprocess
import time
import sys

# Container configuration
CONTAINERS = [
    {'name': 'tiktok-1', 'adb_port': 5555, 'web_port': 6080},
    {'name': 'tiktok-2', 'adb_port': 5556, 'web_port': 6081},
    {'name': 'tiktok-3', 'adb_port': 5557, 'web_port': 6082},
]

TARGET_ACCOUNTS = ['charlidamelio', 'addisonre', 'bellapoarch']
VIDEOS_PER_ACCOUNT = 30
WATCH_TIME = 15  # seconds per video

def run_adb(port, command):
    """Execute ADB command on specific container"""
    full_cmd = f"adb -s localhost:{port} shell {command}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def tap(port, x, y):
    """Tap at coordinates"""
    run_adb(port, f"input tap {x} {y}")
    time.sleep(1)

def swipe(port, x1, y1, x2, y2, duration=500):
    """Swipe gesture"""
    run_adb(port, f"input swipe {x1} {y1} {x2} {y2} {duration}")
    time.sleep(1)

def type_text(port, text):
    """Type text (spaces replaced with %s)"""
    text = text.replace(' ', '%s')
    run_adb(port, f"input text {text}")
    time.sleep(1)

def open_tiktok(port):
    """Open TikTok app"""
    run_adb(port, "am start -n com.zhiliaoapp.musically/.MainActivity")
    time.sleep(3)

def search_account(port, username):
    """Search for TikTok account"""
    # Tap search button
    tap(port, 540, 1800)  # Search icon location
    time.sleep(2)

    # Tap search field
    tap(port, 540, 300)
    time.sleep(1)

    # Type username
    type_text(port, username)
    time.sleep(2)

    # Tap first result
    tap(port, 540, 500)
    time.sleep(2)

def view_videos(port, container_name, target_username, num_videos):
    """View videos from target account"""
    print(f"\n{container_name}: Viewing @{target_username}")

    try:
        # Open TikTok
        open_tiktok(port)

        # Search account
        search_account(port, target_username)

        # Tap first video
        tap(port, 540, 800)
        time.sleep(2)

        # Watch videos
        for i in range(num_videos):
            print(f"  Video {i+1}/{num_videos}...", end=' ', flush=True)

            # Watch for WATCH_TIME seconds
            time.sleep(WATCH_TIME)

            # Swipe up to next video
            swipe(port, 540, 1500, 540, 500, 500)
            time.sleep(2)

            print("✓")

        print(f"  ✓ Watched {num_videos} videos from @{target_username}")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_containers():
    """Check if containers are running"""
    print("Checking Docker containers...")

    result = subprocess.run('docker ps --format "{{.Names}}"', shell=True, capture_output=True, text=True)
    running = result.stdout.strip().split('\n')

    all_running = True
    for container in CONTAINERS:
        name = container['name']
        if name in running:
            print(f"  ✓ {name} is running")
        else:
            print(f"  ✗ {name} is NOT running")
            all_running = False

    return all_running

def connect_adb():
    """Connect ADB to all containers"""
    print("\nConnecting ADB to containers...")

    for container in CONTAINERS:
        port = container['adb_port']
        name = container['name']

        print(f"  Connecting to {name} (port {port})...", end=' ')

        # Connect ADB
        subprocess.run(f'adb connect localhost:{port}', shell=True, capture_output=True)
        time.sleep(1)

        # Check connection
        result = subprocess.run('adb devices', shell=True, capture_output=True, text=True)
        if f'localhost:{port}' in result.stdout:
            print("✓")
        else:
            print("✗")

def main():
    print("=" * 70)
    print("  DOCKER TIKTOK AUTOMATION")
    print("=" * 70)
    print()

    # Check containers
    if not check_containers():
        print("\n✗ Not all containers are running!")
        print("\nStart containers with:")
        print("  cd ~/tiktok-commenter-dm/tiktok-commenter-dm/downloads")
        print("  docker-compose up -d")
        sys.exit(1)

    # Connect ADB
    connect_adb()

    print()
    print("=" * 70)
    print("STARTING AUTOMATION")
    print("=" * 70)
    print()

    # For each container
    for container in CONTAINERS:
        port = container['adb_port']
        name = container['name']

        print(f"\n{'='*70}")
        print(f"  {name.upper()}")
        print(f"{'='*70}")

        # View from each target account
        for target in TARGET_ACCOUNTS:
            view_videos(port, name, target, VIDEOS_PER_ACCOUNT)
            time.sleep(10)  # Break between targets

        print(f"\n✓ {name} completed all targets!")

    # Summary
    total_views = len(CONTAINERS) * len(TARGET_ACCOUNTS) * VIDEOS_PER_ACCOUNT

    print()
    print("=" * 70)
    print("  AUTOMATION COMPLETE!")
    print("=" * 70)
    print()
    print(f"Total views generated: ~{total_views}")
    print(f"Containers used: {len(CONTAINERS)}")
    print(f"Targets viewed: {len(TARGET_ACCOUNTS)}")
    print()

if __name__ == '__main__':
    main()
