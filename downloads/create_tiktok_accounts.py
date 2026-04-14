#!/usr/bin/env python3
"""
Create TikTok accounts in AdsPower browsers
Uses Playwright to automate signup
"""

import requests
import csv
import time
import sys
import re
import base64
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os

ADSPOWER_API = "http://localhost:50325"
CSV_FILE_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_accounts.csv"
GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  # Need modify to mark emails as read

# Word lists for generating unique email addresses
EMAIL_ADJECTIVES = [
    'swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean',
    'forest', 'mountain', 'river', 'thunder', 'lightning', 'storm', 'cloud',
    'wind', 'fire', 'earth', 'water', 'shadow', 'light', 'dark', 'silent',
    'quiet', 'loud', 'fast', 'slow', 'digital', 'cyber', 'tech', 'smart',
    'clever', 'wise', 'bold', 'brave', 'calm', 'wild', 'free', 'pure',
    'royal', 'noble', 'elite', 'prime', 'alpha', 'omega', 'delta', 'gamma',
    'neon', 'laser', 'plasma', 'quantum', 'atomic', 'stellar', 'galactic'
]

EMAIL_NOUNS = [
    'phoenix', 'dragon', 'falcon', 'eagle', 'hawk', 'wolf', 'tiger', 'lion',
    'bear', 'fox', 'deer', 'owl', 'raven', 'sparrow', 'swan', 'dove',
    'star', 'moon', 'sun', 'comet', 'planet', 'orbit', 'galaxy', 'nebula',
    'wave', 'tide', 'stream', 'rain', 'snow', 'frost', 'dew', 'mist',
    'flame', 'blaze', 'ember', 'spark', 'flash', 'bolt', 'ray', 'beam',
    'pixel', 'byte', 'code', 'data', 'link', 'node', 'core', 'hub',
    'echo', 'pulse', 'rhythm', 'beat', 'tone', 'sound', 'voice', 'call'
]


def fetch_account_data():
    """Fetch account data from local CSV file"""
    with open(CSV_FILE_PATH, 'r') as f:
        reader = csv.DictReader(f)
        accounts = list(reader)
    return accounts


def generate_new_email():
    """Generate a new unique email address with timestamp for guaranteed uniqueness"""
    import time
    adj = random.choice(EMAIL_ADJECTIVES)
    noun = random.choice(EMAIL_NOUNS)
    # Use timestamp + random number for guaranteed uniqueness
    timestamp = int(time.time()) % 100000  # Last 5 digits of timestamp
    num = random.randint(10, 99)
    return f"{adj}{noun}{timestamp}{num}@automateyourbizz.xyz"


def update_account_email(account_num, new_email):
    """Update account email in CSV file"""
    try:
        accounts = fetch_account_data()

        # Find and update the account
        for acc in accounts:
            if acc.get('Account #') == str(account_num):
                acc['Email'] = new_email
                break

        # Write back to CSV
        with open(CSV_FILE_PATH, 'w', newline='') as f:
            if accounts:
                fieldnames = accounts[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(accounts)

        print(f"  ✓ Updated email to: {new_email}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to update email: {e}")
        return False


def get_available_browser():
    """Get next available browser from 799 down to 699 (each has different proxy)"""
    # Get accounts already assigned
    accounts = fetch_account_data()
    used_browsers = set()
    for acc in accounts:
        if acc.get('Proxy browser'):
            used_browsers.add(acc['Proxy browser'])

    # Fetch browsers from pages 1 and 2 to cover 699-799 range
    all_profiles = []
    for page_num in [1, 2]:
        try:
            resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page={page_num}&page_size=100", timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                profiles = data.get("data", {}).get("list", [])
                all_profiles.extend(profiles)
        except:
            pass

    # Sort by serial number descending (799, 798, 797... down to 699)
    profiles_sorted = sorted(all_profiles, key=lambda p: int(p.get('serial_number', 0)), reverse=True)

    # Use browser 765 specifically
    for p in profiles_sorted:
        serial = str(p.get('serial_number', ''))
        if serial == '765':
            return p

    return None


def open_browser(user_id):
    """Open an AdsPower browser"""
    try:
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0",
            timeout=60
        )
        data = resp.json()
        if data.get("code") == 0:
            debug_info = data.get("data", {})
            return debug_info
        return None
    except Exception as e:
        print(f"Error opening browser: {e}")
        return None


