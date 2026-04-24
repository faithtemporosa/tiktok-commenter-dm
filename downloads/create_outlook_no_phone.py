#!/usr/bin/env python3
"""
Create Outlook Accounts Without Phone Verification
===================================================
Automate Outlook account creation using Multilogin profiles.
Outlook often doesn't require phone verification.

USAGE:
    python create_outlook_no_phone.py
"""

from multilogin_api import MultiloginClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import string
import json


def generate_random_name():
    """Generate realistic random name"""
    first_names = ["John", "Sarah", "Mike", "Emily", "David", "Jessica",
                   "Chris", "Ashley", "Matt", "Amanda", "James", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Davis", "Miller",
                  "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson"]

    first = random.choice(first_names)
    last = random.choice(last_names)
    number = random.randint(100, 9999)

    return first, last, f"{first.lower()}.{last.lower()}{number}"


def create_outlook_account(driver, save_file="outlook_accounts.json"):
    """
    Create an Outlook account without phone verification

    Args:
        driver: Selenium WebDriver instance
        save_file: JSON file to save account credentials

    Returns:
        dict: Account info if successful, None otherwise
    """

    try:
        # Navigate to Outlook signup
        print("Navigating to Outlook signup...")
        driver.get("https://signup.live.com/")
        time.sleep(3)

        # Generate account details
        first_name, last_name, username = generate_random_name()
        email = f"{username}@outlook.com"
        password = ''.join(random.choices(
            string.ascii_letters + string.digits + "!@#$%", k=16
        ))

        print(f"Creating account: {email}")

        # Enter email
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "liveSwitch"))
        )
        email_input.click()
        time.sleep(1)

        username_input = driver.find_element(By.ID, "MemberName")
        username_input.clear()
        username_input.send_keys(username)
        time.sleep(1)

        # Click Next
        next_btn = driver.find_element(By.ID, "iSignupAction")
        next_btn.click()
        time.sleep(3)

        # Enter password
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "PasswordInput"))
        )
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(1)

        # Click Next
        next_btn = driver.find_element(By.ID, "iSignupAction")
        next_btn.click()
        time.sleep(3)

        # Enter first and last name
        first_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "FirstName"))
        )
        first_name_input.clear()
        first_name_input.send_keys(first_name)
        time.sleep(0.5)

        last_name_input = driver.find_element(By.ID, "LastName")
        last_name_input.clear()
        last_name_input.send_keys(last_name)
        time.sleep(1)

        # Click Next
        next_btn = driver.find_element(By.ID, "iSignupAction")
        next_btn.click()
        time.sleep(3)

        # Birth date
        birth_year = random.randint(1985, 2000)
        birth_month = str(random.randint(1, 12))
        birth_day = str(random.randint(1, 28))

        # Select birth month
        month_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "BirthMonth"))
        )
        month_select.send_keys(birth_month)
        time.sleep(0.5)

        # Enter birth day
        day_input = driver.find_element(By.ID, "BirthDay")
        day_input.clear()
        day_input.send_keys(birth_day)
        time.sleep(0.5)

        # Enter birth year
        year_input = driver.find_element(By.ID, "BirthYear")
        year_input.clear()
        year_input.send_keys(str(birth_year))
        time.sleep(1)

        # Click Next
        next_btn = driver.find_element(By.ID, "iSignupAction")
        next_btn.click()
        time.sleep(5)

        # Check if phone verification is required
        current_url = driver.current_url
        page_source = driver.page_source.lower()

        if "phone" in page_source or "verify" in current_url:
            print("⚠️  Phone verification required - trying to skip...")

            # Try to find "Use email instead" option
            try:
                email_option = driver.find_element(
                    By.XPATH,
                    "//a[contains(text(), 'email') or contains(text(), 'Email')]"
                )
                email_option.click()
                time.sleep(2)
                print("✓ Switched to email verification")
            except:
                print("❌ Cannot skip phone verification")
                return None

        # Handle CAPTCHA if present
        if "captcha" in page_source or "puzzle" in page_source:
            print("⚠️  CAPTCHA detected - you may need to solve it manually")
            print("    Waiting 30 seconds for manual solve...")
            time.sleep(30)

        # Check if account was created successfully
        time.sleep(5)
        if "outlook.live.com" in driver.current_url or "account.microsoft.com" in driver.current_url:
            print(f"✅ Account created successfully: {email}")

            account_info = {
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "birth_date": f"{birth_year}-{birth_month}-{birth_day}",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save to file
            try:
                try:
                    with open(save_file, 'r') as f:
                        accounts = json.load(f)
                except FileNotFoundError:
                    accounts = []

                accounts.append(account_info)

                with open(save_file, 'w') as f:
                    json.dump(accounts, f, indent=2)

                print(f"✓ Saved to {save_file}")
            except Exception as e:
                print(f"⚠️  Could not save to file: {e}")

            return account_info
        else:
            print(f"❌ Account creation may have failed")
            print(f"   Current URL: {driver.current_url}")
            return None

    except Exception as e:
        print(f"❌ Error creating account: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_multiple_accounts(num_accounts=5):
    """
    Create multiple Outlook accounts using Multilogin

    Args:
        num_accounts: Number of accounts to create
    """

    # Load Multilogin config
    import json
    with open('multilogin_config.json', 'r') as f:
        config = json.load(f)

    client = MultiloginClient(
        email=config.get('email', ''),
        password=config.get('password', ''),
        automation_token=config.get('automation_token', '')
    )

    if not client.authenticate():
        print("❌ Failed to authenticate with Multilogin")
        return

    # Get profiles
    profiles = client.get_profiles(limit=100)

    if len(profiles) < num_accounts:
        print(f"⚠️  Only {len(profiles)} profiles available, need {num_accounts}")
        num_accounts = len(profiles)

    print(f"\n{'='*60}")
    print(f"Creating {num_accounts} Outlook Accounts")
    print(f"{'='*60}\n")

    successful = 0
    failed = 0

    for i in range(num_accounts):
        profile = profiles[i]
        profile_id = profile.get('id')
        profile_name = profile.get('name', profile_id)
        folder_id = config.get('folder_id', '')

        print(f"\n[{i+1}/{num_accounts}] Using profile: {profile_name}")

        # Start profile
        driver = client.start_profile(
            folder_id=folder_id,
            profile_id=profile_id
        )

        if not driver:
            print(f"❌ Failed to start profile")
            failed += 1
            continue

        # Create account
        account = create_outlook_account(driver)

        # Stop profile
        client.stop_profile(profile_id=profile_id)

        if account:
            successful += 1
        else:
            failed += 1

        # Wait between accounts
        if i < num_accounts - 1:
            wait_time = random.randint(10, 30)
            print(f"\nWaiting {wait_time} seconds before next account...")
            time.sleep(wait_time)

    print(f"\n{'='*60}")
    print(f"✅ Successfully created: {successful}/{num_accounts}")
    print(f"❌ Failed: {failed}/{num_accounts}")
    print(f"{'='*60}\n")
    print("Accounts saved to: outlook_accounts.json")


if __name__ == "__main__":
    import sys

    # Number of accounts to create
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    print(f"""
╔══════════════════════════════════════════════════════════╗
║     Outlook Account Creator (No Phone Required)          ║
╚══════════════════════════════════════════════════════════╝

Creating {num} Outlook accounts...

NOTE:
- Success rate: ~60-80% (some may still require phone)
- Create 3-5 per day for best results
- Use different Multilogin profiles
- CAPTCHA may appear - solve manually if needed

Press Ctrl+C to cancel
    """)

    time.sleep(3)

    try:
        create_multiple_accounts(num_accounts=num)
    except KeyboardInterrupt:
        print("\n\n⏹  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
