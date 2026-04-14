#!/usr/bin/env python3
"""Move your mouse, this prints the position every second"""
import pyautogui
import time

print("Move your mouse to find positions. Press Ctrl+C to stop.")
print()
try:
    while True:
        pos = pyautogui.position()
        print(f"Position: x={pos.x}, y={pos.y}    ", end="\r")
        time.sleep(0.2)
except KeyboardInterrupt:
    print()
    print("Done")
