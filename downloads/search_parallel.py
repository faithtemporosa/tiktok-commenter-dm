#!/usr/bin/env python3
"""
Search TikTok for Minnesota profiles using 2 browsers in parallel
"""

import requests
import json
import time
import csv
import sys
import os
import re
import threading
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"

# Split queries between browsers
QUERIES_BROWSER1 = [
    "Minnesota hockey",
    "Minnesota Vikings fan",
    "Minnesota Twins fan",
    "Minnesota Wild fan",
    "Minnesota lakes",
    "Minnesota fishing",
    "Minnesota hunting",
    "Minnesota camping",
    "Minnesota winter",
    "Minnesota snow",
    "Minnesota realtor",
    "Minnesota makeup",
    "Minnesota hair stylist",
    "Minnesota photographer",
    "Minnesota artist",
    "Minnesota musician",
    "Minnesota nurse",
    "Minnesota teacher",
    "Minnesota college",
    "University of Minnesota",
    "Minnesota State",
]

QUERIES_BROWSER2 = [
    "MN TikTok",
    "MN creator",
    "MN life",
    "MN mom",
    "MN dad",
    "MPLS",
    "Twin Cities",
    "Twin Cities TikTok",
    "Minneapolis creator",
    "Minneapolis food",
    "Minneapolis fashion",
    "St Paul creator",
    "Minnesota beauty",
    "Minnesota blogger",
    "Minnesota vlogger",
    "Minnesota couple",
    "Minnesota wedding",
    "Minnesota pets",
    "Minnesota dogs",
    "Minnesota cats",
]

# Shared state
all_profiles = {}
lock = threading.Lock()

def log(msg):
    print(msg, flush=True)

def get_browser_profile(name):
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page=1&page_size=500", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for profile in data.get("data", {}).get("list", []):
                if profile.get("name") == name:
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

def parse_followers(count_str):
    if not count_str:
        return 0
    count_str = str(count_str).replace(',', '')
    if 'M' in count_str or 'm' in count_str:
        return float(count_str.replace('M', '').replace('m', '')) * 1000000
    elif 'K' in count_str or 'k' in count_str:
        return float(count_str.replace('K', '').replace('k', '')) * 1000
    elif 'B' in count_str or 'b' in count_str:
        return float(count_str.replace('B', '').replace('b', '')) * 1000000000
    else:
        try:
            return float(count_str)
        except:
            return 0

def search_with_browser(browser_name, queries, existing_usernames):
    """Search using a specific browser"""
    global all_profiles

    profile = get_browser_profile(browser_name)
    if not profile:
        log(f"[{browser_name}] Could not find browser profile")
        return

    user_id = profile.get("user_id")
    log(f"[{browser_name}] Starting...")

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
        log(f"[{browser_name}] Opening browser...")
        browser_info = open_browser(user_id)
        if not browser_info:
            log(f"[{browser_name}] Failed to open browser")
            return
        time.sleep(3)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        log(f"[{browser_name}] No WebSocket endpoint")
        return

    skip_words = {'follow', 'following', 'followers', 'likes', 'videos', 'share', 'message',
                  'search', 'users', 'top', 'accounts', 'live', 'shop', 'explore', 'inbox',
                  'upload', 'profile', 'more', 'login', 'signup', 'home', 'trending',
                  'discover', 'company', 'program', 'terms', 'privacy', 'creator', 'business',
                  'effect', 'hashtag', 'sound', 'log', 'out', 'settings', 'help', 'feedback'}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.new_page()

            for query in queries:
                log(f"[{browser_name}] Searching: '{query}'")

                try:
                    search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
                    page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)

                    # Click Users tab
                    try:
                        page.click("text=Users", timeout=5000)
                        time.sleep(3)
                    except:
                        pass

                    # Scroll
                    for _ in range(30):
                        page.evaluate("window.scrollBy(0, 1000)")
                        time.sleep(0.3)
                    time.sleep(2)

                    # Extract
                    body_text = page.locator("body").inner_text()
                    lines = body_text.split('\n')
                    lines = [l.strip() for l in lines if l.strip()]

                    found_count = 0
                    for i, line in enumerate(lines):
                        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._]{1,23}$', line) and ' ' not in line:
                            username = line.lower()

                            if username in skip_words:
                                continue

                            with lock:
                                if username in existing_usernames or username in all_profiles:
                                    continue

                            try:
                                next_lines = lines[i+1:i+6]
                                next_text = ' '.join(next_lines)

                                follower_match = re.search(r'([\d,.]+[KMB]?)\s*Followers?', next_text)
                                if follower_match:
                                    follower_count = follower_match.group(1)
                                    follower_num = parse_followers(follower_count)

                                    if follower_num < 4000:
                                        continue

                                    with lock:
                                        all_profiles[username] = {
                                            "username": username,
                                            "profile_url": f"https://www.tiktok.com/@{username}",
                                            "follower_count": follower_count,
                                            "found_in_query": query
                                        }
                                        existing_usernames.add(username)

                                    log(f"  [{browser_name}] @{username}: {follower_count} followers")
                                    found_count += 1
                            except:
                                pass

                    log(f"  [{browser_name}] Found {found_count} new profiles")

                except Exception as e:
                    log(f"  [{browser_name}] Error: {e}")

                time.sleep(2)

            page.close()

    except Exception as e:
        log(f"[{browser_name}] Error: {e}")

def save_results():
    global all_profiles

    results = list(all_profiles.values())
    results.sort(key=lambda x: parse_followers(x.get("follower_count", "0")), reverse=True)

    with open("minnesota_tiktok_profiles.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("minnesota_tiktok_profiles.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "profile_url", "follower_count", "found_in_query"])
        writer.writeheader()
        writer.writerows(results)

    log(f"\nSaved {len(results)} profiles to files")

def main():
    global all_profiles

    log("=" * 60)
    log("  Parallel TikTok Search (2 browsers)")
    log("=" * 60)

    # Load existing data
    existing_usernames = set()
    if os.path.exists("minnesota_tiktok_profiles.json"):
        try:
            with open("minnesota_tiktok_profiles.json", "r") as f:
                existing = json.load(f)
                for item in existing:
                    all_profiles[item["username"]] = item
                    existing_usernames.add(item["username"])
            log(f"Loaded {len(all_profiles)} existing profiles")
        except:
            pass

    # Start both browsers in parallel threads
    thread1 = threading.Thread(target=search_with_browser, args=("tt46", QUERIES_BROWSER1, existing_usernames))
    thread2 = threading.Thread(target=search_with_browser, args=("tt47", QUERIES_BROWSER2, existing_usernames))

    thread1.start()
    thread2.start()

    # Wait for both to complete
    thread1.join()
    thread2.join()

    # Save final results
    save_results()

    log("\n" + "=" * 60)
    log(f"  Complete! Total: {len(all_profiles)} profiles with 4000+ followers")
    log("=" * 60)

if __name__ == "__main__":
    main()
