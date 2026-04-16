#!/usr/bin/env python3
"""
Simple 20-minute viewing timer
Helps you stay on track during manual viewing sessions
"""

import time
import os
from datetime import datetime

def play_sound():
    """Play completion sound"""
    os.system('afplay /System/Library/Sounds/Glass.aiff')

def viewing_timer(account_name):
    """Run a 20-minute viewing timer"""

    print()
    print("=" * 70)
    print(f"  VIEWING SESSION: {account_name}")
    print("=" * 70)
    print()
    print("What to do:")
    print("  1. Open TikTok on your iPhone")
    print(f"  2. Switch to {account_name}")
    print("  3. View these accounts (10 videos each):")
    print("     • @charlidamelio")
    print("     • @addisonre")
    print("     • @bellapoarch")
    print()
    print("This timer will count down 20 minutes.")
    print("You'll hear a sound when time is up.")
    print()
    input("Press Enter when ready to start...")

    # Start timer
    duration_minutes = 20
    duration_seconds = duration_minutes * 60

    start_time = time.time()

    print()
    print(f"Timer started: {datetime.now().strftime('%I:%M %p')}")
    print(f"Will end at: {datetime.fromtimestamp(start_time + duration_seconds).strftime('%I:%M %p')}")
    print()
    print("Viewing in progress...", end='', flush=True)

    # Update every minute
    for i in range(duration_minutes):
        time.sleep(60)
        remaining = duration_minutes - (i + 1)
        if remaining > 0:
            print(f"\n{remaining} minutes remaining...", end='', flush=True)
        else:
            print()

    # Done!
    print()
    print()
    print("=" * 70)
    print("  ✓ SESSION COMPLETE!")
    print("=" * 70)
    print()
    print(f"You watched for {duration_minutes} minutes")
    print(f"Approximate videos viewed: ~30")
    print()

    # Play sound
    for _ in range(3):
        play_sound()
        time.sleep(0.5)

    # Ask for confirmation
    completed = input("Did you complete the session? (y/n): ").strip().lower()

    if completed == 'y':
        print()
        print("✓ Session logged!")
        return True
    else:
        print()
        print("⚠ Session not completed - you can try again later")
        return False

def main():
    """Main menu"""

    accounts = ['Account 1', 'Account 2', 'Account 3']

    while True:
        print()
        print("=" * 70)
        print("  TIKTOK MANUAL VIEWING TIMER")
        print("=" * 70)
        print()
        print("Which account are you viewing with?")
        print()
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account}")
        print(f"  4. Exit")
        print()

        choice = input("Enter choice (1-4): ").strip()

        if choice == '4':
            print()
            print("Goodbye!")
            break

        if choice in ['1', '2', '3']:
            account = accounts[int(choice) - 1]
            viewing_timer(account)
        else:
            print()
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
