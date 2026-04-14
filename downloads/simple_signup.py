#!/usr/bin/env python3
"""Simple TikTok signup - fills form, user manually clicks Send code and Submit"""

import requests
import time
import random
import string
import sys
import re
import pickle
import os
from playwright.sync_api import sync_playwright
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64

ADSPOWER_API = "http://localhost:50325"

def get_gmail_service():
    """Get Gmail API service"""
    token_path = os.path.join(os.path.dirname(__file__), 'gmail_token.pickle')
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
    return build('gmail', 'v1', credentials=creds)

def get_verification_code(email_address, max_wait=60):
    """Fetch TikTok verification code from Gmail"""
    service = get_gmail_service()
    start_time = time.time()

    while time.time() - start_time < max_wait:
        # Search for unread TikTok verification emails
        query = f"to:{email_address} from:TikTok is:unread subject:verification"
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])

        if messages:
            msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()

            # Get email body
            payload = msg.get('payload', {})
            body = ""

            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            else:
                data = payload.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            # Extract 6-digit code
            code_match = re.search(r'\b(\d{6})\b', body)
            if code_match:
                # Mark as read
                service.users().messages().modify(
                    userId='me', id=messages[0]['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                return code_match.group(1)

        print("Waiting for code...")
        time.sleep(5)

    return None

# Generate unique email - PURE RANDOM CHARACTERS
def generate_email():
    chars = ''.join(random.choices(string.ascii_lowercase, k=6))
    nums = ''.join(random.choices(string.digits, k=6))
    return f"{chars}{nums}@automateyourbizz.xyz"

# Generate unique username
def generate_username():
    chars = ''.join(random.choices(string.ascii_lowercase, k=6))
    nums = ''.join(random.choices(string.digits, k=4))
    return f"{chars}{nums}"

# Generate random valid birthdate (18-30 years old)
def generate_birthdate():
    import datetime
    current_year = datetime.datetime.now().year
    year = random.randint(current_year - 30, current_year - 18)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe for all months
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    return {'year': str(year), 'month': month_names[month - 1], 'day': str(day)}

# Store credentials to CSV
def save_credentials(browser_num, email, password, username, birthdate):
    import csv
    filepath = os.path.join(os.path.dirname(__file__), 'new_tiktok_accounts.csv')
    file_exists = os.path.exists(filepath)

    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['browser', 'email', 'password', 'username', 'birthdate'])
        writer.writerow([browser_num, email, password, username, f"{birthdate['month']} {birthdate['day']}, {birthdate['year']}"])

# Generate password that meets TikTok requirements
def generate_password():
    return "TikTok@2026"

# Get browser
def get_browser(serial_num):
    for page_num in range(1, 10):  # Check up to 10 pages (1000 browsers)
        time.sleep(0.5)  # Avoid rate limiting
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page={page_num}&page_size=100", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for p in data.get("data", {}).get("list", []):
                if str(p.get('serial_number')) == str(serial_num):
                    return p
    return None

def open_browser(user_id):
    resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0", timeout=60)
    data = resp.json()
    if data.get("code") == 0:
        return data.get("data", {})
    return None

def run_signup(browser_num):
    """Run signup for a single browser. Returns: 'filled', 'logged_in', or 'error'"""
    print("=" * 50)
    print(f"  Browser {browser_num}")
    print("=" * 50)

    profile = get_browser(browser_num)
    if not profile:
        print(f"Browser {browser_num} not found!")
        return "error", None, None

    print(f"Opening: {profile.get('name')} (Serial #{profile.get('serial_number')})")

    browser_info = open_browser(profile.get('user_id'))
    if not browser_info:
        print("Failed to open browser!")
        return "error", None, None

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    email = generate_email()
    password = generate_password()

    print(f"Email: {email}")
    print(f"Password: {password}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]

            # Close extra tabs
            pages = context.pages
            if len(pages) > 1:
                for extra in pages[1:]:
                    extra.close()
                time.sleep(1)

            page = context.pages[0] if context.pages else context.new_page()

            # Go to signup
            print("Opening TikTok signup...")
            page.goto("https://www.tiktok.com/signup", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Check if already logged in
            if "/foryou" in page.url or "/@" in page.url:
                print("⚠️ ALREADY LOGGED IN - Skipping")
                return "logged_in", None, None

            # Close QR code popup if present
            try:
                close_btn = page.locator("[aria-label='Close'], button:has-text('×'), .close-button").first
                if close_btn.is_visible(timeout=2000):
                    print("Closing QR code popup...")
                    close_btn.click()
                    time.sleep(1)
            except:
                pass

            # Click "Use phone or email"
            print("Clicking 'Use phone or email'...")
            page.click("text=Use phone or email")
            time.sleep(2)

            # Click "Sign up with email"
            print("Selecting email signup...")
            page.click("text=Email")
            time.sleep(2)

            # Fill birthdate (random valid)
            birthdate = generate_birthdate()
            print(f"Filling birthdate: {birthdate['month']} {birthdate['day']}, {birthdate['year']}")

            page.wait_for_selector("[role='combobox'][aria-label*='Month']", timeout=10000)
            time.sleep(1)

            # Month
            page.locator("[role='combobox'][aria-label*='Month']").click()
            time.sleep(0.5)
            page.locator(f"[role='option']:has-text('{birthdate['month']}')").first.click()
            time.sleep(0.5)

            # Day
            page.locator("[role='combobox'][aria-label*='Day']").click()
            time.sleep(0.5)
            page.locator(f"[role='option']:has-text('{birthdate['day']}')").first.click()
            time.sleep(0.5)

            # Year
            page.locator("[role='combobox'][aria-label*='Year']").click()
            time.sleep(0.5)
            page.locator(f"[role='option']:has-text('{birthdate['year']}')").first.click()
            time.sleep(1)
            print("✓ Birthdate set")

            # Fill email
            print(f"Entering email: {email}")
            email_input = page.locator("input[type='text']").first
            email_input.fill(email)
            time.sleep(2)

            # Fill password
            print(f"Entering password: {password}")
            password_input = page.locator("input[type='password']").first
            password_input.fill(password)
            time.sleep(2)

            # Click Send code TWICE (first click activates, second click sends)
            print("Clicking 'Send code' (1st click)...")
            send_button = page.locator("button:has-text('Send code')").first
            send_button.click()
            time.sleep(2)

            print("Clicking 'Send code' (2nd click - actually sends)...")
            send_button.click()
            time.sleep(3)

            # Fetch verification code from Gmail
            print("Waiting for verification code...")
            code = get_verification_code(email, max_wait=60)

            if code:
                print(f"Got code: {code}")

                # Enter the code
                code_input = page.locator("input[placeholder*='code'], input[name*='code']").first
                code_input.fill(code)
                time.sleep(2)

                # Click Next/Submit
                print("Clicking Next...")
                next_button = page.locator("button:has-text('Next'), button[type='submit']").first
                next_button.click()
                time.sleep(3)

                # Enter username
                username = generate_username()
                print(f"Entering username: {username}")
                try:
                    username_input = page.locator("input[placeholder*='Username'], input[name*='username']").first
                    username_input.wait_for(timeout=10000)
                    username_input.fill(username)
                    time.sleep(2)

                    # Click Sign up / Submit
                    print("Clicking Sign up...")
                    signup_button = page.locator("button:has-text('Sign up'), button[type='submit']").first
                    signup_button.click()
                    time.sleep(3)

                    # Save credentials to CSV
                    save_credentials(browser_num, email, password, username, birthdate)
                    print(f"✓ Credentials saved to new_tiktok_accounts.csv")
                except:
                    print("Username field not found - may need manual entry")

                print("✓ SIGNUP COMPLETE!")

            # Close browser after signup
            print("Closing browser...")
            browser.close()
            time.sleep(2)
            # Close AdsPower browser
            try:
                requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile.get('user_id')}", timeout=10)
            except:
                pass
            else:
                print("⚠️ No code received - manually enter code")

            print()

            return "filled", email, password

    except Exception as e:
        print(f"Error: {e}")
        # Close browser on error
        try:
            requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile.get('user_id')}", timeout=10)
            print("Browser closed.")
        except:
            pass
        return "error", None, None

# Main - run multiple browsers
if __name__ == "__main__":
    browsers = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [754, 753, 752, 751]

    results = []
    for browser_num in browsers:
        result, email, password = run_signup(browser_num)
        if result == "filled":
            results.append((browser_num, email, password))
        elif result == "logged_in":
            print(f"Browser {browser_num}: Already logged in\n")
        else:
            print(f"Browser {browser_num}: Error\n")

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY - All forms filled, manually click Send code & Submit")
    print("=" * 60)
    for browser_num, email, password in results:
        print(f"Browser {browser_num}: {email} / {password}")
    print()
