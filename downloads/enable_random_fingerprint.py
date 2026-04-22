#!/usr/bin/env python3
"""
DEPRECATED: Enable Random Fingerprint for All AdsPower Profiles
Uses pyautogui to click through each profile.

Do not run this for TikTok profiles. Broad random fingerprint changes can switch
profiles away from their stable Windows identity and trigger platform mismatch
signals.

BEFORE RUNNING:
1. Open AdsPower
2. Make sure profile list is visible
3. Select the FIRST profile (tt1 or whichever you want to start from)
4. Run this script

To adjust positions, edit the POSITIONS dict below.
"""

import time
import sys

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.1
except ImportError:
    print("Install pyautogui: pip install pyautogui")
    sys.exit(1)

# =============================================================================
# POSITIONS - Edit these based on your screen
# =============================================================================
# To find positions: move mouse and run:
#   python3 -c "import pyautogui, time; time.sleep(3); print(pyautogui.position())"

POSITIONS = {
    # Advanced tab in the edit dialog
    "advanced_tab_x": 640,
    "advanced_tab_y": 31,

    # Random fingerprint toggle (after scrolling down in Advanced tab)
    "toggle_x": 310,
    "toggle_y": 533,

    # OK button
    "ok_x": 343,
    "ok_y": 672,
}

# How many profiles to process
TOTAL_PROFILES = 505
START_FROM = 23  # Start from this profile number (1-indexed)


def main():
    print("This script is deprecated and intentionally blocked.")
    print("Use update_adspower_os_windows.py to keep stable Windows fingerprints.")
    return

    print("=" * 60)
    print("  Enable Random Fingerprint - PyAutoGUI")
    print("=" * 60)
    print()
    print("SETUP:")
    print("1. AdsPower should be open with profile list visible")
    print("2. First profile should be SELECTED (highlighted)")
    print("3. Move mouse to TOP-LEFT corner to abort at any time")
    print()
    print(f"Will process {TOTAL_PROFILES} profiles")
    print()
    print("Starting in 5 seconds...")
    print("(Move mouse to top-left corner NOW to abort)")
    print()

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print()
    print("Running...")
    print()

    count = 0

    while count < TOTAL_PROFILES:
        try:
            # Step 1: Press Enter to open edit dialog for selected profile
            pyautogui.press('enter')
            time.sleep(0.7)

            # Step 2: Click Advanced tab
            pyautogui.click(POSITIONS["advanced_tab_x"], POSITIONS["advanced_tab_y"])
            time.sleep(0.4)

            # Step 3: Scroll down to see Random fingerprint toggle
            pyautogui.scroll(-3)
            time.sleep(0.3)

            # Step 4: Click Random fingerprint toggle
            pyautogui.click(POSITIONS["toggle_x"], POSITIONS["toggle_y"])
            time.sleep(0.2)

            # Step 5: Click OK to save
            pyautogui.click(POSITIONS["ok_x"], POSITIONS["ok_y"])
            time.sleep(0.4)

            count += 1
            print(f"[{count}/{TOTAL_PROFILES}] Done")

            # Step 6: Press Down arrow to select next profile
            pyautogui.press('down')
            time.sleep(0.15)

        except pyautogui.FailSafeException:
            print()
            print("ABORTED - Mouse moved to corner")
            break
        except KeyboardInterrupt:
            print()
            print("ABORTED - Ctrl+C pressed")
            break
        except Exception as e:
            print(f"Error: {e}")
            # Try to continue
            pyautogui.press('escape')
            time.sleep(0.3)
            pyautogui.press('down')
            time.sleep(0.2)

    print()
    print("=" * 60)
    print(f"  Completed {count} profiles")
    print("=" * 60)


if __name__ == "__main__":
    main()
