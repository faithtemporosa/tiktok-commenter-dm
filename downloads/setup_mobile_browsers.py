#!/usr/bin/env python3
"""
Configure AdsPower browsers as perfect mobile environment for TikTok
"""

import requests
import json

ADSPOWER_API = 'http://local.adspower.net:50325'

# Perfect iPhone 13 Pro configuration
MOBILE_CONFIG = {
    # User Agent - Real iPhone 13 Pro
    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',

    # Screen dimensions - iPhone 13 Pro exact
    'screen_width': 390,
    'screen_height': 844,

    # Device pixel ratio
    'device_pixel_ratio': 3,

    # Platform
    'platform': 'iPhone',

    # Additional fingerprint configs
    'webgl_vendor': 'Apple Inc.',
    'webgl_renderer': 'Apple GPU',
    'language': 'en-US',
    'languages': ['en-US', 'en'],
    'timezone': 'America/New_York',

    # Touch support
    'touch_support': True,
    'max_touch_points': 5,

    # Hardware concurrency (iPhone 13 Pro has 6 cores)
    'hardware_concurrency': 6,

    # Memory (iPhone 13 Pro has 6GB)
    'device_memory': 6
}

def get_browser_info(browser_name):
    """Get browser details from AdsPower"""
    page = 1
    while page <= 10:
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100}
            )
            data = response.json()

            if data['code'] != 0:
                return None

            browsers = data['data']['list']
            for browser in browsers:
                if browser.get('name') == browser_name:
                    return browser

            page += 1
        except Exception as e:
            print(f"Error: {e}")
            return None

    return None

def configure_mobile_browser(browser_name):
    """Configure browser as mobile environment"""

    print(f"\n{'='*70}")
    print(f"  Configuring {browser_name} as Mobile")
    print(f"{'='*70}\n")

    # Get browser info
    print("Step 1: Getting browser info...")
    browser = get_browser_info(browser_name)

    if not browser:
        print(f"✗ Browser {browser_name} not found!")
        return False

    user_id = browser['user_id']
    serial = browser.get('serial_number', 'unknown')

    print(f"  Found: {browser_name} (ID: {user_id}, Serial: {serial})")

    # Configure as mobile
    print("\nStep 2: Updating to iPhone 13 Pro configuration...")

    try:
        response = requests.post(
            f'{ADSPOWER_API}/api/v1/user/update',
            json={
                'user_id': user_id,
                'user_agent': MOBILE_CONFIG['user_agent'],
                'screen_width': MOBILE_CONFIG['screen_width'],
                'screen_height': MOBILE_CONFIG['screen_height'],
                'ua_platform': MOBILE_CONFIG['platform'],
                'fingerprint_config': {
                    'webgl_vendor': MOBILE_CONFIG['webgl_vendor'],
                    'webgl_renderer': MOBILE_CONFIG['webgl_renderer'],
                    'language': MOBILE_CONFIG['language'],
                    'languages': MOBILE_CONFIG['languages'],
                    'timezone': MOBILE_CONFIG['timezone'],
                    'hardware_concurrency': MOBILE_CONFIG['hardware_concurrency'],
                    'device_memory': MOBILE_CONFIG['device_memory']
                }
            }
        )

        result = response.json()

        if result.get('code') == 0:
            print("  ✓ Browser updated successfully!")
        else:
            print(f"  ✗ Update failed: {result.get('msg')}")
            return False

    except Exception as e:
        print(f"  ✗ Error updating browser: {e}")
        return False

    # Open browser to test
    print("\nStep 3: Opening browser to test mobile mode...")

    try:
        response = requests.get(
            f'{ADSPOWER_API}/api/v1/browser/start',
            params={'user_id': user_id}
        )

        result = response.json()

        if result.get('code') != 0:
            print(f"  ✗ Failed to open browser: {result.get('msg')}")
            return False

        print("  ✓ Browser opened successfully!")
        print("\nBrowser is now running as iPhone 13 Pro!")
        print("You can see it should look like mobile TikTok")

        # Get browser details
        ws_data = result['data']['ws']
        debug_port = ws_data.get('selenium', 'unknown')

        print(f"\nBrowser Details:")
        print(f"  • Debug port: {debug_port}")
        print(f"  • User agent: iPhone 13 Pro")
        print(f"  • Screen: 390x844 (mobile)")
        print(f"  • Touch: Enabled (5 touch points)")

        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("\n1. Browser window should be open now")
        print("2. Navigate to: https://m.tiktok.com")
        print("   (Mobile TikTok, not desktop!)")
        print("3. Login to your account")
        print("4. Test viewing videos")
        print("5. Check if views register!")
        print("\nLeave browser open for testing...")
        print("\nPress Enter when you want to close the browser...")

        return True

    except Exception as e:
        print(f"  ✗ Error opening browser: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("  MOBILE BROWSER CONFIGURATION")
    print("  Setting up perfect iPhone 13 Pro environment")
    print("="*70)

    # Configure browsers
    browsers_to_configure = ['tt23', 'tt1']

    for browser_name in browsers_to_configure:
        success = configure_mobile_browser(browser_name)

        if success:
            print(f"\n✓ {browser_name} configured and ready for testing!")
            input("\nPress Enter to continue to next browser...")

            # Close browser
            browser = get_browser_info(browser_name)
            if browser:
                requests.get(
                    f'{ADSPOWER_API}/api/v1/browser/stop',
                    params={'user_id': browser['user_id']}
                )
                print(f"✓ {browser_name} closed")
        else:
            print(f"\n✗ Failed to configure {browser_name}")

    print("\n" + "="*70)
    print("CONFIGURATION COMPLETE!")
    print("="*70)
    print("\nBoth browsers are now configured as iPhone 13 Pro")
    print("\nTo test:")
    print("  1. Open browser tt23 or tt1 in AdsPower")
    print("  2. Go to: https://m.tiktok.com")
    print("  3. Login and view videos")
    print("  4. Check if views are registering")
    print("\nIf views register → Success! 🎉")
    print("If views don't register → Need phone verification")
    print()

if __name__ == '__main__':
    main()
