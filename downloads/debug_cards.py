#!/usr/bin/env python3
"""Debug script to find correct user card selectors"""

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

        # Scroll
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.3)
        time.sleep(2)

        # Get page text content as a whole
        body_text = page.locator("body").inner_text()

        # Parse user cards from the text
        # Pattern: username line followed by followers and likes
        # Format appears to be:
        # DisplayName
        # username
        # XXK
        # Followers
        # ·
        # XXK
        # Likes
        # Follow

        print("\n=== Parsing page text for user patterns ===")

        lines = body_text.split('\n')
        lines = [l.strip() for l in lines if l.strip()]

        users = []

        for i, line in enumerate(lines):
            # Look for username pattern (lowercase, underscores, numbers)
            if re.match(r'^[a-z][a-z0-9._]*$', line) and len(line) > 2:
                # Check if next few lines have follower pattern
                try:
                    next_lines = lines[i+1:i+6]
                    next_text = ' '.join(next_lines)

                    # Check for follower pattern
                    follower_match = re.search(r'([\d.]+[KMB]?)\s*Followers', next_text)
                    if follower_match:
                        username = line
                        followers = follower_match.group(1)
                        users.append((username, followers))
                        print(f"  @{username}: {followers} followers")
                except:
                    pass

        print(f"\nFound {len(users)} users with follower counts")

        # Close page
        page.close()

if __name__ == "__main__":
    main()
