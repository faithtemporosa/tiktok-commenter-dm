#!/usr/bin/env python3
"""
Check all browser IPs and identify mismatches
"""
import requests
import json
from collections import defaultdict

ADSPOWER_API = 'http://local.adspower.net:50325'

def get_all_browsers():
    """Get all browsers from AdsPower"""
    all_browsers = []
    page = 1

    while True:
        try:
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100}
            )
            data = response.json()

            if data['code'] != 0:
                print(f"Error fetching browsers: {data.get('msg')}")
                break

            browsers = data['data']['list']
            if not browsers:
                break

            all_browsers.extend(browsers)
            page += 1

        except Exception as e:
            print(f"Error: {e}")
            break

    return all_browsers

def main():
    print("=" * 70)
    print("  Browser IP Country Check")
    print("=" * 70)
    print()

    print("Fetching all browsers from AdsPower...")
    browsers = get_all_browsers()
    print(f"Found {len(browsers)} browsers")
    print()

    # Group by IP country
    by_country = defaultdict(list)

    for browser in browsers:
        name = browser.get('name', '')
        serial = browser.get('serial_number', '')
        ip = browser.get('ip', 'No IP')
        country = browser.get('ip_country', 'unknown').upper()

        by_country[country].append({
            'name': name,
            'serial': serial,
            'ip': ip
        })

    # Print summary
    print("=" * 70)
    print("SUMMARY BY COUNTRY")
    print("=" * 70)
    for country in sorted(by_country.keys()):
        count = len(by_country[country])
        print(f"{country}: {count} browsers")
    print()

    # Show non-Philippines browsers
    print("=" * 70)
    print("NON-PHILIPPINES BROWSERS (Need PH proxies if using PH phones)")
    print("=" * 70)

    non_ph_count = 0
    for country in sorted(by_country.keys()):
        if country != 'PH':
            print(f"\n{country} ({len(by_country[country])} browsers):")
            for browser in sorted(by_country[country], key=lambda x: x['serial'])[:20]:  # Show first 20
                print(f"  {browser['name']:15} (serial {browser['serial']:3}) - {browser['ip']}")
                non_ph_count += 1

            if len(by_country[country]) > 20:
                print(f"  ... and {len(by_country[country]) - 20} more")

    print()
    print("=" * 70)
    print(f"TOTAL NON-PH BROWSERS: {non_ph_count}")
    print("=" * 70)
    print()

    # Show Philippines browsers
    if 'PH' in by_country:
        print("=" * 70)
        print(f"PHILIPPINES BROWSERS (Good!) - {len(by_country['PH'])} browsers")
        print("=" * 70)
        for browser in sorted(by_country['PH'], key=lambda x: x['serial'])[:10]:
            print(f"  {browser['name']:15} (serial {browser['serial']:3}) - {browser['ip']}")
        if len(by_country['PH']) > 10:
            print(f"  ... and {len(by_country['PH']) - 10} more")
    else:
        print("=" * 70)
        print("⚠ NO PHILIPPINES PROXIES FOUND!")
        print("=" * 70)
        print("All browsers are using non-PH IPs.")
        print("If you're using PH phone numbers, views won't register.")

    print()
    print("=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)
    print("If accounts were created with Philippines phone numbers,")
    print("they MUST use Philippines proxies to register views/follows.")
    print()

if __name__ == '__main__':
    main()