def close_browser(user_id):
    """Close an AdsPower browser"""
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass


def is_browser_logged_in(browser_info):
    """Check if browser is already logged into TikTok"""
    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Check current URL first (before navigating)
            try:
                current_url = page.url
                if current_url and current_url != "about:blank":
                    if 'tiktok.com' in current_url:
                        if ('foryou' in current_url or 'following' in current_url or '/@' in current_url):
                            return True
            except:
                pass

            # Navigate to TikTok signup to test
            page.goto("https://www.tiktok.com/signup", wait_until="load", timeout=20000)
            time.sleep(3)

            # If browser is logged in, TikTok will redirect away from signup
            current_url = page.url
            is_logged_in = ('/signup' not in current_url and
                           ('foryou' in current_url or
                            'following' in current_url or
                            '/@' in current_url))

            return is_logged_in

    except Exception as e:
        print(f"  ⚠ Error checking login status: {e}")
        # If we can't check, assume logged in to be safe (skip this browser)
        return True


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None

    # Load saved credentials
    if os.path.exists(GMAIL_TOKEN_PATH):
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {GMAIL_CREDENTIALS_PATH}\n"
                    "Please download your OAuth credentials from Google Cloud Console"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save credentials for next time
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def fetch_verification_code(email):
    """Fetch TikTok verification code from Gmail"""
    try:
        print(f"  → Fetching verification code from Gmail for {email}...")

        service = get_gmail_service()

        # Search for recent UNREAD TikTok verification emails sent to this specific address
        # Only get unread emails to ensure we get fresh codes
        query = f'from:noreply@account.tiktok.com to:{email} subject:"is your verification code" is:unread newer_than:10m'

        # Wait up to 6 minutes for the email to arrive (TikTok emails can be slow)
        max_attempts = 36
        for attempt in range(max_attempts):
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5  # Get up to 5 recent messages
            ).execute()

            messages = results.get('messages', [])

            if messages:
                # Check each message (newest first)
                for msg_info in messages:
                    msg = service.users().messages().get(
                        userId='me',
                        id=msg_info['id'],
                        format='full'
                    ).execute()

                    # Extract headers (subject and to address)
                    payload = msg.get('payload', {})
                    headers = payload.get('headers', [])
                    subject = ""
                    to_addr = ""
                    for header in headers:
                        header_name = header.get('name', '').lower()
                        if header_name == 'subject':
                            subject = header.get('value', '')
                        elif header_name == 'to' or header_name == 'delivered-to':
                            to_addr = header.get('value', '')

                    # Since we're processing one account at a time and just sent a code,
                    # the most recent TikTok email should be for the current account.
                    # No filtering needed - just use the first (most recent) result!

                    # Extract verification code patterns
                    code_patterns = [
                        r'(\d{6})\s+is your verification code',  # "123456 is your verification code" (subject)
                        r'verification code[:\s]+(\d{6})',  # "verification code: 123456"
                        r'code[:\s]+(\d{6})',  # "code: 123456"
                        r'\b(\d{6})\b',  # Any 6 digits
                    ]

                    # Try subject line first
                    for pattern in code_patterns:
                        code_match = re.search(pattern, subject, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            print(f"  ✓ Got code: {code} (from subject)")

                            # Mark email as read so we don't reuse it
                            try:
                                service.users().messages().modify(
                                    userId='me',
                                    id=msg_info['id'],
                                    body={'removeLabelIds': ['UNREAD']}
                                ).execute()
                                print(f"    → Marked email as read")
                            except:
                                pass

                            return code

                    # Fall back to checking email body
                    parts = payload.get('parts', [])
                    email_body = ""
                    if parts:
                        for part in parts:
                            mime_type = part.get('mimeType', '')
                            if 'text/plain' in mime_type or 'text/html' in mime_type:
                                data = part.get('body', {}).get('data', '')
                                if data:
                                    email_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                    break
                    else:
                        # Single part message
                        data = payload.get('body', {}).get('data', '')
                        if data:
                            email_body = base64.urlsafe_b64decode(data).decode('utf-8')

                    # Try body if subject didn't work
                    for pattern in code_patterns:
                        code_match = re.search(pattern, email_body, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            print(f"  ✓ Got code: {code} (from body)")

                            # Mark email as read so we don't reuse it
                            try:
                                service.users().messages().modify(
                                    userId='me',
                                    id=msg_info['id'],
                                    body={'removeLabelIds': ['UNREAD']}
                                ).execute()
                                print(f"    → Marked email as read")
                            except:
                                pass

                            return code

            # Wait before checking again
            if attempt < max_attempts - 1:
                print(f"    Waiting for email... ({attempt + 1}/{max_attempts})")
                time.sleep(5)

        print(f"  ✗ No verification code found in Gmail")
        return None

    except Exception as e:
        print(f"  ✗ Error fetching code from Gmail: {e}")
        return None


def create_tiktok_account(browser_info, email, username, password):
    """Create a TikTok account using Playwright"""

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print("No WebSocket endpoint found")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]

            # Close all extra pages/tabs, keep only one
            print("  → Ensuring single tab...")
            pages = context.pages
            if len(pages) > 1:
                print(f"    → Closing {len(pages) - 1} extra tabs...")
                for extra_page in pages[1:]:
                    try:
                        extra_page.close()
                    except:
                        pass
                time.sleep(1)

            # Get or create the page
            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to TikTok signup
            print("  → Opening TikTok signup...")
            page.goto("https://www.tiktok.com/signup", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Click "Use phone or email"
            print("  → Clicking 'Use phone or email'...")
            try:
                page.click("text=Use phone or email", timeout=5000)
                time.sleep(2)
            except:
                pass

            # Click "Email" tab
            print("  → Selecting email signup...")
            try:
                page.click("text=Email", timeout=5000)
                time.sleep(2)
            except:
                pass

            # Fill birthdate FIRST (TikTok requires this)
            print("  → Selecting birthdate...")
            try:
                import datetime
                birth_year = str(datetime.datetime.now().year - 25)

                # Wait for birthdate combobox elements to be ready (not search box!)
                page.wait_for_selector("[role='combobox'][aria-label*='Month']", timeout=10000)
                time.sleep(1)

                # Select Month (custom combobox)
                print("    → Selecting month...")
                month_combobox = page.locator("[role='combobox'][aria-label*='Month']")
                month_combobox.click()
                time.sleep(0.5)
                # Click on "January" option
                page.locator("[role='option']:has-text('January')").first.click()
                time.sleep(0.5)

                # Select Day (15th)
                print("    → Selecting day...")
                day_combobox = page.locator("[role='combobox'][aria-label*='Day']")
                day_combobox.click()
                time.sleep(0.5)
                # Click on day 15
                page.locator("[role='option']:has-text('15')").first.click()
                time.sleep(0.5)

                # Select Year (make account 25 years old)
                print("    → Selecting year...")
                year_combobox = page.locator("[role='combobox'][aria-label*='Year']")
                year_combobox.click()
                time.sleep(0.5)
                # Click on the birth year
                page.locator(f"[role='option']:has-text('{birth_year}')").first.click()
                time.sleep(1)

                print("  ✓ Birthdate selected successfully")
            except Exception as e:
                print(f"  ⚠ Could not set birthdate: {e}")

            # Fill email (slow)
            print(f"  → Entering email: {email}")
            email_input = page.locator("input[type='text']").first
            email_input.fill(email)
            time.sleep(3)  # Slower

            # Fill password (slow)
            print(f"  → Entering password...")
            password_input = page.locator("input[type='password']").first
            password_input.fill(password)
            time.sleep(5)  # Wait longer for TikTok's validation

            # Click "Send code" button - try multiple methods
            print("  → Clicking 'Send code'...")
            code_sent = False
            try:
                # Method 1: Normal click
                send_button = page.locator("button:has-text('Send code'), div:has-text('Send code')").first
                send_button.scroll_into_view_if_needed()
                time.sleep(1)
                send_button.click(force=True, timeout=10000)
                time.sleep(2)

                # Verify click worked - check if "Resend code" countdown appeared (greyed out)
                try:
                    resend_text = page.locator("text=/Resend code/i").first
                    if resend_text.is_visible(timeout=3000):
                        print("    ✓ Code request sent (Resend code countdown visible)")
                        code_sent = True
                except:
                    # Fallback: check if code input field appeared
                    try:
                        code_input = page.locator("input[placeholder*='code' i], input[placeholder*='Enter' i]").first
                        if code_input.is_visible(timeout=2000):
                            print("    ✓ Code request sent (input field appeared)")
                            code_sent = True
                    except:
                        pass

                if not code_sent:
                    # Method 2: Try JavaScript click as fallback
                    print("    → Trying JavaScript click...")
                    page.evaluate("document.querySelector('[type=button]') ? document.querySelector('[type=button]').click() : null")
                    time.sleep(2)
                    code_sent = True

                # Check if TikTok is rate-limiting this browser
                try:
                    if page.locator("text=Maximum number of attempts reached").is_visible(timeout=2000):
                        print("  ⚠ Browser is rate-limited by TikTok")
                        return "rate_limited"
                except:
                    pass

                if code_sent:
                    print("    ✓ No rate limit detected, fetching code...")
            except Exception as e:
                print(f"  ⚠ Error clicking Send code: {e}")
                # Try one more time with JavaScript
                try:
                    print("    → Attempting JavaScript fallback...")
                    page.evaluate("Array.from(document.querySelectorAll('*')).find(el => el.textContent.includes('Send code') && el.onclick).click()")
                    time.sleep(2)
                    code_sent = True
                except:
                    pass

            # Fetch verification code (start immediately, don't wait for input to appear)
            code = fetch_verification_code(email)
            if not code:
                print("  ✗ Could not fetch verification code")
                return False

            # Enter verification code
            print(f"  → Entering verification code: {code}")
            try:
                # Wait briefly for code input field to appear, then enter immediately
                time.sleep(1)
                code_input = page.locator("input[placeholder*='6-digit' i]").first
                code_input.fill(code)
                time.sleep(2)

                # TikTok may auto-verify when all 6 digits are entered
                print("    → Code entered, waiting for auto-verification...")
                time.sleep(3)

                # Check for "Maximum number of attempts" error
                try:
                    if page.locator("text=/Maximum number of attempts/i").is_visible(timeout=2000):
                        print("  ⚠ TikTok error: Maximum number of attempts reached")
                        return "rate_limited"
                except:
                    pass
            except Exception as e:
                print(f"  ✗ Error entering code: {e}")
                # Try alternative method - individual digit inputs
                try:
                    code_inputs = page.locator("input[type='text']").all()
                    if len(code_inputs) >= 6:
                        for i, digit in enumerate(code[:6]):
                            code_inputs[i].fill(digit)
                            time.sleep(0.2)
                        print("    → Code entered in individual fields")
                        time.sleep(3)
                    else:
                        return False
                except:
                    return False

            # PAUSE for user to verify before submitting
            print("  ⏸️  PAUSING - Check the browser now! Waiting 30 seconds before clicking Next...")
            print("     Press Ctrl+C to abort if something is wrong")
            time.sleep(30)

            # Try clicking Next/Sign up button if it exists
            print("  → Looking for Next/Sign up button...")
            try:
                # Look for enabled Next or Sign up button
                if page.locator("button:has-text('Next'):not([disabled])").is_visible(timeout=2000):
                    page.click("button:has-text('Next')")
                    print("    → Clicked 'Next'")
                    time.sleep(5)
                elif page.locator("button:has-text('Sign up'):not([disabled])").is_visible(timeout=2000):
                    page.click("button:has-text('Sign up')")
                    print("    → Clicked 'Sign up'")
                    time.sleep(3)
                else:
                    print("    → No button needed (auto-verified)")
            except:
                print("    → No button needed (auto-verified)")
                pass

            # Check for username prompt and click Skip
            print("  → Checking for username prompt...")
            time.sleep(3)

            # Try multiple selectors for Skip button/link
            skip_clicked = False
            for selector in ["text=Skip", "button:has-text('Skip')", "a:has-text('Skip')", "[class*='skip' i]"]:
                try:
                    skip_element = page.locator(selector).first
                    if skip_element.is_visible(timeout=2000):
                        print(f"  → Found Skip element with selector: {selector}")
                        skip_element.click()
                        print("  → Clicked 'Skip' on username prompt")
                        time.sleep(3)
                        skip_clicked = True
                        break
                except Exception as e:
                    print(f"    → Selector '{selector}' not found: {str(e)[:50]}")
                    continue

            if not skip_clicked:
                print("  → No Skip button found, proceeding anyway")

            # Check if successfully logged in
            print("  → Checking if signup completed...")
            time.sleep(10)  # Wait longer for redirect

            current_url = page.url
            print(f"    Current URL: {current_url}")

            # If we see profile or home page, success
            if "tiktok.com/@" in current_url or "foryou" in current_url or "following" in current_url:
                print("  ✓ Account created successfully!")
                return True
            else:
                # Take screenshot for debugging
                try:
                    screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/signup_failed_{email.split('@')[0]}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"  ⚠ Signup incomplete - screenshot: {screenshot_path}")
                except:
                    pass

                print(f"  ✗ Signup did not complete successfully (URL: {current_url})")
                return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def update_csv_status(account_index, browser_number, status):
    """Update CSV file with browser assignment and status"""
    try:
        # Read all accounts
        accounts = fetch_account_data()

        # Update the specific account
        found = False
        for acc in accounts:
            if acc.get('Account #') == str(account_index):
                acc['Proxy browser'] = str(browser_number)
                acc['Status'] = status
                found = True
                break

        # If account not found (e.g., "used_802"), append a new row
        if not found:
            new_row = {
                'Account #': str(account_index),
                'Proxy browser': str(browser_number),
                'Email': '',
                'Username': '',
                'Password': '',
                'Status': status
            }
            accounts.append(new_row)

        # Write back to CSV
        with open(CSV_FILE_PATH, 'w', newline='') as f:
            fieldnames = ['Account #', 'Proxy browser', 'Email', 'Username', 'Password', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(accounts)

        print(f"  ✓ Updated CSV: Account #{account_index} -> Browser {browser_number}, Status: {status}")
    except Exception as e:
        print(f"  ⚠ Failed to update CSV: {e}")


def main():
    print("=" * 60)
    print("  TikTok Account Creation Automation")
    print("=" * 60)
    print()

    # Fetch accounts
    print("Fetching account data from Google Sheets...")
    accounts = fetch_account_data()

    # Filter for "Not Created"
    pending = [acc for acc in accounts if acc.get('Status', '').strip() == 'Not Created']
    print(f"Found {len(pending)} accounts to create")
    print()

    if not pending:
        print("No accounts need creation!")
        return

    # Process each account
    for i, account in enumerate(pending):
        account_num = account.get('Account #', '?')
        email = account.get('Email', '')
        username = account.get('Username', '')
        password = account.get('Password', '')

        print(f"[{i+1}/{len(pending)}] Account #{account_num}: {username}")
        print(f"  Email: {email}")

        # Ensure no browsers are open before starting (cleanup any lingering instances)
        print(f"  → Checking for open browsers...")
        try:
            resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/active", timeout=5)
            active = resp.json().get("data", {}).get("list", [])
            if active:
                print(f"  → Found {len(active)} open browser(s), closing them...")
                for browser in active:
                    user_id = browser.get("user_id")
                    if user_id:
                        close_browser(user_id)
                        time.sleep(1)
                print(f"  ✓ All browsers closed")
            else:
                print(f"  ✓ No browsers currently open")
        except Exception as e:
            print(f"  ⚠ Could not check active browsers: {e}")

        # Try to find a browser that's not already logged in
        browser_found = False
        max_attempts = 10
        attempt = 0

        while not browser_found and attempt < max_attempts:
            attempt += 1

            # Get available browser
            profile = get_available_browser()
            if not profile:
                print("  ✗ No available browsers!")
                break

            profile_name = profile.get('name', '')
            user_id = profile.get('user_id', '')
            browser_num = str(profile.get('serial_number', ''))

            print(f"  Trying browser: {profile_name} (Serial #{browser_num})")

            # Open browser
            browser_info = open_browser(user_id)
            if not browser_info:
                print(f"  ✗ Failed to open browser")
                close_browser(user_id)
                continue

            time.sleep(2)

            # Check if already logged in
            print(f"  Checking if browser is already logged into TikTok...")
            if is_browser_logged_in(browser_info):
                print(f"  ⚠ Browser {profile_name} is already logged in - marking as used and trying next...")
                # Mark this browser as used so we don't try it again
                update_csv_status(f"used_{browser_num}", browser_num, "already_logged_in")
                close_browser(user_id)
                time.sleep(2)
                continue

            # Browser is not logged in, we can use it
            print(f"  ✓ Browser {profile_name} is available for new account")
            browser_found = True

            # Close and reopen to get fresh connection
            close_browser(user_id)
            time.sleep(2)
            browser_info = open_browser(user_id)
            if not browser_info:
                print(f"  ✗ Failed to reopen browser")
                browser_found = False
                continue
            time.sleep(2)

        if not browser_found:
            print(f"  ✗ Could not find an available browser after {max_attempts} attempts")
            continue

        # Create account with email retry and browser retry logic
        print(f"  Creating TikTok account...")
        success = False
        email_attempts = 0
        max_email_attempts = 1  # Only ONE attempt per browser to avoid rate limiting
        browser_retry = False

        while not success and email_attempts < max_email_attempts:
            email_attempts += 1

            if email_attempts > 1:
                # Generate new email for retry
                print(f"  ⚠ Attempt {email_attempts}: Trying with a new email address...")
                email = generate_new_email()
                update_account_email(account_num, email)
                print(f"  → Using email: {email}")

            result = create_tiktok_account(browser_info, email, username, password)

            # Check if browser is rate-limited
            if result == "rate_limited":
                print(f"  ⚠ Browser {profile_name} is rate-limited by TikTok")
                # Mark browser as rate-limited
                update_csv_status(f"ratelimit_{browser_num}", browser_num, "rate_limited")
                # Close this browser and try with a different one
                print(f"  → Closing rate-limited browser...")
                close_browser(user_id)
                browser_retry = True
                break  # Exit email retry loop to get new browser

            success = result

            if not success and email_attempts < max_email_attempts:
                print(f"  ⚠ Account creation failed, will retry with new email...")
                time.sleep(3)

        # Close browser after account creation
        print(f"  Closing browser...")
        close_browser(user_id)
        print()

        # If browser was rate-limited, decrement counter and retry with new browser
        if browser_retry:
            print(f"  → Retrying account with a different browser...")
            i -= 1  # Retry this account
            time.sleep(5)
            continue

        if success:
            print(f"  ✓ Account creation process started")
            update_csv_status(account_num, browser_num, "created")
        else:
            print(f"  ✗ Failed after {email_attempts} attempts")

        # Small delay before next account
        time.sleep(5)

    print()
    print("=" * 60)
    print(f"  Done! Processed {i+1} accounts")
    print("=" * 60)


if __name__ == "__main__":
    main()
