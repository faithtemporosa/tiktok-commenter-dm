#!/usr/bin/env python3
"""
Search TikTok for Minnesota profiles using multiple browsers in parallel
"""

import requests
import json
import time
import csv
import sys
import os
from playwright.sync_api import sync_playwright
import threading
from queue import Queue

ADSPOWER_API = "http://localhost:50325"
SEARCH_QUERIES = [
    "Minnesota",
    "Minnesota life",
    "Minnesota girl",
    "Minnesota boy",
    "Minnesota TikTok",
    "Minnesota creator",
    "Minnesota influencer",
    "Minnesota vibes",
    "Minnesota small business",
    "Minnesota mom",
    "Minnesota dad",
    "Minnesota fitness",
    "Minnesota food",
    "Minnesota fashion",
    "Minnesota comedy",
    "Minnesota outdoors",
    "Minnesota family",
    "Minnesota travel",
    "Minnesota lifestyle",
    "Minnesota content creator",
]

# Shared results dictionary with lock for thread safety
results_lock = threading.Lock()
all_profiles = {}


def get_browsers_with_session(count=2):
    """Get multiple AdsPower browsers that have active TikTok sessions"""
    try:
        # Get all profiles
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/user/list?page=1&page_size=500",
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            profiles = data.get("data", {}).get("list", [])

            # Use specific browsers: tt24 and tt25
            browsers_with_sessions = []
            for profile in profiles:
                name = profile.get("name", "")
                if name in ["tt24", "tt25"]:
                    browsers_with_sessions.append(profile)
                    if len(browsers_with_sessions) >= count:
                        break

            return browsers_with_sessions[:count]
        return []
    except:
        return []


def open_browser(user_id):
    """Open an AdsPower browser"""
    try:
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}&open_tabs=0",
            timeout=60
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {})
        return None
    except:
        return None


def get_profile_info(page, username):
    """Visit profile page and extract follower count"""
    try:
        profile_url = f"https://www.tiktok.com/@{username}"
        page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # Extract follower count - try multiple selectors
        try:
            # Wait for content to load
            page.wait_for_selector("div[data-e2e='user-page']", timeout=5000)
        except:
            pass

        follower_text = "Unknown"

        try:
            # Method 1: data-e2e attribute
            follower_elem = page.locator("strong[data-e2e='followers-count']").first
            if follower_elem.is_visible(timeout=2000):
                follower_text = follower_elem.inner_text()
                return profile_url, follower_text
        except:
            pass

        try:
            # Method 2: Look for the followers text pattern
            # TikTok shows like "123.4K Followers"
            all_text = page.content()
            import re
            # Match patterns like "1.2M", "123.4K", "1234" followed by "Followers"
            match = re.search(r'([\d.]+[KMB]?)\s*(?:Followers|followers)', all_text)
            if match:
                follower_text = match.group(1)
                return profile_url, follower_text
        except:
            pass

        try:
            # Method 3: Look for any strong tags near "Followers" text
            followers_section = page.locator("text=/Followers/i").first
            if followers_section.is_visible(timeout=2000):
                # Get parent element and find strong tag
                parent = followers_section.locator("xpath=..")
                strong_tags = parent.locator("strong").all()
                for strong in strong_tags:
                    text = strong.inner_text().strip()
                    if text and not text.lower() == "followers":
                        follower_text = text
                        return profile_url, follower_text
        except:
            pass

        return profile_url, follower_text

    except Exception as e:
        return f"https://www.tiktok.com/@{username}", "Unknown"


def search_tiktok_users(browser_info, browser_name, query, max_results=100):
    """Search TikTok for users and extract usernames with follower counts"""

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print(f"[{browser_name}] No WebSocket endpoint found", flush=True)
        return []

    profiles = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to TikTok search
            search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
            print(f"[{browser_name}] → Opening: {search_url}", flush=True)
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            time.sleep(5)

            # Click on "Users" tab
            print(f"[{browser_name}] → Clicking 'Users' tab...", flush=True)
            try:
                page.click("text=Users", timeout=5000)
                time.sleep(3)
            except:
                print(f"[{browser_name}] ⚠ Could not find Users tab", flush=True)

            # Scroll to load more results
            print(f"[{browser_name}] → Scrolling...", flush=True)
            for _ in range(20):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(0.5)

            # Extract usernames
            print(f"[{browser_name}] → Extracting usernames...", flush=True)
            links = page.locator("a[href*='/@']").all()
            usernames_found = []

            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "/@" in href:
                        username = href.split("/@")[1].split("?")[0].split("/")[0]

                        # Check if already in global results
                        with results_lock:
                            if username and username not in all_profiles and username not in usernames_found:
                                usernames_found.append(username)
                except:
                    continue

            # Visit each profile to get follower count
            for i, username in enumerate(usernames_found[:max_results]):
                if len(profiles) >= max_results:
                    break

                print(f"[{browser_name}] [{i+1}/{min(len(usernames_found), max_results)}] @{username}...", end=" ", flush=True)

                profile_url, follower_count = get_profile_info(page, username)

                profile_data = {
                    "username": username,
                    "profile_url": profile_url,
                    "follower_count": follower_count,
                    "found_in_query": query
                }

                profiles.append(profile_data)

                # Add to global results
                with results_lock:
                    all_profiles[username] = profile_data

                print(f"{follower_count} followers", flush=True)
                time.sleep(1)

            print(f"[{browser_name}] → Extracted {len(profiles)} profiles", flush=True)

    except Exception as e:
        print(f"[{browser_name}] ✗ Error: {e}", flush=True)

    return profiles


