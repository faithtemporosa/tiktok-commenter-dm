#!/usr/bin/env python3
"""Debug script to see text structure of TikTok user cards"""

import requests
import time
import re
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"

def get_browser():
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page=1&page_size=500", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for profile in data.get("data", {}).get("list", []):
                if profile.get("name") in ["tt46", "tt47"]:
                    return profile
        return None
    except:
        return None

def open_browser(user_id):
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0", timeout=60)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {})
        return None
    except:
        return None

def main():
    profile = get_browser()
    if not profile:
        print("Could not get browser profile")
        return

    user_id = profile.get("user_id")
    print(f"Using browser: {profile.get('name')}")

    # Check if already open
    browser_info = None
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for b in data.get("data", {}).get("list", []):
                if b.get("user_id") == user_id:
                    browser_info = b
                    break
    except:
        pass

    if not browser_info:
        print("Opening browser...")
        browser_info = open_browser(user_id)
        if not browser_info:
            print("Failed to open browser")
            return
        time.sleep(3)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print("No WebSocket endpoint")
        return

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0]
        page = context.new_page()

        print("Navigating to search...")
        page.goto("https://www.tiktok.com/search?q=Minnesota%20small%20business", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)

        # Click Users tab
        print("Clicking Users tab...")
        try:
            page.click("text=Users", timeout=5000)
            time.sleep(3)
        except:
            print("Could not click Users tab")

        # Scroll to load users
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.3)
        time.sleep(2)

        # Find all links that contain /@
        print("\n=== Analyzing user links ===")
        links = page.locator("a[href*='/@']").all()
        print(f"Found {len(links)} profile links")

        seen_usernames = set()

        for i, link in enumerate(links[:30]):
            try:
                href = link.get_attribute("href")
                print(f"Link {i}: {href}")

                if not href or "/@" not in href:
                    continue

                username = href.split("/@")[1].split("?")[0].split("/")[0]
                if not username or username in seen_usernames:
                    print(f"  Skipping (duplicate or empty)")
                    continue
                seen_usernames.add(username)

                print(f"  Processing @{username}")

                # Get the card container - go up to find an ancestor that has follower info
                # Try different ancestor levels
                found = False
                for level in range(1, 8):
                    xpath = "/".join([".."] * level)
                    try:
                        ancestor = link.locator(f"xpath={xpath}").first
                        text = ancestor.inner_text()

                        if "Followers" in text:
                            print(f"\n  @{username} - Ancestor level {level}:")
                            # Print each line
                            lines = [l.strip() for l in text.split('\n') if l.strip()]
                            for line in lines[:8]:
                                print(f"    {line}")

                            # Try to extract follower count
                            match = re.search(r'([\d,.]+[KMB]?)\s*Followers?', text)
                            if match:
                                print(f"    => Followers: {match.group(1)}")
                            found = True
                            break
                    except Exception as ex:
                        print(f"    Level {level} error: {ex}")
                        continue

                if not found:
                    print(f"  Could not find Followers text for @{username}")

            except Exception as e:
                print(f"Error processing link {i}: {e}")

        # Close the page we created
        page.close()

if __name__ == "__main__":
    main()
