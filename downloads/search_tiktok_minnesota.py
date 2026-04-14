#!/usr/bin/env python3
"""
Search TikTok for Minnesota profiles and extract usernames
Uses Playwright to automate TikTok search
"""

import requests
import json
import time
import csv
import sys
import os
import re
from playwright.sync_api import sync_playwright

ADSPOWER_API = "http://localhost:50325"
SEARCH_QUERIES = [
    # General Minnesota
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
    # Cities
    "Minneapolis",
    "Minneapolis TikTok",
    "St Paul Minnesota",
    "Duluth Minnesota",
    "Rochester Minnesota",
    "Bloomington Minnesota",
    "Brooklyn Park Minnesota",
    "Plymouth Minnesota",
    "Maple Grove Minnesota",
    "Woodbury Minnesota",
    "Eden Prairie Minnesota",
    "St Cloud Minnesota",
    "Mankato Minnesota",
    "Moorhead Minnesota",
    # Specific interests
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
    # Abbreviations people use
    "MN TikTok",
    "MN creator",
    "MN life",
    "MN mom",
    "MN dad",
    "MPLS",
    "Twin Cities",
    "Twin Cities TikTok",
]


def get_browser_with_session(preferred_names=None):
    """Get an AdsPower browser that has an active TikTok session"""
    if preferred_names is None:
        preferred_names = ["tt46", "tt47"]

    try:
        # Get all profiles
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/user/list?page=1&page_size=500",
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            profiles = data.get("data", {}).get("list", [])

            # Find preferred browsers
            for name in preferred_names:
                for profile in profiles:
                    if profile.get("name") == name:
                        return profile

            # Fallback to first available if not found
            if profiles:
                return profiles[0]
        return None
    except:
        return None


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


def close_browser(user_id):
    """Close an AdsPower browser"""
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}", timeout=10)
    except:
        pass


def get_profile_info(page, username):
    """Visit profile page and extract follower count using text parsing"""
    try:
        profile_url = f"https://www.tiktok.com/@{username}"
        page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)

        follower_text = None

        # Method 1: Parse page text for "X Followers" pattern
        # Profile pages show: "1 Following  13 Followers  54 Likes"
        try:
            body_text = page.locator("body").inner_text()

            # Look for pattern: number followed by Followers
            # Handles: "13 Followers", "1.2K Followers", "1.5M Followers"
            match = re.search(r'([\d,.]+[KMB]?)\s*Followers?', body_text)
            if match:
                follower_text = match.group(1)
        except:
            pass

        # Method 2: Try data-e2e attribute
        if not follower_text:
            try:
                follower_elements = page.locator("[data-e2e='followers-count']").all()
                if follower_elements:
                    follower_text = follower_elements[0].inner_text().strip()
            except:
                pass

        # Method 3: Regex search in HTML
        if not follower_text:
            try:
                page_content = page.content()
                match = re.search(r'>([\d,.]+[KkMm]?)<[^>]*>[^<]*Follower', page_content)
                if match:
                    follower_text = match.group(1)
            except:
                pass

        if follower_text:
            return profile_url, follower_text
        return profile_url, "Unknown"

    except Exception as e:
        print(f"      Error getting profile: {e}")
        return f"https://www.tiktok.com/@{username}", "Unknown"


