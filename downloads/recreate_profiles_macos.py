#!/usr/bin/env python3
"""
Delete and recreate tt12-tt505 with macOS settings
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
    return proxies

def get_all_profiles():
    """Get all profiles"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=1000', timeout=30)
    data = resp.json()
    if data.get('code') == 0:
        return data.get('data', {}).get('list', [])
    return []

def delete_profile(user_id):
    """Delete a profile"""
    resp = requests.post(
        f'{ADSPOWER_API}/api/v1/user/delete',
        json={"user_ids": [user_id]},
        timeout=30
    )
    return resp.json().get('code') == 0

def create_profile_macos(name, proxy_string, serial_number):
    """Create profile with macOS settings"""
    parts = proxy_string.split(':')
    if len(parts) != 4:
        return None

    proxy_host, proxy_port, proxy_user, proxy_pass = parts

    payload = {
        "name": name,
        "group_id": "8671133",
        "remark": f"Webshare proxy #{serial_number} - macOS",
        "user_proxy_config": {
            "proxy_soft": "other",
            "proxy_type": "http",
            "proxy_host": proxy_host,
            "proxy_port": proxy_port,
            "proxy_user": proxy_user,
            "proxy_password": proxy_pass
        }
    }

    resp = requests.post(f'{ADSPOWER_API}/api/v1/user/create', json=payload, timeout=30)
    data = resp.json()

    if data.get('code') == 0:
        return data.get('data', {}).get('id')
    else:
        print(f"  Error: {data.get('msg', 'Unknown')}")
        return None

def main():
    print('=' * 60)
    print('  RECREATE PROFILES WITH MACOS SETTINGS')
    print('  Delete tt12-tt505 and recreate with macOS')
    print('=' * 60)
    print()

    # Load proxies
    proxies = load_proxies()
    print(f'✓ Loaded {len(proxies)} proxies')

    # Get all profiles
    print('Loading profiles...')
    all_profiles = get_all_profiles()
    print(f'✓ Loaded {len(all_profiles)} profiles')

    # Find profiles to delete (tt12-tt505)
    to_delete = []
    for p in all_profiles:
        name = p['name']
        if name.startswith('tt') and name[2:].isdigit():
            num = int(name[2:])
            if 12 <= num <= 505:
                to_delete.append(p)

    to_delete.sort(key=lambda x: int(x['name'][2:]))
    print(f'Found {len(to_delete)} profiles to delete/recreate\n')

    # Delete all profiles
    print('STEP 1: Deleting profiles...')
    deleted = 0
    for idx, profile in enumerate(to_delete):
        name = profile['name']
        user_id = profile['user_id']

        print(f'  [{idx+1}/{len(to_delete)}] Deleting {name}...', end=' ', flush=True)

        if delete_profile(user_id):
            print('✓')
            deleted += 1
        else:
            print('✗')

        time.sleep(0.1)

    print(f'\n✓ Deleted {deleted} profiles\n')

    # Recreate with macOS settings
    print('STEP 2: Recreating with macOS settings...')
    created = 0
    failed = 0

    # Start from proxy index 1 (skip index 0 which is for tt11)
    for idx, profile in enumerate(to_delete):
        name = profile['name']
        num = int(name[2:])
        proxy_idx = num - 11  # tt12 uses proxy[1], tt13 uses proxy[2], etc.

        if proxy_idx >= len(proxies):
            print(f'  [{idx+1}/{len(to_delete)}] {name} - No proxy available')
            failed += 1
            continue

        proxy = proxies[proxy_idx]

        print(f'  [{idx+1}/{len(to_delete)}] Creating {name}...', end=' ', flush=True)

        user_id = create_profile_macos(name, proxy, num)

        if user_id:
            print('✓')
            created += 1
        else:
            print('✗')
            failed += 1

        time.sleep(0.3)

    print()
    print('=' * 60)
    print(f'  DONE!')
    print(f'  Deleted: {deleted}')
    print(f'  Created: {created}')
    print(f'  Failed: {failed}')
    print('=' * 60)
    print()
    print('All profiles recreated with macOS platform!')
    print('Refresh AdsPower to see Apple icons.')

if __name__ == "__main__":
    main()
