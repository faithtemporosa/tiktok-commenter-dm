#!/usr/bin/env python3
"""Save tt2 profile to mapping"""

import sys
import json
sys.path.insert(0, '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads')

from comment_target_accounts import open_browser, close_browser, check_login_status, PROFILE_MAPPING_PATH
from playwright.sync_api import sync_playwright

# tt2 browser
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

        if is_logged_in and username:
            print(f'✓ Found account: @{username}')

            # Load existing mapping
            try:
                with open(PROFILE_MAPPING_PATH, 'r') as f:
                    mapping = json.load(f)
            except:
                mapping = {}

            # Save to mapping
            mapping[BROWSER_NAME] = username

            with open(PROFILE_MAPPING_PATH, 'w') as f:
                json.dump(mapping, f, indent=2)

            print(f'✓ Saved {BROWSER_NAME} -> @{username} to {PROFILE_MAPPING_PATH}')
        else:
            print('✗ Not logged in or username not found')

        browser.close()
finally:
    close_browser(USER_ID)
    print('Done!')
