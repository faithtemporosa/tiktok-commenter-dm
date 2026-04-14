#!/usr/bin/env python3
"""
TikTok Bulk Account Signup
Creates TikTok accounts for browsers and saves to CSV files
"""

import requests
import time
from playwright.sync_api import sync_playwright
import csv
import os
import re
import random
import pickle
from googleapiclient.discovery import build
import json

ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = 'tiktok_accounts.csv'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'

# Name generators
ADJECTIVES = ['swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean', 'forest',
              'digital', 'cyber', 'tech', 'smart', 'neon', 'atomic', 'vivid', 'prism',
              'flux', 'zen', 'drift', 'echo', 'nova', 'pixel', 'quantum', 'stellar']
NOUNS = ['phoenix', 'dragon', 'falcon', 'eagle', 'wolf', 'tiger', 'star', 'moon',
         'wave', 'flame', 'pixel', 'pulse', 'echo', 'spark', 'glow', 'path',
         'stream', 'verse', 'core', 'field', 'track', 'scope', 'grid', 'focus']

def generate_email():
    """Generate unique email"""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(100, 999)
    return f"{adj}{noun}{num}@automateyourbizz.xyz"

def generate_username():
    """Generate unique username"""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(10, 99)
    return f"{adj}{noun}{num}"

def generate_password():
    """Generate password"""
    adj = random.choice(ADJECTIVES).capitalize()
    noun = random.choice(NOUNS).capitalize()
    num = random.randint(10, 99)
    return f"{adj}{noun}.{num}"

def get_gmail_service():
    """Get Gmail API service"""
    with open(GMAIL_TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)
    return build('gmail', 'v1', credentials=creds)

def fetch_verification_code(email, max_attempts=30):
    """Fetch TikTok verification code from Gmail"""
    try:
        service = get_gmail_service()
        query = f'from:tiktok to:{email} subject:(verification OR code) is:unread newer_than:10m'

        for attempt in range(max_attempts):
            results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])

            if messages:
                msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')

                code_match = re.search(r'(\d{6})', subject)
                if code_match:
                    code = code_match.group(1)
                    # Mark as read
                    service.users().messages().modify(userId='me', id=messages[0]['id'],
                                                     body={'removeLabelIds': ['UNREAD']}).execute()
                    return code

            if attempt < max_attempts - 1:
                time.sleep(5)

        return None
    except Exception as e:
        print(f"    Error fetching code: {str(e)[:60]}")
        return None