def save_results():
    """Save results to files"""
    with results_lock:
        if not all_profiles:
            return

        results = list(all_profiles.values())

        # Sort by follower count
        def parse_follower_count(count_str):
            if count_str == "Unknown":
                return 0
            try:
                count_str = count_str.strip()
                if "M" in count_str:
                    return float(count_str.replace("M", "")) * 1000000
                elif "K" in count_str:
                    return float(count_str.replace("K", "")) * 1000
                else:
                    return float(count_str)
            except:
                return 0

        results.sort(key=lambda x: parse_follower_count(x["follower_count"]), reverse=True)

        # Save to JSON
        with open("minnesota_tiktok_profiles.json", "w") as f:
            json.dump(results, f, indent=2)

        # Save to CSV
        with open("minnesota_tiktok_profiles.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username", "profile_url", "follower_count", "found_in_query"])
            writer.writeheader()
            writer.writerows(results)

        # Save just usernames
        with open("minnesota_usernames.txt", "w") as f:
            for user in results:
                f.write(f"@{user['username']}\n")


def worker_thread(browser_info, browser_name, query_queue, target_profiles):
    """Worker thread that processes search queries"""
    while True:
        try:
            query = query_queue.get(block=False)
        except:
            break

        # Check if we've reached target
        with results_lock:
            if len(all_profiles) >= target_profiles:
                print(f"[{browser_name}] Target reached, stopping", flush=True)
                break

        print(f"\n[{browser_name}] Searching for: '{query}'", flush=True)
        with results_lock:
            current_count = len(all_profiles)
        print(f"[{browser_name}] Current total: {current_count}/{target_profiles}", flush=True)

        search_tiktok_users(browser_info, browser_name, query, max_results=100)

        # Save after each query
        save_results()

        with results_lock:
            total = len(all_profiles)
        print(f"[{browser_name}] Total profiles now: {total}/{target_profiles}", flush=True)

        time.sleep(2)


def main():
    global all_profiles

    print("=" * 60, flush=True)
    print("  Search TikTok for Minnesota Profiles (Parallel)", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Load existing results
    if os.path.exists("minnesota_tiktok_profiles.json"):
        try:
            with open("minnesota_tiktok_profiles.json", "r") as f:
                existing = json.load(f)
                for item in existing:
                    all_profiles[item["username"]] = item
            print(f"Loaded {len(all_profiles)} existing profiles", flush=True)
        except:
            pass

    # Get browsers
    print("\nGetting browsers with active TikTok sessions...", flush=True)
    browsers = get_browsers_with_session(count=2)

    if len(browsers) < 2:
        print(f"Only found {len(browsers)} browsers with sessions, need 2", flush=True)
        return

    print(f"Using browsers: {browsers[0].get('name')}, {browsers[1].get('name')}", flush=True)
    print(flush=True)

    # Check which browsers are already open
    browser_infos = []
    for browser_profile in browsers:
        user_id = browser_profile.get("user_id")
        name = browser_profile.get("name")

        # Check if already open
        browser_info = None
        try:
            resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                active_browsers = data.get("data", {}).get("list", [])
                for active in active_browsers:
                    if active.get("user_id") == user_id:
                        browser_info = active
                        print(f"{name} already open", flush=True)
                        break
        except:
            pass

        # Open if not already open
        if not browser_info:
            print(f"Opening {name}...", flush=True)
            browser_info = open_browser(user_id)
            if not browser_info:
                print(f"Failed to open {name}", flush=True)
                return
            time.sleep(3)

        browser_infos.append((browser_info, name))

    print(flush=True)

    # Create query queue
    query_queue = Queue()
    for query in SEARCH_QUERIES:
        query_queue.put(query)

    target_profiles = 1000

    # Start worker threads
    threads = []
    for browser_info, name in browser_infos:
        thread = threading.Thread(
            target=worker_thread,
            args=(browser_info, name, query_queue, target_profiles)
        )
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Display results
    print("\n" + "=" * 60, flush=True)
    print(f"  Found {len(all_profiles)} unique Minnesota profiles", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    if all_profiles:
        save_results()

        # Sort for display
        results = list(all_profiles.values())
        def parse_follower_count(count_str):
            if count_str == "Unknown":
                return 0
            try:
                count_str = count_str.strip()
                if "M" in count_str:
                    return float(count_str.replace("M", "")) * 1000000
                elif "K" in count_str:
                    return float(count_str.replace("K", "")) * 1000
                else:
                    return float(count_str)
            except:
                return 0
        results.sort(key=lambda x: parse_follower_count(x["follower_count"]), reverse=True)

        # Display top 20
        print("Top 20 profiles by followers:", flush=True)
        for i, user in enumerate(results[:20]):
            print(f"  {i+1}. @{user['username']} - {user['follower_count']} followers", flush=True)

        if len(results) > 20:
            print(f"  ... and {len(results) - 20} more", flush=True)
        print(flush=True)

        print(f"Saved to minnesota_tiktok_profiles.json", flush=True)
        print(f"Saved to minnesota_tiktok_profiles.csv", flush=True)
        print(f"Saved usernames to minnesota_usernames.txt", flush=True)

        # Summary stats
        print(flush=True)
        print("Summary:", flush=True)
        print(f"  Total profiles: {len(results)}", flush=True)
        with_follower_data = sum(1 for r in results if r["follower_count"] != "Unknown")
        print(f"  Profiles with follower data: {with_follower_data}", flush=True)
    else:
        print("No profiles found", flush=True)


if __name__ == "__main__":
    main()
