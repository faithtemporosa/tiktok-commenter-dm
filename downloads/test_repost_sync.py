#!/usr/bin/env python3
"""Test repost sync to Supabase"""

import requests
import json
import time
from supabase import create_client

supabase_url = 'https://qwnhywiygyvlhjxxrbkk.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bmh5d2l5Z3l2bGhqeHhyYmtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNTkxNzgsImV4cCI6MjA4NjgzNTE3OH0.X7RdTeOPrJCkf8c1oOUGHv1tntDigluOnj7bPw50tKE'
supabase = create_client(supabase_url, supabase_key)

# Get initial count
initial_result = supabase.table('post_reports').select('id', count='exact').execute()
initial_count = initial_result.count or 0
print(f"Initial reposts in Supabase: {initial_count}")

# Sync profiles
print("\nSyncing profiles from AdsPower...")
sync_response = requests.post('http://localhost:9000/api/sync-profiles')
print(f"Sync response: {sync_response.json()}")

time.sleep(2)

# Start repost automation
print("\nStarting repost automation...")
response = requests.post('http://localhost:9000/api/post/start')
print(f"Start response: {response.json()}")

if not response.json().get('ok'):
    print("Failed to start - exiting")
    exit(1)

# Monitor for 3 minutes
print("\nMonitoring progress (checking every 10s for 3 minutes)...")
for i in range(18):  # 18 * 10s = 3 minutes
    time.sleep(10)

    status = requests.get('http://localhost:9000/api/post/status').json()
    running = status.get('running', False)
    current = status.get('current_profile')
    progress = status.get('progress', 0)
    total = status.get('total', 0)
    posts_made = status.get('posts_made', 0)

    # Check Supabase count
    current_result = supabase.table('post_reports').select('id', count='exact').execute()
    current_count = current_result.count or 0
    new_synced = current_count - initial_count

    logs = status.get('logs', [])
    if logs:
        last_log = logs[-1]
    else:
        last_log = "No logs"

    print(f"[{i*10}s] Running: {running} | Profile: {current} | Progress: {progress}/{total}")
    print(f"       Local posts: {posts_made} | Supabase: {current_count} (↑{new_synced} new)")
    print(f"       Last log: {last_log}")
    print()

    if not running and i > 0:
        print("Repost automation finished!")
        break

# Final check
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)

final_result = supabase.table('post_reports').select('id', count='exact').execute()
final_count = final_result.count or 0
total_synced = final_count - initial_count

final_status = requests.get('http://localhost:9000/api/post/status').json()
final_posts = final_status.get('posts_made', 0)

print(f"Total reposts synced to Supabase: {total_synced}")
print(f"Local post count: {final_posts}")

if total_synced > 0:
    print("\n✓ SUCCESS: Reposts are syncing to Supabase!")
    # Show last few
    recent = supabase.table('post_reports').select('*').order('created_at', desc=True).limit(3).execute()
    print("\nLast 3 reposts in Supabase:")
    for post in recent.data:
        print(f"  - {post.get('timestamp')} | {post.get('profile')} | {post.get('content_type')}")
else:
    print("\n✗ WARNING: No new reposts synced to Supabase")
    print("Check bot logs for sync errors")
