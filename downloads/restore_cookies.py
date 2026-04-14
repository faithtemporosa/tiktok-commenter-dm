#!/usr/bin/env python3
"""
Restore saved cookies to browsers and verify login status
"""

import requests
import json
import time
import os
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://local.adspower.net:50325"
COOKIES_DIR = "tiktok_cookies"

def restore_browser_cookies(user_id, name):
    cookie_file = os.path.join(COOKIES_DIR, f"{name}_cookies.json")

    if not os.path.exists(cookie_file):
        print(f"[{name}] No cookie file found")
        return None

    print(f"\n[{name}] Restoring cookies...")

    # Load cookies
    with open(cookie_file, 'r') as f:
        cookies = json.load(f)

    # Open browser
    try:
        resp = requests.get(f'{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}', timeout=60)
        data = resp.json()
        if data.get('code') != 0:
            print(f"  Failed to open: {data.get('msg')}")
            return False
        ws_url = data['data']['ws']['puppeteer']
    except Exception as e:
        print(f"  Error opening: {e}")
        return False

    result = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]

            # Add cookies to context
            try:
                context.add_cookies(cookies)
                print(f"  Added {len(cookies)} cookies")
            except Exception as e:
                print(f"  Cookie add error: {str(e)[:50]}")

            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to TikTok
            page.goto('https://www.tiktok.com', timeout=30000)
            time.sleep(3)

            # Check login status
            url = page.url

            # Look for profile or check if logged in
            try:
                # Click profile icon
                page.click('[data-e2e="profile-icon"]', timeout=5000)
                time.sleep(2)

                if '/@' in page.url:
                    username = page.url.split('@')[1].split('/')[0].split('?')[0]
                    print(f"  ✓ LOGGED IN as @{username}")
                    result = True
                else:
                    print(f"  ✗ LOGGED OUT")
                    result = False
            except:
                # Check for login button
                try:
                    login_visible = page.locator('a:has-text("Log in")').first.is_visible(timeout=2000)
                    if login_visible:
                        print(f"  ✗ LOGGED OUT")
                        result = False
                    else:
                        print(f"  ? UNKNOWN status")
                        result = None
                except:
                    print(f"  ? UNKNOWN status")
                    result = None

    except Exception as e:
        print(f"  Error: {str(e)[:80]}")
        result = False
    finally:
        requests.get(f'{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}', timeout=10)

    return result

def main():
    # Get all profiles
    print("Loading profiles...")
    profiles = []
    page = 1
    while True:
        resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100')
        data = resp.json()
        batch = data.get('data', {}).get('list', [])
        if not batch:
            break
        profiles.extend(batch)
        page += 1
        time.sleep(0.5)

    print(f"Found {len(profiles)} profiles")

    # Filter to only those with cookie files
    profiles_with_cookies = []
    for p in profiles:
        cookie_file = os.path.join(COOKIES_DIR, f"{p['name']}_cookies.json")
        if os.path.exists(cookie_file):
            profiles_with_cookies.append(p)

    print(f"Found {len(profiles_with_cookies)} profiles with saved cookies")

    logged_in = 0
    logged_out = 0
    unknown = 0

    for i, p in enumerate(profiles_with_cookies):
        print(f"\n[{i+1}/{len(profiles_with_cookies)}]", end="")
        result = restore_browser_cookies(p['user_id'], p['name'])

        if result is True:
            logged_in += 1
        elif result is False:
            logged_out += 1
        else:
            unknown += 1

        time.sleep(2)

    print(f"\n{'='*50}")
    print(f"FINAL SUMMARY")
    print(f"{'='*50}")
    print(f"✓ Logged in: {logged_in}")
    print(f"✗ Logged out: {logged_out}")
    print(f"? Unknown: {unknown}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
