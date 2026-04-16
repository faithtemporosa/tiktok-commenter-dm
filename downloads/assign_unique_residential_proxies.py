#!/usr/bin/env python3
"""
Assign unique residential proxies to browsers (1 proxy = 1 browser)
Filters out datacenter IPs and ensures no proxy sharing
"""

import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

ADSPOWER_API = 'http://local.adspower.net:50325'
PROXY_FILE = 'webshare_proxies_fresh.txt'
RESIDENTIAL_PROXIES_FILE = 'residential_proxies_verified.json'

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
                        'password': parts[3],
                        'raw': line
                    })
    return proxies

def check_if_residential(ip):
    """Check if an IP is residential (not datacenter)"""
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}?fields=org,isp', timeout=5)
        data = resp.json()

        if data.get('status') == 'success':
            org = data.get('org', '').lower()
            isp = data.get('isp', '').lower()

            # Datacenter keywords
            datacenter_keywords = [
                'datacenter', 'data center', 'hosting', 'cloud', 'server',
                'digital ocean', 'amazon', 'google', 'microsoft', 'ovh',
                'linode', 'vultr', 'hetzner', 'contabo', 'servermania',
                'colocation', 'dedicated', 'vps', 'ace data', 'egihosting'
            ]

            is_datacenter = any(kw in org or kw in isp for kw in datacenter_keywords)
            return not is_datacenter

        return None  # Unknown

    except Exception as e:
        return None  # Unknown

def identify_residential_proxies(proxies, sample_size=800):
    """Identify residential proxies from the pool using parallel checking"""
    print(f"Checking {sample_size} proxies to identify residential IPs...")
    print("This will take a few minutes...")
    print("=" * 70)

    # Sample proxies to check
    sample = random.sample(proxies, min(sample_size, len(proxies)))

    residential = []
    checked = 0

    def check_proxy(proxy):
        ip = proxy['host']
        is_res = check_if_residential(ip)
        time.sleep(0.3)  # Rate limit
        return (proxy, is_res)

    # Use thread pool for parallel checking
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_proxy, p): p for p in sample}

        for future in as_completed(futures):
            proxy, is_residential = future.result()
            checked += 1

            if is_residential:
                residential.append(proxy)
                print(f"✓ [{checked}/{sample_size}] Found residential: {proxy['host']}")
            elif is_residential is False:
                print(f"✗ [{checked}/{sample_size}] Datacenter: {proxy['host']}")
            else:
                print(f"? [{checked}/{sample_size}] Unknown: {proxy['host']}")

            if checked % 50 == 0:
                print(f"\n  Progress: {checked}/{sample_size} checked, {len(residential)} residential found\n")

    print()
    print("=" * 70)
    print(f"RESULTS: Found {len(residential)} residential proxies")
    print("=" * 70)

    # Save verified residential proxies
    with open(RESIDENTIAL_PROXIES_FILE, 'w') as f:
        json.dump(residential, f, indent=2)

    return residential

def get_all_browsers():
    """Get all browsers from AdsPower"""
    all_browsers = []
    page = 1

    while True:
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100},
                timeout=10
            )
            data = response.json()

            if data['code'] != 0:
                break

            browsers = data['data']['list']
            if not browsers:
                break

            all_browsers.extend(browsers)
            page += 1

        except Exception as e:
            print(f"Error fetching browsers: {e}")
            break

    return all_browsers

def update_browser_proxy(user_id, proxy):
    """Update a browser's proxy configuration"""
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
        return data.get('code') == 0, data.get('msg', '')

    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("UNIQUE RESIDENTIAL PROXY ASSIGNMENT")
    print("=" * 70)
    print()

    # Step 1: Load all proxies
    print("Loading all proxies from file...")
    all_proxies = load_all_proxies()
    print(f"Loaded {len(all_proxies)} total proxies")
    print()

    # Step 2: Try to load previously verified residential proxies
    residential_proxies = []
    try:
        with open(RESIDENTIAL_PROXIES_FILE, 'r') as f:
            residential_proxies = json.load(f)
        print(f"Loaded {len(residential_proxies)} previously verified residential proxies")
        print()
    except:
        print("No previously verified residential proxies found")
        print()

    # Step 3: If we don't have enough, identify more
    browsers = get_all_browsers()
    print(f"Found {len(browsers)} browsers")
    print()

    needed = len(browsers)

    if len(residential_proxies) < needed:
        print(f"Need at least {needed} residential proxies")
        print(f"Currently have {len(residential_proxies)} verified")
        print(f"Will check more proxies to find {needed - len(residential_proxies)} additional")
        print()

        # Check more proxies to find enough residential ones
        sample_size = min(1000, len(all_proxies))
        new_residential = identify_residential_proxies(all_proxies, sample_size=sample_size)
        residential_proxies = new_residential

    if len(residential_proxies) < needed:
        print()
        print("⚠ WARNING: Not enough residential proxies found!")
        print(f"  Need: {needed}")
        print(f"  Have: {len(residential_proxies)}")
        print()
        print("Options:")
        print("1. Continue with available residential proxies (will leave some browsers unchanged)")
        print("2. Use remaining proxies from full pool (may include datacenter IPs)")
        print()
        choice = input("Choose [1/2]: ").strip()

        if choice == '2':
            # Add more proxies from the full pool
            remaining_needed = needed - len(residential_proxies)
            remaining_proxies = [p for p in all_proxies if p not in residential_proxies]
            residential_proxies.extend(remaining_proxies[:remaining_needed])

    # Step 4: Assign unique proxies to browsers (1:1 mapping)
    print()
    print("=" * 70)
    print("ASSIGNING UNIQUE PROXIES TO BROWSERS")
    print("=" * 70)
    print()

    # Shuffle to randomize assignment
    random.shuffle(residential_proxies)

    success_count = 0
    fail_count = 0

    for i, browser in enumerate(browsers):
        if i >= len(residential_proxies):
            print(f"⚠ Ran out of proxies at browser {i+1}/{len(browsers)}")
            break

        user_id = browser['user_id']
        name = browser['name']
        proxy = residential_proxies[i]  # Unique 1:1 assignment

        success, msg = update_browser_proxy(user_id, proxy)

        if success:
            success_count += 1
            print(f"✓ [{i+1}/{len(browsers)}] {name:15} → {proxy['host']}:{proxy['port']}")
        else:
            fail_count += 1
            print(f"✗ [{i+1}/{len(browsers)}] {name:15} → FAILED: {msg}")

        time.sleep(0.2)  # Rate limit

    print()
    print("=" * 70)
    print(f"COMPLETE: {success_count} updated, {fail_count} failed")
    print(f"Each browser now has a UNIQUE proxy (no sharing)")
    print("=" * 70)

if __name__ == "__main__":
    main()
