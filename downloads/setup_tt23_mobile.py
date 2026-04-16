#!/usr/bin/env python3
"""
Configure browser tt23 to act like a mobile phone running TikTok app
"""
import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = 'http://local.adspower.net:50325'

# TikTok mobile app user agents (more authentic than mobile web)
TIKTOK_MOBILE_AGENTS = {
    'iPhone': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly/27.8.3 (iPhone; iOS 15.5; en_US; iPhone13,2; Scale/3.00; 1170x2532)',
    'Android': 'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36 musical_ly_go/28.0.5',
    'iPhone_Alt': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
}

MOBILE_CONFIGS = {
    'iPhone 13 Pro': {
        'user_agent': TIKTOK_MOBILE_AGENTS['iPhone'],
        'viewport': {'width': 390, 'height': 844},
        'device_scale_factor': 3,
    },
    'iPhone 12': {
        'user_agent': TIKTOK_MOBILE_AGENTS['iPhone_Alt'],
        'viewport': {'width': 390, 'height': 844},
        'device_scale_factor': 3,
    },
    'Samsung Galaxy S21': {
        'user_agent': TIKTOK_MOBILE_AGENTS['Android'],
        'viewport': {'width': 360, 'height': 800},
        'device_scale_factor': 4,
    }
}

def get_browser_info(browser_name):
    """Get browser info by name"""
    try:
        page = 1
        while page <= 10:  # Search up to 10 pages (1000 browsers)
            response = requests.get(
                f'{ADSPOWER_API}/api/v1/user/list',
                params={'page': page, 'page_size': 100}
            )
            data = response.json()

            if data['code'] != 0:
                break

            for browser in data['data']['list']:
                if browser.get('name') == browser_name:
                    return browser

            if len(data['data']['list']) < 100:
                break  # Last page

            page += 1

        return None
    except Exception as e:
        print(f"Error getting browser info: {e}")
        return None

def open_browser(browser_serial):
    """Open AdsPower browser"""
    try:
        response = requests.get(f'{ADSPOWER_API}/api/v1/browser/start',
                              params={'serial_number': browser_serial})
        data = response.json()

        if data['code'] != 0:
            print(f"Failed to start browser: {data.get('msg', 'Unknown error')}")
            return None

        debug_port = data['data']['ws']['puppeteer']
        return debug_port
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None

def close_browser(browser_serial):
    """Close AdsPower browser"""
    try:
        requests.get(f'{ADSPOWER_API}/api/v1/browser/stop',
                    params={'serial_number': browser_serial})
    except Exception as e:
        print(f"Error closing browser: {e}")

def configure_mobile_mode(page, config):
    """Configure page to act like mobile TikTok app"""
    try:
        # Set viewport
        page.set_viewport_size(config['viewport'])

        # Override user agent using CDP
        cdp = page.context.new_cdp_session(page)
        cdp.send('Network.setUserAgentOverride', {
            'userAgent': config['user_agent']
        })

        # Enable touch events
        cdp.send('Emulation.setTouchEmulationEnabled', {
            'enabled': True
        })

        # Set device scale factor
        cdp.send('Emulation.setDeviceMetricsOverride', {
            'width': config['viewport']['width'],
            'height': config['viewport']['height'],
            'deviceScaleFactor': config['device_scale_factor'],
            'mobile': True
        })

        print("✓ Mobile mode configured:")
        print(f"  Viewport: {config['viewport']['width']}x{config['viewport']['height']}")
        print(f"  Device scale: {config['device_scale_factor']}x")
        print(f"  Touch events: Enabled")
        print(f"  User agent: {config['user_agent'][:80]}...")

        return True
    except Exception as e:
        print(f"Error configuring mobile mode: {e}")
        return False

def main():
    browser_name = 'tt1'

    print("=" * 80)
    print(f"  Configure {browser_name} as Mobile TikTok App")
    print("=" * 80)
    print()

    # Get browser info
    print(f"Getting {browser_name} browser info...")
    browser_info = get_browser_info(browser_name)

    if not browser_info:
        print(f"Browser {browser_name} not found!")
        return

    browser_serial = browser_info['serial_number']
    current_username = browser_info.get('username', 'Not logged in')

    print(f"✓ Found {browser_name}")
    print(f"  Serial: {browser_serial}")
    print(f"  Username: {current_username}")
    print()

    # Choose device
    print("Choose mobile device emulation:")
    devices = list(MOBILE_CONFIGS.keys())
    for i, device_name in enumerate(devices, 1):
        print(f"{i}. {device_name}")

    choice = input("\nEnter choice (1-3, default: iPhone 13 Pro): ").strip()

    if choice and choice.isdigit() and 1 <= int(choice) <= len(devices):
        device_name = devices[int(choice) - 1]
    else:
        device_name = 'iPhone 13 Pro'

    config = MOBILE_CONFIGS[device_name]

    print()
    print(f"Selected: {device_name}")
    print()

    # Open browser
    print(f"Opening {browser_name}...")
    debug_port = open_browser(browser_serial)

    if not debug_port:
        print("Failed to open browser")
        return

    print(f"✓ Browser opened on port {debug_port}")
    print()

    try:
        with sync_playwright() as p:
            # Connect to browser
            browser = p.chromium.connect_over_cdp(debug_port)
            context = browser.contexts[0]

            # Get or create page
            if context.pages:
                page = context.pages[0]
            else:
                page = context.new_page()

            # Configure mobile mode
            print("Configuring mobile emulation...")
            if not configure_mobile_mode(page, config):
                print("Failed to configure mobile mode")
                return

            print()

            # Go to TikTok
            print("Opening TikTok in mobile mode...")
            page.goto('https://www.tiktok.com/foryou', timeout=30000)
            time.sleep(5)

            # Take screenshot
            page.screenshot(path='downloads/tt23_mobile_setup.png')
            print("✓ Screenshot saved: tt23_mobile_setup.png")

            print()
            print("=" * 80)
            print("  MOBILE MODE ACTIVATED!")
            print("=" * 80)
            print()
            print(f"Browser {browser_name} is now configured as {device_name}")
            print("It will behave like a mobile phone running TikTok.")
            print()
            print("The browser window will show mobile layout.")
            print("You can now:")
            print("  - View videos (views should register)")
            print("  - Like videos")
            print("  - Follow accounts")
            print("  - Comment on videos")
            print()
            print("The mobile configuration will persist for this session.")
            print()
            print("Press ENTER to close the browser...")
            input()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        close_browser(browser_serial)
        print("Browser closed")

if __name__ == '__main__':
    main()
