#!/usr/bin/env python3
"""
Check all browsers and signup if logged out
"""

import requests
import time
from playwright.sync_api import sync_playwright
import re
import json
import csv
import random
import pickle
from googleapiclient.discovery import build

ADSPOWER_API = "http://local.adspower.net:50325"
CSV_PATH = 'tiktok_accounts.csv'
PROFILE_MAPPING_PATH = 'tiktok_profile_mapping.json'
GMAIL_TOKEN_PATH = 'gmail_token.pickle'
COOKIES_DIR = 'tiktok_cookies'

# Create cookies directory if it doesn't exist
import os
os.makedirs(COOKIES_DIR, exist_ok=True)

# Cache for credentials
_credentials_cache = None

def load_credentials_from_csv():
    """Load existing credentials from CSV, indexed by Proxy browser number"""
    global _credentials_cache
    if _credentials_cache is not None:
        return _credentials_cache

    credentials = {}
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxy_browser = row.get('Proxy browser', '')
            status = row.get('Status', '')
            # Only use accounts that were successfully created
            if proxy_browser and proxy_browser.isdigit() and status == 'created':
                credentials[int(proxy_browser)] = {
                    'username': row.get('Username', ''),
                    'password': row.get('Password', ''),
                    'email': row.get('Email', ''),
                }
    _credentials_cache = credentials
    return credentials

ADJECTIVES = ['swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'neon', 'atomic', 'vivid', 'prism', 'flux', 'zen', 'drift', 'echo', 'nova', 'pixel']
NOUNS = ['star', 'wave', 'pulse', 'echo', 'spark', 'flame', 'moon', 'phoenix', 'glow', 'path', 'stream', 'verse', 'core', 'field', 'track', 'scope']

def generate_creds():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(100, 999)
    return f"{adj}{noun}{num}@automateyourbizz.xyz", f"{adj}{noun}{random.randint(10,99)}", f"{adj.capitalize()}{noun.capitalize()}.{random.randint(10,99)}"

def fetch_code(email):
    with open(GMAIL_TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)
    service = build('gmail', 'v1', credentials=creds)
    query = f'from:tiktok to:{email} subject:(verification OR code) is:unread newer_than:10m'

    for attempt in range(30):
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        if results.get('messages'):
            msg = service.users().messages().get(userId='me', id=results['messages'][0]['id'], format='full').execute()
            subject = next((h['value'] for h in msg['payload']['headers'] if h['name'].lower() == 'subject'), '')
            code_match = re.search(r'(\d{6})', subject)
            if code_match:
                service.users().messages().modify(userId='me', id=results['messages'][0]['id'], body={'removeLabelIds': ['UNREAD']}).execute()
                return code_match.group(1)
        if attempt < 29: time.sleep(5)
    return None

def open_browser(user_id):
    response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=30)
    data = response.json()
    return data["data"]["ws"]["puppeteer"] if data.get("code") == 0 else None

def close_browser(user_id):
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}")

def check_login(page):
    """Check if logged in by looking for sidebar elements (multi-language)"""
    try:
        # Check URL first - these URLs only show when logged in
        current_url = page.url
        if 'foryou' in current_url or 'following' in current_url or '@' in current_url:
            return True

        # Check for Messages/Inbox link in sidebar (multiple languages)
        messages_texts = ["Messages", "Žinutės", "Nachrichten", "Messaggi", "Mensajes", "Berichten", "Mensagens", "Wiadomości", "消息"]
        for text in messages_texts:
            try:
                elem = page.locator(f'a:has-text("{text}")').first
                if elem.is_visible(timeout=500):
                    return True
            except:
                continue

        # Check for Activity link
        activity_texts = ["Activity", "Veikla", "Aktivität", "Attività", "Actividad", "Activité"]
        for text in activity_texts:
            try:
                elem = page.locator(f'a:has-text("{text}")').first
                if elem.is_visible(timeout=500):
                    return True
            except:
                continue

        # Check for Friends link
        friends_texts = ["Friends", "Draugai", "Freunde", "Amici", "Amigos", "Amis"]
        for text in friends_texts:
            try:
                elem = page.locator(f'a:has-text("{text}")').first
                if elem.is_visible(timeout=500):
                    return True
            except:
                continue

        # Check for data-e2e elements
        user_elements = ['[data-e2e="nav-inbox"]', '[data-e2e="nav-profile-icon"]']
        for elem_selector in user_elements:
            try:
                elem = page.locator(elem_selector).first
                if elem.is_visible(timeout=500):
                    return True
            except:
                continue

        # Check for Login button (multiple languages) - if found, NOT logged in
        login_texts = ["Log in", "Se connecter", "Anmelden", "Accedi", "Iniciar sesión", "Prisijungti", "Inloggen"]
        for text in login_texts:
            try:
                elem = page.locator(f'a:has-text("{text}"), button:has-text("{text}")').first
                if elem.is_visible(timeout=500):
                    return False
            except:
                continue

        # If we can't determine, assume NOT logged in
        return False

    except Exception as e:
        print(f"(err:{str(e)[:20]})", end=" ")
        return False

