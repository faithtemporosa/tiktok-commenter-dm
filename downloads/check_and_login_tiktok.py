#!/usr/bin/env python3
"""
Check TikTok login status and re-login if needed
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

ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = os.path.join(os.path.dirname(__file__), 'tiktok_accounts.csv')

# Gmail API configuration
GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

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
        print(f"    Fetching TikTok verification code from Gmail for {email}...")
        service = get_gmail_service()

        # Search for TikTok verification emails
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

                    # Look for 6-digit or 4-digit code
                    code_patterns = [
                        r'(\d{6})\s+is your',
                        r'verification code[:\s]+(\d{6})',
                        r'verification code[:\s]+(\d{4})',
                        r'code[:\s]+(\d{6})',
                        r'code[:\s]+(\d{4})',
                        r'\b(\d{6})\b',
                        r'\b(\d{4})\b',
                    ]

                    for pattern in code_patterns:
                        code_match = re.search(pattern, subject, re.IGNORECASE)
                        if code_match:
                            code = code_match.group(1)
                            print(f"    Got code: {code} (from subject)")

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
                            print(f"    Got code: {code} (from body)")

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

            if attempt < max_attempts - 1:
                time.sleep(5)

        print(f"    No verification code found after {max_attempts} attempts")
        return None

    except Exception as e:
        print(f"    Error fetching code: {str(e)[:60]}")
        return None

def load_credentials():
    """Load credentials from CSV, indexed by Proxy browser number"""
    credentials = {}
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxy_browser = row.get('Proxy browser', '')
            status = row.get('Status', '')
            # Only include accounts that were successfully created
            if proxy_browser and proxy_browser.isdigit() and status == 'created':
                email = row.get('Email', '')
                if email and '@' in email:
                    credentials[int(proxy_browser)] = {
                        'browser_num': int(proxy_browser),
                        'username': row.get('Username', ''),
                        'password': row.get('Password', ''),
                        'email': email,
                    }
    return credentials

def get_account_credentials(profile_num):
    """Get credentials by browser number (tt27 -> 27, tt328 -> 328)"""
    creds = load_credentials()
    return creds.get(profile_num)

def open_browser(user_id, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=60)
            data = response.json()
            if data.get("code") == 0:
                time.sleep(2)  # Give browser time to fully start
                return data["data"]["ws"]["puppeteer"]
            elif "Too many" in str(data.get("msg", "")):
                print(f"  Rate limited, waiting...")
                time.sleep(5)
                continue
            else:
                print(f"  Browser start error: {data.get('msg', 'Unknown')}")
        except Exception as e:
            print(f"  Browser start exception: {str(e)[:50]}")
            if attempt < retries - 1:
                time.sleep(3)
    return None

def close_browser(user_id):
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass

def check_and_login_tiktok(profile_id, profile_name, username, password, email=None):
    """Check if logged into TikTok, login if not"""
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
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=60000)

            # Wait for cookies to load and TikTok to process session
            print(f"  Waiting for session to restore from cookies...")
            time.sleep(12)

            # Close any popups/modals that might be blocking (interest selection, etc.)
            try:
                # Try various close button selectors
                close_selectors = [
                    '[aria-label="Close"]',
                    'button:has-text("×")',
                    '.close-button',
                    '[data-e2e="modal-close-inner-button"]',
                    'button[aria-label="Fermer"]',  # French
                    'button[aria-label="Schließen"]',  # German
                ]
                for selector in close_selectors:
                    try:
                        close_btn = page.locator(selector).first
                        if close_btn.is_visible(timeout=500):
                            close_btn.click()
                            time.sleep(1)
                            print(f"  Closed popup modal")
                            break
                    except:
                        continue

                # Also check for interest selection modals by looking for "Continuer" / "Continue" / "Skip" buttons
                skip_selectors = [
                    'button:has-text("Skip")',
                    'button:has-text("Continuer")',  # French
                    'button:has-text("Continue")',
                    'button:has-text("Weiter")',  # German
                ]
                for selector in skip_selectors:
                    try:
                        skip_btn = page.locator(selector).first
                        if skip_btn.is_visible(timeout=500):
                            skip_btn.click()
                            time.sleep(2)
                            print(f"  Clicked skip/continue button")
                            break
                    except:
                        continue
            except:
                pass

            # Check if logged in - need to find POSITIVE indicators of being logged in
            current_url = page.url
            print(f"  Current URL: {current_url}")

            is_logged_in = False

            # Check URL first - these URLs only show when logged in
            if 'foryou' in current_url or 'following' in current_url:
                is_logged_in = True
                print(f"  URL indicates logged in (foryou/following)")
            elif '@' in current_url:
                is_logged_in = True
                print(f"  URL indicates logged in (profile page)")
            else:
                # Check sidebar for logged-in indicators
                # When logged in, sidebar shows: Messages, Activity, Profile (as links)
                # When logged out, sidebar shows: Log in button

                # Check for "Messages" link in sidebar - ONLY visible when logged in
                # Support multiple languages
                messages_texts = [
                    "Messages", "Žinutės", "Nachrichten", "Messaggi", "Mensajes",
                    "Messages", "Berichten", "Mensagens", "Wiadomości", "消息"
                ]
                try:
                    for text in messages_texts:
                        messages_link = page.locator(f'a:has-text("{text}")').first
                        if messages_link.is_visible(timeout=500):
                            is_logged_in = True
                            print(f"  Found Messages link ({text}) - user IS logged in")
                            break
                except:
                    pass

                if not is_logged_in:
                    try:
                        inbox_icon = page.locator('[data-e2e="nav-inbox"], [data-e2e="inbox-icon"]').first
                        if inbox_icon.is_visible(timeout=1000):
                            is_logged_in = True
                            print(f"  Found inbox icon - user IS logged in")
                    except:
                        pass

                if not is_logged_in:
                    # Check for Activity/Veikla/Aktivität link - only when logged in
                    activity_texts = ["Activity", "Veikla", "Aktivität", "Attività", "Actividad", "Activité"]
                    try:
                        for text in activity_texts:
                            activity_link = page.locator(f'a:has-text("{text}")').first
                            if activity_link.is_visible(timeout=500):
                                is_logged_in = True
                                print(f"  Found Activity link ({text}) - user IS logged in")
                                break
                    except:
                        pass

                if not is_logged_in:
                    # Check for Friends/Draugai link - only when logged in
                    friends_texts = ["Friends", "Draugai", "Freunde", "Amici", "Amigos", "Amis"]
                    try:
                        for text in friends_texts:
                            friends_link = page.locator(f'a:has-text("{text}")').first
                            if friends_link.is_visible(timeout=500):
                                is_logged_in = True
                                print(f"  Found Friends link ({text}) - user IS logged in")
                                break
                    except:
                        pass

                if not is_logged_in:
                    # As final check, look for "Log in" button in sidebar - if visible, definitely logged out
                    # Support multiple languages
                    login_texts = ["Log in", "Se connecter", "Anmelden", "Accedi", "Iniciar sesión", "Prisijungti", "Inloggen"]
                    found_login_btn = False
                    try:
                        for text in login_texts:
                            login_check = page.locator(f'nav a:has-text("{text}"), aside a:has-text("{text}")').first
                            if login_check.is_visible(timeout=500):
                                is_logged_in = False
                                found_login_btn = True
                                print(f"  Found Log in button ({text}) - user is NOT logged in")
                                break
                        if not found_login_btn:
                            # No clear indicators either way, assume logged out to be safe
                            is_logged_in = False
                            print(f"  No clear login indicators - will attempt login")
                    except:
                        # Cannot determine - assume logged out to be safe
                        is_logged_in = False
                        print(f"  Could not check login button - will attempt login")

            if is_logged_in:
                print(f"  ✓ Already logged in!")
                return True

            print(f"  ✗ Not logged in - attempting login with CSV credentials...")

            # Take screenshot before looking for login button
            page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_before_login_{profile_name}.png")

            # Click the red "Log in" button on the sidebar to open the modal
            print(f"  Looking for Log in button...")
            try:
                # Try different selectors for the Log in button
                login_clicked = False

                # Approach 1: Try the red button in sidebar by role
                try:
                    red_button = page.get_by_role("link", name="Log in")
                    if red_button.is_visible(timeout=3000):
                        red_button.click()
                        login_clicked = True
                        print(f"  Clicked red Log in button (role)")
                except:
                    pass

                # Approach 2: Try by text content
                if not login_clicked:
                    try:
                        page.click('text="Log in"', timeout=3000)
                        login_clicked = True
                        print(f"  Clicked Log in (text)")
                    except:
                        pass

                # Approach 3: Try the header Log in button
                if not login_clicked:
                    try:
                        header_btn = page.locator('header a:has-text("Log in"), header button:has-text("Log in")').first
                        if header_btn.is_visible(timeout=2000):
                            header_btn.click()
                            login_clicked = True
                            print(f"  Clicked header Log in button")
                    except:
                        pass

                # Approach 4: Try any visible button/link with "Log in" text
                if not login_clicked:
                    all_login_btns = page.locator('a, button').filter(has_text="Log in").all()
                    for btn in all_login_btns:
                        try:
                            if btn.is_visible():
                                btn.click()
                                login_clicked = True
                                print(f"  Clicked a Log in button")
                                break
                        except:
                            continue

                if not login_clicked:
                    print(f"  Could not find Log in button")
                    page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_no_login_btn_{profile_name}.png")
                    return False

                time.sleep(3)
                print(f"  Waiting for login modal...")
            except Exception as e:
                print(f"  Error clicking Log in button: {str(e)[:100]}")
                return False

            # Wait longer for login modal to fully load
            time.sleep(5)

            # Take screenshot of login modal
            screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_login_{profile_name}.png"
            page.screenshot(path=screenshot_path)
            print(f"  Login modal screenshot: {screenshot_path}")

            # Check if login modal is visible (has "Use phone or email" text)
            # If not visible, there might be an interest modal blocking it
            try:
                if not page.get_by_text("Use phone or email").is_visible(timeout=2000):
                    # Interest modal might be blocking - look for it specifically
                    print(f"  Login options not visible, checking for blocking modals...")

                    # Look for interest selection modal by its content
                    if page.get_by_text("What would you like to watch").is_visible(timeout=1000):
                        close_btn = page.locator('[aria-label="Close"]').first
                        close_btn.click()
                        time.sleep(2)
                        print(f"  Closed interest selection modal")

                        # Click login button again
                        login_btn_retry = page.get_by_role("link", name="Log in")
                        login_btn_retry.click()
                        time.sleep(3)
                        print(f"  Clicked Log in button again")
            except Exception as e:
                print(f"  No blocking modal found or error: {str(e)[:50]}")

            # IMPORTANT: Click "Use phone or email" option in the modal
            print(f"  Looking for 'Use phone or email' option...")
            try:
                # Wait for the login modal to be visible
                time.sleep(2)

                # Click the element containing the text (try multiple approaches)
                clicked = False

                # Approach 1: Click "Use phone or email" (current TikTok UI)
                try:
                    page.click('text="Use phone or email"', timeout=3000)
                    clicked = True
                    print(f"  Clicked 'Use phone or email'")
                except:
                    pass

                # Approach 2: Try old text
                if not clicked:
                    try:
                        page.click('text="Use phone / email / username"', timeout=3000)
                        clicked = True
                        print(f"  Clicked 'Use phone / email / username'")
                    except:
                        pass

                # Approach 3: Find by partial text match
                if not clicked:
                    try:
                        page.click('text=/.*phone.*email.*/i', timeout=3000)
                        clicked = True
                        print(f"  Clicked phone/email option (regex)")
                    except:
                        pass

                if clicked:
                    time.sleep(5)  # Wait for form to appear
                else:
                    print(f"  Could not find phone/email login option")
                    page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_login_debug2_{profile_name}.png")
            except Exception as e:
                print(f"  Error clicking email option: {str(e)[:100]}")

            # Make sure we're on "Email or username" tab (not "Use phone")
            try:
                email_tab = page.locator('div:has-text("Email or username"), a:has-text("Use email")').first
                email_tab.click()
                time.sleep(2)
                print(f"  Selected Email or username tab")
            except:
                print(f"  Email/username tab may already be selected")

            # Enter email/username in the modal - try multiple selectors
            try:
                print(f"  Entering email/username: {username}")

                # Try different selectors for the email input
                selectors = [
                    'input[placeholder="Email or username"]',
                    'input[placeholder="Email address"]',
                    'input[name="email"]',
                    'input[type="text"]',
                ]

                email_input = None
                for selector in selectors:
                    try:
                        input_elem = page.locator(selector).first
                        if input_elem.is_visible(timeout=2000):
                            email_input = input_elem
                            print(f"  Found email input with selector: {selector}")
                            break
                    except:
                        continue

                if email_input:
                    email_input.click()
                    email_input.fill(username)
                    time.sleep(1)
                    print(f"  Entered username: {username}")
                else:
                    print(f"  Could not find email input field")
                    return False
            except Exception as e:
                print(f"  Could not enter username: {str(e)[:100]}")
                return False

            # Enter password
            try:
                print(f"  Entering password...")

                # Try multiple selectors for password field
                pwd_selectors = [
                    'input[type="password"]',
                    'input[placeholder="Password"]',
                    'input[placeholder*="password"]',
                    'input[name="password"]',
                ]

                pwd_input = None
                for selector in pwd_selectors:
                    try:
                        input_elem = page.locator(selector).first
                        if input_elem.is_visible(timeout=3000):
                            pwd_input = input_elem
                            print(f"  Found password input with selector: {selector}")
                            break
                    except:
                        continue

                if pwd_input:
                    pwd_input.click()
                    pwd_input.fill(password)
                    time.sleep(1)
                    print(f"  Entered password")
                else:
                    print(f"  Could not find password input field")
                    page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_no_pwd_{profile_name}.png")
                    return False
            except Exception as e:
                print(f"  Could not enter password: {str(e)[:100]}")
                return False

            # Click the "Log in" button in the modal
            try:
                print(f"  Clicking Log in button...")
                # Wait a moment for the button to become enabled
                time.sleep(2)

                # Take screenshot before clicking
                page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_before_submit_{profile_name}.png")

                # Try multiple approaches to click the submit button
                login_clicked = False

                # Approach 1: Find button with type="submit"
                try:
                    submit_btn = page.locator('button[type="submit"]').first
                    if submit_btn.is_visible(timeout=2000):
                        submit_btn.click()
                        login_clicked = True
                        print(f"  Clicked submit button")
                except:
                    pass

                # Approach 2: Look for button in the login form
                if not login_clicked:
                    try:
                        form_btn = page.locator('form button:has-text("Log in")').first
                        if form_btn.is_visible(timeout=2000):
                            form_btn.click()
                            login_clicked = True
                            print(f"  Clicked form Log in button")
                    except:
                        pass

                # Approach 3: Last button with "Log in" text
                if not login_clicked:
                    try:
                        login_btn = page.locator('button:has-text("Log in")').last
                        if login_btn.is_visible(timeout=2000):
                            login_btn.click()
                            login_clicked = True
                            print(f"  Clicked last Log in button")
                    except:
                        pass

                # Approach 4: Press Enter key
                if not login_clicked:
                    try:
                        page.keyboard.press("Enter")
                        login_clicked = True
                        print(f"  Pressed Enter key")
                    except:
                        pass

                if login_clicked:
                    time.sleep(5)
                else:
                    print(f"  Could not click login button")
                    page.screenshot(path=f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_no_submit_{profile_name}.png")
                    return False
            except Exception as e:
                print(f"  Could not click login button: {str(e)[:100]}")
                return False

            # Check if verification code is needed
            try:
                code_input = page.locator('input[placeholder*="verification"], input[placeholder*="code"], input[name="verifyCode"]').first
                if code_input.is_visible(timeout=3000):
                    print(f"  Verification code requested")

                    if email:
                        # Fetch code from Gmail
                        code = fetch_tiktok_verification_code(email)
                        if code:
                            print(f"  Entering verification code...")
                            code_input.fill(code)
                            time.sleep(2)

                            # Click submit/verify button
                            try:
                                verify_btn = page.locator('button:has-text("Verify"), button:has-text("Submit"), button[type="submit"]').first
                                verify_btn.click()
                                time.sleep(5)
                                print(f"  Submitted verification code")
                            except:
                                print(f"  No verify button found, code may auto-submit")
                                time.sleep(3)
                        else:
                            print(f"  Could not fetch verification code")
                            return False
                    else:
                        print(f"  No email provided to fetch verification code")
                        return False
            except:
                print(f"  No verification code requested")

            # Check if logged in
            current_url = page.url
            is_logged_in = ('foryou' in current_url or 'following' in current_url or '@' in current_url)

            if is_logged_in:
                print(f"  ✓ Login successful!")
                return True
            else:
                print(f"  ✗ Login may have failed - URL: {current_url}")
                # Take screenshot for debugging
                screenshot_path = f"/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_login_debug_{profile_name}.png"
                page.screenshot(path=screenshot_path)
                print(f"  Screenshot saved: {screenshot_path}")
                return False

    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
        return False
    finally:
        print(f"  Closing browser...")
        close_browser(profile_id)

def main():
    import sys

    # Initialize Gmail API
    print("Initializing Gmail API...")
    try:
        get_gmail_service()
        print("Gmail API ready")
    except Exception as e:
        print(f"Warning: Gmail API not available: {str(e)[:60]}")
        print("Will skip verification code handling")

    num_to_process = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    # Load credentials first to know which browsers have accounts
    all_credentials = load_credentials()
    print(f"Found {len(all_credentials)} browsers with saved credentials")

    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    data = response.json()

    if data.get("code") != 0:
        print(f"Error: {data.get('msg')}")
        return

    profiles = data.get("data", {}).get("list", [])
    print(f"Found {len(profiles)} browser profiles")

    # Create a map of browser number to profile
    profile_map = {}
    for p in profiles:
        match = re.search(r'(\d+)', p.get("name", "tt999"))
        if match:
            profile_map[int(match.group(1))] = p

    # Only process browsers that have credentials
    browsers_with_creds = sorted(all_credentials.keys())
    browsers_to_process = browsers_with_creds[start_index:start_index + num_to_process]
    print(f"Processing {len(browsers_to_process)} browsers with credentials (from index {start_index})")

    logged_in = 0
    logged_out = 0

    for browser_num in browsers_to_process:
        profile = profile_map.get(browser_num)
        if not profile:
            print(f"\ntt{browser_num}: Browser not found in AdsPower, skipping")
            continue

        profile_id = profile.get("user_id")
        profile_name = profile.get("name", profile_id)

        credentials = all_credentials[browser_num]
        username = credentials.get("username")
        password = credentials.get("password")
        email = credentials.get("email")

        result = check_and_login_tiktok(profile_id, profile_name, username, password, email)

        if result:
            logged_in += 1
        else:
            logged_out += 1

        # Wait between profiles
        time.sleep(random.randint(2, 4))

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Logged in: {logged_in}")
    print(f"  Logged out/failed: {logged_out}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