def search_tiktok_users(browser_info, query, max_results=100, existing_usernames=None):
    """Search TikTok for users and extract usernames with follower counts from search results"""

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print("No WebSocket endpoint found")
        return []

    if existing_usernames is None:
        existing_usernames = set()

    profiles = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]

            # Create a new page to avoid conflicts with existing pages
            page = context.new_page()

            try:
                # Navigate to TikTok search
                search_url = f"https://www.tiktok.com/search?q={query.replace(' ', '%20')}"
                print(f"  → Opening: {search_url}", flush=True)
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)

                # Click on "Users" tab to search for accounts
                print("  → Clicking 'Users' tab...", flush=True)
                try:
                    page.click("text=Users", timeout=5000)
                    time.sleep(3)
                except:
                    print("  ⚠ Could not find Users tab, searching on main page", flush=True)

                # Scroll to load more results
                print("  → Scrolling to load results...", flush=True)
                for _ in range(30):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(0.3)
                time.sleep(2)

                # Extract usernames and follower counts using text parsing
                print("  → Extracting usernames and follower counts...", flush=True)

                # Get page text content
                body_text = page.locator("body").inner_text()
                lines = body_text.split('\n')
                lines = [l.strip() for l in lines if l.strip()]

                # Parse user cards from text
                # Format:
                # DisplayName
                # username
                # XXK
                # Followers
                # ·
                # XXK
                # Likes

                for i, line in enumerate(lines):
                    if len(profiles) >= max_results:
                        break

                    # Look for username pattern - TikTok usernames are flexible
                    # They can contain letters, numbers, underscores, dots
                    # Must be 2-24 chars, and line should look like a username (no spaces)
                    if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._]{1,23}$', line) and ' ' not in line:
                        username = line.lower()  # Normalize to lowercase

                        # Skip common non-username words and UI elements
                        skip_words = {'follow', 'following', 'followers', 'likes', 'videos', 'share', 'message',
                                      'search', 'users', 'top', 'accounts', 'live', 'shop', 'explore', 'inbox',
                                      'upload', 'profile', 'more', 'login', 'signup', 'home', 'trending',
                                      'discover', 'company', 'program', 'terms', 'privacy', 'creator', 'business',
                                      'effect', 'hashtag', 'sound', 'log', 'out', 'settings', 'help', 'feedback'}
                        if username in skip_words:
                            continue

                        # Skip if already processed
                        if username in existing_usernames:
                            continue

                        # Check if next lines have follower pattern
                        try:
                            next_lines = lines[i+1:i+6]
                            next_text = ' '.join(next_lines)

                            # Look for follower count
                            follower_match = re.search(r'([\d,.]+[KMB]?)\s*Followers?', next_text)
                            if follower_match:
                                follower_count = follower_match.group(1)

                                # Parse follower count to number
                                def parse_followers(count_str):
                                    count_str = count_str.replace(',', '')
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

                                follower_num = parse_followers(follower_count)

                                # Skip accounts with less than 4000 followers
                                if follower_num < 4000:
                                    continue

                                profiles.append({
                                    "username": username,
                                    "profile_url": f"https://www.tiktok.com/@{username}",
                                    "follower_count": follower_count
                                })
                                existing_usernames.add(username)
                                print(f"    @{username}: {follower_count} followers", flush=True)
                        except:
                            pass

                print(f"  → Extracted {len(profiles)} profiles with follower counts", flush=True)

            finally:
                # Close the page we created
                try:
                    page.close()
                except:
                    pass

    except Exception as e:
        print(f"  ✗ Error: {e}", flush=True)

    return profiles


def save_results(all_profiles):
    """Save results to files"""
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


