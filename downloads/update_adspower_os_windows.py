#!/usr/bin/env python3
"""
Update AdsPower browser profiles so their OS/fingerprint presents as Windows.

This intentionally does not send any proxy fields, so existing proxy settings are
left alone by AdsPower's update endpoint.
"""

import argparse
import json
import time
from pathlib import Path

import requests


ADSPOWER_BASE_URLS = (
    "http://local.adspower.net:50325",
    "http://localhost:50325",
)

WINDOWS_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36"
)

WINDOWS_FINGERPRINT = {
    "webrtc": "disabled",
    "automatic_timezone": "1",
    "language_switch": "1",
    "page_language_switch": "1",
    "ua": WINDOWS_USER_AGENT,
    "screen_resolution": "random",
    "fonts": [],
    "canvas": "1",
    "webgl_image": "1",
    "webgl": "3",
    "audio": "1",
    "hardware_concurrency": "8",
    "device_memory": "8",
    "flash": "block",
    "media_devices": "1",
    "client_rects": "1",
    "webgl_vendor": "Google Inc. (Intel)",
    "webgl_renderer": (
        "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"
    ),
}


def find_adspower_base_url(timeout=10):
    for base_url in ADSPOWER_BASE_URLS:
        try:
            payload = request_json(
                "GET",
                f"{base_url}/api/v1/user/list",
                params={"page": 1, "page_size": 1},
                timeout=timeout,
            )
            if payload.get("code") == 0:
                return base_url
        except Exception:
            continue
    raise RuntimeError("AdsPower local API is not reachable on port 50325")


def request_json(method, url, *, retries=6, **kwargs):
    for attempt in range(1, retries + 1):
        response = requests.request(method, url, **kwargs)
        payload = response.json()
        message = str(payload.get("msg", ""))
        if payload.get("code") != -1 or "Too many request" not in message:
            return payload

        wait_seconds = min(2 * attempt, 12)
        print(f"AdsPower rate limit hit, waiting {wait_seconds}s before retry {attempt}/{retries}")
        time.sleep(wait_seconds)

    return payload


def fetch_profiles(base_url, page_size=100, limit=None):
    profiles = []
    page = 1

    while True:
        payload = request_json(
            "GET",
            f"{base_url}/api/v1/user/list",
            params={"page": page, "page_size": page_size},
            timeout=30,
        )
        if payload.get("code") != 0:
            raise RuntimeError(f"AdsPower list failed: {payload}")

        batch = payload.get("data", {}).get("list", [])
        if not batch:
            break

        profiles.extend(batch)
        if limit and len(profiles) >= limit:
            return profiles[:limit]

        total = payload.get("data", {}).get("count")
        if total and len(profiles) >= int(total):
            break

        page += 1
        time.sleep(0.1)

    return profiles


def update_profile(base_url, profile):
    user_id = profile["user_id"]
    payload = {
        "user_id": user_id,
        "fingerprint_config": WINDOWS_FINGERPRINT,
    }

    result = request_json(
        "POST",
        f"{base_url}/api/v1/user/update",
        json=payload,
        timeout=30,
    )
    return result


def stop_profile(base_url, profile):
    user_id = profile["user_id"]
    return request_json(
        "GET",
        f"{base_url}/api/v1/browser/stop",
        params={"user_id": user_id},
        timeout=15,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Set all AdsPower profile OS/fingerprints to Windows."
    )
    parser.add_argument("--limit", type=int, default=None, help="Only update N profiles")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which profiles would be updated without changing them",
    )
    parser.add_argument(
        "--output",
        default="downloads/adspower_windows_os_updates.json",
        help="Write update results to this JSON file",
    )
    parser.add_argument(
        "--stop-first",
        action="store_true",
        help="Stop each AdsPower browser before updating its fingerprint",
    )
    args = parser.parse_args()

    base_url = find_adspower_base_url()
    profiles = fetch_profiles(base_url, limit=args.limit)
    print(f"AdsPower API: {base_url}")
    print(f"Profiles found: {len(profiles)}")

    results = []
    for index, profile in enumerate(profiles, start=1):
        name = profile.get("name") or profile.get("user_id")
        user_id = profile.get("user_id")

        if args.dry_run:
            print(f"[{index}/{len(profiles)}] DRY RUN {name} ({user_id}) -> Windows")
            results.append({"user_id": user_id, "name": name, "dry_run": True})
            continue

        try:
            stop_result = None
            if args.stop_first:
                stop_result = stop_profile(base_url, profile)
                time.sleep(0.2)

            result = update_profile(base_url, profile)
            ok = result.get("code") == 0
            status = "OK" if ok else "FAILED"
            print(f"[{index}/{len(profiles)}] {status} {name} ({user_id})")
            results.append(
                {
                    "user_id": user_id,
                    "name": name,
                    "ok": ok,
                    "stop_result": stop_result,
                    "result": result,
                }
            )
        except Exception as exc:
            print(f"[{index}/{len(profiles)}] ERROR {name} ({user_id}): {exc}")
            results.append(
                {
                    "user_id": user_id,
                    "name": name,
                    "ok": False,
                    "error": str(exc),
                }
            )

        time.sleep(0.15)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    if not args.dry_run:
        success_count = sum(1 for item in results if item.get("ok"))
        failure_count = len(results) - success_count
        print(f"Done. Updated: {success_count}. Failed: {failure_count}.")
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    main()
