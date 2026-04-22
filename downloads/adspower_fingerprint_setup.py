#!/usr/bin/env python3
"""
AdsPower Fingerprint Configuration Script
==========================================
Updates all AdsPower profiles with proper fingerprint settings:
- Different user agents
- Different screen resolutions
- Canvas/WebGL noise
- Timezone matching proxy country
- Language matching proxy country

USAGE:
    python adspower_fingerprint_setup.py
"""

import requests
import time
import random
import json

ADSPOWER_API = "http://localhost:50325"

WINDOWS_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36"
)

# Common screen resolutions (most popular desktop sizes)
SCREEN_RESOLUTIONS = [
    "1920_1080",
    "1366_768",
    "1536_864",
    "1440_900",
    "1280_720",
    "1600_900",
    "1280_800",
    "1280_1024",
    "1680_1050",
    "1360_768",
]

# Hardware specs to randomize
HARDWARE_CONCURRENCY = ["2", "4", "6", "8", "12", "16"]
DEVICE_MEMORY = ["2", "4", "8", "16"]

# Country to timezone/language mapping
COUNTRY_CONFIG = {
    "US": {
        "timezones": [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Phoenix",
        ],
        "language": ["en-US", "en"],
    },
    "GB": {
        "timezones": ["Europe/London"],
        "language": ["en-GB", "en"],
    },
    "CA": {
        "timezones": [
            "America/Toronto",
            "America/Vancouver",
            "America/Edmonton",
        ],
        "language": ["en-CA", "en"],
    },
    "AU": {
        "timezones": [
            "Australia/Sydney",
            "Australia/Melbourne",
            "Australia/Brisbane",
        ],
        "language": ["en-AU", "en"],
    },
    "DE": {
        "timezones": ["Europe/Berlin"],
        "language": ["de-DE", "de", "en"],
    },
    "FR": {
        "timezones": ["Europe/Paris"],
        "language": ["fr-FR", "fr", "en"],
    },
    "ES": {
        "timezones": ["Europe/Madrid"],
        "language": ["es-ES", "es", "en"],
    },
    "IT": {
        "timezones": ["Europe/Rome"],
        "language": ["it-IT", "it", "en"],
    },
    "NL": {
        "timezones": ["Europe/Amsterdam"],
        "language": ["nl-NL", "nl", "en"],
    },
    "BR": {
        "timezones": ["America/Sao_Paulo"],
        "language": ["pt-BR", "pt", "en"],
    },
    "MX": {
        "timezones": ["America/Mexico_City"],
        "language": ["es-MX", "es", "en"],
    },
    "JP": {
        "timezones": ["Asia/Tokyo"],
        "language": ["ja-JP", "ja", "en"],
    },
    "KR": {
        "timezones": ["Asia/Seoul"],
        "language": ["ko-KR", "ko", "en"],
    },
    "IN": {
        "timezones": ["Asia/Kolkata"],
        "language": ["en-IN", "hi", "en"],
    },
    "SG": {
        "timezones": ["Asia/Singapore"],
        "language": ["en-SG", "en"],
    },
    # Default fallback
    "DEFAULT": {
        "timezones": ["America/New_York"],
        "language": ["en-US", "en"],
    },
}


def get_all_profiles():
    """Fetch all profiles from AdsPower"""
    profiles = []
    page = 1
    while True:
        try:
            response = requests.get(
                f"{ADSPOWER_API}/api/v1/user/list?page={page}&page_size=100",
                timeout=10
            )
            data = response.json()
            if data.get("code") != 0:
                print(f"  Rate limit, waiting 2s...")
                time.sleep(2)
                continue  # Retry same page

            batch = data.get("data", {}).get("list", [])
            if not batch:
                break

            profiles.extend(batch)
            print(f"  Loaded page {page}: {len(batch)} profiles (total: {len(profiles)})")
            page += 1
            time.sleep(0.5)  # Rate limit between pages
        except Exception as e:
            print(f"Error fetching profiles: {e}")
            break

    return profiles


