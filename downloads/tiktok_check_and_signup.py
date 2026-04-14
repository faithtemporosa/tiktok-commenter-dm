#!/usr/bin/env python3
"""
Check TikTok login status and create new account if not logged in
Saves new credentials to CSV
"""

import requests
import time
from playwright.sync_api import sync_playwright
import csv
import os
import re
import random
import base64
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime

ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = os.path.join(os.path.dirname(__file__), 'tiktok_accounts.csv')

# Gmail API configuration
GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Email generation
EMAIL_ADJECTIVES = ['swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean', 'forest', 'digital', 'cyber', 'tech', 'smart', 'neon', 'atomic']
EMAIL_NOUNS = ['phoenix', 'dragon', 'falcon', 'eagle', 'wolf', 'tiger', 'star', 'moon', 'wave', 'flame', 'pixel', 'pulse', 'echo']

_gmail_service = None

def get_gmail_service():
    """Get Gmail API service"""
    global _gmail_service
    if _gmail_service is not None:
        return _gmail_service

    creds = None
    if os.path.exists(GMAIL_TOKEN_PATH):
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    _gmail_service = build('gmail', 'v1', credentials=creds)
    return _gmail_service

def fetch_tiktok_verification_code(email, max_attempts=24):
    """Fetch TikTok verification code from Gmail"""
    try:
        print(f"    Fetching TikTok code from Gmail for {email}...")
        service = get_gmail_service()

        query = f'from:tiktok to:{email} subject:(verification OR code) is:unread newer_than:10m'

        for attempt in range(max_attempts):
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()

            messages = results.get('messages', [])

            if messages:
                for msg_info in messages:
                    msg = service.users().messages().get(
                        userId='me',
                        id=msg_info['id'],
                        format='full'
                    ).execute()

                    payload = msg.get('payload', {})
                    headers = payload.get('headers', [])
                    subject = ""
                    for header in headers:
                        if header.get('name', '').lower() == 'subject':
                            subject = header.get('value', '')

                    code_patterns = [r'(\d{6})\s+is your', r'verification code[:\s]+(\d{6})', r'code[:\s]+(\d{6})', r'\b(\d{6})\b', r'\b(\d{4})\b']

                    for pattern in code_patterns:
                        code_match = re.search(pattern, subject, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            print(f"    Got code: {code}")
                            service.users().messages().modify(userId='me', id=msg_info['id'], body={'removeLabelIds': ['UNREAD']}).execute()
                            return code

                    # Check body
                    parts = payload.get('parts', [])
                    email_body = ""
                    if parts:
                        for part in parts:
                            if 'text' in part.get('mimeType', ''):
                                data = part.get('body', {}).get('data', '')
                                if data:
                                    email_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                    break
                    else:
                        data = payload.get('body', {}).get('data', '')
                        if data:
                            email_body = base64.urlsafe_b64decode(data).decode('utf-8')

                    for pattern in code_patterns:
                        code_match = re.search(pattern, email_body, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            print(f"    Got code: {code}")
                            service.users().messages().modify(userId='me', id=msg_info['id'], body={'removeLabelIds': ['UNREAD']}).execute()
                            return code

            if attempt < max_attempts - 1:
                time.sleep(5)

        return None
    except Exception as e:
        print(f"    Error fetching code: {str(e)[:60]}")
        return None

def generate_new_email():
    """Generate unique email"""
    adj = random.choice(EMAIL_ADJECTIVES)
    noun = random.choice(EMAIL_NOUNS)
    num = random.randint(100, 999)
    return f"{adj}{noun}{num}@automateyourbizz.xyz"

def generate_username():
    """Generate username"""
    adj = random.choice(['nova', 'urban', 'tech', 'digital', 'cyber'])
    noun = random.choice(['pulse', 'wave', 'track', 'spark', 'flow'])
    num = random.randint(10, 99)
    return f"{adj}{noun}{num}"

def generate_password():
    """Generate secure password"""
    return f"TikTok{random.randint(1000, 9999)}!Pass"

def update_csv_account(account_num, email, username, password):
    """Update CSV with new account details"""
    try:
        with open(CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            accounts = list(reader)
            fieldnames = reader.fieldnames

        # Update the account
        for acc in accounts:
            if acc.get('Account #') == str(account_num):
                acc['Email'] = email
                acc['Username'] = username
                acc['Password'] = password
                acc['Status'] = 'active'
                break

        # Write back
        with open(CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(accounts)

        print(f"  ✓ Updated CSV with new account")
        return True
    except Exception as e:
        print(f"  ✗ Failed to update CSV: {e}")
        return False

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def create_tiktok_account(page, email, username, password):
    """Create TikTok account"""
    try:
        print("  → Opening TikTok signup...")
        page.goto("https://www.tiktok.com/signup", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        print("  → Clicking 'Use phone or email'...")
        try:
            page.click("text=Use phone or email", timeout=5000)
            time.sleep(2)
        except:
            pass

        print("  → Selecting email signup...")
        try:
            page.click("text=Email", timeout=5000)
            time.sleep(2)
        except:
            pass

        print("  → Selecting birthdate...")
        try:
            birth_year = str(datetime.datetime.now().year - 25)
            page.wait_for_selector("[role='combobox'][aria-label*='Month']", timeout=10000)
            time.sleep(1)

            # Select Month
            month_combobox = page.locator("[role='combobox'][aria-label*='Month']")
            month_combobox.click()
            time.sleep(0.5)
            page.locator("[role='option']:has-text('January')").first.click()
            time.sleep(0.5)

            # Select Day
            day_combobox = page.locator("[role='combobox'][aria-label*='Day']")
            day_combobox.click()
            time.sleep(0.5)
            page.locator("[role='option']:has-text('15')").first.click()
            time.sleep(0.5)

            # Select Year
            year_combobox = page.locator("[role='combobox'][aria-label*='Year']")
            year_combobox.click()
            time.sleep(0.5)
            page.locator(f"[role='option']:has-text('{birth_year}')").first.click()
            time.sleep(1)

            print("  ✓ Birthdate selected")
        except Exception as e:
            print(f"  ⚠ Could not set birthdate: {e}")

        print(f"  → Entering email: {email}")
        email_input = page.locator("input[type='text']").first
        email_input.fill(email)
        time.sleep(3)

        print(f"  → Entering password...")
        password_input = page.locator("input[type='password']").first
        password_input.fill(password)
        time.sleep(5)

        print("  → Clicking 'Send code'...")
        send_button = page.locator("button:has-text('Send code'), div:has-text('Send code')").first
        send_button.scroll_into_view_if_needed()
        time.sleep(1)
        send_button.click(force=True, timeout=10000)
        time.sleep(5)

        # Check for rate limit
        try:
            if page.locator("text=Maximum number of attempts reached").is_visible(timeout=2000):
                print("  ⚠ Browser is rate-limited")
                return False
        except:
            pass

        # Fetch verification code
        code = fetch_tiktok_verification_code(email)
        if not code:
            print("  ✗ Could not get verification code")
            return False

        print(f"  → Entering code: {code}")
        code_input = page.locator("input[placeholder*='code' i], input[placeholder*='Enter' i]").first
        code_input.wait_for(state="visible", timeout=10000)
        code_input.fill(code)
        time.sleep(2)

        # Click Sign up
        print("  → Clicking 'Sign up'...")
        signup_btn = page.locator("button:has-text('Sign up'), button:has-text('Next')").first
        signup_btn.click(timeout=10000)
        time.sleep(10)

        # Fill username
        print(f"  → Entering username: {username}")
        try:
            username_input = page.locator("input[placeholder*='username' i]").first
            username_input.wait_for(state="visible", timeout=10000)
            username_input.fill(username)
            time.sleep(2)

            # Click Continue/Next
            continue_btn = page.locator("button:has-text('Continue'), button:has-text('Next')").first
            continue_btn.click(timeout=10000)
            time.sleep(5)
        except:
            print("  ⚠ Username step may have been skipped")

        # Check if logged in
        current_url = page.url
        is_logged_in = ('foryou' in current_url or 'following' in current_url or '@' in current_url)

        if is_logged_in:
            print("  ✓ Account created successfully!")
            return True
        else:
            print(f"  ⚠ Signup may not be complete - URL: {current_url}")
            return False

    except Exception as e:
        print(f"  ✗ Signup error: {str(e)[:100]}")
        return False

def check_and_signup(profile_id, profile_name, account_num):
    """Check if logged in, signup if not"""
    print(f"\n{'='*60}")
    print(f"Checking {profile_name}")
    print(f"{'='*60}")

    debug_url = open_browser(profile_id)
    if not debug_url:
        print(f"  Failed to open browser")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            # Keep only 1 tab
            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            print(f"  Navigating to TikTok...")
            page.goto("https://www.tiktok.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            current_url = page.url

            # Check if logged in
            is_logged_in = ('foryou' in current_url or 'following' in current_url or '@' in current_url)

            if is_logged_in:
                print(f"  ✓ Already logged in!")
                return True

            print(f"  ✗ Not logged in - creating new account...")

            # Generate new credentials
            email = generate_new_email()
            username = generate_username()
            password = generate_password()

            print(f"  New Email: {email}")
            print(f"  New Username: {username}")

            # Create account
            if create_tiktok_account(page, email, username, password):
                # Update CSV
                update_csv_account(account_num, email, username, password)
                return True
            else:
                return False

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
        return False
    finally:
        print(f"  Closing browser...")
        close_browser(profile_id)

def main():
    import sys

    print("Initializing Gmail API...")
    try:
        get_gmail_service()
        print("Gmail API ready\n")
    except Exception as e:
        print(f"Warning: Gmail API not available: {str(e)[:60]}")

    num_to_process = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))
    profiles_to_process = profiles[start_index:start_index + num_to_process]

    print(f"Processing {len(profiles_to_process)} profiles (from index {start_index})")

    success = 0
    failed = 0

    for profile in profiles_to_process:
        profile_id = profile.get("user_id")
        profile_name = profile.get("name", profile_id)

        # Get profile number (tt1 -> 1, tt2 -> 2)
        match = re.search(r'(\d+)', profile_name)
        profile_num = int(match.group(1)) if match else 0
        account_num = profile_num - 1  # Account # is 0-indexed

        if check_and_signup(profile_id, profile_name, account_num):
            success += 1
        else:
            failed += 1

        time.sleep(random.randint(3, 6))

    print(f"\n{'='*60}")
    print(f"SUMMARY: Success={success}, Failed={failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
