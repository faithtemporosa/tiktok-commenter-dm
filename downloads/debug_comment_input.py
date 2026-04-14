#!/usr/bin/env python3
"""Debug script to find comment input structure on TikTok"""

import requests
import time
from playwright.sync_api import sync_playwright

ADSPOWER_API = 'http://local.adspower.net:50325'

def open_browser(user_id):
    resp = requests.get(f'{ADSPOWER_API}/api/v1/browser/start?user_id={user_id}', timeout=60)
    data = resp.json()
    if data.get('code') == 0:
        return data['data']['ws']['puppeteer']
    return None

def close_browser(user_id):
    requests.get(f'{ADSPOWER_API}/api/v1/browser/stop?user_id={user_id}')

def main():
    # Get first browser
    resp = requests.get(f'{ADSPOWER_API}/api/v1/user/list?page_size=1', timeout=30)
    browsers = resp.json().get('data', {}).get('list', [])
    if not browsers:
        print("No browsers found")
        return

    browser = browsers[0]
    user_id = browser['user_id']
    browser_name = browser['name']

    print(f"Opening {browser_name}...")
    ws_url = open_browser(user_id)
    if not ws_url:
        print("Failed to open browser")
        return

    try:
        with sync_playwright() as p:
            browser_conn = p.chromium.connect_over_cdp(ws_url)
            context = browser_conn.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # Go to a target account's video
            print("Going to flockboynation profile...")
            page.goto('https://www.tiktok.com/@flockboynation', timeout=30000)
            time.sleep(4)

            # Get video links
            videos = page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a').forEach(a => {
                    if (a.href && a.href.includes('/video/')) {
                        links.push(a.href);
                    }
                });
                return [...new Set(links)];
            }''')

            if videos:
                print(f"Found {len(videos)} videos")
                print(f"Opening first video: {videos[0]}")
                page.goto(videos[0], timeout=30000)
                time.sleep(5)  # Wait for page to fully load

                # Close any popups by pressing Escape
                print("Closing any popups...")
                page.keyboard.press('Escape')
                time.sleep(1)
                page.keyboard.press('Escape')
                time.sleep(1)

                # Try clicking X button on any modal
                page.evaluate('''() => {
                    // Close any modals/popups
                    const closeButtons = document.querySelectorAll('[aria-label="Close"], [class*="close" i], button svg');
                    for (let btn of closeButtons) {
                        try { btn.click(); } catch(e) {}
                    }
                }''')
                time.sleep(1)

                # Take screenshot after closing popups
                page.screenshot(path='debug_video_page_1_after_popup.png')
                print("Saved screenshot: debug_video_page_1_after_popup.png")

                # Click on the comment icon to expand comments section
                print("Clicking comment icon...")
                clicked = page.evaluate('''() => {
                    // Try clicking comment icon
                    const commentIcon = document.querySelector('[data-e2e="comment-icon"]');
                    if (commentIcon) {
                        commentIcon.click();
                        return "clicked comment-icon";
                    }

                    // Try clicking Comments tab
                    const commentsTab = document.querySelector('[data-e2e="browse-comment-button"], button:has-text("Comments")');
                    if (commentsTab) {
                        commentsTab.click();
                        return "clicked comments tab";
                    }

                    return "no element found";
                }''')
                print(f"Click result: {clicked}")
                time.sleep(3)

                # Take screenshot after clicking
                page.screenshot(path='debug_video_page_2_after_click.png')
                print("Saved screenshot: debug_video_page_2_after_click.png")

                # Now check for comment input
                debug_info = page.evaluate('''() => {
                    const info = [];

                    // Check all input-like elements
                    info.push("=== INPUT elements ===");
                    document.querySelectorAll('input').forEach((el, i) => {
                        if (el.offsetParent) {
                            info.push(`Input ${i}: placeholder="${el.placeholder}", name="${el.name}", type="${el.type}"`);
                        }
                    });

                    // Check contenteditable
                    info.push("\\n=== CONTENTEDITABLE elements ===");
                    document.querySelectorAll('[contenteditable]').forEach((el, i) => {
                        if (el.offsetParent) {
                            const rect = el.getBoundingClientRect();
                            info.push(`Editable ${i}: tag=${el.tagName}, class="${el.className.substring(0,80)}", pos=(${Math.round(rect.x)},${Math.round(rect.y)}), size=(${Math.round(rect.width)}x${Math.round(rect.height)})`);
                        }
                    });

                    // Check data-e2e attributes related to comment
                    info.push("\\n=== data-e2e elements containing 'comment' ===");
                    document.querySelectorAll('[data-e2e*="comment" i]').forEach((el, i) => {
                        if (el.offsetParent) {
                            info.push(`E2E ${i}: ${el.getAttribute('data-e2e')}, tag=${el.tagName}, class="${el.className.substring(0,60)}"`);
                        }
                    });

                    // Check for placeholder text "Add comment"
                    info.push("\\n=== Elements with 'comment' placeholder ===");
                    document.querySelectorAll('[placeholder*="comment" i], [aria-placeholder*="comment" i]').forEach((el, i) => {
                        info.push(`Placeholder ${i}: placeholder="${el.placeholder || el.getAttribute('aria-placeholder')}", tag=${el.tagName}`);
                    });

                    // Check class names containing 'comment' or 'input'
                    info.push("\\n=== Classes containing CommentInput or DivInput ===");
                    document.querySelectorAll('[class*="CommentInput"], [class*="DivInput"]').forEach((el, i) => {
                        if (el.offsetParent) {
                            info.push(`ClassMatch ${i}: tag=${el.tagName}, class="${el.className.substring(0,100)}"`);
                        }
                    });

                    // Check for any editor divs
                    info.push("\\n=== Draft/Editor elements ===");
                    document.querySelectorAll('[class*="Draft"], [class*="Editor"]').forEach((el, i) => {
                        if (el.offsetParent) {
                            info.push(`Editor ${i}: tag=${el.tagName}, class="${el.className.substring(0,100)}"`);
                        }
                    });

                    // Check for any div with "Add comment" text
                    info.push("\\n=== Elements containing 'Add comment' text ===");
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    let node;
                    while (node = walker.nextNode()) {
                        if (node.textContent.includes('Add comment')) {
                            const parent = node.parentElement;
                            if (parent) {
                                info.push(`Text: "${node.textContent.substring(0,50)}", parent tag=${parent.tagName}, class="${parent.className.substring(0,60)}"`);
                            }
                        }
                    }

                    return info.join("\\n");
                }''')

                print("\n" + "="*60)
                print("DEBUG INFO FROM PAGE (after clicking comment):")
                print("="*60)
                print(debug_info)
                print("="*60)

                # Also save to file
                with open('debug_comment_structure.txt', 'w') as f:
                    f.write(debug_info)
                print("\nSaved debug info to debug_comment_structure.txt")

            browser_conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    close_browser(user_id)

if __name__ == "__main__":
    main()
