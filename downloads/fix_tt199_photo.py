#!/usr/bin/env python3
"""Fix tt199 profile picture"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from playwright.sync_api import sync_playwright
from comment_target_accounts import open_browser, close_browser, ADSPOWER_API
import requests

def get_browser_id(browser_name):
    """Get browser user_id from AdsPower"""
    try:
        response = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page=1&page_size=1000')
        data = response.json()
        if data.get('code') != 0:
            return None
        for browser in data['data']['list']:
            if browser.get('name') == browser_name:
                return browser.get('user_id')
        return None
    except:
        return None

def fix_tt199_photo():
    """Fix tt199 profile picture"""
    print('[tt199] Fixing profile picture...')

    base_path = '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads'
    pic_path = f'{base_path}/profile_pics/tt199_profile.jpg'

    # Get browser ID
    user_id = get_browser_id('tt199')
    if not user_id:
        print('✗ Could not find browser tt199')
        return False

    # Open browser
    ws_url = open_browser(user_id)
    if not ws_url:
        print('✗ Failed to open browser')
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to profile
            print('  Navigating to profile...')
            page.goto('https://www.tiktok.com/', timeout=30000)
            time.sleep(2)

            # Click Profile link
            try:
                profile_link = page.locator('[data-e2e="nav-profile"], a:has-text("Profile")').first
                profile_link.click(timeout=5000)
                time.sleep(3)
            except:
                page.goto('https://www.tiktok.com/@cosmicwave471', timeout=30000)
                time.sleep(3)

            # Click Edit profile
            print('  Opening Edit profile...')
            edit_btn = page.locator('button:has-text("Edit profile")').first
            edit_btn.click(timeout=5000)
            time.sleep(3)

            # Click on profile photo
            print('  Uploading profile picture...')
            photo_element = page.locator('div:has-text("Profile photo") img').first
            photo_element.click(timeout=5000)
            time.sleep(2)

            # Upload file
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(pic_path, timeout=5000)
            time.sleep(3)

            # Click Apply
            apply_btn = page.locator('button:has-text("Apply")').first
            apply_btn.click(timeout=5000)
            time.sleep(2)
            print('  ✓ Profile picture uploaded')

            # Click Save
            print('  Saving changes...')
            save_btn = page.locator('button:has-text("Save")').first
            save_btn.click(timeout=5000)
            time.sleep(3)
            print('  ✓ Changes saved!')

            # Screenshot
            page.screenshot(path=f'{base_path}/tt199_fixed_final.png')

            browser.close()
    except Exception as e:
        print(f'✗ Error: {e}')
        close_browser(user_id)
        return False

    close_browser(user_id)
    print('✓ tt199 profile picture fixed!')
    return True

if __name__ == '__main__':
    fix_tt199_photo()
