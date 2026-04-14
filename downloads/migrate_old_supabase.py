#!/usr/bin/env python3
"""
Migrate data from old Supabase to new Supabase
"""
import json
from supabase import create_client

# Old Supabase (now resumed)
OLD_SUPABASE_URL = "https://qwnhywiygyvlhjxxrbkk.supabase.co"
OLD_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bmh5d2l5Z3l2bGhqeHhyYmtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNTkxNzgsImV4cCI6MjA4NjgzNTE3OH0.X7RdTeOPrJCkf8c1oOUGHv1tntDigluOnj7bPw50tKE"

# New Supabase
NEW_SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
NEW_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"

old_supabase = create_client(OLD_SUPABASE_URL, OLD_SUPABASE_KEY)
new_supabase = create_client(NEW_SUPABASE_URL, NEW_SUPABASE_KEY)

def migrate_comments():
    """Migrate comment_reports from old to new Supabase"""
    print("\n" + "="*60)
    print("MIGRATING COMMENTS")
    print("="*60)

    try:
        # Get all comments from old Supabase (with pagination)
        print("Fetching comments from old Supabase...")
        old_comments = []
        page_size = 1000
        offset = 0

        while True:
            result = old_supabase.table('comment_reports').select('*').range(offset, offset + page_size - 1).execute()
            batch = result.data

            if not batch:
                break

            old_comments.extend(batch)
            offset += page_size
            print(f"  Fetched {len(old_comments)} comments so far...")

            if len(batch) < page_size:
                break

        print(f"Found {len(old_comments)} total comments in old Supabase")

        # Get existing comments in new Supabase
        result = new_supabase.table('comment_reports').select('timestamp,profile,video_id').execute()
        existing = {(c['timestamp'], c['profile'], c['video_id']) for c in result.data}

        print(f"Found {len(existing)} comments already in new Supabase")

        # Filter out duplicates and remove fields not in new schema
        new_comments = []
        for comment in old_comments:
            key = (comment.get('timestamp'), comment.get('profile'), comment.get('video_id'))
            if key not in existing:
                # Remove fields not in new schema
                clean_comment = {k: v for k, v in comment.items() if k not in {'received_at'}}
                new_comments.append(clean_comment)

        print(f"Will import {len(new_comments)} new comments")

        if not new_comments:
            print("✓ All comments already migrated!")
            return

        # Import in batches
        batch_size = 100
        imported = 0

        for i in range(0, len(new_comments), batch_size):
            batch = new_comments[i:i+batch_size]
            try:
                new_supabase.table('comment_reports').upsert(batch, on_conflict='timestamp,profile,video_id').execute()
                imported += len(batch)
                print(f"  Imported {imported}/{len(new_comments)} comments")
            except Exception as e:
                print(f"  Error in batch {i}: {e}")

        print(f"\n✓ Successfully migrated {imported} comments!")

    except Exception as e:
        print(f"Error migrating comments: {e}")
        import traceback
        traceback.print_exc()

def migrate_dms():
    """Migrate dm_reports from old to new Supabase"""
    print("\n" + "="*60)
    print("MIGRATING DMS")
    print("="*60)

    try:
        print("Fetching DMs from old Supabase...")
        result = old_supabase.table('dm_reports').select('*').execute()
        old_dms = result.data

        print(f"Found {len(old_dms)} DMs in old Supabase")

        # Get existing DMs
        result = new_supabase.table('dm_reports').select('timestamp,profile,username').execute()
        existing = {(d['timestamp'], d['profile'], d['username']) for d in result.data}

        print(f"Found {len(existing)} DMs already in new Supabase")

        # Filter duplicates
        new_dms = []
        for dm in old_dms:
            key = (dm.get('timestamp'), dm.get('profile'), dm.get('username'))
            if key not in existing:
                # Remove fields not in new schema
                clean_dm = {k: v for k, v in dm.items() if k not in {'last_updated', 'search_mode'}}
                new_dms.append(clean_dm)

        print(f"Will import {len(new_dms)} new DMs")

        if not new_dms:
            print("✓ All DMs already migrated!")
            return

        # Import in batches
        batch_size = 100
        imported = 0

        for i in range(0, len(new_dms), batch_size):
            batch = new_dms[i:i+batch_size]
            try:
                new_supabase.table('dm_reports').upsert(batch, on_conflict='timestamp,profile,username').execute()
                imported += len(batch)
                print(f"  Imported {imported}/{len(new_dms)} DMs")
            except Exception as e:
                print(f"  Error in batch {i}: {e}")

        print(f"\n✓ Successfully migrated {imported} DMs!")

    except Exception as e:
        print(f"Error migrating DMs: {e}")
        import traceback
        traceback.print_exc()

def migrate_posts():
    """Migrate post_reports from old to new Supabase"""
    print("\n" + "="*60)
    print("MIGRATING POSTS")
    print("="*60)

    try:
        print("Fetching posts from old Supabase...")
        result = old_supabase.table('post_reports').select('*').execute()
        old_posts = result.data

        print(f"Found {len(old_posts)} posts in old Supabase")

        # Get existing posts (using 'video' not 'video_id')
        result = new_supabase.table('post_reports').select('timestamp,profile,video').execute()
        existing = {(p['timestamp'], p['profile'], p['video']) for p in result.data}

        print(f"Found {len(existing)} posts already in new Supabase")

        # Filter duplicates
        new_posts = []
        for post in old_posts:
            # Old schema uses video_id, new uses video
            video_key = post.get('video_id') or post.get('video')
            key = (post.get('timestamp'), post.get('profile'), video_key)
            if key not in existing:
                # Rename video_id to video if needed
                clean_post = {k: v for k, v in post.items()}
                if 'video_id' in clean_post and 'video' not in clean_post:
                    clean_post['video'] = clean_post.pop('video_id')
                new_posts.append(clean_post)

        print(f"Will import {len(new_posts)} new posts")

        if not new_posts:
            print("✓ All posts already migrated!")
            return

        # Import in batches
        batch_size = 100
        imported = 0

        for i in range(0, len(new_posts), batch_size):
            batch = new_posts[i:i+batch_size]
            try:
                new_supabase.table('post_reports').upsert(batch, on_conflict='timestamp,profile,video').execute()
                imported += len(batch)
                print(f"  Imported {imported}/{len(new_posts)} posts")
            except Exception as e:
                print(f"  Error in batch {i}: {e}")

        print(f"\n✓ Successfully migrated {imported} posts!")

    except Exception as e:
        print(f"Error migrating posts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("  OLD SUPABASE → NEW SUPABASE MIGRATION")
    print("="*60)

    migrate_comments()
    migrate_dms()
    migrate_posts()

    print("\n" + "="*60)
    print("  MIGRATION COMPLETE!")
    print("="*60)

    # Show final counts
    result = new_supabase.table('comment_reports').select('timestamp', count='exact').execute()
    print(f"\n  Total Comments: {result.count}")

    result = new_supabase.table('dm_reports').select('timestamp', count='exact').execute()
    print(f"  Total DMs: {result.count}")

    result = new_supabase.table('post_reports').select('timestamp', count='exact').execute()
    print(f"  Total Posts: {result.count}")

    print("\n" + "="*60)
