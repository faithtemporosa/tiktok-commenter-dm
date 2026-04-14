#!/usr/bin/env python3
"""
Update all AdsPower browser profiles with fresh proxies from webshare_proxies_2500.txt
"""

import requests
import json
import time
import sys

ADSPOWER_API = "http://local.adspower.net:50325"
PROXY_FILE = "webshare_proxies_fresh.txt"

def load_proxies():
    """Load proxies from file"""
    proxies = []
    with open(PROXY_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split(':')
                if len(parts) >= 4:
                    proxies.append({
                        'host': parts[0],
                        'port': parts[1],
                        'user': parts[2],
                        'password': parts[3]
                    })
    return proxies

def get_all_browsers():
    """Get all browser profiles from AdsPower"""
    browsers = []
    page = 1
    page_size = 100

    while True:
        for attempt in range(3):
            try:
                time.sleep(1)  # Rate limit delay
                resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list", params={
                    'page': page,
                    'page_size': page_size
                }, timeout=30)
                data = resp.json()

                if data.get('code') != 0:
                    if 'Too many request' in str(data.get('msg', '')):
                        print(f"  Rate limited, waiting 3s...")
                        time.sleep(3)
                        continue
                    print(f"Error: {data.get('msg')}")
                    break

                page_list = data.get('data', {}).get('list', [])
                if not page_list:
                    return browsers

                browsers.extend(page_list)
                print(f"Loaded page {page}: {len(page_list)} browsers (total: {len(browsers)})")

                if len(page_list) < page_size:
                    return browsers

                page += 1
                break

            except Exception as e:
                print(f"Error loading browsers: {e}")
                time.sleep(2)

        else:
            # All retries failed
            break

    return browsers

def update_browser_proxy(user_id, proxy, retries=3):
    """Update a browser's proxy configuration with retries"""
    for attempt in range(retries):
        try:
            # Build the proxy config
            proxy_config = {
                "proxy_soft": "other",
                "proxy_type": "http",
                "proxy_host": proxy['host'],
                "proxy_port": proxy['port'],
                "proxy_user": proxy['user'],
                "proxy_password": proxy['password']
            }

            # Update the browser profile
            resp = requests.post(f"{ADSPOWER_API}/api/v1/user/update", json={
                'user_id': user_id,
                'user_proxy_config': proxy_config
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
    print("AdsPower Browser Proxy Updater")
    print("="*60)

    # Load proxies
    print(f"\nLoading proxies from {PROXY_FILE}...")
    proxies = load_proxies()
    print(f"Loaded {len(proxies)} proxies")

    if not proxies:
        print("No proxies found!")
        return

    # Get all browsers
    print(f"\nLoading browser profiles from AdsPower...")
    browsers = get_all_browsers()
    print(f"Found {len(browsers)} browser profiles")

    if not browsers:
        print("No browsers found!")
        return

    # Sort browsers by name for consistent ordering
    browsers.sort(key=lambda x: x.get('name', ''))

    # Update each browser with a fresh proxy
    print(f"\n{'='*60}")
    print("Updating browser proxies...")
    print(f"{'='*60}")

    success_count = 0
    fail_count = 0

    for i, browser in enumerate(browsers):
        user_id = browser.get('user_id')
        name = browser.get('name', 'Unknown')

        # Use proxy based on browser index (cycling if more browsers than proxies)
        proxy = proxies[i % len(proxies)]

        success, msg = update_browser_proxy(user_id, proxy)

        if success:
            success_count += 1
            print(f"✓ [{i+1}/{len(browsers)}] {name}: {proxy['host']}:{proxy['port']}")
        else:
            fail_count += 1
            print(f"✗ [{i+1}/{len(browsers)}] {name}: FAILED - {msg}")

        # Delay between updates to avoid rate limiting
        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {success_count} updated, {fail_count} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
