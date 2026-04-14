#!/usr/bin/env python3
"""
Remove proxies from all AdsPower browser profiles to allow direct connection
"""

import requests
import time

ADSPOWER_API = "http://local.adspower.net:50325"

def get_all_browsers():
    """Get all browser profiles from AdsPower"""
    browsers = []
    page = 1
    page_size = 100

    while True:
        try:
            time.sleep(1)
            resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list", params={
                'page': page,
                'page_size': page_size
            }, timeout=30)
            data = resp.json()

            if data.get('code') != 0:
                break

            page_list = data.get('data', {}).get('list', [])
            if not page_list:
                break

            browsers.extend(page_list)
            print(f"Loaded page {page}: {len(page_list)} browsers (total: {len(browsers)})")

            if len(page_list) < page_size:
                break

            page += 1

        except Exception as e:
            print(f"Error: {e}")
            break

    return browsers

def remove_proxy(user_id, retries=3):
    """Remove proxy from a browser"""
    for attempt in range(retries):
        try:
            resp = requests.post(f"{ADSPOWER_API}/api/v1/user/update", json={
                'user_id': user_id,
                'user_proxy_config': {
                    'proxy_soft': 'no_proxy'
                }
            }, timeout=30)

            data = resp.json()
            if data.get('code') == 0:
                return True, ""

            msg = data.get('msg', '')
            if 'Too many request' in msg:
                time.sleep(2)
                continue

            return False, msg

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return False, str(e)

    return False, "Max retries exceeded"

def main():
    print("="*60)
    print("Removing proxies from all AdsPower browsers")
    print("="*60)

    browsers = get_all_browsers()
    print(f"\nFound {len(browsers)} browsers")

    success = 0
    failed = 0

    for i, browser in enumerate(browsers):
        user_id = browser.get('user_id')
        name = browser.get('name', 'Unknown')

        ok, msg = remove_proxy(user_id)

        if ok:
            success += 1
            print(f"✓ [{i+1}/{len(browsers)}] {name}: proxy removed")
        else:
            failed += 1
            print(f"✗ [{i+1}/{len(browsers)}] {name}: FAILED - {msg}")

        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} updated, {failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
