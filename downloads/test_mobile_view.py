#!/usr/bin/env python3
"""
Test TikTok with mobile emulation to see if views register
Uses iPhone interface to mimic mobile phone
"""
import requests
import time
import random
from playwright.sync_api import sync_playwright

ADSPOWER_API = 'http://local.adspower.net:50325'

# Mobile device configurations
MOBILE_DEVICES = {
    'iPhone 13': {
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'viewport': {'width': 390, 'height': 844},
        'device_scale_factor': 3,
        'is_mobile': True,
        'has_touch': True,
    },
    'iPhone 12': {
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
        'viewport': {'width': 390, 'height': 844},
        'device_scale_factor': 3,
        'is_mobile': True,
        'has_touch': True,
    },
    'Samsung Galaxy S21': {
        'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
        'viewport': {'width': 360, 'height': 800},
        'device_scale_factor': 4,
        'is_mobile': True,
        'has_touch': True,
    }
}

def open_browser(browser_serial):
    """Open AdsPower browser"""
    try:
        response = requests.get(f'{ADSPOWER_API}/api/v1/browser/start',
                              params={'serial_number': browser_serial})
        data = response.json()

        if data['code'] != 0:
            print(f"Failed to start browser: {data.get('msg', 'Unknown error')}")
            return None

        debug_port = data['data']['ws']['puppeteer']
        return debug_port
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None

def close_browser(browser_serial):
    """Close AdsPower browser"""
    try:
        requests.get(f'{ADSPOWER_API}/api/v1/browser/stop',
                    params={'serial_number': browser_serial})
    except Exception as e:
        print(f"Error closing browser: {e}")

def test_mobile_view(page, target_username):
    """View target account's videos with mobile interface"""
    try:
        # Go to target profile
        profile_url = f'https://www.tiktok.com/@{target_username}'
        print(f"\nOpening {profile_url} (mobile view)...")
        page.goto(profile_url, timeout=30000)
        time.sleep(5)

        # Take screenshot
        page.screenshot(path='downloads/mobile_profile_view.png')
        print("Screenshot saved: mobile_profile_view.png")

        # Get video links
        print("\nFinding videos...")
        video_links = []
        try:
            # Find video elements on mobile interface
            video_elements = page.locator('a[href*="/video/"]').all()
            for elem in video_elements[:5]:  # Get first 5 videos
                href = elem.get_attribute('href')
                if href and '/video/' in href:
                    full_url = f'https://www.tiktok.com{href}' if href.startswith('/') else href
                    video_links.append(full_url)

            print(f"Found {len(video_links)} videos")
        except Exception as e:
            print(f"Error finding videos: {e}")

        # Watch videos
        if video_links:
            print(f"\nWatching {len(video_links)} videos (mobile mode)...")
            for i, video_url in enumerate(video_links, 1):
                try:
                    print(f"\n  Video {i}/{len(video_links)}: {video_url}")
                    page.goto(video_url, timeout=30000)

                    # Random watch time (8-15 seconds)
                    watch_time = random.randint(8, 15)
                    print(f"  Watching for {watch_time}s...")
                    time.sleep(watch_time)

                    # Take screenshot
                    page.screenshot(path=f'downloads/mobile_video_{i}.png')
                    print(f"  Screenshot saved: mobile_video_{i}.png")

                except Exception as e:
                    print(f"  Error watching video: {e}")
                    continue

            print(f"\n✓ Watched {len(video_links)} videos in mobile mode")
        else:
            print("No videos found to watch")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    # Test browser (change this to your browser)
    browser_serial = 503  # tt503
    target_account = input("Enter target TikTok username (without @): ").strip()

    if not target_account:
        target_account = "charlidamelio"  # Default for testing

    # Choose device
    print("\nAvailable mobile devices:")
    for i, device_name in enumerate(MOBILE_DEVICES.keys(), 1):
        print(f"{i}. {device_name}")

    device_choice = input("\nChoose device (1-3, or press ENTER for iPhone 13): ").strip()
    device_names = list(MOBILE_DEVICES.keys())

    if device_choice and device_choice.isdigit() and 1 <= int(device_choice) <= 3:
        device_name = device_names[int(device_choice) - 1]
    else:
        device_name = 'iPhone 13'

    device = MOBILE_DEVICES[device_name]

    print("=" * 70)
    print(f"  Testing Mobile View - Browser {browser_serial}")
    print(f"  Device: {device_name}")
    print(f"  Target: @{target_account}")
    print("=" * 70)
    print()

    # Open browser
    debug_port = open_browser(browser_serial)
    if not debug_port:
        print("Failed to open browser")
        return

    print(f"✓ Browser opened on port {debug_port}")

    try:
        with sync_playwright() as p:
            # Connect to existing browser
            browser = p.chromium.connect_over_cdp(debug_port)

            # Create new context with mobile emulation
            context = browser.contexts[0]

            # Get existing page or create new one
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()

            # Set mobile viewport and user agent
            print(f"\n✓ Setting mobile emulation ({device_name})...")
            page.set_viewport_size(device['viewport'])

            # Override user agent using CDP
            cdp = page.context.new_cdp_session(page)
            cdp.send('Network.setUserAgentOverride', {
                'userAgent': device['user_agent']
            })

            print(f"  Viewport: {device['viewport']['width']}x{device['viewport']['height']}")
            print(f"  User Agent: {device['user_agent'][:60]}...")
            print()

            # Test mobile view
            success = test_mobile_view(page, target_account)

            if success:
                print("\n" + "=" * 70)
                print("  MOBILE VIEW TEST COMPLETE!")
                print("=" * 70)
                print("\nNow check TikTok analytics to see if views registered.")
                print("Compare these view counts with desktop view counts.")
            else:
                print("\n" + "=" * 70)
                print("  TEST INCOMPLETE")
                print("=" * 70)

            print("\nBrowser will remain open for you to verify.")
            print("Press ENTER to close the browser...")
            input()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        close_browser(browser_serial)
        print("Browser closed")

if __name__ == '__main__':
    main()
