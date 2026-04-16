#!/usr/bin/env python3
"""
TikTok Viewing Scheduler & Tracker
Reminds you when to view with each account and tracks daily progress
"""

import json
import time
from datetime import datetime, timedelta
import os

# Configuration
ACCOUNTS = [
    {'name': 'Account 1', 'schedule': '09:00'},  # 9 AM
    {'name': 'Account 2', 'schedule': '14:00'},  # 2 PM
    {'name': 'Account 3', 'schedule': '19:00'},  # 7 PM
]

TARGET_ACCOUNTS = ['charlidamelio', 'addisonre', 'bellapoarch']
VIDEOS_PER_TARGET = 30
VIEW_TIME_MINUTES = 20

TRACKER_FILE = 'downloads/view_tracker.json'

def load_tracker():
    """Load viewing history"""
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {'sessions': [], 'stats': {}}

def save_tracker(data):
    """Save viewing history"""
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_session(account_name, target, videos_watched):
    """Log a completed viewing session"""
    tracker = load_tracker()

    session = {
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'account': account_name,
        'target': target,
        'videos_watched': videos_watched
    }

    tracker['sessions'].append(session)

    # Update daily stats
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in tracker['stats']:
        tracker['stats'][today] = {'total_views': 0, 'accounts_used': set()}

    tracker['stats'][today]['total_views'] += videos_watched
    tracker['stats'][today]['accounts_used'] = list(set(tracker['stats'][today].get('accounts_used', [])) | {account_name})

    save_tracker(tracker)
    print(f"✓ Logged: {account_name} viewed {videos_watched} videos from @{target}")

def show_schedule():
    """Show today's viewing schedule"""
    print("=" * 80)
    print("  TIKTOK VIEWING SCHEDULE - Today")
    print("=" * 80)
    print()

    now = datetime.now()
    current_time = now.strftime('%H:%M')

    for account in ACCOUNTS:
        scheduled = account['schedule']
        account_name = account['name']

        if current_time < scheduled:
            status = f"⏰ Upcoming at {scheduled}"
        elif current_time >= scheduled:
            # Check if already completed today
            tracker = load_tracker()
            today = now.strftime('%Y-%m-%d')
            today_sessions = [s for s in tracker['sessions'] if s['date'] == today and s['account'] == account_name]

            if len(today_sessions) >= len(TARGET_ACCOUNTS):
                status = "✓ Completed"
            else:
                status = "⚠ TIME TO VIEW!"

        print(f"{account_name:15} {scheduled}  {status}")

    print()
    print("What to do:")
    print(f"  1. Open TikTok on iPhone")
    print(f"  2. Switch to the scheduled account")
    print(f"  3. Search & view these accounts:")
    for target in TARGET_ACCOUNTS:
        print(f"     - @{target} ({VIDEOS_PER_TARGET} videos, {VIEW_TIME_MINUTES} mins)")
    print(f"  4. Mark as complete when done")
    print()

def show_stats():
    """Show viewing statistics"""
    tracker = load_tracker()

    print("=" * 80)
    print("  VIEWING STATISTICS")
    print("=" * 80)
    print()

    if not tracker['sessions']:
        print("No viewing sessions recorded yet.")
        print()
        return

    # Last 7 days
    print("Last 7 Days:")
    print()

    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        stats = tracker['stats'].get(date, {})
        total_views = stats.get('total_views', 0)
        accounts_used = len(stats.get('accounts_used', []))

        if total_views > 0:
            print(f"  {date}:  {total_views:3} views  ({accounts_used} accounts)")
        else:
            print(f"  {date}:  No views")

    print()

    # Today's progress
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = tracker['stats'].get(today, {})
    today_views = today_stats.get('total_views', 0)
    today_accounts = len(today_stats.get('accounts_used', []))

    print(f"Today's Progress:")
    print(f"  • Total views: {today_views}")
    print(f"  • Accounts used: {today_accounts}/3")
    print(f"  • Target per day: {len(TARGET_ACCOUNTS) * VIDEOS_PER_TARGET * 3} views")

    if today_views > 0:
        completion = (today_views / (len(TARGET_ACCOUNTS) * VIDEOS_PER_TARGET * 3)) * 100
        print(f"  • Completion: {completion:.1f}%")

    print()

def mark_complete():
    """Mark a viewing session as complete"""
    print()
    print("Which account did you just finish viewing with?")
    for i, account in enumerate(ACCOUNTS, 1):
        print(f"  {i}. {account['name']}")

    choice = input("\nEnter number (1-3): ").strip()

    if choice not in ['1', '2', '3']:
        print("Invalid choice")
        return

    account = ACCOUNTS[int(choice) - 1]

    print()
    print("Which target account did you view?")
    for i, target in enumerate(TARGET_ACCOUNTS, 1):
        print(f"  {i}. @{target}")

    target_choice = input("\nEnter number (1-3): ").strip()

    if target_choice not in ['1', '2', '3']:
        print("Invalid choice")
        return

    target = TARGET_ACCOUNTS[int(target_choice) - 1]

    videos = input(f"\nHow many videos did you watch? (default: {VIDEOS_PER_TARGET}): ").strip()
    videos = int(videos) if videos else VIDEOS_PER_TARGET

    log_session(account['name'], target, videos)
    print()
    show_stats()

def send_reminder():
    """Check if it's time to view and send reminder"""
    now = datetime.now()
    current_time = now.strftime('%H:%M')

    for account in ACCOUNTS:
        if account['schedule'] == current_time:
            print()
            print("=" * 80)
            print(f"  ⏰ REMINDER: Time to view with {account['name']}!")
            print("=" * 80)
            print()
            print("Steps:")
            print(f"  1. Open TikTok on iPhone")
            print(f"  2. Switch to {account['name']}")
            print(f"  3. View these accounts:")
            for target in TARGET_ACCOUNTS:
                print(f"     - Search @{target}")
                print(f"     - Tap first video")
                print(f"     - Let it auto-play for {VIEW_TIME_MINUTES} mins")
            print(f"  4. Run this script and mark as complete")
            print()

            # Play system sound
            os.system('afplay /System/Library/Sounds/Glass.aiff')

def interactive_menu():
    """Show interactive menu"""
    while True:
        print()
        print("=" * 80)
        print("  TIKTOK VIEW SCHEDULER")
        print("=" * 80)
        print()
        print("Options:")
        print("  1. Show today's schedule")
        print("  2. Mark session as complete")
        print("  3. View statistics")
        print("  4. Start reminder daemon (runs in background)")
        print("  5. Exit")
        print()

        choice = input("Enter choice (1-5): ").strip()

        if choice == '1':
            show_schedule()
        elif choice == '2':
            mark_complete()
        elif choice == '3':
            show_stats()
        elif choice == '4':
            print()
            print("Starting reminder daemon...")
            print("Press Ctrl+C to stop")
            print()
            try:
                while True:
                    send_reminder()
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                print()
                print("Stopped reminder daemon")
        elif choice == '5':
            print()
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

def main():
    print()
    print("=" * 80)
    print("  TIKTOK VIEWING ASSISTANT")
    print("=" * 80)
    print()
    print("This tool helps you manage viewing across your 3 TikTok accounts.")
    print()

    # Show quick overview
    show_schedule()
    show_stats()

    # Start interactive menu
    interactive_menu()

if __name__ == '__main__':
    main()
