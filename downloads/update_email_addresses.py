#!/usr/bin/env python3
"""
Update email addresses for accounts with 'Not Created' status
Generate fresh email addresses to avoid TikTok rate limiting
"""

import csv
import random

CSV_FILE = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_accounts.csv"

# Word lists for generating unique email addresses
adjectives = [
    'swift', 'bright', 'cosmic', 'lunar', 'solar', 'crystal', 'ocean',
    'forest', 'mountain', 'river', 'thunder', 'lightning', 'storm', 'cloud',
    'wind', 'fire', 'earth', 'water', 'shadow', 'light', 'dark', 'silent',
    'quiet', 'loud', 'fast', 'slow', 'digital', 'cyber', 'tech', 'smart',
    'clever', 'wise', 'bold', 'brave', 'calm', 'wild', 'free', 'pure',
    'royal', 'noble', 'elite', 'prime', 'alpha', 'omega', 'delta', 'gamma',
    'neon', 'laser', 'plasma', 'quantum', 'atomic', 'stellar', 'galactic'
]

nouns = [
    'phoenix', 'dragon', 'falcon', 'eagle', 'hawk', 'wolf', 'tiger', 'lion',
    'bear', 'fox', 'deer', 'owl', 'raven', 'sparrow', 'swan', 'dove',
    'star', 'moon', 'sun', 'comet', 'planet', 'orbit', 'galaxy', 'nebula',
    'wave', 'tide', 'stream', 'rain', 'snow', 'frost', 'dew', 'mist',
    'flame', 'blaze', 'ember', 'spark', 'flash', 'bolt', 'ray', 'beam',
    'pixel', 'byte', 'code', 'data', 'link', 'node', 'core', 'hub',
    'echo', 'pulse', 'rhythm', 'beat', 'tone', 'sound', 'voice', 'call'
]

def generate_unique_email(used_emails):
    """Generate a unique email address"""
    while True:
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        num = random.randint(100, 999)
        email = f"{adj}{noun}{num}@automateyourbizz.xyz"

        if email not in used_emails:
            return email

def update_email_addresses():
    """Update email addresses for 'Not Created' accounts"""
    rows = []
    used_emails = set()
    updated_count = 0

    # Read CSV
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get('Status', '').strip()
            current_email = row.get('Email', '').strip()

            # Track existing emails
            if current_email:
                used_emails.add(current_email)

            rows.append(row)

    # Update emails for 'Not Created' accounts
    for row in rows:
        status = row.get('Status', '').strip()

        if status == 'Not Created':
            old_email = row.get('Email', '')
            new_email = generate_unique_email(used_emails)
            used_emails.add(new_email)

            row['Email'] = new_email
            updated_count += 1

            print(f"Account #{row['Account #']}: {old_email} → {new_email}")

    # Write back to CSV
    with open(CSV_FILE, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"\n✓ Updated {updated_count} email addresses")
    print("All 'Not Created' accounts now have fresh email addresses")

if __name__ == "__main__":
    print("=" * 60)
    print("Updating Email Addresses for Not Created Accounts")
    print("=" * 60)
    print()
    update_email_addresses()
