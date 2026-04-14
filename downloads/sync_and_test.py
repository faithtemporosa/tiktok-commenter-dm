#!/usr/bin/env python3
"""Sync profiles and test repost"""

import requests
import json
import time

# First sync profiles
print("Syncing profiles from AdsPower...")
sync_response = requests.post('http://localhost:9000/api/sync-profiles')
print(f"Sync response: {sync_response.json()}")

# Wait a moment for sync to complete
time.sleep(2)

# Now start repost for tt5
print("\nStarting repost test for tt5...")
response = requests.post('http://localhost:9000/api/post/start',
                        json={'profile_ids': ['tt5']})
print(f"Start response: {response.json()}")

# Monitor progress
print("\nMonitoring progress...")
for i in range(48):  # Check every 5 seconds for 4 minutes
    time.sleep(5)
    status = requests.get('http://localhost:9000/api/post/status').json()

    running = status.get('running', False)
    current = status.get('current_profile')
    progress = status.get('progress', 0)
    total = status.get('total', 0)
    posts_made = status.get('posts_made', 0)

    logs = status.get('logs', [])
    if logs:
        print(f"  [{i*5}s] {logs[-1]}")
    else:
        print(f"  [{i*5}s] Running: {running} | Profile: {current} | Progress: {progress}/{total} | Posts: {posts_made}")

    if not running and i > 2:
        print("\nRepost completed!")
        break

# Check final logs
final_status = requests.get('http://localhost:9000/api/post/status').json()
print("\nFinal logs:")
for log in final_status.get('logs', [])[-10:]:
    print(f"  {log}")

print(f"\nFinal posts made: {final_status.get('posts_made', 0)}")
