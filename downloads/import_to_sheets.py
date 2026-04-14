#!/usr/bin/env python3
"""
Import CSV to Google Sheets using browser - File > Import method
"""

import asyncio
import os
import requests
from playwright.async_api import async_playwright

ADSPOWER_API = "http://local.adspower.net:50325"
BROWSER_NAME = "tt46"
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
    log("Import CSV to Google Sheets via browser")
    log(f"CSV file: {CSV_PATH}")

    # Check CSV exists
    if not os.path.exists(CSV_PATH):
        log("CSV file not found!")
        return

    # Count rows
    with open(CSV_PATH, 'r') as f:
        row_count = sum(1 for _ in f)
    log(f"CSV has {row_count} rows")

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

        # Navigate to Google Sheet
        log("Opening Google Sheet...")
        await page.goto(SHEET_URL, wait_until='load', timeout=90000)
        await asyncio.sleep(8)

        # Click on Youtube tab
        log("Clicking Youtube tab...")
        try:
            await page.click("text=Youtube", timeout=8000)
            await asyncio.sleep(2)
        except:
            log("Youtube tab click failed, may already be selected")

        # Use File menu to Import
        log("Opening File menu...")
        try:
            # Click File menu
            await page.click('text="File"', timeout=5000)
            await asyncio.sleep(1)

            # Click Import
            log("Clicking Import...")
            await page.click('text="Import"', timeout=5000)
            await asyncio.sleep(2)

            # Click Upload tab
            log("Clicking Upload tab...")
            await page.click('text="Upload"', timeout=5000)
            await asyncio.sleep(1)

            # Upload the file
            log("Uploading CSV file...")
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(CSV_PATH)
                await asyncio.sleep(5)

                # Wait for import options and select "Replace current sheet"
                log("Selecting import options...")
                try:
                    await page.click('text="Replace current sheet"', timeout=5000)
                except:
                    pass

                # Click Import data button
                log("Clicking Import data...")
                try:
                    await page.click('text="Import data"', timeout=5000)
                    await asyncio.sleep(3)
                    log("Import complete!")
                except:
                    log("Could not find Import data button")
            else:
                log("Could not find file input")

        except Exception as e:
            log(f"Import failed: {e}")
            log("Trying alternative: direct cell input...")

            # Alternative: Go to A2 and type data row by row
            await page.keyboard.press("Escape")
            await asyncio.sleep(1)

            # Read CSV and input data
            import csv
            with open(CSV_PATH, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)

            # Click on cell A2
            log("Going to cell A2...")
            await page.keyboard.press("Control+Home")
            await asyncio.sleep(0.5)
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)

            # Type each row (skip header, limit for testing)
            log(f"Typing {min(len(rows)-1, 50)} rows...")
            for i, row in enumerate(rows[1:51]):  # Skip header, do first 50 rows
                for j, cell in enumerate(row):
                    cell_text = str(cell)[:200].replace('\n', ' ').replace('\t', ' ')
                    await page.keyboard.type(cell_text)
                    if j < len(row) - 1:
                        await page.keyboard.press("Tab")
                await page.keyboard.press("Enter")
                if (i + 1) % 10 == 0:
                    log(f"  Typed {i + 1} rows...")
                await asyncio.sleep(0.1)

            log("Typing complete!")

        await asyncio.sleep(3)
        log("Done! Check the Google Sheet.")
        await page.close()

if __name__ == "__main__":
    asyncio.run(main())
