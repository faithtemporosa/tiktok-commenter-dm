#!/usr/bin/env python3
"""
Reset accounts that were marked as 'created' but aren't actually logged in
"""

import csv

CSV_FILE = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/tiktok_accounts.csv"

# Accounts #6-21 were marked as created but aren't logged in
# Browser serials: 802, 801, 800, 798, 797, 796, 795, 794, 793, 792, 791, 790, 789, 788
FAILED_BROWSERS = ['802', '801', '800', '798', '797', '796', '795', '794', '793', '792', '791', '790', '789', '788']

def reset_accounts():
    """Reset failed accounts to 'Not Created'"""
    rows = []

    # Read CSV
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            browser = str(row.get('Proxy browser', '')).strip()

            # If this browser was in the failed list, reset it
            if browser in FAILED_BROWSERS:
                print(f"Resetting Account #{row['Account #']}: {row.get('Username', 'N/A')} (Browser {browser})")
                row['Proxy browser'] = ''
                row['Status'] = 'Not Created'

            rows.append(row)

    # Write back
    with open(CSV_FILE, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"\n✓ Reset {len(FAILED_BROWSERS)} accounts to 'Not Created'")
    print("These accounts can now be created properly with the fixed script.")

if __name__ == "__main__":
    print("=" * 60)
    print("Resetting Failed Account Creations")
    print("=" * 60)
    reset_accounts()
