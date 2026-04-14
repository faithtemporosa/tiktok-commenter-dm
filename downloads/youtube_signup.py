#!/usr/bin/env python3
"""
Create YouTube/Google accounts using TikTok email addresses
Fetches verification codes from Gmail API (same as TikTok signup)
"""

import requests
import time
from playwright.sync_api import sync_playwright
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import base64
import pickle
import os
import csv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = os.path.join(os.path.dirname(__file__), 'tiktok_accounts.csv')

# Gmail API configuration (same as TikTok)
GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Videos to watch and like after signup
VIDEOS_TO_WATCH = [
    "https://www.youtube.com/watch?v=kpLgGkYTcag",
    "https://www.youtube.com/watch?v=s4XUJlNnHtU",
    "https://www.youtube.com/watch?v=5o3f1yE9N1E",
    "https://www.youtube.com/watch?v=XkokY3AVUKE",
]

# Thread-safe locks
print_lock = threading.Lock()
gmail_lock = threading.Lock()
_gmail_service = None

def safe_print(msg):
    with print_lock:
        print(msg, flush=True)

def get_gmail_service():
    """Get Gmail API service (thread-safe singleton)"""
    global _gmail_service
    with gmail_lock:
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

def fetch_google_verification_code(email, max_attempts=36):
    """Fetch Google verification code from Gmail (similar to TikTok code fetching)"""
    try:
        safe_print(f"    Fetching verification code from Gmail for {email}...")
        service = get_gmail_service()

        # Search for Google verification emails
        query = f'from:google to:{email} subject:(verification OR code OR verify) is:unread newer_than:10m'

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

                    # Look for 6-digit code in subject
                    code_patterns = [
                        r'(\d{6})\s+is your',
                        r'verification code[:\s]+(\d{6})',
                        r'code[:\s]+(\d{6})',
                        r'\b(\d{6})\b',
                    ]

                    for pattern in code_patterns:
                        code_match = re.search(pattern, subject, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            safe_print(f"    Got code: {code} (from subject)")

                            # Mark as read
                            try:
                                service.users().messages().modify(
                                    userId='me',
                                    id=msg_info['id'],
                                    body={'removeLabelIds': ['UNREAD']}
                                ).execute()
                            except:
                                pass
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
                            safe_print(f"    Got code: {code} (from body)")

                            try:
                                service.users().messages().modify(
                                    userId='me',
                                    id=msg_info['id'],
                                    body={'removeLabelIds': ['UNREAD']}
                                ).execute()
                            except:
                                pass
                            return code

            if attempt < max_attempts - 1:
                safe_print(f"    Waiting for email... ({attempt + 1}/{max_attempts})")
                time.sleep(5)

        safe_print(f"    No verification code found")
        return None

    except Exception as e:
        safe_print(f"    Error fetching code: {e}")
        return None

# Load credentials from CSV once (by Account #)
_credentials_cache = None

def load_credentials():
    global _credentials_cache
    if _credentials_cache is not None:
        return _credentials_cache

    _credentials_cache = {}
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            account_num = row.get('Account #', '')
            if account_num and account_num.isdigit():
                email = row.get('Email', '')
                if email and '@' in email:
                    _credentials_cache[int(account_num)] = {
                        'account_num': int(account_num),
                        'username': row.get('Username', ''),
                        'password': row.get('Password', ''),
                        'email': email,
                        'status': row.get('Status', ''),
                    }
    return _credentials_cache

def get_account_credentials(profile_num):
    """Get credentials by profile number (tt1 = 0, tt2 = 1, etc.)"""
    creds = load_credentials()
    account_num = profile_num - 1
    return creds.get(account_num)

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    if data.get("code") == 0:
        return data["data"]["ws"]["puppeteer"]
    return None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def watch_and_like_videos(page, profile_name):
    safe_print(f"  [{profile_name}] Watching and liking {len(VIDEOS_TO_WATCH)} videos...")

    for i, video_url in enumerate(VIDEOS_TO_WATCH, 1):
        try:
            safe_print(f"    [{profile_name}] [{i}/{len(VIDEOS_TO_WATCH)}] Opening video...")
            page.goto(video_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            try:
                like_selectors = [
                    'like-button-view-model button',
                    '#segmented-like-button button',
                    'ytd-menu-renderer button[aria-label*="like"]',
                ]

                like_btn = None
                for selector in like_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=2000):
                            like_btn = btn
                            break
                    except:
                        continue

                if like_btn:
                    aria_pressed = like_btn.get_attribute("aria-pressed")
                    if aria_pressed != "true":
                        like_btn.click()
                        safe_print(f"    [{profile_name}] [{i}/{len(VIDEOS_TO_WATCH)}] Liked!")
                        time.sleep(1)
                    else:
                        safe_print(f"    [{profile_name}] [{i}/{len(VIDEOS_TO_WATCH)}] Already liked")
                else:
                    safe_print(f"    [{profile_name}] [{i}/{len(VIDEOS_TO_WATCH)}] Like button not found")
            except Exception as e:
                safe_print(f"    [{profile_name}] Could not like: {str(e)[:50]}")

            watch_time = random.randint(30, 45)
            safe_print(f"    [{profile_name}] [{i}/{len(VIDEOS_TO_WATCH)}] Watching for {watch_time}s...")
            time.sleep(watch_time)

        except Exception as e:
            safe_print(f"    [{profile_name}] Error: {str(e)[:50]}")

    safe_print(f"  [{profile_name}] Finished watching videos")

def signup_google_account(page, profile_name, email, password, username, birthdate):
    """Sign up for Google account using existing email"""
    safe_print(f"  [{profile_name}] Starting Google signup with {email}")

    try:
        from datetime import datetime as dt
        birthdate_obj = dt.strptime(birthdate, "%B %d, %Y")
        month = birthdate_obj.strftime("%B")
        day = str(birthdate_obj.day)
        year = str(birthdate_obj.year)
    except:
        month, day, year = "January", "1", "2001"

    first_name = username[:20].capitalize()
    last_name = "User"

    try:
        # Click Create account
        safe_print(f"  [{profile_name}] Clicking Create account...")
        create_btn = page.locator('button:has-text("Create account"), span:has-text("Create account")').first
        create_btn.wait_for(state="visible", timeout=10000)
        create_btn.click()
        time.sleep(2)

        # Personal use
        try:
            personal = page.locator('li:has-text("For my personal use"), li:has-text("For personal use")').first
            personal.wait_for(state="visible", timeout=5000)
            personal.click()
            time.sleep(2)
        except:
            pass

        # Name
        safe_print(f"  [{profile_name}] Filling name: {first_name} {last_name}")
        page.locator('input[name="firstName"]').first.fill(first_name)
        time.sleep(0.5)
        page.locator('input[name="lastName"]').first.fill(last_name)
        time.sleep(0.5)

        # Next
        page.locator('button:has-text("Next")').first.click()
        time.sleep(3)

        # Birthdate - click dropdown and select
        safe_print(f"  [{profile_name}] Filling birthdate...")
        page.click('#month')
        time.sleep(0.5)
        page.click(f'li:has-text("{month}")')
        time.sleep(0.5)

        page.fill('input#day', day)
        page.fill('input#year', year)
        time.sleep(0.5)

        # Gender - click dropdown and select
        page.click('#gender')
        time.sleep(0.5)
        page.click('li:has-text("Rather not say")')
        time.sleep(1)

        # Next
        page.locator('button:has-text("Next")').first.click()
        time.sleep(3)

        # Click "Use your existing email" link
        safe_print(f"  [{profile_name}] Clicking 'Use your existing email'...")
        page.click('text=Use your existing email')
        time.sleep(2)

        # Enter email
        safe_print(f"  [{profile_name}] Entering email: {email}")
        email_input = page.locator('input[type="email"], input[name="Email"]').first
        email_input.wait_for(state="visible", timeout=10000)
        email_input.fill(email)
        time.sleep(1)

        # Next
        page.locator('button:has-text("Next")').first.click()
        time.sleep(5)

        # Wait for verification code input
        safe_print(f"  [{profile_name}] Waiting for verification code step...")
        try:
            code_input = page.locator('input[name="code"], input[type="tel"], input[aria-label*="code" i]').first
            code_input.wait_for(state="visible", timeout=15000)

            # Fetch code from Gmail
            code = fetch_google_verification_code(email)
            if code:
                safe_print(f"  [{profile_name}] Entering code: {code}")
                code_input.fill(code)
                time.sleep(1)

                # Next/Verify
                page.locator('button:has-text("Next"), button:has-text("Verify")').first.click()
                time.sleep(5)
            else:
                safe_print(f"  [{profile_name}] Could not get verification code")
                return False
        except Exception as e:
            safe_print(f"  [{profile_name}] Verification step: {str(e)[:60]}")

        # Password
        safe_print(f"  [{profile_name}] Setting password...")
        try:
            pwd_input = page.locator('input[type="password"], input[name="Passwd"]').first
            pwd_input.wait_for(state="visible", timeout=10000)
            pwd_input.fill(password)
            time.sleep(1)

            try:
                confirm = page.locator('input[name="PasswdAgain"]').first
                if confirm.is_visible(timeout=2000):
                    confirm.fill(password)
            except:
                pass

            page.locator('button:has-text("Next")').first.click()
            time.sleep(5)
        except Exception as e:
            safe_print(f"  [{profile_name}] Password error: {str(e)[:60]}")

        # Handle QR code / 2FA step - try to skip or use alternative
        try:
            # Look for "Skip" button
            skip_btn = page.locator('button:has-text("Skip"), span:has-text("Skip"), a:has-text("Skip")').first
            if skip_btn.is_visible(timeout=3000):
                safe_print(f"  [{profile_name}] Skipping QR/2FA step...")
                skip_btn.click()
                time.sleep(3)
        except:
            pass

        # Try "Not now" or "Do this later"
        try:
            not_now = page.locator('button:has-text("Not now"), span:has-text("Not now"), a:has-text("Not now"), button:has-text("Do this later")').first
            if not_now.is_visible(timeout=2000):
                safe_print(f"  [{profile_name}] Clicking 'Not now'...")
                not_now.click()
                time.sleep(3)
        except:
            pass

        # Try "I\'ll do this later" or similar
        try:
            later = page.locator('button:has-text("later"), a:has-text("later")').first
            if later.is_visible(timeout=2000):
                safe_print(f"  [{profile_name}] Clicking 'later' option...")
                later.click()
                time.sleep(3)
        except:
            pass

        # Skip phone if asked
        try:
            skip = page.locator('button:has-text("Skip"), span:has-text("Skip")').first
            if skip.is_visible(timeout=3000):
                skip.click()
                time.sleep(2)
        except:
            pass

        # Agree to terms
        try:
            agree = page.locator('button:has-text("I agree"), button:has-text("Agree")').first
            if agree.is_visible(timeout=3000):
                agree.click()
                time.sleep(3)
        except:
            pass

        safe_print(f"  [{profile_name}] Checking if signup completed...")

        # Take screenshot to debug
        screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/signup_debug_{profile_name}.png"
        page.screenshot(path=screenshot_path)
        safe_print(f"  [{profile_name}] Screenshot saved: {screenshot_path}")
        time.sleep(5)

        # Go to YouTube to verify
        page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)

        try:
            page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first.wait_for(state="visible", timeout=5000)
            safe_print(f"  [{profile_name}] Signup incomplete")
            return False
        except:
            safe_print(f"  [{profile_name}] Signup successful!")
            return True

    except Exception as e:
        safe_print(f"  [{profile_name}] Signup error: {str(e)[:100]}")
        return False

