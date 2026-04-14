#!/usr/bin/env python3
"""
Push YouTube CSV data to Google Sheets using browser automation
"""

import asyncio
import csv
import requests
from playwright.async_api import async_playwright

ADSPOWER_API = "http://local.adspower.net:50325"
BROWSER_NAME = "tt46"
# Direct link to the Youtube sheet tab (gid for Youtube tab)
SHEET_URL = "https://docs.google.com/spreadsheets/d/18IKNtGj-f_Kguds3K-0sHsWDHzsJ-n3CtdgjsOwlPF4/edit#gid=1744548982"
CSV_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/minnesota_youtube_profiles.csv"

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
    except Exception as e:
        log(f"Error getting profile: {e}")
    return None

def open_browser(user_id):
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}", timeout=60)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data")
    except Exception as e:
        log(f"Error opening browser: {e}")
    return None

async def main():
    log("Push YouTube data to Google Sheets")

    # Read CSV data
    log(f"Reading CSV: {CSV_PATH}")
    rows = []
    with open(CSV_PATH, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    log(f"Total rows: {len(rows)}")

    # Get browser
    profile = get_browser_profile(BROWSER_NAME)
    if not profile:
        log(f"Could not find browser profile: {BROWSER_NAME}")
        return

    user_id = profile.get("user_id")

    # Check if browser is already open
    browser_info = None
    try:
        resp = requests.get(f"{ADSPOWER_API}/api/v1/browser/local-active", timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            for b in data.get("data", {}).get("list", []):
                if b.get("user_id") == user_id:
                    browser_info = b
                    log("Using existing browser")
                    break
    except:
        pass

    if not browser_info:
        log("Opening browser...")
        browser_info = open_browser(user_id)
        if not browser_info:
            log("Failed to open browser")
            return
        await asyncio.sleep(3)

    ws_endpoint = browser_info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        log("No WebSocket endpoint")
        return

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0]
        page = await context.new_page()

        # Navigate to the Google Sheet (Youtube tab directly via gid)
        log("Opening Google Sheet (Youtube tab)...")
        await page.goto(SHEET_URL, wait_until='load', timeout=90000)
        await asyncio.sleep(10)

        # Double-click on the Youtube tab to ensure it's selected
        log("Ensuring Youtube tab is selected...")
        try:
            youtube_tab = page.locator("text=Youtube").first
            await youtube_tab.click(timeout=5000)
            await asyncio.sleep(2)
        except Exception as e:
            log(f"Tab click note: {e}")

        # Go to cell A1 first
        log("Going to cell A1...")
        await page.keyboard.press("Control+Home")
        await asyncio.sleep(1)

        # Prepare tab-separated data for pasting (include header)
        tsv_lines = []
        for row in rows:
            escaped_row = [str(cell).replace('\t', ' ').replace('\n', ' ') for cell in row]
            tsv_lines.append('\t'.join(escaped_row))
        tsv_data = '\n'.join(tsv_lines)

        log(f"Pasting {len(rows)} rows of data...")

        # Write to clipboard using CDP
        try:
            client = await context.new_cdp_session(page)
            await client.send('Browser.setClipboard', {
                'data': tsv_data,
                'dataType': 'text/plain'
            })
        except:
            # Fallback: use pyperclip if available
            try:
                import pyperclip
                pyperclip.copy(tsv_data)
            except:
                pass

        # Paste using keyboard shortcut
        await page.keyboard.press("Meta+v")  # Use Meta for Mac
        await asyncio.sleep(2)
        await page.keyboard.press("Control+v")  # Also try Control
        await asyncio.sleep(3)

        log("Paste command sent!")
        log("Please check the Google Sheet to verify the data.")

        # Keep page open for verification
        await asyncio.sleep(5)
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
