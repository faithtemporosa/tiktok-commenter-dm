#!/usr/bin/env python3
"""
Extract TikTok credentials from all AdsPower profiles
"""

import requests
import json
import time
import csv

ADSPOWER_API = "http://localhost:50325"

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
            print(f"  Loaded page {page}: {len(batch)} profiles (total: {len(profiles)})")
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"Error: {e}")
            break
    return profiles


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
    except Exception as e:
        return []


def extract_tiktok_data(cookies):
    """Extract TikTok session data from cookies"""
    data = {
        "sessionid": None,
        "uid_tt": None,
        "csrf_token": None,
        "msToken": None,
    }

    for cookie in cookies:
        name = cookie.get("name", "")
        value = cookie.get("value", "")

        if name == "sessionid":
            data["sessionid"] = value
        elif name == "uid_tt":
            data["uid_tt"] = value
        elif name == "tt_csrf_token":
            data["csrf_token"] = value
        elif name == "msToken":
            data["msToken"] = value

    return data


def main():
    print("=" * 60)
    print("  Extract TikTok Credentials from AdsPower")
    print("=" * 60)
    print()

    # Get all profiles
    print("Fetching profiles...")
    profiles = get_all_profiles()
    print(f"Found {len(profiles)} profiles")
    print()

    # Extract credentials
    print("Extracting TikTok session data...")
    results = []

    for i, profile in enumerate(profiles):
        user_id = profile.get("user_id")
        name = profile.get("name", user_id)

        print(f"[{i+1}/{len(profiles)}] {name}...", end=" ", flush=True)

        cookies = get_profile_cookies(user_id)
        tiktok_data = extract_tiktok_data(cookies)

        result = {
            "profile_name": name,
            "user_id": user_id,
            "has_session": bool(tiktok_data["sessionid"]),
            "sessionid": tiktok_data["sessionid"],
            "uid_tt": tiktok_data["uid_tt"],
            "csrf_token": tiktok_data["csrf_token"],
            "msToken": tiktok_data["msToken"],
        }
        results.append(result)

        if tiktok_data["sessionid"]:
            print("✓ Logged in")
        else:
            print("✗ No session")

        time.sleep(0.1)

    print()

    # Save to JSON
    json_file = "tiktok_credentials.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {json_file}")

    # Save to CSV
    csv_file = "tiktok_credentials.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved to {csv_file}")

    # Summary
    logged_in = sum(1 for r in results if r["has_session"])
    print()
    print(f"Summary: {logged_in}/{len(results)} profiles have active TikTok sessions")


if __name__ == "__main__":
    main()
