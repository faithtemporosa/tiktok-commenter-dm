#!/usr/bin/env python3
"""Test signup for tt2 with enhanced debugging"""

import sys
sys.path.insert(0, '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads')

from comment_target_accounts import open_browser, close_browser, check_login_status, auto_signup
from playwright.sync_api import sync_playwright

# tt2 browser ID
USER_ID = 'k19g5b2u'
BROWSER_NAME = 'tt2'

print(f'\n{"="*60}')
print(f'Testing signup for {BROWSER_NAME} with enhanced debugging')
print(f'{"="*60}\n')

print(f'Opening browser {BROWSER_NAME}...')
ws_url = open_browser(USER_ID)

if not ws_url:
    print('Failed to open browser!')
    exit(1)

try:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print('Checking login status...')
        is_logged_in, username = check_login_status(page)

        if is_logged_in:
            print(f'\n✓ {BROWSER_NAME} already logged in as @{username}')
            print('Skipping signup - account already exists')
        else:
            print(f'\nNot logged in - running auto-signup with debugging...\n')
            success, new_username = auto_signup(page, BROWSER_NAME)

            if success:
                print(f'\n{"="*60}')
                print(f'✓ SIGNUP SUCCESSFUL!')
                print(f'{BROWSER_NAME} is now @{new_username}')
                print(f'{"="*60}\n')
            else:
                print(f'\n{"="*60}')
                print(f'✗ SIGNUP FAILED')
                print(f'Check the debug output above for details')
                print(f'{"="*60}\n')

        browser.close()
finally:
    close_browser(USER_ID)
    print('Done!')