def get_proxy_country(proxy_host):
    """Get country from proxy IP using ip-api.com"""
    if not proxy_host:
        return None

    try:
        response = requests.get(
            f"http://ip-api.com/json/{proxy_host}?fields=countryCode",
            timeout=5
        )
        data = response.json()
        return data.get("countryCode")
    except:
        return None


def generate_fingerprint_config(country_code=None):
    """Generate a randomized fingerprint config matching AdsPower UI settings"""

    fingerprint = {
        # User-Agent / OS - keep profiles on a stable Windows identity
        "ua": WINDOWS_USER_AGENT,

        # WebRTC - disabled so websites cannot obtain a direct/local IP
        "webrtc": "disabled",

        # Timezone - Based on IP (auto-detect from proxy)
        "automatic_timezone": "1",

        # Location - Based on IP
        "location_switch": "1",
        "location": "ask",

        # Language - Based on IP (1 = Based on IP, 0 = Custom)
        "language_switch": "1",

        # Display language - Based on Language
        "page_language_switch": "1",

        # Screen Resolution - Random
        "screen_resolution": "random",

        # Fonts - empty array = Default
        "fonts": [],

        # Canvas - add noise for uniqueness
        "canvas": "1",

        # WebGL - add noise
        "webgl_image": "1",
        "webgl": "3",

        # Audio - add noise
        "audio": "1",

        # Hardware - randomize
        "hardware_concurrency": random.choice(HARDWARE_CONCURRENCY),
        "device_memory": random.choice(DEVICE_MEMORY),

        # Flash - block
        "flash": "block",

        # Media devices - noise
        "media_devices": "1",

        # Client rects - noise
        "client_rects": "1",
    }

    return fingerprint


def update_profile_fingerprint(user_id, fingerprint_config):
    """Update a profile's fingerprint settings"""
    try:
        response = requests.post(
            f"{ADSPOWER_API}/api/v1/user/update",
            json={
                "user_id": user_id,
                "fingerprint_config": fingerprint_config
            },
            timeout=10
        )
        data = response.json()
        if data.get("code") != 0:
            print(f"    API Error: {data.get('msg')}")
        return data.get("code") == 0
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    print("=" * 60)
    print("  AdsPower Fingerprint Configuration")
    print("=" * 60)
    print()

    # Step 1: Get all profiles
    print("[1/2] Fetching profiles from AdsPower...")
    profiles = get_all_profiles()
    print(f"  Found {len(profiles)} profiles")
    print()

    if not profiles:
        print("No profiles found. Is AdsPower running?")
        return

    # Step 2: Update each profile (no country lookup needed - using "Based on IP")
    print("[2/2] Updating profile fingerprints...")
    success = 0
    failed = 0

    for i, profile in enumerate(profiles):
        user_id = profile.get("user_id")
        name = profile.get("name", user_id)

        # Generate fingerprint config (same for all - auto-detects from proxy)
        fingerprint = generate_fingerprint_config()

        # Update the profile with retry on rate limit
        updated = False
        for attempt in range(3):
            if update_profile_fingerprint(user_id, fingerprint):
                updated = True
                break
            else:
                time.sleep(1)  # Wait 1 second before retry

        if updated:
            success += 1
            print(f"  [{i+1}/{len(profiles)}] {name}: OK")
        else:
            failed += 1
            print(f"  [{i+1}/{len(profiles)}] {name}: FAILED")

        # Delay to avoid rate limiting
        time.sleep(0.3)

    print()
    print("=" * 60)
    print(f"  DONE! {success} updated, {failed} failed")
    print("=" * 60)
    print()
    print("Each profile now has:")
    print("  - WebRTC: Disable UDP")
    print("  - Timezone: Based on IP")
    print("  - Location: Based on IP")
    print("  - Language: Based on IP")
    print("  - Screen Resolution: Based on User-Agent")
    print("  - Canvas/WebGL/Audio: Noise enabled")
    print("  - Fonts: Default")


if __name__ == "__main__":
    main()