def signup_account(page, email, username, password):
    """Signup new account in already-open browser"""
    try:
        print(f"    → Signup: {email} / {username}")

        # Go to signup
        page.goto("https://www.tiktok.com/signup/phone-or-email/email", wait_until="domcontentloaded", timeout=45000)
        time.sleep(5)

        # Birthdate
        page.locator("[role='combobox'][aria-label*='Month']").click(); time.sleep(0.5)
        page.locator("[role='option']:has-text('January')").first.click(); time.sleep(0.5)
        page.locator("[role='combobox'][aria-label*='Day']").click(); time.sleep(0.5)
        page.locator("[role='option']:has-text('15')").first.click(); time.sleep(0.5)
        page.locator("[role='combobox'][aria-label*='Year']").click(); time.sleep(0.5)
        page.locator("[role='option']:has-text('2001')").first.click(); time.sleep(1)

        # Email & password
        page.locator("input[type='text']").first.fill(email); time.sleep(2)
        page.locator("input[type='password']").first.fill(password); time.sleep(3)

        # Send code (click twice)
        print("    → Sending code...")
        for _ in range(3):
            try:
                if page.locator("button:has-text('Send code')").first.is_visible(timeout=2000):
                    page.locator("button:has-text('Send code')").first.click(force=True); time.sleep(4)
                    if page.locator("text=/Resend code/i").is_visible(timeout=1000):
                        break
            except: pass

        # Get code
        code = fetch_code(email)
        if not code:
            print("    ✗ No code")
            return False, None
        print(f"    → Code: {code}")

        # Enter code
        page.locator("input[placeholder*='code' i]").first.fill(code); time.sleep(2)
        page.locator("button:has-text('Next'), button:has-text('Sign up')").first.click(); time.sleep(8)

        # Username
        try:
            if page.locator("input[placeholder='Username']").first.is_visible(timeout=5000):
                page.locator("input[placeholder='Username']").first.fill(username); time.sleep(3)
                page.locator("button:has-text('Sign up')").first.click(timeout=15000); time.sleep(10)
        except: pass

        # Get TikTok username
        time.sleep(5)
        tiktok_username = page.url.split('@')[1].split('/')[0] if '@' in page.url else username
        return True, tiktok_username

    except Exception as e:
        print(f"    ✗ Signup error: {str(e)[:80]}")
        return False, None

