#!/usr/bin/env python3
"""
Import existing JSON data to new Supabase database
"""
import json
from supabase import create_client

SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_comments():
    """Import comment history"""
    try:
        with open('tiktok_comments_history.json', 'r') as f:
            file_data = json.load(f)

        # Extract the report array
        data = file_data.get('report', []) if isinstance(file_data, dict) else file_data

        if not data:
            print("No comments to import")
            return

        print(f"Importing {len(data)} comments...")

        # Import in batches of 100
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            try:
                supabase.table('comment_reports').upsert(batch, on_conflict='timestamp,profile,video_id').execute()
                print(f"  Imported {min(i+batch_size, len(data))}/{len(data)} comments")
            except Exception as e:
                print(f"  Error in batch {i}-{i+batch_size}: {e}")

        print(f"✓ Imported {len(data)} comments successfully!")
    except FileNotFoundError:
        print("No comment history file found")
    except Exception as e:
        print(f"Error importing comments: {e}")

def import_dms():
    """Import DM history"""
    try:
        with open('tiktok_dm_history.json', 'r') as f:
            file_data = json.load(f)

        # Extract the report array and remove fields not in schema
        data = file_data.get('report', []) if isinstance(file_data, dict) else file_data

        if not data:
            print("No DMs to import")
            return

        # Remove fields not in schema
        cleaned_data = []
        exclude_fields = {'last_updated', 'search_mode'}  # Fields not in schema
        for record in data:
            if isinstance(record, dict):
                # Only keep fields that exist in the schema
                cleaned_record = {k: v for k, v in record.items() if k not in exclude_fields}
                cleaned_data.append(cleaned_record)

        print(f"Importing {len(cleaned_data)} DMs...")
        if cleaned_data:
            supabase.table('dm_reports').upsert(cleaned_data, on_conflict='timestamp,profile,username').execute()
        print(f"✓ Imported {len(cleaned_data)} DMs successfully!")
    except FileNotFoundError:
        print("No DM history file found")
    except Exception as e:
        print(f"Error importing DMs: {e}")

def import_posts():
    """Import post history"""
    try:
        with open('tiktok_post_history.json', 'r') as f:
            file_data = json.load(f)

        # Extract the report array
        data = file_data.get('report', []) if isinstance(file_data, dict) else file_data

        if not data:
            print("No posts to import")
            return

        print(f"Importing {len(data)} posts...")

        # Import in batches of 100
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            try:
                supabase.table('post_reports').upsert(batch, on_conflict='timestamp,profile,video').execute()
                print(f"  Imported {min(i+batch_size, len(data))}/{len(data)} posts")
            except Exception as e:
                print(f"  Error in batch {i}-{i+batch_size}: {e}")

        print(f"✓ Imported {len(data)} posts successfully!")
    except FileNotFoundError:
        print("No post history file found")
    except Exception as e:
        print(f"Error importing posts: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  Importing Data to Supabase")
    print("=" * 60)

    import_comments()
    print()
    import_dms()
    print()
    import_posts()

    print("\n" + "=" * 60)
    print("  Import Complete!")
    print("=" * 60)
    print("\nRefresh your Vercel dashboard: https://tiktok-commenter-dm.vercel.app")
