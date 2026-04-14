#!/usr/bin/env python3
"""Migrate tiktok_accounts from CSV to new Supabase"""

import csv
from supabase import create_client

# New Supabase
NEW_URL = 'https://gisbdbbsvwjcjwovwklg.supabase.co'
NEW_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI'

print("=" * 60)
print("SUPABASE MIGRATION - TikTok Accounts")
print("=" * 60)

print("\nStep 1: Reading accounts from CSV...")
accounts = []
csv_path = '/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_accounts.csv'

with open(csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Skip rows with non-numeric Account # (like skip_803, used_802)
        account_num = row.get('Account #', '')
        if not account_num.isdigit():
            continue

        proxy_browser = row.get('Proxy browser', '')
        if not proxy_browser or not proxy_browser.isdigit():
            continue

        accounts.append({
            'browser_num': int(proxy_browser),
            'username': row.get('Username', ''),
            'password': row.get('Password', ''),
            'email': row.get('Email', ''),
            'status': row.get('Status', 'active'),
        })

print(f"  Found {len(accounts)} valid accounts")

print("\n" + "=" * 60)
print("Step 2: CREATE TABLE in Supabase Dashboard")
print("=" * 60)
print("""
Go to: https://supabase.com/dashboard/project/gisbdbbsvwjcjwovwklg/sql

Run this SQL:

CREATE TABLE IF NOT EXISTS tiktok_accounts (
    id SERIAL PRIMARY KEY,
    browser_num INTEGER UNIQUE,
    username TEXT,
    password TEXT,
    email TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE tiktok_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations" ON tiktok_accounts
    FOR ALL USING (true) WITH CHECK (true);
""")

print("\nPress Enter after creating the table...")
input()

print("\nStep 3: Inserting data...")
new_supabase = create_client(NEW_URL, NEW_KEY)

success = 0
failed = 0

for account in accounts:
    try:
        new_supabase.table('tiktok_accounts').insert(account).execute()
        success += 1
        if success % 50 == 0:
            print(f"  Inserted {success} accounts...")
    except Exception as e:
        failed += 1
        if failed <= 5:  # Only show first 5 errors
            print(f"  Failed browser_num={account.get('browser_num')}: {str(e)[:80]}")

print(f"\n{'=' * 60}")
print(f"DONE! Success: {success}, Failed: {failed}")
print(f"{'=' * 60}")
