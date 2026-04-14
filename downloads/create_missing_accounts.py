#!/usr/bin/env python3
"""
Create missing TikTok accounts in Supabase
Identifies accounts that exist in profile mapping but not in Supabase
"""
import json
from supabase import create_client

SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_missing_accounts():
    """Create accounts for browsers that don't have them in Supabase"""
    try:
        # Load profile mapping (browser_id -> username)
        with open('tiktok_profile_mapping.json', 'r') as f:
            profile_mapping = json.load(f)

        print(f"Found {len(profile_mapping)} browsers in mapping")

        # Get existing accounts from Supabase
        result = supabase.table('tiktok_accounts').select('browser_num').execute()
        existing_browser_nums = {acc['browser_num'] for acc in result.data}

        print(f"Found {len(existing_browser_nums)} existing accounts in Supabase")

        # Find missing browsers
        all_browser_nums = {int(bid.replace('tt', '')) for bid in profile_mapping.keys()}
        missing_browser_nums = all_browser_nums - existing_browser_nums

        print(f"\nMissing {len(missing_browser_nums)} accounts")

        if not missing_browser_nums:
            print("✓ All accounts already exist!")
            return

        # Create missing account records
        missing_accounts = []
        for browser_id, username in profile_mapping.items():
            browser_num = int(browser_id.replace('tt', ''))

            # Only create if missing
            if browser_num in missing_browser_nums:
                account = {
                    'browser_num': browser_num,
                    'username': username,
                    'email': f'tt{browser_num}@temp.com',  # Use browser_num for unique email
                    'password': 'password',
                    'status': 'active'
                }
                missing_accounts.append(account)

        print(f"Creating {len(missing_accounts)} missing accounts...")

        # Import in batches of 100
        batch_size = 100
        total_created = 0

        for i in range(0, len(missing_accounts), batch_size):
            batch = missing_accounts[i:i+batch_size]
            try:
                supabase.table('tiktok_accounts').upsert(batch, on_conflict='browser_num').execute()
                total_created += len(batch)
                print(f"  Created {total_created}/{len(missing_accounts)} accounts")
            except Exception as e:
                print(f"  Error in batch {i}-{i+batch_size}: {e}")

        print(f"\n✓ Successfully created {total_created} missing accounts!")

        # Verify final count
        result = supabase.table('tiktok_accounts').select('browser_num').execute()
        final_count = len(result.data)
        print(f"✓ Total accounts in Supabase: {final_count}/{len(profile_mapping)}")

    except Exception as e:
        print(f"Error creating missing accounts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("  Creating Missing TikTok Accounts")
    print("=" * 60)
    create_missing_accounts()
    print("\n" + "=" * 60)
    print("  Complete!")
    print("=" * 60)
