#!/usr/bin/env python3
"""
Update proxies only for browsers listed in not_logged_in_browsers.json.
"""

import json
import os
import random
import sys
import time
from datetime import datetime

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADSPOWER_API = "http://local.adspower.net:50325"
NOT_LOGGED_IN_FILE = os.path.join(BASE_DIR, "not_logged_in_browsers.json")
PROXY_FILE = os.path.join(BASE_DIR, "webshare_proxies_fresh.txt")
RESULT_FILE = os.path.join(BASE_DIR, "not_logged_in_proxy_updates.json")


def load_not_logged_in_profiles():
    with open(NOT_LOGGED_IN_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = []
    seen = set()
    for item in data.get("browsers", []):
        profile = (item.get("profile") or "").strip()
        if profile and profile not in seen:
            profiles.append(profile)
            seen.add(profile)
    return profiles


def load_proxies():
    proxies = []
    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 4:
                proxies.append({
                    "host": parts[0],
                    "port": parts[1],
                    "user": parts[2],
                    "password": parts[3],
                })
    return proxies


def get_all_browsers():
    browsers = []
    page = 1
    page_size = 100

    while True:
        try:
            time.sleep(0.8)
            resp = requests.get(
                f"{ADSPOWER_API}/api/v1/user/list",
                params={"page": page, "page_size": page_size},
                timeout=30,
            )
            data = resp.json()

            if data.get("code") != 0:
                msg = data.get("msg", "")
                if "Too many" in msg:
                    print("  Rate limited, waiting 3 seconds...")
                    time.sleep(3)
                    continue
                print(f"  AdsPower error: {msg}")
                break

            page_list = data.get("data", {}).get("list", [])
            if not page_list:
                break

            browsers.extend(page_list)
            print(f"  Loaded page {page}: {len(page_list)} browsers (total: {len(browsers)})")

            if len(page_list) < page_size:
                break
            page += 1

        except Exception as e:
            print(f"  Error loading browser page {page}: {e}")
            break

    return browsers


def update_browser_proxy(user_id, proxy, retries=3):
    proxy_config = {
        "proxy_soft": "other",
        "proxy_type": "http",
        "proxy_host": proxy["host"],
        "proxy_port": proxy["port"],
        "proxy_user": proxy["user"],
        "proxy_password": proxy["password"],
    }

    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{ADSPOWER_API}/api/v1/user/update",
                json={"user_id": user_id, "user_proxy_config": proxy_config},
                timeout=30,
            )
            data = resp.json()

            if data.get("code") == 0:
                return True, ""

            msg = data.get("msg", "Unknown error")
            if "Too many" in msg and attempt < retries - 1:
                time.sleep(2.5)
                continue
            return False, msg
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5)
                continue
            return False, str(e)

    return False, "Max retries exceeded"


def main():
    print("=" * 72)
    print("TARGETED PROXY UPDATE - Not Logged In Browsers Only")
    print("=" * 72)

    target_profiles = load_not_logged_in_profiles()
    print(f"Target profiles from not_logged_in_browsers.json: {len(target_profiles)}")

    proxies = load_proxies()
    print(f"Fresh proxies loaded: {len(proxies)}")
    if not proxies:
        print("No proxies found. Stopping.")
        return 1

    random.shuffle(proxies)

    print("Loading AdsPower browsers...")
    browsers = get_all_browsers()
    browsers_by_name = {b.get("name", "").strip(): b for b in browsers if b.get("name")}
    print(f"AdsPower browsers loaded: {len(browsers_by_name)}")

    missing = [name for name in target_profiles if name not in browsers_by_name]
    targets = [browsers_by_name[name] for name in target_profiles if name in browsers_by_name]

    if missing:
        print(f"Missing in AdsPower: {len(missing)}")
        print("  " + ", ".join(missing[:25]) + (" ..." if len(missing) > 25 else ""))

    print()
    print(f"Updating {len(targets)} browser proxies...")
    print("=" * 72)

    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_count": len(target_profiles),
        "matched_count": len(targets),
        "missing": missing,
        "updated": [],
        "failed": [],
    }

    for i, browser in enumerate(targets):
        name = browser.get("name", "Unknown")
        user_id = browser.get("user_id")
        proxy = proxies[i % len(proxies)]

        ok, msg = update_browser_proxy(user_id, proxy)
        if ok:
            results["updated"].append({
                "profile": name,
                "user_id": user_id,
                "proxy": f"{proxy['host']}:{proxy['port']}",
            })
            print(f"✓ [{i + 1}/{len(targets)}] {name:16} -> {proxy['host']}:{proxy['port']}")
        else:
            results["failed"].append({
                "profile": name,
                "user_id": user_id,
                "error": msg,
            })
            print(f"✗ [{i + 1}/{len(targets)}] {name:16} FAILED - {msg}")

        time.sleep(0.35)

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("=" * 72)
    print(f"COMPLETE: {len(results['updated'])} updated, {len(results['failed'])} failed")
    print(f"Result file: {RESULT_FILE}")
    print("=" * 72)
    return 0 if not results["failed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
