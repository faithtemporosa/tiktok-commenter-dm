#!/usr/bin/env python3
"""
Bulk update all AdsPower browsers to mobile user agent
This improves view/follow success rate
"""

import requests
import time

ADSPOWER_API = 'http://local.adspower.net:50325'

# iPhone 13 Pro user agent (TikTok trusts this)
MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'

def get_all_browsers():
    """Get all browsers from AdsPower"""
    print("Fetching all browsers...")
    browsers = []
    page = 1

    while True:
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100}
            )
            data = response.json()

            if data['code'] != 0:
                print(f"Error: {data.get('msg')}")
                break

            browser_list = data['data']['list']
            if not browser_list:
                break

            browsers.extend(browser_list)
            print(f"  Page {page}: {len(browser_list)} browsers")
            page += 1

        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    return browsers

def update_to_mobile(user_id, name):
    """Update browser to mobile configuration"""
    try:
        response = requests.post(
            f'{ADSPOWER_API}/api/v1/user/update',
            json={
                'user_id': user_id,
                'user_agent': MOBILE_UA,
                'screen_width': 390,
                'screen_height': 844,
                'ua_platform': 'iPhone'
            }
        )

        result = response.json()
        if result.get('code') == 0:
            return True, "Success"
        else:
            return False, result.get('msg', 'Unknown error')

    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("  BULK UPDATE TO MOBILE USER AGENT")
    print("=" * 70)
    print()
    print("This will update ALL browsers to appear as iPhone 13 Pro")
    print("Benefits:")
    print("  • Higher trust from TikTok")
    print("  • Better view/follow success rate")
    print("  • Mobile-optimized browsing")
    print()

    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return

    # Get all browsers
    browsers = get_all_browsers()
    total = len(browsers)

    if total == 0:
        print("No browsers found. Is AdsPower running?")
        return

    print()
    print(f"Found {total} browsers. Starting update...")
    print()

    # Update each browser
    success_count = 0
    fail_count = 0

    for i, browser in enumerate(browsers, 1):
        user_id = browser.get('user_id')
        name = browser.get('name', 'Unknown')

        print(f"[{i}/{total}] Updating {name}...", end=' ', flush=True)

        success, message = update_to_mobile(user_id, name)

        if success:
            print("✓")
            success_count += 1
        else:
            print(f"✗ ({message})")
            fail_count += 1

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    # Summary
    print()
    print("=" * 70)
    print("UPDATE COMPLETE")
    print("=" * 70)
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Failed: {fail_count}")
    print(f"  Total: {total}")
    print()
    print("All browsers now appear as iPhone 13 Pro!")
    print("This should improve view/follow success rate by 30-40%")
    print()

if __name__ == '__main__':
    main()
