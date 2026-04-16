#!/usr/bin/env python3
"""Check browser tt1 and use it to verify view counts"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import json
from playwright.sync_api import sync_playwright
from comment_target_accounts import open_browser, close_browser, check_login_status
import requests

ADSPOWER_API = 'http://local.adspower.net:50325'

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

def check_tt1():
    """Check browser tt1"""
    print('Checking browser tt1...\n')

    browser_name = 'tt1'
    user_id = get_browser_id(browser_name)
    if not user_id:
        print(f'✗ Could not find browser {browser_name}')
        return

    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'✗ Failed to open browser')
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Check login status
            print('Checking login status...')
            is_logged_in, username = check_login_status(page)

            if is_logged_in:
                print(f'✓ Browser tt1 is logged in as: @{username}\n')
            else:
                print(f'✗ Browser tt1 is NOT logged in\n')
                browser.close()
                close_browser(user_id)
                return

            # Now check view counts using tt1
            account = 'flockboynation'
            print(f'Checking view counts for @{account} using tt1...')
            page.goto(f'https://www.tiktok.com/@{account}', timeout=30000)
            time.sleep(5)

            # Scroll to load videos
            for _ in range(3):
                page.evaluate('window.scrollBy(0, 1000)')
                time.sleep(1)

            # Take screenshot
            page.screenshot(path='tt1_view_check_page.png')
            print('✓ Screenshot saved to tt1_view_check_page.png')

            # Get video data
            videos = page.evaluate('''() => {
                const videoData = [];

                // Try different selectors for video containers
                const selectors = [
                    '[data-e2e="user-post-item"]',
                    '[class*="DivItemContainer"]',
                    'div[class*="video"]',
                    'a[href*="/video/"]'
                ];

                let videoElements = [];
                for (const selector of selectors) {
                    videoElements = document.querySelectorAll(selector);
                    if (videoElements.length > 0) {
                        console.log(`Found ${videoElements.length} videos with selector: ${selector}`);
                        break;
                    }
                }

                // Limit to first 5 videos
                const videosToCheck = Array.from(videoElements).slice(0, 5);

                videosToCheck.forEach((el, idx) => {
                    // Get video link
                    let link = 'N/A';
                    if (el.href && el.href.includes('/video/')) {
                        link = el.href;
                    } else {
                        const linkEl = el.querySelector('a[href*="/video/"]');
                        link = linkEl ? linkEl.href : 'N/A';
                    }

                    // Try to find view count
                    let viewText = 'N/A';
                    const viewSelectors = [
                        'strong',
                        '[class*="count"]',
                        '[class*="view"]',
                        'span'
                    ];

                    for (const viewSel of viewSelectors) {
                        const viewEl = el.querySelector(viewSel);
                        if (viewEl && viewEl.textContent.match(/[\\d.]+[KMB]?/)) {
                            viewText = viewEl.textContent.trim();
                            break;
                        }
                    }

                    videoData.push({
                        index: idx + 1,
                        views: viewText,
                        link: link
                    });
                });

                return videoData;
            }''')

            print(f'\nView counts for first {len(videos)} videos from @{account} (via tt1):')
            print('=' * 70)
            for video in videos:
                print(f"Video {video['index']}: {video['views']} views")
                print(f"  Link: {video['link']}")
                print()

            # Save to file
            with open('tt1_view_counts.json', 'w') as f:
                json.dump({
                    'browser': browser_name,
                    'logged_in_as': username,
                    'account': account,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'videos': videos
                }, f, indent=2)

            print(f'✓ Saved snapshot to tt1_view_counts.json')

            browser.close()

    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        close_browser(user_id)
        return

    close_browser(user_id)

if __name__ == '__main__':
    check_tt1()
