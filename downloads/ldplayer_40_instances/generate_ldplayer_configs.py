#!/usr/bin/env python3
"""
Generate emulator_configs.json for 40 LDPlayer instances

Automatically creates configuration for all LDPlayer instances with proper port mapping.

Usage: python3 generate_ldplayer_configs.py
"""

import json
import subprocess

def get_ldplayer_instances():
    """Get list of LDPlayer instances from ldconsole"""
    try:
        # Run ldconsole list2
        result = subprocess.run(
            ['C:\\Program Files\\LDPlayer\\LDPlayer9\\ldconsole.exe', 'list2'],
            capture_output=True,
            text=True,
            shell=True
        )

        instances = []
        lines = result.stdout.strip().split('\n')

        for line in lines:
            if 'TikTok-' in line:
                parts = line.split(',')
                index = int(parts[0])
                name = parts[1]
                instances.append({
                    'index': index,
                    'name': name
                })

        return instances
    except Exception as e:
        print(f"Could not get LDPlayer instances automatically: {e}")
        print("Generating default config for 40 instances...")
        return None

def generate_config(num_instances=40):
    """Generate emulator config for N instances"""

    # Try to get actual instances
    actual_instances = get_ldplayer_instances()

    if actual_instances:
        print(f"Found {len(actual_instances)} LDPlayer instances")
        emulators = []

        for inst in actual_instances:
            # LDPlayer port mapping: index * 2 + 5554
            # Instance 0 = 5555, Instance 1 = 5557, etc.
            port = 5555 + (inst['index'] * 2)

            emulators.append({
                'name': inst['name'],
                'udid': f'127.0.0.1:{port}',
                'tiktok_account': f"account_{inst['index'] + 1}",
                'device_name': 'LDPlayer',
                'port': port,
                'index': inst['index']
            })

    else:
        # Generate default config
        print(f"Generating default config for {num_instances} instances")
        emulators = []

        for i in range(num_instances):
            port = 5555 + (i * 2)
            emulators.append({
                'name': f'TikTok-{i+1}',
                'udid': f'127.0.0.1:{port}',
                'tiktok_account': f'account_{i+1}',
                'device_name': 'LDPlayer',
                'port': port,
                'index': i
            })

    config = {
        'emulators': emulators,
        'settings': {
            'parallel_emulators': 5,  # Run 5 at a time
            'comments_per_account': 2,
            'appium_server': 'http://localhost:4723'
        },
        'notes': [
            f'Total instances: {len(emulators)}',
            'Port mapping: 5555 + (index * 2)',
            'Start instances: .\\start_all_ldplayers.ps1',
            'Connect via ADB: adb connect 127.0.0.1:PORT',
            'Run automation: python3 comment_target_emulator.py'
        ]
    }

    # Save config
    with open('emulator_configs.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✓ Generated emulator_configs.json")
    print(f"  Total emulators: {len(emulators)}")
    print(f"  Port range: {emulators[0]['port']} - {emulators[-1]['port']}")
    print(f"  Parallel execution: {config['settings']['parallel_emulators']} at a time")

    # Print first 5 and last 5
    print("\nFirst 5 instances:")
    for emu in emulators[:5]:
        print(f"  {emu['name']}: {emu['udid']}")

    print("\n...")
    print("\nLast 5 instances:")
    for emu in emulators[-5:]:
        print(f"  {emu['name']}: {emu['udid']}")

    return config

def verify_adb_connections():
    """Verify all emulators are connected via ADB"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        devices = [line.split('\t')[0] for line in result.stdout.split('\n')[1:] if '\tdevice' in line]

        print(f"\n✓ ADB connected devices: {len(devices)}")
        if devices:
            print("Connected:")
            for device in devices[:10]:  # Show first 10
                print(f"  - {device}")
            if len(devices) > 10:
                print(f"  ... and {len(devices) - 10} more")

        return devices
    except:
        print("\nADB not available or no devices connected")
        return []

if __name__ == '__main__':
    print("="*60)
    print("LDPlayer Configuration Generator")
    print("="*60)

    # Generate config
    config = generate_config(40)

    # Check ADB connections
    print("\nChecking ADB connections...")
    devices = verify_adb_connections()

    if len(devices) < len(config['emulators']):
        print(f"\nNote: Only {len(devices)}/{len(config['emulators'])} instances connected to ADB")
        print("\nTo connect all instances:")
        print("  1. Start instances: .\\start_all_ldplayers.ps1")
        print("  2. Wait 2-3 minutes for all to boot")
        print("  3. Connect via ADB: .\\connect_all_adb.ps1")

    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Install TikTok on all instances")
    print("2. Login to TikTok on each instance")
    print("3. Update tiktok_account field in emulator_configs.json")
    print("4. Start Appium: appium")
    print("5. Run automation: python3 comment_target_emulator.py")