def login_account(page, username, password, email=None):
    """Login to existing account"""
    try:
        print(f"    → Login: {username}")

        # First close any interest modals
        try:
            skip_btns = ['button:has-text("Skip")', 'button:has-text("Continuer")', 'button:has-text("Continue")']
            for selector in skip_btns:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=500):
                        btn.click()
                        time.sleep(2)
                        break
                except:
                    continue
        except:
            pass

        # Click Log in button (multi-language)
        login_clicked = False

        # Method 1: Try the red sidebar button directly
        try:
            all_login_btns = page.locator('a, button').filter(has_text="Log in").all()
            for btn in all_login_btns:
                try:
                    if btn.is_visible(timeout=500):
                        btn.click(force=True)
                        login_clicked = True
                        time.sleep(3)
                        break
                except:
                    continue
        except Exception as e:
            print(f"    (login btn error: {str(e)[:30]})")

        # Method 2: Try clicking by text
        if not login_clicked:
            try:
                page.click('text="Log in"', timeout=3000, force=True)
                login_clicked = True
                time.sleep(3)
            except:
                pass

        # Method 3: Try other languages
        if not login_clicked:
            login_texts = ["Se connecter", "Anmelden", "Accedi", "Iniciar sesión", "Prisijungti"]
            for text in login_texts:
                try:
                    page.click(f'text="{text}"', timeout=2000, force=True)
                    login_clicked = True
                    time.sleep(3)
                    break
                except:
                    continue

        # Method 4: Fallback - try locator approach
        if not login_clicked:
            try:
                login_btn = page.locator('a:has-text("Log in"), button:has-text("Log in")').first
                if login_btn.is_visible(timeout=3000):
                    login_btn.click()
                    login_clicked = True
                    time.sleep(3)
            except:
                pass

        if not login_clicked:
            print("    ✗ No login button found")
            page.screenshot(path=f'debug_no_login_btn.png')
            return False

        # Wait for login modal
        time.sleep(3)

        # Click "Use phone or email" (multi-language options)
        phone_email_clicked = False
        phone_email_options = [
            'text="Use phone or email"',
            'text="Use phone / email / username"',
            'text="Utiliser le téléphone / e-mail / nom"',
            'text=/.*phone.*email.*/i',
            'text=/.*téléphone.*email.*/i',
        ]
        for selector in phone_email_options:
            try:
                page.click(selector, timeout=2000)
                phone_email_clicked = True
                time.sleep(3)
                break
            except:
                continue

        if not phone_email_clicked:
            # Maybe we're already on the form
            pass

        # Try to click "Email or username" tab if available
        try:
            email_tab = page.locator('a:has-text("Email or username"), div:has-text("Email or username")').first
            if email_tab.is_visible(timeout=1000):
                email_tab.click()
                time.sleep(2)
        except:
            pass

        # Enter username
        username_entered = False
        try:
            username_selectors = ['input[placeholder*="Email" i]', 'input[placeholder*="username" i]', 'input[type="text"]']
            for selector in username_selectors:
                try:
                    email_input = page.locator(selector).first
                    if email_input.is_visible(timeout=1000):
                        email_input.fill(username)
                        username_entered = True
                        time.sleep(1)
                        break
                except:
                    continue
        except:
            pass

        if not username_entered:
            print("    ✗ No username input")
            return False

        # Enter password
        password_entered = False
        try:
            pwd_input = page.locator('input[type="password"]').first
            if pwd_input.is_visible(timeout=2000):
                pwd_input.fill(password)
                password_entered = True
                time.sleep(1)
        except:
            pass

        if not password_entered:
            print("    ✗ No password input")
            return False

        # Submit login
        try:
            page.keyboard.press("Enter")
            time.sleep(5)
        except:
            pass

        # Check if verification code needed
        try:
            code_input = page.locator('input[placeholder*="code" i], input[placeholder*="verification" i]').first
            if code_input.is_visible(timeout=3000):
                print("    → Verification code needed")
                if email:
                    code = fetch_code(email)
                    if code:
                        print(f"    → Got code: {code}")
                        code_input.fill(code)
                        time.sleep(2)
                        page.keyboard.press("Enter")
                        time.sleep(5)
                    else:
                        print("    ✗ No code received")
                        return False
                else:
                    print("    ✗ No email for verification")
                    return False
        except:
            pass

        # Check if logged in
        time.sleep(3)
        if check_login(page):
            return True

        # Check URL
        if 'foryou' in page.url or 'following' in page.url or '@' in page.url:
            return True

        return False

    except Exception as e:
        print(f"    ✗ Login error: {str(e)[:50]}")
        return False

def save_cookies(page, profile_name):
    """Export browser cookies to JSON file as backup"""
    try:
        cookies = page.context.cookies()
        cookie_file = os.path.join(COOKIES_DIR, f'{profile_name}_cookies.json')
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        print(f"    → Saved {len(cookies)} cookies to {cookie_file}")
        return True
    except Exception as e:
        print(f"    ⚠ Cookie save error: {str(e)[:50]}")
        return False

def save_account(profile_name, serial, email, username, password, tiktok_username):
    """Save to CSV and mapping"""
    # Update CSV
    rows = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader: rows.append(row)

    # Find or add row
    profile_num = int(profile_name[2:])
    account_num = str(profile_num - 1)

    found = False
    for row in rows:
        if row.get('Account #') == account_num:
            row['Email'] = email
            row['Username'] = username
            row['Password'] = password
            row['Status'] = 'created'
            row['Proxy browser'] = str(serial)
            found = True
            break

    if not found:
        rows.append({'Account #': account_num, 'Proxy browser': str(serial), 'Email': email,
                    'Username': username, 'Password': password, 'Status': 'created'})

    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Update mapping
    with open(PROFILE_MAPPING_PATH, 'r') as f: mapping = json.load(f)
    mapping[profile_name] = tiktok_username
    with open(PROFILE_MAPPING_PATH, 'w') as f: json.dump(mapping, f, indent=2)

