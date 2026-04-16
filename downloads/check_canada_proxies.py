#!/usr/bin/env python3
"""
Check which browsers are using Canada proxies and why
"""
import requests
import json

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
                break

            browsers = data['data']['list']
            if not browsers:
                break

            all_browsers.extend(browsers)
            page += 1

        except Exception as e:
            print(f"Error: {e}")
            return None

    return all_browsers

def main():
    print("=" * 80)
    print("  CANADA PROXY INVESTIGATION")
    print("=" * 80)
    print()

    browsers = get_all_browsers()
    if browsers is None:
        print("⚠ ERROR: Cannot connect to AdsPower. Make sure it's running!")
        return

    # Find Canada browsers
    canada_browsers = []
    us_browsers = []
    other_browsers = []

    for browser in browsers:
        name = browser.get('name', '')
        serial = browser.get('serial_number', '')
        ip = browser.get('ip', 'No IP')
        country = browser.get('ip_country', 'unknown').upper()
        proxy_config = browser.get('user_proxy_config', {})

        browser_info = {
            'name': name,
            'serial': serial,
            'ip': ip,
            'country': country,
            'proxy_type': proxy_config.get('proxy_soft', 'Not Set'),
            'proxy_url': proxy_config.get('proxy_url', 'Not Set'),
        }

        if country == 'CA':
            canada_browsers.append(browser_info)
        elif country == 'US':
            us_browsers.append(browser_info)
        else:
            other_browsers.append(browser_info)

    print(f"Total Browsers: {len(browsers)}")
    print(f"  • US: {len(us_browsers)}")
    print(f"  • Canada: {len(canada_browsers)}")
    print(f"  • Other: {len(other_browsers)}")
    print()

    if canada_browsers:
        print("=" * 80)
        print(f"BROWSERS USING CANADA PROXIES ({len(canada_browsers)} found)")
        print("=" * 80)
        print()

        for browser in canada_browsers:
            print(f"Browser: {browser['name']}")
            print(f"  Serial: {browser['serial']}")
            print(f"  IP: {browser['ip']}")
            print(f"  Country: {browser['country']}")
            print(f"  Proxy Type: {browser['proxy_type']}")
            if browser['proxy_url'] != 'Not Set':
                # Don't show full proxy URL for security
                print(f"  Proxy Configured: Yes")
            else:
                print(f"  Proxy Configured: No")
            print()

        print("=" * 80)
        print("WHY THIS HAPPENS")
        print("=" * 80)
        print()
        print("Possible Reasons:")
        print()
        print("1. PROXY PROVIDER ISSUE")
        print("   • Your proxy provider assigned Canada IPs instead of US")
        print("   • Some proxy pools rotate between US/CA")
        print("   • Canada IPs might be cheaper in the proxy pool")
        print()
        print("2. IP GEOLOCATION DATABASE")
        print("   • The IP might actually be US, but geolocated as Canada")
        print("   • Different geolocation databases give different results")
        print("   • TikTok uses its own geolocation (might differ)")
        print()
        print("3. PROXY ROTATION")
        print("   • If using rotating proxies, location can change")
        print("   • One request = US, next request = Canada")
        print()
        print("=" * 80)
        print("IMPACT ON TIKTOK")
        print("=" * 80)
        print()
        print("If TikTok account shows Canada location:")
        print()
        print("  ✓ Account created while using Canada proxy")
        print("  ✗ Now using US proxy = Region mismatch")
        print("  ✗ Views/follows won't register (location changed)")
        print()
        print("Solution:")
        print("  • Check if these 2 accounts were created on Canada proxy")
        print("  • If yes, they MUST always use Canada proxy")
        print("  • Or create new accounts with consistent US proxies")
        print()

    # Show sample US browsers
    print("=" * 80)
    print(f"SAMPLE US BROWSERS (showing first 5 of {len(us_browsers)})")
    print("=" * 80)
    print()

    for browser in us_browsers[:5]:
        print(f"{browser['name']:15} - IP: {browser['ip']}")

    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    print("To avoid region inconsistency:")
    print()
    print("1. Use STICKY proxies (not rotating)")
    print("   • Same account = Same proxy every time")
    print("   • Prevents region changes")
    print()
    print("2. Verify proxy location BEFORE creating account")
    print("   • Check: https://ipapi.co/json/")
    print("   • Confirm it shows correct country")
    print()
    print("3. Keep account region consistent")
    print("   • Canada account → Always use Canada proxy")
    print("   • US account → Always use US proxy")
    print()

if __name__ == '__main__':
    main()
