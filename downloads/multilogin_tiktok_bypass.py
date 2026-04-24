#!/usr/bin/env python3
"""
TikTok Mobile Web Bypass for Multilogin
========================================
Bypass TikTok's "Download App" prompts on mobile web version.

USAGE:
    from multilogin_tiktok_bypass import bypass_tiktok_prompts

METHODS:
    1. Desktop User Agent (Recommended)
    2. Block Download Prompts with JavaScript
    3. Use Direct URLs
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def use_desktop_mode(driver):
    """
    Best solution: Use desktop user agent even on mobile profiles
    TikTok desktop web is fully functional
    """
    # Set desktop user agent
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.get("https://www.tiktok.com")
    return driver


def block_app_download_prompts(driver):
    """
    Inject JavaScript to hide/block app download prompts
    """
    # JavaScript to remove download prompts
    js_code = """
    // Remove download app banners
    setInterval(function() {
        // Common TikTok app download prompt selectors
        const selectors = [
            '[data-e2e="app-download-banner"]',
            '[class*="download-app"]',
            '[class*="app-banner"]',
            '[class*="mobile-download"]',
            'a[href*="app.adjust.com"]',
            'a[href*="tiktok.com/download"]',
            '.mobile-open-app-btn',
            '[class*="open-app"]'
        ];

        selectors.forEach(function(selector) {
            document.querySelectorAll(selector).forEach(function(el) {
                el.remove();
            });
        });

        // Remove popup overlays
        document.querySelectorAll('[class*="modal"]').forEach(function(modal) {
            if (modal.innerText.includes('Get the app') ||
                modal.innerText.includes('Download') ||
                modal.innerText.includes('Open in app')) {
                modal.remove();
            }
        });
    }, 1000);

    // Block navigation to app stores
    window.addEventListener('click', function(e) {
        const href = e.target.closest('a')?.href || '';
        if (href.includes('app.adjust.com') ||
            href.includes('/download') ||
            href.includes('apps.apple.com') ||
            href.includes('play.google.com')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    }, true);
    """

    driver.execute_script(js_code)
    return driver


def close_app_prompt_if_exists(driver):
    """
    Close app download prompt if it appears
    """
    try:
        # Try to find and click close button on app download prompt
        close_selectors = [
            "button[aria-label='Close']",
            "button[aria-label='Dismiss']",
            ".tiktok-close-button",
            "[data-e2e='modal-close-inner-button']",
            "svg[class*='close']",
        ]

        for selector in close_selectors:
            try:
                close_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                close_btn.click()
                print("✓ Closed app download prompt")
                time.sleep(0.5)
                break
            except:
                continue
    except:
        pass


def bypass_tiktok_prompts(driver, method="desktop"):
    """
    Main function to bypass TikTok app download prompts

    Args:
        driver: Selenium WebDriver instance
        method: "desktop" (recommended), "block", or "close"

    Returns:
        driver: Modified WebDriver instance
    """

    if method == "desktop":
        # Best solution: Use desktop user agent
        print("Using desktop mode (bypasses all mobile prompts)...")
        use_desktop_mode(driver)

    elif method == "block":
        # Block prompts with JavaScript
        print("Blocking app download prompts with JavaScript...")
        driver.get("https://www.tiktok.com")
        time.sleep(2)
        block_app_download_prompts(driver)

    elif method == "close":
        # Just close the prompt when it appears
        print("Closing app download prompts...")
        driver.get("https://www.tiktok.com")
        time.sleep(2)
        close_app_prompt_if_exists(driver)

    return driver


def navigate_without_prompts(driver, url):
    """
    Navigate to TikTok URL while avoiding app download prompts

    Args:
        url: TikTok URL to navigate to
    """
    # Use desktop user agent
    use_desktop_mode(driver)

    # Navigate
    driver.get(url)
    time.sleep(2)

    # Close any prompts that still appear
    close_app_prompt_if_exists(driver)

    return driver


# Example usage
if __name__ == "__main__":
    from multilogin_api import MultiloginClient

    # Initialize Multilogin
    client = MultiloginClient(
        email="your@email.com",
        password="yourpassword"
    )
    client.authenticate()

    # Start a profile
    driver = client.start_profile(
        folder_id="your_folder_id",
        profile_id="your_profile_id"
    )

    # Method 1: Use desktop mode (RECOMMENDED)
    print("\n=== Method 1: Desktop Mode (Best) ===")
    bypass_tiktok_prompts(driver, method="desktop")
    time.sleep(5)

    # Method 2: Block prompts with JavaScript
    print("\n=== Method 2: Block with JavaScript ===")
    bypass_tiktok_prompts(driver, method="block")
    time.sleep(5)

    # Method 3: Navigate to specific URLs
    print("\n=== Method 3: Direct Navigation ===")
    navigate_without_prompts(driver, "https://www.tiktok.com/@username")
    time.sleep(5)

    # Clean up
    client.stop_profile(profile_id="your_profile_id")
    print("\n✓ Done!")
