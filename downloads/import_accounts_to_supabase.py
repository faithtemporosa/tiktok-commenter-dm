#!/usr/bin/env python3
"""Import TikTok accounts from CSV to Supabase"""

import csv
import os
from supabase import create_client

SUPABASE_URL = "https://qwnhywiygyvlhjxxrbkk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bmh5d2l5Z3l2bGhqeHhyYmtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNTkxNzgsImV4cCI6MjA4NjgzNTE3OH0.X7RdTeOPrJCkf8c1oOUGHv1tntDigluOnj7bPw50tKE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_accounts():
    # Import from both CSV files
    csv_files = [
        ('tiktok_accounts.csv', {'browser': 'Proxy browser', 'email': 'Email', 'password': 'Password', 'username': 'Username', 'status': 'Status'}),
        ('new_tiktok_accounts.csv', {'browser': 'browser', 'email': 'email', 'password': 'password', 'username': 'username', 'birthdate': 'birthdate'}),
    ]

    imported = 0
    skipped = 0

    for csv_file, field_map in csv_files:
        csv_path = os.path.join(os.path.dirname(__file__), csv_file)
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            continue

        print(f"\n--- Importing from {csv_file} ---")
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Use browser number if available, otherwise use Account # + 1 for tiktok_accounts.csv
                    # (Account #0 = tt1 = Browser 1, Account #6 = tt7 = Browser 7, etc.)
                    browser_val = row.get(field_map['browser'], '').strip()
                    if not browser_val and 'Account #' in row:
                        account_num = row['Account #'].strip()
                        if account_num:
                            browser_val = str(int(account_num) + 1)  # Account # + 1 = browser number
                    if not browser_val:
                        continue  # Skip rows without any browser identifier
                    browser_num = int(browser_val)
                    email = row[field_map['email']]
                    password = row[field_map['password']]
                    username = row.get(field_map.get('username', ''), '') or ''
                    birthdate = row.get(field_map.get('birthdate', ''), '') or ''
                    status_raw = row.get(field_map.get('status', ''), 'active') or 'active'
                    status = 'active' if status_raw in ['created', 'active'] else status_raw

                    supabase.table('tiktok_accounts').upsert({
                        'browser_num': browser_num,
                        'email': email,
                        'password': password,
                        'username': username,
                        'birthdate': birthdate,
                        'status': status
                    }, on_conflict='browser_num').execute()
                    imported += 1
                    print(f"Imported: Browser {browser_num} - {email}")
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        skipped += 1
                        print(f"Skipped (duplicate): {row}")
                    else:
                        print(f"Error importing: {e}")

    print(f"\nDone! Imported: {imported}, Skipped: {skipped}")

if __name__ == "__main__":
    import_accounts()