def open_browser(user_id):
    """Open AdsPower browser"""
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    """Close AdsPower browser"""
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def signup_account(profile_id, profile_name, email, username, password):
    """Create TikTok account"""
    print(f"\n{'='*60}")
    print(f"Signing up {profile_name}")
    print(f"  Email: {email}")
    print(f"  Username: {username}")
    print(f"{'='*60}")

    debug_url = open_browser(profile_id)
    if not debug_url:
        print("  ✗ Failed to open browser")
        return False, None

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            # Go to TikTok signup
            print("  → Opening TikTok signup...")
            page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="networkidle", timeout=60000)
            time.sleep(3)

            # Fill birthdate
            print("  → Filling birthdate...")
            birth_year = str(2001)
            page.locator("[role='combobox'][aria-label*='Month']").click()
            time.sleep(0.5)
            page.locator("[role='option']:has-text('January')").first.click()
            time.sleep(0.5)

            page.locator("[role='combobox'][aria-label*='Day']").click()
            time.sleep(0.5)
            page.locator("[role='option']:has-text('15')").first.click()
            time.sleep(0.5)

            page.locator("[role='combobox'][aria-label*='Year']").click()
            time.sleep(0.5)
            page.locator(f"[role='option']:has-text('{birth_year}')").first.click()
            time.sleep(1)

            # Enter email
            print(f"  → Entering email...")
            email_input = page.locator("input[type='text']").first
            email_input.fill(email)
            time.sleep(2)

            # Enter password
            print(f"  → Entering password...")
            password_input = page.locator("input[type='password']").first
            password_input.fill(password)
            time.sleep(3)

            # Click Send code twice
            print("  → Clicking 'Send code'...")
            for attempt in range(3):
                try:
                    send_btn = page.locator("button:has-text('Send code')").first
                    if send_btn.is_visible(timeout=2000):
                        send_btn.click(force=True)
                        time.sleep(4)

                        # Check if Resend code appeared
                        if page.locator("text=/Resend code/i").is_visible(timeout=1000):
                            print("  ✓ Code sent!")
                            break
                except:
                    pass

            # Fetch verification code
            print("  → Fetching verification code...")
            code = fetch_verification_code(email)
            if not code:
                print("  ✗ Could not get verification code")
                return False, None

            print(f"  ✓ Got code: {code}")

            # Enter code
            code_input = page.locator("input[placeholder*='code' i]").first
            code_input.fill(code)
            time.sleep(2)

            # Click Next/Sign up
            page.locator("button:has-text('Next'), button:has-text('Sign up')").first.click()
            time.sleep(8)

            # Handle username creation
            print(f"  → Creating username: {username}")
            try:
                username_input = page.locator("input[placeholder='Username']").first
                if username_input.is_visible(timeout=5000):
                    username_input.fill(username)
                    time.sleep(3)

                    # Click Sign up
                    signup_btn = page.locator("button:has-text('Sign up')").first
                    signup_btn.click(timeout=15000)
                    time.sleep(10)
            except Exception as e:
                print(f"  ⚠ Username step: {str(e)[:50]}")

            # Get final TikTok username
            time.sleep(5)
            current_url = page.url
            tiktok_username = None

            # Try to get username from URL or page
            if '@' in current_url:
                tiktok_username = current_url.split('@')[1].split('/')[0].split('?')[0]

            if not tiktok_username:
                try:
                    # Try to find username in page
                    profile_text = page.locator('[data-e2e="browse-username"]').first.text_content(timeout=3000)
                    if profile_text and profile_text.startswith('@'):
                        tiktok_username = profile_text[1:]
                except:
                    tiktok_username = username

            is_logged_in = ('foryou' in current_url or 'following' in current_url or '@' in current_url)

            if is_logged_in:
                print(f"  ✓ Signup successful! TikTok username: @{tiktok_username}")
                return True, tiktok_username
            else:
                print(f"  ⚠ Signup incomplete - URL: {current_url}")
                return False, tiktok_username

    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        return False, None
    finally:
        close_browser(profile_id)

def update_csv(account_num, browser_num, email, username, password):
    """Update tiktok_accounts.csv"""
    rows = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    for row in rows:
        if row.get('Account #') == str(account_num):
            row['Email'] = email
            row['Username'] = username
            row['Password'] = password
            row['Status'] = 'created'
            row['Proxy browser'] = str(browser_num)
            break

    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def update_profile_mapping(profile_name, tiktok_username):
    """Update tiktok_profile_mapping.json"""
    if os.path.exists(PROFILE_MAPPING_PATH):
        with open(PROFILE_MAPPING_PATH, 'r') as f:
            mapping = json.load(f)
    else:
        mapping = {}

    mapping[profile_name] = tiktok_username

    with open(PROFILE_MAPPING_PATH, 'w') as f:
        json.dump(mapping, f, indent=2)

def main():
    import sys

    start_browser = int(sys.argv[1]) if len(sys.argv) > 1 else 798
    end_browser = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print("Fetching browser list...")
    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    profiles = response.json()['data']['list']
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))

    # Create browser number to profile mapping
    browser_to_profile = {}
    for profile in profiles:
        serial_num = profile.get('serial_number')
        browser_to_profile[serial_num] = profile

    success_count = 0
    fail_count = 0

    # Process browsers from start_browser down to end_browser
    for browser_num in range(start_browser, end_browser - 1, -1):
        if browser_num not in browser_to_profile:
            print(f"\nBrowser {browser_num} not found, skipping...")
            continue

        profile = browser_to_profile[browser_num]
        profile_id = profile['user_id']
        profile_name = profile['name']

        # Get account number (tt1 = Account #0)
        match = re.search(r'(\d+)', profile_name)
        profile_num = int(match.group(1)) if match else 0
        account_num = profile_num - 1

        # Generate credentials
        email = generate_email()
        username = generate_username()
        password = generate_password()

        # Signup
        success, tiktok_username = signup_account(profile_id, profile_name, email, username, password)

        if success and tiktok_username:
            # Update both CSVs
            update_csv(account_num, browser_num, email, username, password)
            update_profile_mapping(profile_name, tiktok_username)
            print(f"  ✓ Saved to CSV and profile mapping")
            success_count += 1
        else:
            fail_count += 1

        # Wait between signups
        time.sleep(random.randint(5, 10))

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
