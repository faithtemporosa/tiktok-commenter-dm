#!/usr/bin/env python3
"""Test YouTube signup with one browser"""

import requests
import time
from playwright.sync_api import sync_playwright
from supabase import create_client

ADSPOWER_API = "http://local.adspower.net:50325"
supabase_url = 'https://qwnhywiygyvlhjxxrbkk.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bmh5d2l5Z3l2bGhqeHhyYmtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNTkxNzgsImV4cCI6MjA4NjgzNTE3OH0.X7RdTeOPrJCkf8c1oOUGHv1tntDigluOnj7bPw50tKE'

# Get first profile
print("Fetching profiles...")
response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=10", timeout=10)
data = response.json()
profiles = data.get("data", {}).get("list", [])

if not profiles:
    print("No profiles found!")
    exit(1)

# Use first profile (tt1)
import re
def sort_key(p):
    name = p.get("name", "")
    match = re.search(r'(\d+)', name)
    return int(match.group(1)) if match else 999

profiles = sorted(profiles, key=sort_key)
profile = profiles[0]

profile_id = profile.get("user_id")
profile_name = profile.get("name")
serial_num = profile.get("serial_number")

print(f"\nUsing profile: {profile_name} (Serial: {serial_num})")

# Get credentials - use browser 7 which has credentials
supabase = create_client(supabase_url, supabase_key)
result = supabase.table('tiktok_accounts').select('*').eq('browser_num', 7).execute()

if not result.data:
    print("No credentials found for browser 7!")
    # Try to find first available credentials
    result = supabase.table('tiktok_accounts').select('*').limit(1).execute()
    if not result.data:
        print("No credentials found in database!")
        exit(1)
    print(f"Using first available account instead (browser {result.data[0].get('browser_num')})")

creds = result.data[0]
email = creds.get("email")
password = creds.get("password")
birthdate = creds.get("birthdate", "January 1, 2001")
username = creds.get("username", "user")

print(f"Email: {email}")
print(f"Username: {username}")
print(f"Birthdate: {birthdate}")

# Open browser
print("\nOpening browser...")
response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=30)
debug_url = response.json()["data"]["ws"]["puppeteer"]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(debug_url)
    context = browser.contexts[0]

    # Open new tab for YouTube
    print("Opening YouTube in new tab...")
    page = context.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)

    print("\n" + "="*60)
    print("Browser is open with YouTube")
    print("=" * 60)
    print("\nManual steps:")
    print("1. Click 'Sign in' in top right")
    print("2. Click 'Create account'")
    print("3. Fill in the form with these details:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Birthdate: {birthdate}")
    print(f"   Username: {username}")
    print("\n4. Complete any verification (phone, captcha, etc.)")
    print("\nPress Enter when done to close...")
    input()

print("Done!")
