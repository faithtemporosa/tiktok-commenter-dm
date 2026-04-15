#!/usr/bin/env python3
"""
Fast unique proxy assignment - 1 proxy per browser
Assigns proxies immediately without slow verification
"""

import requests
import time
import random

ADSPOWER_API = 'http://local.adspower.net:50325'
PROXY_FILE = 'webshare_proxies_fresh.txt'

def load_all_proxies():
    """Load all proxies from file"""
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
    """Get all browsers from AdsPower"""
    all_browsers = []
    page = 1

    print("Fetching browsers from AdsPower...")
    while page <= 10:  # Max 10 pages = 1000 browsers
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100},
                timeout=10
            )
            data = response.json()

            if data['code'] != 0:
                if 'Too many' in data.get('msg', ''):
                    print(f"  Rate limited, waiting 2 seconds...")
                    time.sleep(2)
                    continue
                break

            browsers = data['data']['list']
            if not browsers:
                break

            all_browsers.extend(browsers)
            print(f"  Loaded page {page}: {len(browsers)} browsers (total: {len(all_browsers)})")
            page += 1
            time.sleep(1)  # Rate limit prevention

        except Exception as e:
            print(f"Error fetching browsers: {e}")
            break

    return all_browsers

def filter_likely_datacenter_ips(proxies):
    """Quick filter of obvious datacenter IPs based on known ranges"""
    # Known datacenter IP prefixes (from our earlier checks)
    datacenter_prefixes = [
        '142.111.',  # ACE Data Centers
        '38.154.',   # Servermania
        '45.39.',    # EGIHosting
        '172.120.',  # EGIHosting
        '103.251.'   # Code200
    ]

    filtered = []
    removed = 0

    for proxy in proxies:
        ip = proxy['host']
        if not any(ip.startswith(prefix) for prefix in datacenter_prefixes):
            filtered.append(proxy)
        else:
            removed += 1

    if removed > 0:
        print(f"Filtered out {removed} known datacenter IPs")

    return filtered

def update_browser_proxy(user_id, proxy, retries=3):
    """Update a browser's proxy configuration"""
    for attempt in range(retries):
        try:
            proxy_config = {
                "proxy_soft": "other",
                "proxy_type": "http",
                "proxy_host": proxy['host'],
                "proxy_port": proxy['port'],
                "proxy_user": proxy['user'],
                "proxy_password": proxy['password']
            }

            resp = requests.post(f"{ADSPOWER_API}/api/v1/user/update", json={
                'user_id': user_id,
                'user_proxy_config': proxy_config
            }, timeout=30)

            data = resp.json()

            if data.get('code') == 0:
                return True, ""

            if 'Too many request' in data.get('msg', ''):
                time.sleep(2)
                continue

            return False, data.get('msg', 'Unknown error')

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return False, str(e)

    return False, "Max retries exceeded"

def main():
    print("=" * 70)
    print("FAST UNIQUE PROXY ASSIGNMENT (1 proxy = 1 browser)")
    print("=" * 70)
    print()

    # Load all proxies
    print("Loading proxies...")
    all_proxies = load_all_proxies()
    print(f"Loaded {len(all_proxies)} total proxies")
    print()

    # Quick filter of known datacenter IPs
    filtered_proxies = filter_likely_datacenter_ips(all_proxies)
    print(f"After filtering: {len(filtered_proxies)} proxies available")
    print()

    # Get all browsers
    browsers = get_all_browsers()
    print(f"\nFound {len(browsers)} browsers")
    print()

    if len(filtered_proxies) < len(browsers):
        print("⚠ WARNING: More browsers than filtered proxies!")
        print(f"  Browsers: {len(browsers)}")
        print(f"  Proxies:  {len(filtered_proxies)}")
        print()
        print("Will use all available proxies, then cycle through them")
        print()

    # Shuffle proxies for random distribution
    random.shuffle(filtered_proxies)

    print("=" * 70)
    print("ASSIGNING UNIQUE PROXIES")
    print("=" * 70)
    print()

    success_count = 0
    fail_count = 0
    used_proxies = set()

    for i, browser in enumerate(browsers):
        # Get unique proxy (1:1 mapping, with cycling if needed)
        proxy_index = i % len(filtered_proxies)
        proxy = filtered_proxies[proxy_index]
        proxy_key = f"{proxy['host']}:{proxy['port']}"

        # Track if this proxy was already used
        is_reused = proxy_key in used_proxies
        used_proxies.add(proxy_key)

        user_id = browser['user_id']
        name = browser.get('name', 'Unknown')

        success, msg = update_browser_proxy(user_id, proxy)

        if success:
            success_count += 1
            reuse_marker = " (REUSED)" if is_reused else ""
            print(f"✓ [{i+1}/{len(browsers)}] {name:15} → {proxy['host']}:{proxy['port']}{reuse_marker}")
        else:
            fail_count += 1
            print(f"✗ [{i+1}/{len(browsers)}] {name:15} → FAILED: {msg}")

        # Rate limit
        time.sleep(0.25)

    print()
    print("=" * 70)
    print(f"COMPLETE")
    print(f"  Updated: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Unique proxies used: {len(used_proxies)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
