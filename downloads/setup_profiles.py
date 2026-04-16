#!/usr/bin/env python3
"""
Setup TikTok profiles with AI-generated images and bios
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import random
import requests
from playwright.sync_api import sync_playwright
from comment_target_accounts import (
    open_browser,
    close_browser,
    ADSPOWER_API
)

# Profile configurations
PROFILES = {
    'tt199': {
        'username': 'cosmicwave471',
        'bio': 'Just vibing ✨ | Coffee enthusiast ☕',
    },
    'tt200': {
        'username': 'drifttrack626',
        'bio': 'Living life one day at a time 🌊 | Music lover 🎵',
    },
    'tt201': {
        'username': 'quantumstar717',
        'bio': 'Dreamer 💫 | Adventure seeker 🌍',
    }
}

def download_ai_profile_pic(save_path):
    """Download AI-generated profile picture"""
    try:
        # Use random user API for realistic AI-generated photos
        response = requests.get('https://randomuser.me/api/?gender=female', timeout=30)
        data = response.json()

        # Get the large profile picture
        pic_url = data['results'][0]['picture']['large']

        # Download the image
        pic_response = requests.get(pic_url, timeout=30)
        with open(save_path, 'wb') as f:
            f.write(pic_response.content)

        print(f'  ✓ Downloaded profile picture: {save_path}')
        return True
    except Exception as e:
        print(f'  ✗ Failed to download profile picture: {e}')

        # Try alternative: thispersondoesnotexist.com
        try:
            print('  Trying alternative source...')
            pic_url = f'https://thispersondoesnotexist.com/image?t={int(time.time())}'
            pic_response = requests.get(pic_url, timeout=30)
            with open(save_path, 'wb') as f:
                f.write(pic_response.content)
            print(f'  ✓ Downloaded profile picture from alternative source')
            return True
        except Exception as e2:
            print(f'  ✗ Alternative also failed: {e2}')
            return False

def setup_profile(browser_name, user_id, profile_config):
    """Setup profile picture and bio for a browser"""
    print(f'\n[{browser_name}] Setting up profile...')

    # Use absolute paths
    base_path = '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads'
    pic_path = f'{base_path}/profile_pics/{browser_name}_profile.jpg'
    os.makedirs(f'{base_path}/profile_pics', exist_ok=True)

    if not download_ai_profile_pic(pic_path):
        print(f'  ✗ Skipping {browser_name} - could not download profile picture')
        return False

    # Open browser
    ws_url = open_browser(user_id)
    if not ws_url:
        print(f'  ✗ Failed to open browser')
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # First, get the actual logged-in username
            print(f'  Getting logged-in username...')
            page.goto('https://www.tiktok.com/', timeout=30000)
            time.sleep(3)

            # Click on profile link in sidebar or top menu
            try:
                profile_link = page.locator('[data-e2e="nav-profile"], a:has-text("Profile")').first
                profile_link.wait_for(state='visible', timeout=5000)
                profile_link.click()
                time.sleep(3)
                print(f'  ✓ Navigated to profile page')
            except Exception as e:
                print(f'  ⚠ Could not find profile link: {str(e)[:80]}')
                # Try going to /me endpoint which redirects to logged-in user's profile
                page.goto('https://www.tiktok.com/@me', timeout=30000)
                time.sleep(3)

            page.screenshot(path=f'{base_path}/debug_{browser_name}_profile_page.png')

            # Click "Edit profile" button on profile page
            print(f'  Clicking Edit profile button...')
            try:
                edit_btn = page.locator('button:has-text("Edit profile")').first
                edit_btn.wait_for(state='visible', timeout=5000)
                edit_btn.click()
                time.sleep(3)
                print(f'  ✓ Edit profile modal opened')
            except Exception as e:
                print(f'  ✗ Could not click Edit profile: {str(e)[:80]}')
                return False

            page.screenshot(path=f'{base_path}/debug_{browser_name}_edit_modal.png')

            # Upload profile picture
            print(f'  Uploading profile picture...')
            pic_uploaded = False

            # Wait for Edit profile modal to be fully loaded
            time.sleep(2)

            # Method 1: Click on the pencil/edit icon or avatar directly
            try:
                print(f'  Looking for profile photo edit button...')

                # The pencil icon is usually in a button or clickable element near the avatar
                # Try clicking elements within the Profile photo section
                selectors = [
                    # Direct button with edit icon
                    'button[aria-label*="photo"]',
                    'button[aria-label*="Upload"]',
                    'button[aria-label*="Change"]',
                    # Clickable div/span containing the edit icon
                    'div[role="button"]:near(:text("Profile photo"))',
                    # SVG or icon elements that might be clickable
                    'svg[data-e2e*="edit"]',
                    # The avatar container itself might be clickable
                    'img[alt]:near(:text("Profile photo"))',
                ]

                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        element.wait_for(state='visible', timeout=2000)
                        element.click()
                        print(f'  ✓ Clicked edit icon with selector: {selector}')
                        time.sleep(2)

                        # Now file input should appear
                        file_input = page.locator('input[type="file"]').first
                        file_input.set_input_files(pic_path, timeout=5000)
                        time.sleep(3)
                        print(f'  ✓ File uploaded')

                        # Click Apply button to confirm the photo
                        try:
                            apply_btn = page.locator('button:has-text("Apply")').first
                            apply_btn.wait_for(state='visible', timeout=5000)
                            apply_btn.click()
                            time.sleep(2)
                            print(f'  ✓ Clicked Apply button')
                        except Exception as apply_err:
                            print(f'  ⚠ Apply button not found: {str(apply_err)[:60]}')

                        pic_uploaded = True
                        break
                    except:
                        continue
            except Exception as e:
                print(f'  Edit icon click failed: {str(e)[:80]}')

            # Method 2: Try clicking the avatar/profile photo using Playwright locators
            if not pic_uploaded:
                try:
                    print(f'  Trying to click on avatar/profile photo...')
                    # Look for elements near "Profile photo" text
                    photo_selectors = [
                        'img[alt*="avatar"]',
                        'img[alt*="profile"]',
                        'div:has-text("Profile photo") img',
                        'div:has-text("Profile photo") + * img',
                        'div:has-text("Profile photo") button',
                        'div:has-text("Profile photo") svg',
                    ]

                    for selector in photo_selectors:
                        try:
                            element = page.locator(selector).first
                            element.wait_for(state='visible', timeout=2000)
                            element.click()
                            print(f'  ✓ Clicked photo element: {selector}')
                            time.sleep(2)

                            file_input = page.locator('input[type="file"]').first
                            file_input.set_input_files(pic_path, timeout=5000)
                            time.sleep(3)
                            print(f'  ✓ File uploaded')

                            # Click Apply button
                            try:
                                apply_btn = page.locator('button:has-text("Apply")').first
                                apply_btn.wait_for(state='visible', timeout=5000)
                                apply_btn.click()
                                time.sleep(2)
                                print(f'  ✓ Clicked Apply button')
                            except Exception as apply_err:
                                print(f'  ⚠ Apply button not found: {str(apply_err)[:60]}')

                            pic_uploaded = True
                            break
                        except:
                            continue
                except Exception as e:
                    print(f'  Avatar click failed: {str(e)[:80]}')

            # Method 3: Find file input and upload directly using JavaScript
            if not pic_uploaded:
                try:
                    print(f'  Trying direct file input with JavaScript...')

                    # Create a file from the path and use JavaScript to assign it
                    # First, make file input visible
                    file_input_exists = page.evaluate("""() => {
                        const inputs = document.querySelectorAll('input[type="file"]');
                        if (inputs.length > 0) {
                            inputs[0].style.display = 'block';
                            inputs[0].style.visibility = 'visible';
                            inputs[0].style.opacity = '1';
                            inputs[0].style.position = 'relative';
                            return true;
                        }
                        return false;
                    }""")

                    if file_input_exists:
                        time.sleep(1)
                        file_input = page.locator('input[type="file"]').first
                        file_input.set_input_files(pic_path, timeout=5000)
                        time.sleep(3)
                        print(f'  ✓ File uploaded via direct input')

                        # Click Apply button
                        try:
                            apply_btn = page.locator('button:has-text("Apply")').first
                            apply_btn.wait_for(state='visible', timeout=5000)
                            apply_btn.click()
                            time.sleep(2)
                            print(f'  ✓ Clicked Apply button')
                        except Exception as apply_err:
                            print(f'  ⚠ Apply button not found: {str(apply_err)[:60]}')

                        pic_uploaded = True
                except Exception as e:
                    print(f'  Direct input failed: {str(e)[:80]}')

            if pic_uploaded:
                print(f'  ✓ Profile picture uploaded successfully')
            else:
                print(f'  ⚠ Could not upload profile picture')

            page.screenshot(path=f'{base_path}/debug_{browser_name}_after_photo.png')

            # Set bio
            print(f'  Setting bio text...')
            try:
                # Try multiple bio input selectors - be more specific to avoid selecting wrong textareas
                bio_selectors = [
                    'textarea[placeholder*="Bio"]',
                    'div:has-text("Bio") ~ textarea',
                    'textarea[name="bio"]',
                ]

                bio_set = False
                for selector in bio_selectors:
                    try:
                        bio_input = page.locator(selector).first
                        bio_input.wait_for(state='visible', timeout=3000)
                        bio_input.click()
                        time.sleep(0.5)
                        # Clear existing content using fill('')
                        bio_input.fill('')
                        time.sleep(0.5)
                        # Fill new bio
                        bio_input.fill(profile_config['bio'])
                        time.sleep(1)
                        print(f'  ✓ Bio text entered: {profile_config["bio"]}')
                        bio_set = True
                        break
                    except:
                        continue

                if not bio_set:
                    print(f'  ⚠ Could not find bio input')
            except Exception as e:
                print(f'  ⚠ Bio update failed: {str(e)[:100]}')

            page.screenshot(path=f'{base_path}/debug_{browser_name}_after_bio.png')

            # Save all changes
            print(f'  Saving profile changes...')
            try:
                save_btn = page.locator('button:has-text("Save")').first
                save_btn.wait_for(state='visible', timeout=5000)
                save_btn.click()
                time.sleep(3)
                print(f'  ✓ Profile changes saved!')
            except Exception as e:
                print(f'  ⚠ Save button click failed: {str(e)[:100]}')

            # Take final screenshot
            page.screenshot(path=f'{base_path}/profile_setup_{browser_name}_final.png')
            print(f'  ✓ Screenshot saved')

            browser.close()

    except Exception as e:
        print(f'  ✗ Error during profile setup: {e}')
        close_browser(user_id)
        return False

    close_browser(user_id)
    print(f'  ✓ {browser_name} profile setup complete!')
    return True

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

def main():
    print('=' * 60)
    print('  Profile Setup - AI-Generated Images')
    print('=' * 60)
    print()

    for browser_name, profile_config in PROFILES.items():
        user_id = get_browser_id(browser_name)
        if not user_id:
            print(f'✗ Could not find browser: {browser_name}')
            continue

        setup_profile(browser_name, user_id, profile_config)

        # Wait between browsers
        time.sleep(5)

    print()
    print('=' * 60)
    print('  Setup Complete!')
    print('=' * 60)

if __name__ == '__main__':
    main()
