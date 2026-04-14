#!/usr/bin/env python3
"""
Find Minnesota Profiles and Extract TikTok Usernames
Searches all AdsPower profiles for Minnesota-based proxies and gets their TikTok usernames
"""

import requests
import json
import time
import csv

ADSPOWER_API = "http://localhost:50325"
PROFILE_MAPPING_FILE = "tiktok_profile_mapping.json"


def get_all_profiles():
    """Get all profiles from AdsPower"""
    profiles = []
    page = 1
    while True:
        try:
            resp = requests.get(
                f"{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100",
                timeout=10
            )
            data = resp.json()
            if data.get("code") != 0:
                time.sleep(1)
                continue
            batch = data.get("data", {}).get("list", [])
            if not batch:
                break
            profiles.extend(batch)
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"Error: {e}")
            break
    return profiles


def get_profile_details(user_id):
    """Get detailed profile information including proxy"""
    try:
        resp = requests.get(
            f"{ADSPOWER_API}/api/v1/user/detail?user_id={user_id}",
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {})
        return None
    except:
        return None


def get_profile_cookies(user_id):
    """Get cookies for a profile"""
    try:
        resp = requests.get(
            f"{ADSPOWER_API}/api/v2/browser-profile/cookies?profile_id={user_id}",
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0 and data.get("data", {}).get("cookies"):
            cookies_str = data["data"]["cookies"]
            if cookies_str:
                return json.loads(cookies_str)
        return []
    except:
        return []


def extract_tiktok_username(cookies):
    """Extract TikTok username from cookies"""
    # Look for username in cookies
    for cookie in cookies:
        name = cookie.get("name", "")
        value = cookie.get("value", "")

        # TikTok sometimes stores username in a cookie
        if name == "tt_webid_v2" or name == "sessionid":
            # We need to make an API call to get the actual username
            # For now, just check if logged in
            if name == "sessionid" and value:
                return True
    return False


def get_username_from_mapping(browser_name):
    """Get TikTok username from tiktok_profile_mapping.json"""
    try:
        with open(PROFILE_MAPPING_FILE, "r") as f:
            mapping = json.load(f)
            return mapping.get(browser_name)
    except:
        return None


def check_proxy_location(proxy_config):
    """Check if proxy is in Minnesota"""
    if not proxy_config:
        return False, None

    proxy_soft = proxy_config.get("proxy_soft", "")
    proxy_type = proxy_config.get("proxy_type", "")
    proxy_host = proxy_config.get("proxy_host", "")
    proxy_port = proxy_config.get("proxy_port", "")
    proxy_user = proxy_config.get("proxy_user", "")

    # Check if there's proxy info
    if not proxy_host:
        return False, None

    # Try to get location from IP geolocation
    try:
        resp = requests.get(
            f"https://ipapi.co/{proxy_host}/json/",
            timeout=5
        )
        data = resp.json()
        region = data.get("region", "")
        city = data.get("city", "")
        country = data.get("country_name", "")

        # Check if Minnesota
        is_minnesota = "minnesota" in region.lower() or "mn" in region.lower()
        location = f"{city}, {region}, {country}" if city else f"{region}, {country}"

        return is_minnesota, location
    except:
        return False, None


def main():
    print("=" * 60)
    print("  Find Minnesota Profiles")
    print("=" * 60)
    print()

    # Get all profiles
    print("Fetching all profiles...")
    profiles = get_all_profiles()
    print(f"Found {len(profiles)} total profiles")
    print()

    # Load existing username mapping
    print("Loading TikTok username mapping...")
    try:
        with open(PROFILE_MAPPING_FILE, "r") as f:
            username_mapping = json.load(f)
        print(f"Loaded {len(username_mapping)} usernames from mapping file")
    except:
        username_mapping = {}
        print("No mapping file found")
    print()

    # Search for Minnesota profiles
    print("Searching for Minnesota profiles...")
    print()

    minnesota_profiles = []

    for i, profile in enumerate(profiles):
        user_id = profile.get("user_id")
        name = profile.get("name", user_id)

        print(f"[{i+1}/{len(profiles)}] Checking {name}...", end=" ", flush=True)

        # Get detailed profile info
        details = get_profile_details(user_id)
        if not details:
            print("✗ Could not fetch details")
            continue

        # Check proxy location
        proxy_config = details.get("user_proxy_config", {})
        is_minnesota, location = check_proxy_location(proxy_config)

        if is_minnesota:
            print(f"✓ MINNESOTA - {location}")

            # Get TikTok username
            tiktok_username = username_mapping.get(name)

            if not tiktok_username:
                # Try to get from cookies
                cookies = get_profile_cookies(user_id)
                has_session = extract_tiktok_username(cookies)
                if has_session:
                    tiktok_username = "Logged in (username unknown)"

            minnesota_profiles.append({
                "browser_name": name,
                "user_id": user_id,
                "location": location,
                "tiktok_username": tiktok_username or "Not logged in",
                "proxy_host": proxy_config.get("proxy_host", ""),
            })
        else:
            if location:
                print(f"✗ {location}")
            else:
                print("✗ No proxy")

        time.sleep(0.2)

    print()
    print("=" * 60)
    print(f"  Found {len(minnesota_profiles)} Minnesota profiles")
    print("=" * 60)
    print()

    if minnesota_profiles:
        # Display results
        print("Minnesota Profiles:")
        print()
        for profile in minnesota_profiles:
            print(f"Browser: {profile['browser_name']}")
            print(f"  Location: {profile['location']}")
            print(f"  TikTok Username: {profile['tiktok_username']}")
            print(f"  Proxy: {profile['proxy_host']}")
            print()

        # Save to JSON
        json_file = "minnesota_profiles.json"
        with open(json_file, "w") as f:
            json.dump(minnesota_profiles, f, indent=2)
        print(f"Saved to {json_file}")

        # Save to CSV
        csv_file = "minnesota_profiles.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["browser_name", "tiktok_username", "location", "proxy_host", "user_id"])
            writer.writeheader()
            writer.writerows(minnesota_profiles)
        print(f"Saved to {csv_file}")
        print()

        # Summary
        print("Summary:")
        with_usernames = sum(1 for p in minnesota_profiles if p["tiktok_username"] not in ["Not logged in", "Logged in (username unknown)"])
        print(f"  {with_usernames}/{len(minnesota_profiles)} profiles have known TikTok usernames")
    else:
        print("No Minnesota profiles found")


if __name__ == "__main__":
    main()
