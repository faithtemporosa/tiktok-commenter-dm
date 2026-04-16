#!/usr/bin/env python3
"""
Test TikTok with your native Mac browser (not AdsPower)
This uses your real Mac's Chrome/Safari to see if views register
"""
import time
import random
from playwright.sync_api import sync_playwright

def test_native_browser(target_account="charlidamelio", use_mobile=True):
    """Test with native Mac browser"""

    if not target_account:
        target_account = "charlidamelio"

    print()
    print("=" * 70)
    print("  Testing with Native Mac Browser")
    print("=" * 70)
    print(f"  Target: @{target_account}")
    print(f"  Mobile mode: {'Yes (iPhone)' if use_mobile else 'No (Desktop)'}")
    print("=" * 70)
    print()

    with sync_playwright() as p:
        # Launch a regular Chrome browser (not AdsPower)
        print("Launching your Mac's browser...")

        if use_mobile:
            # Use mobile emulation
            browser = p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )

            # iPhone 13 Pro device
            device = p.devices['iPhone 13 Pro']
            context = browser.new_context(**device)
            page = context.new_page()

            print("✓ Browser launched (iPhone 13 Pro mode)")
        else:
            # Regular desktop browser
            browser = p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            context = browser.new_context()
            page = context.new_page()

            print("✓ Browser launched (Desktop mode)")

        print()

        try:
            # Go to target profile
            profile_url = f'https://www.tiktok.com/@{target_account}'
            print(f"Opening {profile_url}...")
            page.goto(profile_url, timeout=60000)
            time.sleep(5)

            # Take screenshot
            page.screenshot(path='downloads/native_browser_profile.png')
            print("✓ Screenshot saved: native_browser_profile.png")
            print()

            # Check if logged in
            print("Checking login status...")
            try:
                if 'Log in' in page.content() or 'Sign up' in page.content():
                    print("⚠ Not logged in to TikTok")
                    print()
                    print("⚠ MANUAL LOGIN MAY BE REQUIRED")
                    print("The browser window is open - log in if needed")
                    print("Waiting 15 seconds for you to log in...")
                    time.sleep(15)
                    print()
                else:
                    print("✓ Appears to be logged in")
            except:
                pass

            # Find videos
            print("Finding videos...")
            video_links = []

            try:
                # Wait for videos to load
                page.wait_for_selector('a[href*="/video/"]', timeout=10000)

                # Get video links
                video_elements = page.locator('a[href*="/video/"]').all()
                for elem in video_elements[:5]:
                    href = elem.get_attribute('href')
                    if href and '/video/' in href:
                        full_url = f'https://www.tiktok.com{href}' if href.startswith('/') else href
                        if full_url not in video_links:
                            video_links.append(full_url)

                print(f"✓ Found {len(video_links)} videos")
            except Exception as e:
                print(f"⚠ Error finding videos: {e}")
                print("Trying to find any video links on page...")

            if not video_links:
                print("No videos found. The browser window is open.")
                print("Waiting 30 seconds then closing...")
                time.sleep(30)
                return

            # Watch videos
            print()
            print(f"Watching {len(video_links)} videos...")
            print("(Using native Mac browser - no AdsPower)")
            print()

            for i, video_url in enumerate(video_links, 1):
                try:
                    print(f"  Video {i}/{len(video_links)}: {video_url}")
                    page.goto(video_url, timeout=30000)

                    # Random watch time
                    watch_time = random.randint(10, 20)
                    print(f"  Watching for {watch_time}s...")
                    time.sleep(watch_time)

                    # Take screenshot
                    page.screenshot(path=f'downloads/native_video_{i}.png')
                    print(f"  ✓ Screenshot: native_video_{i}.png")
                    print()

                except Exception as e:
                    print(f"  Error: {e}")
                    continue

            print("=" * 70)
            print("  TEST COMPLETE!")
            print("=" * 70)
            print()
            print(f"Watched {len(video_links)} videos using native Mac browser")
            print("(No AdsPower, no proxy)")
            print()
            print("Now check TikTok analytics:")
            print(f"  1. Go to @{target_account}'s profile")
            print("  2. Check if view counts increased")
            print("  3. Compare with AdsPower browser results")
            print()
            print("This will tell us if the problem is:")
            print("  - AdsPower being detected (if native works)")
            print("  - Proxy/IP issues (if native also fails)")
            print("  - Account issues (if neither works)")
            print()
            print("Browser will remain open for 30 seconds...")
            time.sleep(30)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print()
            print("Closing in 10 seconds...")
            time.sleep(10)

        finally:
            browser.close()
            print("Browser closed")

if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "charlidamelio"
    mobile = sys.argv[2].lower() == 'y' if len(sys.argv) > 2 else True

    print("=" * 70)
    print("  Native Mac Browser Test")
    print("=" * 70)
    print(f"  Target: @{target}")
    print(f"  Mode: {'Mobile (iPhone)' if mobile else 'Desktop'}")
    print("=" * 70)
    print()

    test_native_browser(target, mobile)
