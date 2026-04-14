#!/usr/bin/env python3
"""Sign up specific browsers with username creation"""

import sys
import time
sys.path.insert(0, '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads')

from comment_target_accounts import get_all_browsers, open_browser, close_browser, auto_signup, check_login_status
from playwright.sync_api import sync_playwright

# Specific browser serial numbers to sign up
TARGET_BROWSERS = [500, 501, 504]  # Add more as needed

print('=' * 60)
print('  TikTok Auto-Signup - Specific Browsers')
print('=' * 60)
print(f'\nTarget browsers: {TARGET_BROWSERS}')
print('\nFeatures:')
print('  ✓ Automatic email verification code retrieval')
print('  ✓ Username creation from email prefix')
print('  ✓ Account creation date tracking')
print('  ✓ Profile mapping saved automatically')
print()

# Get all browsers
print('Loading browsers from AdsPower...')
all_browsers = get_all_browsers()

# Filter to only target browsers
browsers = [b for b in all_browsers if int(b.get('serial_number', 0)) in TARGET_BROWSERS]
print(f'Found {len(browsers)}/{len(TARGET_BROWSERS)} target browsers\n')

if not browsers:
    print('No matching browsers found!')
    exit(1)

# Process each browser
success_count = 0
failed_count = 0
already_logged_in = 0

for idx, browser in enumerate(browsers):
    user_id = browser['user_id']
    browser_name = browser['name']
    serial = browser.get('serial_number', 'unknown')

    print(f'\n[{idx+1}/{len(browsers)}] Browser {serial} ({browser_name})')
    print('-' * 60)

    # Open browser
    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'✗ Failed to open browser')
        failed_count += 1
        continue

    try:
        with sync_playwright() as p:
            browser_conn = p.chromium.connect_over_cdp(ws_url)
            context = browser_conn.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Check if already logged in
            print(f'Checking login status...')
            is_logged_in, username = check_login_status(page)

            if is_logged_in:
                print(f'✓ Already logged in as @{username}')
                already_logged_in += 1
            else:
                print(f'Not logged in - starting signup...')
                print(f'This will:')
                print(f'  1. Navigate to TikTok signup')
                print(f'  2. Fill in email and password')
                print(f'  3. Click "Send code" button')
                print(f'  4. Wait for Gmail verification code')
                print(f'  5. Enter verification code')
                print(f'  6. Set username from email prefix')
                print(f'  7. Save account to profile mapping')
                print()

                # Run auto-signup
                signup_success, new_username = auto_signup(page, browser_name)

                if signup_success:
                    print(f'\n✓ SUCCESS! {browser_name} is now @{new_username}')
                    success_count += 1
                else:
                    print(f'\n✗ FAILED - Signup did not complete')
                    failed_count += 1

            browser_conn.close()

    except Exception as e:
        print(f'✗ Error: {str(e)[:100]}')
        failed_count += 1
    finally:
        close_browser(user_id)
        time.sleep(2)  # Brief delay between browsers

# Final summary
print('\n' + '=' * 60)
print('  SIGNUP SUMMARY')
print('=' * 60)
print(f'Total browsers processed: {len(browsers)}')
print(f'Already logged in: {already_logged_in}')
print(f'Newly signed up: {success_count}')
print(f'Failed: {failed_count}')
print('=' * 60)
print()

if success_count > 0:
    print('✓ New accounts have been saved to tiktok_profile_mapping.json')
    print('✓ Account creation dates saved to account_creation_dates.json')
    print('✓ These accounts have 30-day new account limits (2 follows/day, 2 comments/day)')
