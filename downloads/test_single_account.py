#!/usr/bin/env python3
"""
Test creating a single TikTok account
"""

import requests
import time
import pickle
import os
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

ADSPOWER_API = "http://localhost:50325"
GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Test account
TEST_EMAIL = "testnova123@automateyourbizz.xyz"
TEST_PASSWORD = "N0v@T3stP@ss123!"
TEST_BROWSER_SERIAL = "801"  # Browser tt500

def get_gmail_service():
    """Authenticate and return Gmail API service"""
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

    return build('gmail', 'v1', credentials=creds)

def fetch_verification_code(email):
    """Fetch TikTok verification code from Gmail"""
    print(f"  → Fetching verification code from Gmail for {email}...")
    service = get_gmail_service()
    query = f'from:noreply@account.tiktok.com to:{email} newer_than:2m'

    max_attempts = 12
    for attempt in range(max_attempts):
        print(f"    Waiting for email... ({attempt+1}/{max_attempts})")
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

                # Extract email body
                import base64
                import re

                payload = msg.get('payload', {})
                body = ''

                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain':
                            data = part.get('body', {}).get('data', '')
                            if data:
                                body = base64.urlsafe_b64decode(data).decode('utf-8')
                                break
                else:
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')

                # Search for 6-digit code
                code_patterns = [
                    r'verification code[:\s]+(\d{6})',
                    r'code[:\s]+(\d{6})',
                    r'\b(\d{6})\b',
                ]

                for pattern in code_patterns:
                    match = re.search(pattern, body, re.IGNORECASE)
                    if match:
                        code = match.group(1)
                        print(f"  ✓ Got code: {code}")
                        return code

        time.sleep(10)

    print("  ✗ Could not fetch verification code")
    return None

def find_browser_by_serial(serial_num):
    """Find browser by serial number"""
    profiles = []
    page = 1
    while True:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100", timeout=10)
        data = resp.json()
        if data.get("code") != 0:
            break
        batch = data.get("data", {}).get("list", [])
        if not batch:
            break
        profiles.extend(batch)
        page += 1
        if page > 10:
            break

    for profile in profiles:
        if str(profile.get('serial_number', '')) == str(serial_num):
            return profile
    return None

def open_browser(user_id):
    """Open browser"""
    resp = requests.get(
        f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0",
        timeout=60
    )
    data = resp.json()
    if data.get("code") == 0:
        return data.get("data", {})
    return None

def close_browser(user_id):
    """Close browser"""
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass

def create_account():
    """Create single test account"""
    print("=" * 60)
    print("Creating Test TikTok Account")
    print("=" * 60)
    print(f"Email: {TEST_EMAIL}")
    print(f"Password: {TEST_PASSWORD}")
    print(f"Browser: {TEST_BROWSER_SERIAL}")
    print()

    profile = find_browser_by_serial(TEST_BROWSER_SERIAL)
    if not profile:
        print(f"Browser {TEST_BROWSER_SERIAL} not found!")
        return False

    user_id = profile.get('user_id')
    profile_name = profile.get('name')
    print(f"Opening browser {profile_name}...")

    browser_info = open_browser(user_id)
    if not browser_info:
        print("Failed to open browser!")
        return False

    time.sleep(2)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            print("Step 1: Opening TikTok signup...")
            page.goto("https://www.tiktok.com/signup", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step1.png")

            print("Step 2: Clicking 'Use phone or email'...")
            try:
                page.click("text=Use phone or email", timeout=5000)
                time.sleep(2)
            except:
                pass

            print("Step 3: Selecting email signup...")
            try:
                page.click("text=Email", timeout=5000)
                time.sleep(2)
            except:
                pass

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step3.png")

            print("Step 4: Selecting birthdate...")
            try:
                import datetime
                birth_year = str(datetime.datetime.now().year - 25)

                page.wait_for_selector("[role='combobox']", timeout=5000)
                time.sleep(1)

                # Month
                print("  → Month...")
                month_combobox = page.locator("[role='combobox'][aria-label*='Month']")
                month_combobox.click()
                time.sleep(0.5)
                page.locator("[role='option']:has-text('January')").first.click()
                time.sleep(0.5)

                # Day
                print("  → Day...")
                day_combobox = page.locator("[role='combobox'][aria-label*='Day']")
                day_combobox.click()
                time.sleep(0.5)
                page.locator("[role='option']:has-text('15')").first.click()
                time.sleep(0.5)

                # Year
                print("  → Year...")
                year_combobox = page.locator("[role='combobox'][aria-label*='Year']")
                year_combobox.click()
                time.sleep(0.5)
                page.locator(f"[role='option']:has-text('{birth_year}')").first.click()
                time.sleep(1)

                print("  ✓ Birthdate selected")
            except Exception as e:
                print(f"  ✗ Error selecting birthdate: {e}")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step4.png")

            print("Step 5: Entering email...")
            email_input = page.locator("input[type='text']").first
            email_input.fill(TEST_EMAIL)
            time.sleep(1)

            print("Step 6: Entering password...")
            password_input = page.locator("input[type='password']").first
            password_input.fill(TEST_PASSWORD)
            time.sleep(1)

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step6.png")

            print("Step 7: Clicking 'Send code'...")
            try:
                page.click("text=Send code", timeout=5000)
                time.sleep(3)
            except Exception as e:
                print(f"  ✗ Error: {e}")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step7.png")

            print("Step 8: Waiting for code input...")
            time.sleep(5)

            print("Step 9: Fetching verification code...")
            code = fetch_verification_code(TEST_EMAIL)
            if not code:
                print("Failed to get code!")
                return False

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step9.png")

            print("Step 10: Entering verification code...")
            try:
                code_inputs = page.locator("input[type='text']").all()
                if len(code_inputs) >= 6:
                    for i, digit in enumerate(code[:6]):
                        code_inputs[i].fill(digit)
                        time.sleep(0.2)
                else:
                    page.locator("input[type='text']").first.fill(code)
                time.sleep(2)
            except Exception as e:
                print(f"  ✗ Error: {e}")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step10.png")

            print("Step 11: Clicking 'Sign up'...")
            try:
                page.click("button:has-text('Sign up')", timeout=5000)
                time.sleep(5)
            except Exception as e:
                print(f"  ✗ Error: {e}")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step11.png")

            print("Step 12: Checking for username prompt...")
            time.sleep(2)
            try:
                skip_button = page.locator("button:has-text('Skip')").first
                if skip_button.is_visible(timeout=3000):
                    print("  → Clicking 'Skip'...")
                    skip_button.click()
                    time.sleep(2)
            except:
                print("  → No Skip button")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_step12.png")

            print("Step 13: Waiting for redirect...")
            time.sleep(10)

            current_url = page.url
            print(f"Final URL: {current_url}")

            page.screenshot(path="/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/test_final.png")

            if "foryou" in current_url or "@" in current_url or "following" in current_url:
                print("✓✓✓ ACCOUNT CREATED SUCCESSFULLY! ✓✓✓")
                return True
            else:
                print("✗✗✗ ACCOUNT NOT CREATED ✗✗✗")
                return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\nPress Enter to close browser...")
        input()
        close_browser(user_id)

if __name__ == "__main__":
    create_account()
