#!/usr/bin/env python3
"""Debug script to see TikTok search page structure"""

import requests
import time
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

        # Create a new page to avoid conflicts
        page = context.new_page()

        # Go to search
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

        # Scroll a bit
        for _ in range(5):
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(0.3)

        time.sleep(2)

        # Print all divs that contain "Followers"
        print("\n=== Divs containing 'Followers' ===")
        divs = page.locator("div:has-text('Followers')").all()
        print(f"Found {len(divs)} divs with 'Followers' text")

        for i, div in enumerate(divs[:10]):
            try:
                text = div.inner_text()
                # Only print if it looks like a user card (has @ username)
                if "@" in text and "Followers" in text:
                    print(f"\n--- Card {i} ---")
                    lines = [l.strip() for l in text.split('\n') if l.strip()][:6]
                    for line in lines:
                        print(f"  {line}")
            except:
                pass

        # Try to get outer HTML of a user card
        print("\n=== Looking for user card elements ===")

        # Try different selectors
        selectors = [
            "[data-e2e='search-user-container']",
            "[data-e2e='search-user-card']",
            "[class*='DivUserCardContainer']",
            "[class*='UserCard']",
        ]

        for sel in selectors:
            elements = page.locator(sel).all()
            if elements:
                print(f"Found {len(elements)} elements with selector: {sel}")
                try:
                    html = elements[0].evaluate("el => el.outerHTML")
                    print(f"Sample HTML (first 500 chars):\n{html[:500]}")
                except:
                    pass

        # Save page HTML for inspection
        html = page.content()
        with open("debug_page.html", "w") as f:
            f.write(html)
        print("\nSaved full page HTML to debug_page.html")

if __name__ == "__main__":
    main()
