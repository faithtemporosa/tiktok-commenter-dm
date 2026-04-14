#!/usr/bin/env python3
"""
Record Mouse Positions for PyAutoGUI
Helps you capture exact coordinates for automation

HOW TO USE:
1. Run this script
2. When prompted, move your mouse to the position you want to record
3. Press ENTER to capture that position
4. Repeat for all positions
5. Script will output the coordinates for you to update enable_random_fingerprint.py
"""

import time
import sys

try:
    import pyautogui
except ImportError:
    print("Install pyautogui: pip install pyautogui")
    sys.exit(1)


def record_position(description):
    """Record a single mouse position"""
    print(f"\n{description}")
    print("Move your mouse to the desired position, then press ENTER...")
    input()

    pos = pyautogui.position()
    print(f"  ✓ Recorded: X={pos.x}, Y={pos.y}")
    return pos.x, pos.y


def main():
    print("=" * 60)
    print("  Mouse Position Recorder for PyAutoGUI")
    print("=" * 60)
    print()
    print("SETUP:")
    print("1. Open AdsPower with the profile list visible")
    print("2. Select ANY profile in the list (e.g., tt490)")
    print("3. Keep AdsPower window in focus")
    print()
    print("Ready to record positions...")
    print()

    positions = {}

    # Record each position
    print("We'll record the following positions:")
    print("  1. Advanced tab (in edit dialog)")
    print("  2. Random fingerprint toggle")
    print("  3. OK button")
    print()
    input("Press ENTER to start...")
    print()

    # Step 1: Open profile edit dialog first
    print("STEP 1: Press ENTER on selected profile to open edit dialog")
    print("(This will happen automatically - just verify the dialog opens)")
    input("Press ENTER to open edit dialog...")
    pyautogui.press('enter')
    time.sleep(1)

    # Step 2: Record Advanced tab position
    x, y = record_position("STEP 2: Move mouse to 'Advanced' tab and press ENTER")
    positions['advanced_tab_x'] = x
    positions['advanced_tab_y'] = y

    # Step 3: Click Advanced tab
    print("\nClicking Advanced tab...")
    pyautogui.click(x, y)
    time.sleep(0.5)

    # Step 4: Scroll down
    print("\nScrolling down to see Random fingerprint toggle...")
    pyautogui.scroll(-3)
    time.sleep(0.5)

    # Step 5: Record toggle position
    x, y = record_position("STEP 3: Move mouse to 'Random fingerprint' toggle and press ENTER")
    positions['toggle_x'] = x
    positions['toggle_y'] = y

    # Step 6: Record OK button position
    x, y = record_position("STEP 4: Move mouse to 'OK' button and press ENTER")
    positions['ok_x'] = x
    positions['ok_y'] = y

    # Close dialog
    print("\nClosing dialog...")
    pyautogui.press('escape')
    time.sleep(0.5)

    # Summary
    print()
    print("=" * 60)
    print("  RECORDED POSITIONS")
    print("=" * 60)
    print()
    print("Copy these values to enable_random_fingerprint.py:")
    print()
    print("POSITIONS = {")
    print(f'    "advanced_tab_x": {positions["advanced_tab_x"]},')
    print(f'    "advanced_tab_y": {positions["advanced_tab_y"]},')
    print(f'    "toggle_x": {positions["toggle_x"]},')
    print(f'    "toggle_y": {positions["toggle_y"]},')
    print(f'    "ok_x": {positions["ok_x"]},')
    print(f'    "ok_y": {positions["ok_y"]},')
    print("}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
