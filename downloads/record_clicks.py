#!/usr/bin/env python3
"""
Mouse Click Recorder (Simple Version)
======================================
Records your mouse clicks and positions to help build automation scripts.

USAGE:
    python3 record_clicks.py

HOW IT WORKS:
    - Shows current mouse position in real-time
    - Press ENTER to record current position
    - Press 's' + ENTER to take screenshot
    - Press 'q' + ENTER to quit and save

OUTPUT:
    recorded_clicks.json - All recorded click positions
    screenshots/ - Screenshots taken during recording
"""

import pyautogui
import time
import json
import os
from datetime import datetime
import threading

# Create screenshots directory
os.makedirs("screenshots", exist_ok=True)

# Global state
recorded_actions = []
recording = True
action_count = 0

def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def position_monitor():
    """Continuously show mouse position"""
    global recording
    while recording:
        x, y = pyautogui.position()
        print(f"\r📍 Mouse position: ({x:4d}, {y:4d})  |  Press ENTER to record, 'q' to quit    ", end="", flush=True)
        time.sleep(0.1)

def take_screenshot(name="click"):
    """Take a screenshot"""
    global action_count
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        screenshot_path = f"screenshots/{name}_{action_count}_{timestamp}.png"
        pyautogui.screenshot(screenshot_path)
        return screenshot_path
    except Exception as e:
        print(f"\n⚠️ Screenshot failed: {e}")
        return None

def record_position(note=""):
    """Record current mouse position"""
    global action_count
    action_count += 1

    x, y = pyautogui.position()

    action = {
        "id": action_count,
        "type": "position",
        "x": x,
        "y": y,
        "note": note,
        "timestamp": get_timestamp()
    }

    # Take screenshot
    screenshot_path = take_screenshot("pos")
    if screenshot_path:
        action["screenshot"] = screenshot_path

    recorded_actions.append(action)

    print(f"\n✅ [{action_count}] Recorded position: ({x}, {y})")
    if note:
        print(f"   Note: {note}")
    if screenshot_path:
        print(f"   📸 Screenshot: {screenshot_path}")
    print()

def save_recording():
    """Save recorded actions to JSON"""
    output_file = "recorded_clicks.json"

    with open(output_file, 'w') as f:
        json.dump({
            "recorded_at": datetime.now().isoformat(),
            "total_actions": len(recorded_actions),
            "actions": recorded_actions
        }, f, indent=2)

    print(f"\n✅ Saved {len(recorded_actions)} positions to {output_file}")

def main():
    global recording

    print("""
╔══════════════════════════════════════════════════════════╗
║              Mouse Position Recorder                     ║
╚══════════════════════════════════════════════════════════╝

INSTRUCTIONS:
1. Open the TAMU directory website: https://directory.tamu.edu/
2. Position your mouse over elements you want to record
3. Use the commands below to record positions

COMMANDS:
    ENTER        → Record current mouse position + screenshot
    s + ENTER    → Take screenshot only
    note + ENTER → Record position with a note (e.g., "search_box")
    q + ENTER    → Quit and save recording

WORKFLOW:
1. Hover over search box → type "search_box" + ENTER
2. Hover over search button → type "search_button" + ENTER
3. Hover over first result → type "first_result" + ENTER
4. Hover over email field → type "email_field" + ENTER
5. Hover over phone field → type "phone_field" + ENTER
6. Type "q" to quit and save

Starting in 3 seconds...
    """)

    time.sleep(3)

    # Start position monitor in background
    monitor_thread = threading.Thread(target=position_monitor, daemon=True)
    monitor_thread.start()

    print("\n🔴 RECORDING STARTED\n")
    print("-" * 60)

    while recording:
        try:
            user_input = input().strip().lower()

            if user_input == 'q':
                recording = False
                break
            elif user_input == 's':
                screenshot_path = take_screenshot("manual")
                if screenshot_path:
                    print(f"\n📸 Screenshot saved: {screenshot_path}\n")
            elif user_input == '':
                record_position()
            else:
                # User typed a note
                record_position(note=user_input)

        except KeyboardInterrupt:
            recording = False
            break
        except EOFError:
            recording = False
            break

    save_recording()

    print("\n" + "=" * 60)
    print("RECORDING SUMMARY")
    print("=" * 60)

    if recorded_actions:
        print(f"\nRecorded {len(recorded_actions)} positions:\n")
        for action in recorded_actions:
            note = f" - {action['note']}" if action.get('note') else ""
            print(f"  [{action['id']}] ({action['x']:4d}, {action['y']:4d}){note}")

    print(f"\nFiles saved:")
    print(f"  📄 recorded_clicks.json")
    print(f"  📁 screenshots/")
    print("\nYou can now share these files with me to update the scraper!")

if __name__ == "__main__":
    main()
