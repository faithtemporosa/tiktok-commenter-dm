#!/usr/bin/env python3
"""Start a test repost for tt5"""

import requests
import json
import time

# Start repost for tt5
print("Starting repost test for tt5...")
response = requests.post('http://localhost:9000/api/post/start',
                        json={'profile_ids': ['tt5']})
print(f"Start response: {response.json()}")

# Monitor progress
print("\nMonitoring progress (will check for 2 minutes)...")
for i in range(24):  # Check every 5 seconds for 2 minutes
    time.sleep(5)
    status = requests.get('http://localhost:9000/api/post/status').json()

    running = status.get('running', False)
    current = status.get('current_profile')
    progress = status.get('progress', 0)
    total = status.get('total', 0)
    posts_made = status.get('posts_made', 0)

    print(f"  [{i*5}s] Running: {running} | Profile: {current} | Progress: {progress}/{total} | Posts: {posts_made}")

    if not running and i > 0:
        print("\nRepost completed!")
        break

print("\nFinal status:")
final_status = requests.get('http://localhost:9000/api/post/status').json()
print(json.dumps(final_status, indent=2))
