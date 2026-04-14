#!/usr/bin/env python3
"""Quick signup for tt2 browser"""

import sys
sys.path.insert(0, '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads')

from comment_target_accounts import open_browser, close_browser, check_login_status, auto_signup
from playwright.sync_api import sync_playwright

# tt2 browser ID
USER_ID = 'k19g5b2u'
BROWSER_NAME = 'tt2'

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
            print(f'✓ {BROWSER_NAME} already logged in as @{username}')
        else:
            print(f'Not logged in - running auto-signup...')
            success, new_username = auto_signup(page, BROWSER_NAME)

            if success:
                print(f'✓ Signup successful! {BROWSER_NAME} is now @{new_username}')
            else:
                print(f'✗ Signup failed')

        browser.close()
finally:
    close_browser(USER_ID)
    print('Done!')