def main():
    print("=" * 60, flush=True)
    print("  Search TikTok for Minnesota Profiles", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Get a browser with active TikTok session
    print("Getting AdsPower browser with active TikTok session...", flush=True)
    profile = get_browser_with_session()
    if not profile:
        print("Could not get browser profile", flush=True)
        return

    user_id = profile.get("user_id")
    profile_name = profile.get("name", user_id)
    print(f"Using browser: {profile_name}", flush=True)
    print(flush=True)

    # Load existing results if any
    all_profiles = {}
    if os.path.exists("minnesota_tiktok_profiles.json"):
        try:
            with open("minnesota_tiktok_profiles.json", "r") as f:
                existing = json.load(f)
                for item in existing:
                    all_profiles[item["username"]] = item
            print(f"Loaded {len(all_profiles)} existing profiles", flush=True)
        except:
            pass

    # Check if browser is already open
    browser_info = None
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            active_browsers = data.get("data", {}).get("list", [])
            for browser in active_browsers:
                if browser.get("user_id") == user_id:
                    browser_info = browser
                    print("Browser already open, using existing session", flush=True)
                    break
    except:
        pass

    # Open browser if not already open
    if not browser_info:
        print("Opening browser...", flush=True)
        browser_info = open_browser(user_id)
        if not browser_info:
            print("Failed to open browser", flush=True)
            return
        time.sleep(3)

    print(flush=True)

    # Search for each query until we get 1000 profiles
    target_profiles = 1000

    for query in SEARCH_QUERIES:
        if len(all_profiles) >= target_profiles:
            print(f"\nReached target of {target_profiles} profiles!", flush=True)
            break

        print(f"\nSearching for: '{query}'", flush=True)
        print(f"  Current count: {len(all_profiles)}/{target_profiles}", flush=True)

        # Search for up to 100 profiles per query
        profiles = search_tiktok_users(
            browser_info,
            query,
            max_results=100,
            existing_usernames=set(all_profiles.keys())
        )

        for profile in profiles:
            username = profile["username"]
            if username not in all_profiles:
                all_profiles[username] = {
                    "username": username,
                    "profile_url": profile["profile_url"],
                    "follower_count": profile["follower_count"],
                    "found_in_query": query
                }

        print(f"  Total profiles collected: {len(all_profiles)}/{target_profiles}", flush=True)

        # Save results after each query
        print(f"  Saving results...", flush=True)
        save_results(all_profiles)

        time.sleep(3)

    # Display results
    print("\n" + "=" * 60, flush=True)
    print(f"  Found {len(all_profiles)} unique Minnesota profiles", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    if all_profiles:
        # Final save
        save_results(all_profiles)

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


def rescrape_unknown():
    """Re-scrape profiles with Unknown follower counts"""
    print("=" * 60, flush=True)
    print("  Re-scraping profiles with Unknown follower counts", flush=True)
    print("=" * 60, flush=True)

    # Load existing data
    if not os.path.exists("minnesota_tiktok_profiles.json"):
        print("No existing data found", flush=True)
        return

    with open("minnesota_tiktok_profiles.json", "r") as f:
        all_profiles = json.load(f)

    # Find profiles with Unknown or 0 follower counts
    unknown_profiles = [p for p in all_profiles if p.get("follower_count") in ["Unknown", "0", 0]]
    print(f"Found {len(unknown_profiles)} profiles with Unknown/0 follower counts", flush=True)

    if not unknown_profiles:
        print("All profiles have follower data!", flush=True)
        return

    # Get browser
    profile = get_browser_with_session()
    if not profile:
        print("Could not get browser profile", flush=True)
        return

    user_id = profile.get("user_id")
    print(f"Using browser: {profile.get('name', user_id)}", flush=True)

    # Check if browser is already open
    browser_info = None
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for browser in data.get("data", {}).get("list", []):
                if browser.get("user_id") == user_id:
                    browser_info = browser
                    break
    except:
        pass

    if not browser_info:
        print("Opening browser...", flush=True)
        browser_info = open_browser(user_id)
        if not browser_info:
            print("Failed to open browser", flush=True)
            return
        time.sleep(3)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        print("No WebSocket endpoint found", flush=True)
        return

    updated = 0
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        for i, profile_data in enumerate(unknown_profiles):
            username = profile_data["username"]
            print(f"[{i+1}/{len(unknown_profiles)}] @{username}...", end=" ", flush=True)

            _, follower_count = get_profile_info(page, username)

            if follower_count != "Unknown":
                # Update in the main list
                for p in all_profiles:
                    if p["username"] == username:
                        p["follower_count"] = follower_count
                        break
                updated += 1
                print(f"✓ {follower_count}", flush=True)
            else:
                print("✗ Still unknown", flush=True)

            time.sleep(1.5)

            # Save every 10 profiles
            if (i + 1) % 10 == 0:
                save_results({p["username"]: p for p in all_profiles})
                print(f"  Saved progress... ({updated} updated so far)", flush=True)

    # Final save
    save_results({p["username"]: p for p in all_profiles})
    print(f"\nDone! Updated {updated} out of {len(unknown_profiles)} profiles", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rescrape":
        rescrape_unknown()
    else:
        main()
