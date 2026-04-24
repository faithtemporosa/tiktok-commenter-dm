#!/usr/bin/env python3
"""
TikTok Auto Signup - Android Emulator Version
==============================================
Creates new TikTok accounts on Android emulator using Appium.
Uses temp email (mail.tm) for verification.

SETUP:
    pip install appium-python-client requests

RUN ON SERVER:
    python tiktok_signup_emulator.py --emulator emulator-5556

"""

import sys
import requests
import time
import json
import random
import string
import re
from datetime import datetime, timedelta

try:
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_APPIUM = True
except ImportError:
    HAS_APPIUM = False
    print("ERROR: Install Appium: pip install appium-python-client")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================
APPIUM_SERVER = "http://localhost:4723"
TIKTOK_PACKAGE = "com.ss.android.ugc.trill"
TIKTOK_ACTIVITY = ".MainActivity"

# =============================================================================
# TEMP EMAIL (mail.tm)
# =============================================================================
MAILTM_API = "https://api.mail.tm"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def create_temp_email():
    """Create a temporary email using mail.tm API"""
    try:
        # Get available domains
        r = requests.get(f"{MAILTM_API}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        if not domains:
            return None, None
        domain = domains[0]["domain"]

        # Generate random address
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"{username}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        # Create account
        r = requests.post(f"{MAILTM_API}/accounts", json={"address": email, "password": password}, timeout=10)
        if r.status_code in (200, 201):
            log(f"  ✓ Temp email created: {email}")
            return email, password
        else:
            log(f"  ✗ Failed to create email: {r.text[:100]}")
            return None, None
    except Exception as e:
        log(f"  ✗ Email creation error: {e}")
        return None, None

def get_mailtm_token(email, password):
    """Get auth token for mail.tm"""
    try:
        r = requests.post(f"{MAILTM_API}/token", json={"address": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def wait_for_verification_code(email, password, timeout=120):
    """Poll mail.tm inbox for TikTok verification code"""
    log(f"  ⏳ Waiting for verification email (max {timeout}s)...")
    token = get_mailtm_token(email, password)
    if not token:
        log("  ✗ Could not get mail.tm token")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{MAILTM_API}/messages", headers=headers, timeout=10)
            messages = r.json().get("hydra:member", [])
            for msg in messages:
                subject = msg.get("subject", "").lower()
                if "tiktok" in subject or "verify" in subject or "code" in subject:
                    # Get full message
                    msg_r = requests.get(f"{MAILTM_API}/messages/{msg['id']}", headers=headers, timeout=10)
                    body = msg_r.json().get("text", "") or msg_r.json().get("html", "")
                    # Extract 6-digit code
                    codes = re.findall(r'\b\d{6}\b', body)
                    if codes:
                        log(f"  ✓ Got verification code: {codes[0]}")
                        return codes[0]
        except Exception as e:
            pass
        time.sleep(5)

    log("  ✗ Verification code timeout")
    return None

# =============================================================================
# HELPERS
# =============================================================================
def generate_password():
    """Generate a strong password"""
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=14))

def generate_birthday():
    """Generate a random birthday for an 18-25 year old"""
    today = datetime.now()
    age_days = random.randint(18 * 365, 25 * 365)
    bday = today - timedelta(days=age_days)
    return bday.strftime("%Y-%m-%d"), bday.month, bday.day, bday.year

def generate_username():
    """Generate a TikTok username"""
    prefix = random.choice(['user', 'tiktok', 'tt', 'cool', 'epic'])
    suffix = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{suffix}"

# =============================================================================
# APPIUM HELPERS
# =============================================================================
def take_screenshot(driver, name):
    """Take screenshot for debugging"""
    try:
        filename = f"/tmp/tiktok_signup_{name}_{int(time.time())}.png"
        driver.save_screenshot(filename)
        log(f"  📸 Screenshot saved: {filename}")
        return filename
    except:
        return None

def safe_click(driver, by, value, timeout=10):
    """Safely click an element"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        element.click()
        return True
    except Exception as e:
        log(f"  ⚠ Could not click {value}: {e}")
        return False

def safe_send_keys(driver, by, value, text, timeout=10):
    """Safely send keys to an element"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        element.clear()
        element.send_keys(text)
        return True
    except Exception as e:
        log(f"  ⚠ Could not send keys to {value}: {e}")
        return False

# =============================================================================
# TIKTOK SIGNUP AUTOMATION
# =============================================================================
def run_tiktok_signup(emulator_id):
    """Run TikTok signup flow on Android emulator"""
    log(f"\n{'='*60}")
    log(f"  Starting TikTok signup on {emulator_id}")
    log(f"{'='*60}")

    # Create temp email
    email, email_pass = create_temp_email()
    if not email:
        log(f"  ✗ Could not create temp email")
        return False

    tiktok_password = generate_password()
    birthdate_str, bday_month, bday_day, bday_year = generate_birthday()
    username = generate_username()

    log(f"  Account Info:")
    log(f"    Email: {email}")
    log(f"    Password: {tiktok_password}")
    log(f"    Birthday: {bday_month}/{bday_day}/{bday_year}")
    log(f"    Username: {username}")

    # Configure Appium
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = emulator_id
    options.udid = emulator_id
    options.app_package = TIKTOK_PACKAGE
    options.app_activity = TIKTOK_ACTIVITY
    options.no_reset = True
    options.auto_grant_permissions = True

    driver = None
    success = False

    try:
        log(f"  → Connecting to Appium server...")
        driver = webdriver.Remote(APPIUM_SERVER, options=options)
        log(f"  ✓ Connected to TikTok app")
        time.sleep(5)

        take_screenshot(driver, "01_app_opened")

        # Look for "Sign up" or "Me" tab to access profile/signup
        log(f"  → Looking for signup option...")

        # Try to find and click Profile/Me tab first
        try:
            me_tab = driver.find_element(AppiumBy.XPATH, "//*[@text='Me' or @content-desc='Me']")
            me_tab.click()
            time.sleep(2)
            take_screenshot(driver, "02_me_tab")
        except:
            log(f"  ⚠ Could not find Me tab, continuing...")

        # Look for Sign up button
        try:
            signup_btn = driver.find_element(AppiumBy.XPATH, "//*[@text='Sign up' or contains(@text, 'Sign up')]")
            signup_btn.click()
            time.sleep(2)
            take_screenshot(driver, "03_signup_clicked")
        except:
            log(f"  ⚠ Could not find Sign up button")

        # Click "Use phone or email"
        log(f"  → Selecting email signup method...")
        try:
            phone_email = driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'phone or email') or contains(@text, 'Phone or email')]")
            phone_email.click()
            time.sleep(2)
            take_screenshot(driver, "04_phone_email")
        except:
            log(f"  ⚠ Could not find phone/email option")

        # Click "Sign up with email"
        try:
            email_btn = driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'email') and contains(@text, 'Sign up')]")
            email_btn.click()
            time.sleep(2)
            take_screenshot(driver, "05_email_method")
        except:
            log(f"  ⚠ Could not find email signup button")

        # Enter birthday
        log(f"  → Entering birthday...")
        try:
            # Month
            month_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText[contains(@text, 'Month') or @content-desc='Month']")
            month_field.click()
            month_field.send_keys(str(bday_month))
            time.sleep(0.5)

            # Day
            day_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText[contains(@text, 'Day') or @content-desc='Day']")
            day_field.click()
            day_field.send_keys(str(bday_day))
            time.sleep(0.5)

            # Year
            year_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText[contains(@text, 'Year') or @content-desc='Year']")
            year_field.click()
            year_field.send_keys(str(bday_year))
            time.sleep(0.5)

            take_screenshot(driver, "06_birthday_entered")

            # Click Next
            next_btn = driver.find_element(AppiumBy.XPATH, "//*[@text='Next' or @content-desc='Next']")
            next_btn.click()
            time.sleep(2)
        except Exception as e:
            log(f"  ⚠ Birthday entry failed: {e}")

        # Enter email
        log(f"  → Entering email: {email}")
        try:
            email_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText[contains(@text, 'Email') or @content-desc='Email']")
            email_field.click()
            email_field.send_keys(email)
            time.sleep(1)
            take_screenshot(driver, "07_email_entered")
        except Exception as e:
            log(f"  ✗ Could not enter email: {e}")
            take_screenshot(driver, "07_email_failed")

        # Click "Send code" or "Next"
        try:
            send_code_btn = driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Send code') or @text='Next']")
            send_code_btn.click()
            time.sleep(2)
            take_screenshot(driver, "08_code_sent")
        except:
            log(f"  ⚠ Could not click Send code")

        # Wait for verification code
        code = wait_for_verification_code(email, email_pass, timeout=120)
        if not code:
            log(f"  ✗ No verification code received")
            take_screenshot(driver, "09_no_code")
            return False

        # Enter verification code
        log(f"  → Entering verification code: {code}")
        try:
            # Find code input fields (usually 6 separate fields)
            for i, digit in enumerate(code):
                code_field = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")[i]
                code_field.send_keys(digit)
                time.sleep(0.2)
            time.sleep(2)
            take_screenshot(driver, "10_code_entered")
        except Exception as e:
            log(f"  ✗ Could not enter code: {e}")
            # Try as single field
            try:
                code_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText")
                code_field.send_keys(code)
                time.sleep(1)
            except:
                pass

        # Enter password
        log(f"  → Setting password...")
        try:
            pw_field = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText[@password='true']")
            pw_field.click()
            pw_field.send_keys(tiktok_password)
            time.sleep(1)
            take_screenshot(driver, "11_password_entered")
        except Exception as e:
            log(f"  ⚠ Could not enter password: {e}")

        # Click Sign up / Create account
        try:
            signup_final = driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'Sign up') or contains(@text, 'Create')]")
            signup_final.click()
            time.sleep(5)
            take_screenshot(driver, "12_signup_submitted")
        except:
            log(f"  ⚠ Could not click final signup button")

        # Check if successful
        time.sleep(3)
        take_screenshot(driver, "13_final_result")

        # Try to detect success (e.g., For You page visible)
        try:
            foryou = driver.find_element(AppiumBy.XPATH, "//*[contains(@text, 'For You') or contains(@text, 'Following')]")
            if foryou:
                log(f"  ✓ Signup successful!")
                success = True
        except:
            log(f"  ⚠ Could not confirm signup success")

        if success:
            # Save account info
            account_data = {
                "email": email,
                "password": tiktok_password,
                "username": username,
                "birthdate": birthdate_str,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "emulator": emulator_id
            }

            # Save to file
            with open("/tmp/tiktok_account_created.json", "w") as f:
                json.dump(account_data, f, indent=2)

            log(f"\n  ✓✓✓ ACCOUNT CREATED SUCCESSFULLY ✓✓✓")
            log(f"  Email: {email}")
            log(f"  Password: {tiktok_password}")
            log(f"  Saved to: /tmp/tiktok_account_created.json")

    except Exception as e:
        log(f"  ✗ Error during signup: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            take_screenshot(driver, "error")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return success

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='TikTok Signup - Android Emulator')
    parser.add_argument('--emulator', default='emulator-5556', help='Emulator ID (e.g., emulator-5556)')
    parser.add_argument('--appium', default='http://localhost:4723', help='Appium server URL')
    args = parser.parse_args()

    APPIUM_SERVER = args.appium

    print("=" * 60)
    print("  TikTok Auto Signup - Android Emulator")
    print("=" * 60)
    print(f"  Emulator: {args.emulator}")
    print(f"  Appium: {APPIUM_SERVER}")
    print("=" * 60)

    success = run_tiktok_signup(args.emulator)

    if success:
        print("\n✓ Signup completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Signup failed")
        sys.exit(1)
