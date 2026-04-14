#!/usr/bin/env python3
"""Monitor YouTube signup progress"""

import time
import os

print("YouTube Signup Monitor")
print("=" * 60)
print("\nMonitoring youtube_signup.log...")
print("Press Ctrl+C to stop monitoring\n")

last_size = 0

try:
    while True:
        if os.path.exists('youtube_signup.log'):
            size = os.path.getsize('youtube_signup.log')
            if size > last_size:
                with open('youtube_signup.log', 'r') as f:
                    f.seek(last_size)
                    new_content = f.read()
                    print(new_content, end='')
                    last_size = size
        time.sleep(2)
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