def process_youtube(profile_id, profile_name, email, password, birthdate, username):
    safe_print(f"\n{'='*60}")
    safe_print(f"Processing {profile_name}")
    safe_print(f"Email: {email}")
    safe_print(f"{'='*60}")

    debug_url = open_browser(profile_id)
    if not debug_url:
        safe_print(f"  [{profile_name}] Failed to open browser")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]

            while len(context.pages) > 1:
                context.pages[-1].close()

            page = context.pages[0] if context.pages else context.new_page()

            # First try Gmail login to check if account exists
            safe_print(f"  [{profile_name}] Navigating to Gmail...")
            page.goto("https://accounts.google.com/signin", wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            is_logged_in = False

            # Check if already logged in (shows account chooser or Gmail inbox)
            try:
                # If we see email input, we're not logged in
                email_input = page.locator('input[type="email"]').first
                email_input.wait_for(state="visible", timeout=5000)
                safe_print(f"  [{profile_name}] Not logged in")
            except:
                safe_print(f"  [{profile_name}] Already logged in!")
                is_logged_in = True

            if not is_logged_in:
                try:
                    # Try login with email
                    safe_print(f"  [{profile_name}] Trying login...")
                    email_input = page.locator('input[type="email"]').first
                    email_input.fill(email)
                    time.sleep(1)

                    page.locator('button:has-text("Next")').first.click()
                    time.sleep(3)

                    try:
                        pwd_input = page.locator('input[type="password"], input[name="Passwd"]').first
                        pwd_input.wait_for(state="visible", timeout=5000)
                        pwd_input.fill(password)
                        time.sleep(1)

                        page.locator('button:has-text("Next")').first.click()
                        time.sleep(5)

                        safe_print(f"  [{profile_name}] Logged in!")
                        is_logged_in = True
                    except:
                        safe_print(f"  [{profile_name}] Account doesn't exist, creating...")
                        page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
                        time.sleep(2)
                        page.locator('a[aria-label*="Sign in"], button:has-text("Sign in")').first.click()
                        time.sleep(3)

                        if signup_google_account(page, profile_name, email, password, username, birthdate):
                            is_logged_in = True

                except Exception as e:
                    safe_print(f"  [{profile_name}] Error: {str(e)[:60]}")

            if is_logged_in:
                watch_and_like_videos(page, profile_name)
                return True
            else:
                safe_print(f"  [{profile_name}] Could not login/signup")
                return False

    except Exception as e:
        safe_print(f"  [{profile_name}] Browser error: {str(e)[:100]}")
        return False
    finally:
        safe_print(f"  [{profile_name}] Closing browser...")
        try:
            close_browser(profile_id)
        except:
            pass

def process_profile(profile_data):
    profile, profile_num = profile_data
    profile_id = profile.get("user_id")
    profile_name = profile.get("name", profile_id)

    credentials = get_account_credentials(profile_num)
    if not credentials:
        safe_print(f"\n{profile_name} - No credentials, skipping")
        return False

    email = credentials.get("email")
    password = credentials.get("password")
    birthdate = credentials.get("birthdate", "January 1, 2001")
    username = credentials.get("username", "user")

    if not email or not password:
        safe_print(f"\n{profile_name} - Missing credentials, skipping")
        return False

    return process_youtube(profile_id, profile_name, email, password, birthdate, username)

def main():
    import sys

    num_to_process = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    num_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    print("Initializing Gmail API...")
    try:
        get_gmail_service()
        print("Gmail API ready")
    except Exception as e:
        print(f"Gmail API error: {e}")

    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    print(f"Found {len(profiles)} profiles")

    def sort_key(p):
        match = re.search(r'(\d+)', p.get("name", ""))
        return int(match.group(1)) if match else 999

    profiles = sorted(profiles, key=sort_key)
    profiles_to_process = profiles[start_index:start_index + num_to_process]
    print(f"Processing {len(profiles_to_process)} profiles (from index {start_index}), {num_workers} at a time")

    # Extract profile number from name (tt1 -> 1, tt2 -> 2, etc.)
    def get_profile_num(p):
        match = re.search(r'(\d+)', p.get("name", ""))
        return int(match.group(1)) if match else 0

    profile_data_list = [(p, get_profile_num(p)) for p in profiles_to_process]

    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(process_profile, pd): pd for pd in profile_data_list}
        for future in as_completed(futures):
            try:
                if future.result():
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                safe_print(f"Error: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY: Success={success}, Failed={failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
