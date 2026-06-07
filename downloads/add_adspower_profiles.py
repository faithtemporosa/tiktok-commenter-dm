#!/usr/bin/env python3
"""
Add new browser profiles to AdsPower with fresh Webshare proxies
"""

import requests
import time
import sys

ADSPOWER_API = 'http://local.adspower.net:50325'
PROXY_FILE = '../webshare_proxies_1000.txt'

def load_proxies():
    """Load proxies from file"""
    with open(PROXY_FILE, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    print(f"✓ Loaded {len(proxies)} proxies from {PROXY_FILE}")
    return proxies

def get_existing_profiles():
    """Get list of existing profiles"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=200', timeout=30)
    data = resp.json()
    if data.get('code') == 0:
        profiles = data.get('data', {}).get('list', [])
        return profiles
    return []

def create_profile(name, proxy_string, serial_number):
    """
    Create a new AdsPower profile with proxy

    proxy_string format: ip:port:username:password
    """
    # Parse proxy
    parts = proxy_string.split(':')
    if len(parts) != 4:
        print(f"  ✗ Invalid proxy format: {proxy_string}")
        return None

    proxy_host, proxy_port, proxy_user, proxy_pass = parts

    # AdsPower profile creation payload - minimal config
    payload = {
        "name": name,
        "group_id": "8671133",  # Tiktok group
        "remark": f"Webshare proxy #{serial_number}",
        "user_proxy_config": {
            "proxy_soft": "other",
            "proxy_type": "http",
            "proxy_host": proxy_host,
            "proxy_port": proxy_port,
            "proxy_user": proxy_user,
            "proxy_password": proxy_pass
        }
    }

    try:
        resp = requests.post(
            f'{ADSPOWER_API}/api/v1/user/create',
            json=payload,
            timeout=30
        )
        data = resp.json()

        if data.get('code') == 0:
            user_id = data.get('data', {}).get('id')
            return user_id
        else:
            print(f"  ✗ API Error: {data.get('msg', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"  ✗ Exception: {str(e)[:100]}")
        return None

def main():
    print('=' * 60)
    print('  ADD ADSPOWER PROFILES WITH FRESH PROXIES')
    print('=' * 60)

    # Get number of profiles to create
    if len(sys.argv) > 1:
        try:
            num_to_create = int(sys.argv[1])
        except ValueError:
            print("Usage: python3 add_adspower_profiles.py [number_of_profiles]")
            print("Example: python3 add_adspower_profiles.py 50")
            return
    else:
        num_to_create = 50  # Default

    print(f"\nWill create {num_to_create} new profiles\n")

    # Load proxies
    proxies = load_proxies()
    if len(proxies) < num_to_create:
        print(f"⚠ Warning: Only {len(proxies)} proxies available for {num_to_create} profiles")
        num_to_create = len(proxies)

    # Get existing profiles
    existing = get_existing_profiles()
    print(f"✓ Found {len(existing)} existing profiles")

    # Find highest tt number
    tt_numbers = []
    for p in existing:
        name = p.get('name', '')
        if name.startswith('tt') and name[2:].isdigit():
            tt_numbers.append(int(name[2:]))

    start_num = max(tt_numbers) + 1 if tt_numbers else 1
    print(f"✓ Starting from tt{start_num}\n")

    # Create profiles
    created_count = 0
    failed_count = 0

    for i in range(num_to_create):
        profile_num = start_num + i
        profile_name = f"tt{profile_num}"
        proxy = proxies[i]

        print(f"[{i+1}/{num_to_create}] Creating {profile_name}...")
        print(f"  Proxy: {proxy.split(':')[0]}:{proxy.split(':')[1]}")

        user_id = create_profile(profile_name, proxy, profile_num)

        if user_id:
            print(f"  ✓ Created! ID: {user_id}")
            created_count += 1
        else:
            print(f"  ✗ Failed")
            failed_count += 1

        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
        print()

    print('=' * 60)
    print(f'  DONE!')
    print(f'  Created: {created_count}')
    print(f'  Failed: {failed_count}')
    print('=' * 60)

if __name__ == "__main__":
    main()
