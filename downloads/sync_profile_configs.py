#!/usr/bin/env python3
"""
Sync AdsPower profile configurations
Copies tt11's fingerprint configuration to tt12-tt505
"""

import requests
import time
import sys

ADSPOWER_API = 'http://local.adspower.net:50325'

def get_profile_details(user_id):
    """Get detailed profile configuration"""
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/detail?user_id={user_id}', timeout=30)
    data = resp.json()
    if data.get('code') == 0:
        return data.get('data', {})
    return None

def update_profile(user_id, config):
    """Update profile configuration"""
    resp = requests.post(
        f'{ADSPOWER_API}/api/v1/user/update',
        json=config,
        timeout=30
    )
    data = resp.json()
    success = data.get('code') == 0
    error_msg = data.get('msg', '') if not success else ''
    return success, error_msg

def get_all_profiles():
    """Get all profiles - use large page_size to get all at once"""
    resp = requests.get(
        f'{ADSPOWER_API}/api/v1/user/list?page_size=1000',
        timeout=30
    )
    data = resp.json()
    if data.get('code') == 0:
        profiles = data.get('data', {}).get('list', [])
        return profiles
    return []

def main():
    print('=' * 60)
    print('  SYNC ADSPOWER PROFILE CONFIGURATIONS')
    print('  Copy tt11 config to tt12-tt505')
    print('=' * 60)
    print()

    # Get all profiles
    print('Loading profiles...')
    all_profiles = get_all_profiles()
    print(f'✓ Loaded {len(all_profiles)} profiles')

    # Find tt11
    tt11 = None
    for p in all_profiles:
        if p['name'] == 'tt11':
            tt11 = p
            break

    if not tt11:
        print('✗ tt11 not found!')
        return

    print(f'✓ Found tt11 (user_id: {tt11["user_id"]})')

    # Create fingerprint configuration based on tt11 settings
    # Based on user's screenshots: macOS, SunBrowser, Apple WebGL, etc.
    config_template = {
        'sys_app_cate_id': '0',
        'ipchecker': 'ip2location',
        'fingerprint_config': {
            'platform': 'mac',  # macOS platform
            'automatic_timezone': '1',  # Based on IP
            'webrtc': 'forward',  # Forward mode
            'location': 'ask',  # Ask each time
            'location_switch': '1',
            'timezone': '1',  # Based on IP
            'language': ['en-US', 'en'],  # Language array
            'page_language_switch': '1',
            'page_language': '1',  # Based on Language
            'webgl_image': '1',
            'canvas': '1',
            'webgl': '1',
            'audio': '1',
            'client_rects': '1',
            'speech_switch': '1',
            'device_name_switch': '1',
            'do_not_track': 'default',
            'hardware_concurrency': '4',
            'device_memory': '8',
        }
    }

    print('✓ Configuration template created')

    print(f'\nConfiguration to apply:')
    print(f'  Fingerprint config: {len(config_template["fingerprint_config"])} settings')
    print(f'  IP checker: {config_template["ipchecker"]}')
    print()

    # Find target profiles (tt12-tt505)
    target_profiles = []
    for p in all_profiles:
        name = p['name']
        if name.startswith('tt') and name[2:].isdigit():
            num = int(name[2:])
            if 12 <= num <= 505:
                target_profiles.append(p)

    target_profiles.sort(key=lambda x: int(x['name'][2:]))
    print(f'Found {len(target_profiles)} target profiles (tt12-tt505)\n')

    # Update each profile
    updated = 0
    failed = 0

    for idx, profile in enumerate(target_profiles):
        name = profile['name']
        user_id = profile['user_id']

        print(f'[{idx+1}/{len(target_profiles)}] {name}...', end=' ', flush=True)

        # Build update payload
        update_config = {
            'user_id': user_id,
            **config_template
        }

        success, error = update_profile(user_id, update_config)
        if success:
            print('✓')
            updated += 1
        else:
            print(f'✗ {error[:50] if error else "unknown error"}')
            failed += 1
            # Print first error details for debugging
            if failed == 1:
                print(f'\n  First error details: {error}\n')

        # Small delay to avoid overwhelming API
        time.sleep(0.2)

    print()
    print('=' * 60)
    print(f'  DONE!')
    print(f'  Updated: {updated}')
    print(f'  Failed: {failed}')
    print('=' * 60)

if __name__ == "__main__":
    main()