def process_browser(profile_id, profile_name, serial):
    """Check browser and signup if needed"""
    print(f"{profile_name}...", end=" ", flush=True)

    debug_url = open_browser(profile_id)
    if not debug_url:
        print("✗ Failed to open")
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(debug_url)
            context = browser.contexts[0]
            while len(context.pages) > 1: context.pages[-1].close()
            page = context.pages[0] if context.pages else context.new_page()

            # Check login
            page.goto("https://www.tiktok.com/", wait_until="networkidle", timeout=60000)
            time.sleep(15)  # Increased wait for session cookies

            # Close popups
            try:
                close_btn = page.locator('[aria-label="Close"]').first
                if close_btn.is_visible(timeout=1000): close_btn.click(); time.sleep(2)
            except: pass

            # Wait a bit more for page to stabilize after closing popup
            time.sleep(3)

            # Take screenshot for debugging
            page.screenshot(path=f'debug_{profile_name}_check.png')

            is_logged_in = check_login(page)

            print(f"(login_check={is_logged_in})", end=" ")

            if is_logged_in:
                # Get username
                current_url = page.url
                tiktok_username = None
                if '@' in current_url:
                    tiktok_username = current_url.split('@')[1].split('/')[0].split('?')[0]

                print(f"✓ Logged in{' as @' + tiktok_username if tiktok_username else ''}")

                # Save cookies as backup
                save_cookies(page, profile_name)

                # Update mapping if we have username
                if tiktok_username:
                    with open(PROFILE_MAPPING_PATH, 'r') as f: mapping = json.load(f)
                    if profile_name not in mapping:
                        mapping[profile_name] = tiktok_username
                        with open(PROFILE_MAPPING_PATH, 'w') as f: json.dump(mapping, f, indent=2)

                return True

            else:
                # Get browser number from profile name (tt27 -> 27)
                match = re.search(r'(\d+)', profile_name)
                browser_num = int(match.group(1)) if match else 0

                # Load existing credentials for this browser
                credentials = load_credentials_from_csv()
                creds = credentials.get(browser_num)

                if creds:
                    print(f"✗ Logged out - logging in with existing credentials...")
                    username = creds['username']
                    password = creds['password']
                    email = creds['email']

                    success = login_account(page, username, password, email)

                    if success:
                        save_cookies(page, profile_name)
                        print(f"    ✓ Login successful! @{username}")
                        return True
                    else:
                        print(f"    ✗ Login failed")
                        return False
                else:
                    print(f"✗ Logged out - no existing credentials, signing up...")

                    # Generate credentials and signup (fallback)
                    email, username, password = generate_creds()
                    success, tiktok_username = signup_account(page, email, username, password)

                    if success and tiktok_username:
                        save_account(profile_name, serial, email, username, password, tiktok_username)
                        save_cookies(page, profile_name)
                        print(f"    ✓ Signup complete! @{tiktok_username}")
                        return True
                    else:
                        print(f"    ✗ Signup failed")
                        return False

    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return False

    finally:
        close_browser(profile_id)

def main():
    import sys

    # Get start profile number from command line (default tt23 = browser 45)
    start_profile_num = int(sys.argv[1]) if len(sys.argv) > 1 else 23

    print("Fetching browsers...")
    response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
    profiles = response.json()['data']['list']
    profiles = sorted(profiles, key=lambda p: int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)))

    # Filter to start from specific profile number
    filtered_profiles = [p for p in profiles if int(re.search(r'(\d+)', p.get("name", "tt999")).group(1)) >= start_profile_num]

    print(f"Processing {len(filtered_profiles)} browsers (starting from tt{start_profile_num})\n")
    print("="*60)

    success = 0
    failed = 0

    for i, profile in enumerate(filtered_profiles, 1):
        print(f"[{i}/{len(filtered_profiles)}] ", end="")

        if process_browser(profile['user_id'], profile['name'], profile.get('serial_number', '?')):
            success += 1
        else:
            failed += 1

        time.sleep(3)  # Wait between browsers

    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total: {len(filtered_profiles)}")
    print(f"✓ Success: {success}")
    print(f"✗ Failed: {failed}")
    print("="*60)

if __name__ == "__main__":
    main()
