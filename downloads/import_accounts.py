#!/usr/bin/env python3
"""
Import TikTok accounts/profiles to Supabase
"""
import json
from supabase import create_client

SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_profiles():
    """Import profiles from profile mapping and credentials"""
    try:
        # Load profile mapping (browser_id -> username)
        with open('tiktok_profile_mapping.json', 'r') as f:
            profile_mapping = json.load(f)

        # Try to load credentials if available
        credentials_dict = {}
        try:
            with open('tiktok_credentials.json', 'r') as f:
                credentials = json.load(f)
                # Convert list to dict if needed
                if isinstance(credentials, list):
                    for c in credentials:
                        if 'browser' in c:
                            credentials_dict[f"tt{c['browser']}"] = c
                        elif 'browser_id' in c:
                            credentials_dict[c['browser_id']] = c
                else:
                    credentials_dict = credentials
        except FileNotFoundError:
            pass

        print(f"Found {len(profile_mapping)} profiles in mapping")

        # Create account records
        accounts = []
        for browser_id, username in profile_mapping.items():
            # Extract browser number from ID (e.g., "tt7" -> 7)
            browser_num = int(browser_id.replace('tt', ''))

            # Get credentials if available
            cred = credentials_dict.get(browser_id, {})

            account = {
                'browser_num': browser_num,
                'username': username,
                'email': cred.get('email', f'{username}@temp.com'),
                'password': cred.get('password', 'password'),
                'status': 'active'
            }
            accounts.append(account)

        # Import in batches
        batch_size = 100
        total_imported = 0

        for i in range(0, len(accounts), batch_size):
            batch = accounts[i:i+batch_size]
            try:
                supabase.table('tiktok_accounts').upsert(batch, on_conflict='browser_num').execute()
                total_imported += len(batch)
                print(f"  Imported {total_imported}/{len(accounts)} accounts")
            except Exception as e:
                print(f"  Error in batch {i}-{i+batch_size}: {e}")

        print(f"✓ Successfully imported {total_imported} accounts!")

    except Exception as e:
        print(f"Error importing profiles: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("  Importing TikTok Accounts to Supabase")
    print("=" * 60)
    import_profiles()
    print("\n" + "=" * 60)
    print("  Import Complete!")
    print("=" * 60)
