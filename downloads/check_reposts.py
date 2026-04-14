#!/usr/bin/env python3
"""Quick script to check repost status in Supabase"""

from supabase import create_client
from datetime import datetime, timezone as tz

supabase_url = 'https://qwnhywiygyvlhjxxrbkk.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF3bmh5d2l5Z3l2bGhqeHhyYmtrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEyNTkxNzgsImV4cCI6MjA4NjgzNTE3OH0.X7RdTeOPrJCkf8c1oOUGHv1tntDigluOnj7bPw50tKE'

supabase = create_client(supabase_url, supabase_key)

# Get total count
total_result = supabase.table('post_reports').select('id', count='exact').execute()
print(f"Total reposts in database: {total_result.count or 0}")

# Get today's count (using UTC midnight like the bot does)
utc_now = datetime.now(tz.utc)
utc_midnight = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)
today_iso = utc_midnight.strftime("%Y-%m-%dT%H:%M:%S+00:00")

today_result = supabase.table('post_reports').select('id', count='exact').gte('timestamp', today_iso).execute()
print(f"Reposts today (UTC): {today_result.count or 0}")

# Get last 5 reposts
recent_result = supabase.table('post_reports').select('*').order('created_at', desc=True).limit(5).execute()
print(f"\nLast 5 reposts:")
for post in recent_result.data:
    print(f"  {post.get('timestamp')} - {post.get('profile')} - {post.get('status')} - {post.get('content_type')}")

# Check DMs too
dm_total = supabase.table('dm_reports').select('id', count='exact').execute()
dm_today = supabase.table('dm_reports').select('id', count='exact').gte('timestamp', today_iso).execute()
print(f"\nTotal DMs: {dm_total.count or 0}")
print(f"DMs today (UTC): {dm_today.count or 0}")
