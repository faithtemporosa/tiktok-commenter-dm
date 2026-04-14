#!/usr/bin/env python3
"""
AdsPower TikTok Direct Commenter v2
===================================
Directly comments on TikTok videos using JavaScript injection for reliability.

SETUP:
    pip install requests flask playwright emergentintegrations
    playwright install chromium

RUN:
    python tiktok_commenter.py

Open http://localhost:9090
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import requests
import time
import json
import csv
import io
import re
import threading
import random
import traceback
import asyncio
import webbrowser
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template_string, jsonify, request

# AI for reply drafting
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    HAS_AI = True
except ImportError:
    HAS_AI = False
    print("Note: Install emergentintegrations for AI replies: pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/")

# Supabase for cloud sync
try:
    from supabase import create_client
    SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Note: Install supabase for cloud sync: pip install supabase")

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("ERROR: Install playwright: pip install playwright && playwright install chromium")

# =============================================================================
# CONFIGURATION
# =============================================================================
ADSPOWER_API = "http://localhost:50325"
GOOGLE_SHEET_ID = "1cgjxB09nXSsKMEFwNxQlDzl8xVDyQgT0o8aKm6YOJ-o"
SHEET_NAMES = ["Bump Connect", "Kollabsy", "Bump Syndicate"]

# Cloud API for real-time reporting (update this URL after deployment)
CLOUD_API_URL = "https://bump-tiktok-bot.preview.emergentagent.com/api"

MIN_DELAY_BETWEEN_COMMENTS = 30
MAX_DELAY_BETWEEN_COMMENTS = 60
VIDEOS_PER_PROFILE = 1000  # Target: 1000 videos per profile per day

# =============================================================================
# GLOBAL STATE
# =============================================================================
app = Flask(__name__)
profiles = []
comments_cache = {}
commented_videos = set()

REPORT_FILE = "tiktok_comments_history.json"
DM_REPORT_FILE = "tiktok_dm_history.json"
DM_TARGETS_FILE = "tiktok_dm_targets.json"
POST_QUEUE_FILE = "tiktok_post_queue.json"
POST_HISTORY_FILE = "tiktok_post_history.json"
SCREENSHOTS_FOLDER = "comment_screenshots"
NOT_LOGGED_IN_FILE = "not_logged_in_browsers.json"

# Track browsers that are not logged in
not_logged_in_browsers = []

def load_not_logged_in():
    """Load list of browsers that are not logged in"""
    global not_logged_in_browsers
    try:
        with open(NOT_LOGGED_IN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            not_logged_in_browsers = data.get("browsers", [])
    except:
        not_logged_in_browsers = []

def save_not_logged_in():
    """Save list of browsers that are not logged in"""
    try:
        with open(NOT_LOGGED_IN_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "browsers": not_logged_in_browsers,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(not_logged_in_browsers)
            }, f, indent=2)
    except:
        pass

def track_not_logged_in(profile_name, source="unknown"):
    """Track a browser that is not logged in"""
    global not_logged_in_browsers
    entry = {
        "profile": profile_name,
        "detected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source  # commenter, dm, repost
    }
    # Check if already tracked
    existing = [b for b in not_logged_in_browsers if b.get("profile") == profile_name]
    if not existing:
        not_logged_in_browsers.append(entry)
        save_not_logged_in()
        print(f"  📝 Tracked not-logged-in: {profile_name}")

def clear_not_logged_in():
    """Clear the not logged in list"""
    global not_logged_in_browsers
    not_logged_in_browsers = []
    save_not_logged_in()

def get_not_logged_in_list():
    """Get list of not logged in browsers"""
    return not_logged_in_browsers

# Create screenshots folder if it doesn't exist
import os
if not os.path.exists(SCREENSHOTS_FOLDER):
    os.makedirs(SCREENSHOTS_FOLDER)

settings = {
    "min_delay": MIN_DELAY_BETWEEN_COMMENTS,
    "max_delay": MAX_DELAY_BETWEEN_COMMENTS,
    "videos_per_profile": VIDEOS_PER_PROFILE,
    "parallel_browsers": 2,  # Number of browsers to run in parallel (1-10, recommended: 2-3)
    "target_hashtag": "",  # Target hashtag to search (e.g., #socialmedia)
}

# DM Settings - Updated for brand outreach
dm_settings = {
    "enabled": False,
    "max_dms_per_profile": 100,  # Max 100 DMs per profile per day
    "max_dms_total": 2500,  # Max 2500 DMs total per day
    "parallel_browsers": 2,  # 2 profiles open at the same time
    "min_delay": 45,  # Seconds between DMs
    "max_delay": 90,
    "target_mode": "brand_search",  # brand_search, specific, hashtag, commenters, followers
    "target_hashtag": "",
    "target_account": "",
    "target_video_url": "",
}

# Search queries to find brands/companies needing social media management
DM_BRAND_SEARCH_QUERIES = [
    "small business owner",
    "startup founder",
    "entrepreneur life",
    "new business",
    "local business",
    "ecommerce brand",
    "clothing brand",
    "beauty brand",
    "fitness brand",
    "restaurant owner",
    "salon owner",
    "real estate agent",
    "coach business",
    "consulting business",
    "agency owner",
    "marketing agency",
    "brand launch",
    "product launch",
    "dropshipping",
    "amazon fba",
    "etsy seller",
    "shopify store",
    "boutique owner",
    "jewelry brand",
    "skincare brand",
    "supplement brand",
    "food brand",
    "beverage brand",
    "tech startup",
    "saas founder",
]

# DM Targets and Messages
dm_targets = {
    "specific_users": [],
    "scraped_brands": [],  # Brands found via search
    "messages": {
        "default": "Hey! 👋 I noticed your brand and love what you're doing! We help businesses like yours grow on social media. Check out bumpsyndicate.xyz - we'd love to help you scale! 🚀",
        "groups": {}
    }
}

# Daily DM tracking per profile: {"profile_name": {"2026-02-19": 50}}
DM_TRACKER_FILE = "tiktok_dm_tracker.json"
dm_tracker = {}

dm_status = {
    "running": False,
    "current_profile": None,
    "current_profile_index": 0,
    "profiles_completed": [],
    "progress": 0,
    "total": 0,
    "dms_sent": 0,
    "dms_sent_today": 0,
    "logs": [],
    "report": [],
    "sent_to": set()  # Track who we've already DMed
}

# =============================================================================
# AI REPLY SYSTEM - Track replies and draft AI responses
# =============================================================================
EMERGENT_LLM_KEY = "sk-emergent-6Ba3bF3C70c6aE08f9"
REPLIES_FILE = "tiktok_dm_replies.json"

# Reply tracking
reply_status = {
    "checking": False,
    "last_check": None,
    "pending_replies": [],  # Messages received that need response
    "draft_replies": [],    # AI-drafted replies pending approval
    "approved_replies": [], # Approved replies ready to send
    "sent_replies": [],     # Sent reply history
    "logs": [],
}

AI_SYSTEM_PROMPT = """You are a professional but friendly social media marketing assistant for Bump Syndicate (bumpsyndicate.xyz). 

Your role is to draft reply messages to potential clients who responded to our outreach DMs about social media management services.

Guidelines:
- Be professional but warm and approachable
- Keep replies concise (2-3 sentences max)
- Show genuine interest in their business
- Gently guide towards scheduling a call or visiting bumpsyndicate.xyz
- Don't be pushy or salesy
- Use emojis sparingly (1-2 max)
- Address their specific questions or concerns if mentioned
- Always maintain a helpful, consultative tone

Examples of good replies:
- "Thanks for getting back to us! 😊 We'd love to learn more about your brand. Would you be open to a quick 15-min call this week?"
- "Great to hear from you! What's your biggest challenge with social media right now? We might have some quick wins for you."
- "Appreciate the response! Feel free to check out some of our case studies at bumpsyndicate.xyz/results - happy to chat whenever works for you!"
"""

def reply_log(message):
    """Log for reply operations"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [REPLY] {message}"
    reply_status["logs"].append(log_entry)
    print(log_entry)
    if len(reply_status["logs"]) > 200:
        reply_status["logs"] = reply_status["logs"][-200:]

def load_replies_data():
    """Load reply tracking data"""
    global reply_status
    try:
        with open(REPLIES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            reply_status["pending_replies"] = data.get("pending_replies", [])
            reply_status["draft_replies"] = data.get("draft_replies", [])
            reply_status["approved_replies"] = data.get("approved_replies", [])
            reply_status["sent_replies"] = data.get("sent_replies", [])
            print(f"✓ Loaded {len(reply_status['pending_replies'])} pending, {len(reply_status['draft_replies'])} drafts, {len(reply_status['approved_replies'])} approved replies")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading replies: {e}")

def save_replies_data():
    """Save reply tracking data"""
    try:
        with open(REPLIES_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "pending_replies": reply_status["pending_replies"],
                "draft_replies": reply_status["draft_replies"],
                "approved_replies": reply_status["approved_replies"],
                "sent_replies": reply_status["sent_replies"],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving replies: {e}")

async def draft_ai_reply(username, their_message, original_outreach):
    """Use AI to draft a reply to a message"""
    if not HAS_AI:
        return f"Thanks for your response! We'd love to chat more about how we can help your brand grow. Check out bumpsyndicate.xyz!"
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"reply-{username}-{int(time.time())}",
            system_message=AI_SYSTEM_PROMPT
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"""Draft a reply to this message:

Username: @{username}
Their reply: "{their_message}"
Our original outreach: "{original_outreach}"

Keep it short (2-3 sentences), professional but friendly. Don't include any greeting like "Hi" since this is a DM reply."""
        )
        
        response = await chat.send_message(user_message)
        return response.strip()
    except Exception as e:
        reply_log(f"✗ AI error: {e}")
        return f"Thanks for getting back! We'd love to learn more about your brand and how we can help. Feel free to check out bumpsyndicate.xyz 😊"

def check_dm_replies_for_profile(page, profile_name):
    """Check TikTok DM inbox for replies to our outreach"""
    new_replies = []
    reply_log(f"  📥 Checking inbox for {profile_name}...")
    
    try:
        # Navigate to DM inbox
        page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
        # Check if logged in
        if "login" in page.url.lower():
            reply_log(f"  ⚠ Not logged in")
            return []
        
        # Get list of conversations with unread messages
        conversations = page.evaluate('''() => {
            const convos = [];
            // Find conversation list items
            const items = document.querySelectorAll('[class*="ConversationItem"], [class*="MessageListItem"], [data-e2e*="message"]');
            
            items.forEach(item => {
                // Check for unread indicator
                const hasUnread = item.querySelector('[class*="unread"], [class*="Unread"], [class*="badge"]') !== null;
                const usernameEl = item.querySelector('[class*="Username"], [class*="name"], a[href*="/@"]');
                const previewEl = item.querySelector('[class*="Preview"], [class*="lastMessage"], [class*="content"]');
                
                if (usernameEl) {
                    let username = '';
                    if (usernameEl.href && usernameEl.href.includes('/@')) {
                        username = usernameEl.href.match(/@([a-zA-Z0-9_.]+)/)?.[1] || '';
                    } else {
                        username = usernameEl.textContent.replace('@', '').trim();
                    }
                    
                    const preview = previewEl ? previewEl.textContent.trim() : '';
                    
                    if (username) {
                        convos.push({
                            username: username,
                            preview: preview.substring(0, 100),
                            hasUnread: hasUnread,
                            element_index: Array.from(items).indexOf(item)
                        });
                    }
                }
            });
            
            return convos;
        }''')
        
        reply_log(f"  Found {len(conversations)} conversations")
        
        # Filter to users we've previously DMed
        sent_to = dm_status.get("sent_to", set())
        for convo in conversations:
            username = convo.get("username", "")
            if username in sent_to or username in [r.get("username") for r in dm_status.get("report", [])]:
                # This is a reply to our outreach!
                # Check if we already have this reply
                existing = [r for r in reply_status["pending_replies"] + reply_status["draft_replies"] + reply_status["sent_replies"] 
                           if r.get("username") == username]
                
                if not existing:
                    # Click to open conversation and get full message
                    try:
                        page.evaluate(f'''(index) => {{
                            const items = document.querySelectorAll('[class*="ConversationItem"], [class*="MessageListItem"], [data-e2e*="message"]');
                            if (items[index]) items[index].click();
                        }}''', convo.get("element_index", 0))
                        time.sleep(2)
                        
                        # Get the last message from them
                        last_message = page.evaluate('''() => {
                            const messages = document.querySelectorAll('[class*="MessageBubble"], [class*="messageContent"], [class*="TextMessage"]');
                            // Get messages that are NOT from us (received messages)
                            const received = [];
                            messages.forEach(msg => {
                                const isReceived = msg.closest('[class*="received"], [class*="Received"], [class*="left"]') !== null ||
                                                   !msg.closest('[class*="sent"], [class*="Sent"], [class*="right"]');
                                if (isReceived) {
                                    received.push(msg.textContent.trim());
                                }
                            });
                            return received.length > 0 ? received[received.length - 1] : '';
                        }''')
                        
                        if last_message and len(last_message) > 0:
                            # Find our original outreach message
                            original = ""
                            for r in dm_status.get("report", []):
                                if r.get("username") == username:
                                    original = r.get("message", "")
                                    break
                            
                            new_reply = {
                                "id": f"reply_{username}_{int(time.time())}",
                                "username": username,
                                "their_message": last_message[:500],
                                "original_outreach": original,
                                "profile": profile_name,
                                "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "status": "pending"
                            }
                            new_replies.append(new_reply)
                            reply_status["pending_replies"].append(new_reply)
                            reply_log(f"  ✓ New reply from @{username}: {last_message[:50]}...")
                    except Exception as e:
                        reply_log(f"  ⚠ Error reading conversation: {str(e)[:50]}")
        
        return new_replies
        
    except Exception as e:
        reply_log(f"  ✗ Error checking inbox: {str(e)[:80]}")
        return []

def send_reply_to_user(page, username, reply_message):
    """Send a reply message to a user"""
    try:
        reply_log(f"  → Sending reply to @{username}...")
        
        # Navigate to messages
        page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # Find and click the conversation
        clicked = page.evaluate(f'''(targetUser) => {{
            const items = document.querySelectorAll('[class*="ConversationItem"], [class*="MessageListItem"], [data-e2e*="message"]');
            for (let item of items) {{
                const text = item.textContent.toLowerCase();
                if (text.includes(targetUser.toLowerCase())) {{
                    item.click();
                    return true;
                }}
            }}
            return false;
        }}''', username)
        
        if not clicked:
            reply_log(f"  ⚠ Could not find conversation with @{username}")
            return False
        
        time.sleep(2)
        
        # Find message input
        input_result = page.evaluate('''() => {
            const selectors = [
                '[data-e2e="message-input"]',
                '[class*="DivInputContainer"] [contenteditable="true"]',
                '[class*="MessageInput"] [contenteditable="true"]',
                'div[contenteditable="true"]'
            ];
            
            for (let sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.offsetParent) {
                    el.click();
                    el.focus();
                    return {success: true};
                }
            }
            return {success: false};
        }''')
        
        if not input_result.get('success'):
            reply_log(f"  ⚠ Could not find message input")
            return False
        
        time.sleep(0.5)
        
        # Type the reply
        page.keyboard.type(reply_message, delay=random.randint(20, 50))
        time.sleep(1)
        
        # Send
        page.keyboard.press("Enter")
        time.sleep(2)
        
        reply_log(f"  ✓ Reply sent to @{username}")
        return True
        
    except Exception as e:
        reply_log(f"  ✗ Error sending reply: {str(e)[:80]}")
        return False

def run_check_replies(ws_endpoint, profile_name):
    """Check DM inbox for replies using a browser"""
    if not HAS_PLAYWRIGHT:
        return []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            
            new_replies = check_dm_replies_for_profile(page, profile_name)
            
            browser.close()
            return new_replies
    except Exception as e:
        reply_log(f"✗ Error: {e}")
        return []

def run_send_approved_replies(ws_endpoint, profile_name):
    """Send all approved replies using a browser"""
    if not HAS_PLAYWRIGHT:
        return 0
    
    sent_count = 0
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            
            # Filter approved replies for this profile
            profile_replies = [r for r in reply_status["approved_replies"] if r.get("profile") == profile_name]
            
            for reply in profile_replies:
                if send_reply_to_user(page, reply["username"], reply["draft_message"]):
                    sent_count += 1
                    reply["status"] = "sent"
                    reply["sent_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    reply_status["sent_replies"].append(reply)
                    reply_status["approved_replies"].remove(reply)
                    save_replies_data()
                    
                    # Delay between sends
                    time.sleep(random.randint(30, 60))
            
            browser.close()
            return sent_count
    except Exception as e:
        reply_log(f"✗ Error: {e}")
        return sent_count

def start_check_replies():
    """Start checking for replies across all profiles"""
    if reply_status["checking"]:
        return False
    
    reply_status["checking"] = True
    reply_status["logs"] = []
    
    reply_log("═" * 50)
    reply_log("📥 Checking for DM Replies...")
    reply_log("═" * 50)
    
    if not profiles:
        reply_log("✗ No profiles loaded!")
        reply_status["checking"] = False
        return False
    
    def run():
        total_new = 0
        try:
            for profile in profiles[:5]:  # Check first 5 profiles
                if not reply_status["checking"]:
                    break
                
                profile_id = profile.get("user_id")
                profile_name = profile.get("name", profile_id)
                
                reply_log(f"")
                reply_log(f"▶ Checking: {profile_name}")
                
                browser_data = open_browser(profile_id)
                if browser_data:
                    try:
                        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
                        if ws_endpoint:
                            time.sleep(3)
                            new_replies = run_check_replies(ws_endpoint, profile_name)
                            total_new += len(new_replies)
                    finally:
                        close_browser(profile_id)

                time.sleep(5)  # Delay between profiles
            
            # Generate AI drafts for new replies
            if total_new > 0:
                reply_log("")
                reply_log("🤖 Generating AI draft replies...")
                
                for pending in reply_status["pending_replies"]:
                    if pending.get("status") == "pending":
                        try:
                            # Run async AI call
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            draft = loop.run_until_complete(draft_ai_reply(
                                pending["username"],
                                pending["their_message"],
                                pending.get("original_outreach", "")
                            ))
                            loop.close()
                            
                            draft_entry = {
                                **pending,
                                "draft_message": draft,
                                "status": "draft",
                                "drafted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            reply_status["draft_replies"].append(draft_entry)
                            reply_status["pending_replies"].remove(pending)
                            
                            reply_log(f"  ✓ Draft for @{pending['username']}: {draft[:50]}...")
                            save_replies_data()
                        except Exception as e:
                            reply_log(f"  ✗ Draft error: {e}")
            
        except Exception as e:
            reply_log(f"✗ Fatal error: {e}")
        finally:
            reply_status["checking"] = False
            reply_status["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_replies_data()
            reply_log("")
            reply_log("═" * 50)
            reply_log(f"✅ Check complete! Found {total_new} new replies")
            reply_log(f"   Drafts ready for approval: {len(reply_status['draft_replies'])}")
            reply_log("═" * 50)
    
    threading.Thread(target=run, daemon=True).start()
    return True

def start_send_approved():
    """Send all approved replies"""
    if reply_status["checking"]:
        return False
    
    approved = reply_status["approved_replies"]
    if not approved:
        reply_log("⚠ No approved replies to send")
        return False
    
    reply_status["checking"] = True
    reply_log("═" * 50)
    reply_log(f"📤 Sending {len(approved)} approved replies...")
    reply_log("═" * 50)
    
    def run():
        total_sent = 0
        try:
            # Group by profile
            by_profile = {}
            for reply in approved:
                profile_name = reply.get("profile", "")
                if profile_name not in by_profile:
                    by_profile[profile_name] = []
                by_profile[profile_name].append(reply)
            
            for profile_name, replies in by_profile.items():
                # Find profile
                profile = next((p for p in profiles if p.get("name") == profile_name), None)
                if not profile:
                    reply_log(f"⚠ Profile {profile_name} not found")
                    continue
                
                reply_log(f"")
                reply_log(f"▶ Sending from: {profile_name} ({len(replies)} replies)")
                
                browser_data = open_browser(profile.get("user_id"))
                if browser_data:
                    try:
                        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
                        if ws_endpoint:
                            time.sleep(3)
                            sent = run_send_approved_replies(ws_endpoint, profile_name)
                            total_sent += sent
                    finally:
                        close_browser(profile.get("user_id"))

                time.sleep(10)  # Delay between profiles
            
        except Exception as e:
            reply_log(f"✗ Fatal error: {e}")
        finally:
            reply_status["checking"] = False
            save_replies_data()
            reply_log("")
            reply_log("═" * 50)
            reply_log(f"✅ Sent {total_sent} replies!")
            reply_log("═" * 50)
    
    threading.Thread(target=run, daemon=True).start()
    return True

# Post Settings
post_settings = {
    "enabled": True,
    "min_delay": 300,  # 5 min between reposts
    "max_delay": 600,  # 10 min between reposts
    "max_reposts_per_day": 2,  # Max 2 reposts per profile per day
}

# Profile to TikTok username mapping
# Maps internal profile names (tt1, tt2, etc.) to actual TikTok usernames
PROFILE_MAPPING_FILE = "tiktok_profile_mapping.json"
profile_usernames = {}

def load_profile_mapping():
    """Load profile to TikTok username mapping from file"""
    global profile_usernames
    try:
        with open(PROFILE_MAPPING_FILE, 'r', encoding='utf-8') as f:
            profile_usernames = json.load(f)
    except:
        profile_usernames = {}

def save_profile_mapping():
    """Save profile to TikTok username mapping to file"""
    try:
        with open(PROFILE_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(profile_usernames, f, indent=2)
    except:
        pass

def get_tiktok_username(profile_name):
    """Get TikTok username for a profile, returns None if not mapped"""
    return profile_usernames.get(profile_name)

def set_tiktok_username(profile_name, tiktok_username):
    """Set TikTok username for a profile"""
    profile_usernames[profile_name] = tiktok_username.replace("@", "")
    save_profile_mapping()

# Load mapping on startup
load_profile_mapping()
load_not_logged_in()

# Repost schedule: Monday = brand content, Tue-Sun = social media content
BRAND_SEARCH_TERMS = [
    "bumpconnect", "bump connect", "kollabsy", "bumpsyndicate", "bump syndicate",
    "bumpconnect.com", "kollabsy.xyz", "bumpsyndicate.xyz",
]
SOCIAL_MEDIA_SEARCH_TERMS = [
    "social media tips", "content creator tips", "social media marketing",
    "grow your following", "social media strategy", "creator economy",
    "tiktok growth", "influencer tips", "content creation", "digital marketing",
]

# Source accounts to repost from - scrapes their latest videos
REPOST_SOURCE_ACCOUNTS = [
    "lifeadventuresafterfifty",
]

# Post Queue - auto-populated by scheduler
post_queue = []

# Daily repost tracking per profile: {"profile_name": {"2026-02-19": 2}}
REPOST_TRACKER_FILE = "tiktok_repost_tracker.json"
repost_tracker = {}

post_status = {
    "running": False,
    "current_profile": None,
    "progress": 0,
    "total": 0,
    "posts_made": 0,
    "logs": [],
    "history": [],
    "last_run": None,
    "next_run": None,
}

# Scheduler state
scheduler_running = False  # Disabled - was running daily reposts

automation_status = {
    "running": False,
    "current_profile": None,
    "progress": 0,
    "total": 0,
    "logs": [],
    "completed": [],
    "comments_posted": 0,
    "report": []
}

def load_report_history():
    """Load past reports from file on startup"""
    global automation_status
    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            automation_status["report"] = data.get("report", [])
            automation_status["comments_posted"] = len(automation_status["report"])
            print(f"✓ Loaded {len(automation_status['report'])} comments from history")
    except FileNotFoundError:
        print("No history file found, starting fresh")
        automation_status["report"] = []
        automation_status["comments_posted"] = 0
    except Exception as e:
        print(f"Error loading history: {e}")
        automation_status["report"] = []
        automation_status["comments_posted"] = 0

def save_report_history():
    """Save ALL reports to file for persistence"""
    try:
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "report": automation_status["report"],
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def send_to_cloud(report_data):
    """Send a single comment report to Supabase for real-time dashboard"""
    if not HAS_SUPABASE:
        return False
    try:
        # Get screenshot and upload to storage
        screenshot = report_data.get('screenshot', '')
        screenshot_url = upload_screenshot_to_storage(screenshot) if screenshot else None
        screenshot_filename = os.path.basename(screenshot) if screenshot else ''

        supabase.table('comment_reports').insert({
            'timestamp': report_data.get('timestamp'),
            'profile': report_data.get('profile'),
            'video_url': report_data.get('video_url'),
            'video_id': report_data.get('video_id'),
            'comment': report_data.get('comment'),
            'sheet': report_data.get('sheet'),
            'screenshot': screenshot_url or screenshot_filename
        }).execute()
        log(f"    ☁️ Synced to Supabase" + (" with screenshot" if screenshot_url else ""))
        return True
    except Exception as e:
        if 'duplicate' in str(e).lower() or '23505' in str(e):
            log(f"    ⚠ Already in cloud (duplicate)")
        else:
            log(f"    ⚠ Cloud sync error: {e}")
    return False

def upload_screenshot_to_storage(screenshot_path):
    """Upload screenshot to Supabase Storage and return public URL"""
    if not HAS_SUPABASE or not screenshot_path:
        return None
    try:
        filename = os.path.basename(screenshot_path)
        full_path = screenshot_path if os.path.isabs(screenshot_path) else os.path.join(SCREENSHOTS_FOLDER, filename)
        if not os.path.exists(full_path):
            return None

        with open(full_path, 'rb') as f:
            file_data = f.read()

        # Upload to Supabase Storage bucket 'screenshots'
        storage_path = f"comments/{filename}"
        supabase.storage.from_('screenshots').upload(storage_path, file_data, {"content-type": "image/png", "upsert": "true"})

        # Get public URL
        public_url = supabase.storage.from_('screenshots').get_public_url(storage_path)
        return public_url
    except Exception as e:
        print(f"Screenshot upload error: {e}")
        return None

def sync_all_to_cloud():
    """Sync all local reports to Supabase (for bulk sync)"""
    if not automation_status["report"] or not HAS_SUPABASE:
        return 0

    synced = 0
    for report in automation_status["report"]:
        try:
            # Get screenshot filename and try to upload
            screenshot = report.get('screenshot', '')
            screenshot_filename = os.path.basename(screenshot) if screenshot else ''
            screenshot_url = upload_screenshot_to_storage(screenshot) if screenshot else None

            supabase.table('comment_reports').insert({
                'timestamp': report.get('timestamp'),
                'profile': report.get('profile'),
                'video_url': report.get('video_url'),
                'video_id': report.get('video_id'),
                'comment': report.get('comment'),
                'sheet': report.get('sheet'),
                'screenshot': screenshot_url or screenshot_filename
            }).execute()
            synced += 1
        except Exception as e:
            if 'duplicate' not in str(e).lower() and '23505' not in str(e):
                print(f"Sync error: {e}")

    log(f"☁️ Synced {synced} reports to Supabase")
    return synced

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    automation_status["logs"].append(log_entry)
    try:
        print(log_entry)
    except UnicodeEncodeError:
        print(log_entry.encode('ascii', errors='replace').decode('ascii'))
    if len(automation_status["logs"]) > 200:
        automation_status["logs"] = automation_status["logs"][-200:]
    
    # Send logs to cloud (non-blocking)
    try:
        threading.Thread(target=sync_logs_to_cloud, daemon=True).start()
    except:
        pass

def sync_logs_to_cloud():
    """Send current logs and status to Supabase"""
    if not HAS_SUPABASE:
        return

    try:
        log_entries = []
        for log_line in automation_status["logs"][-50:]:  # Send last 50 logs
            # Parse timestamp from log line
            if log_line.startswith("[") and "]" in log_line:
                ts = log_line[1:log_line.index("]")]
                msg = log_line[log_line.index("]")+2:]
            else:
                ts = datetime.now().strftime("%H:%M:%S")
                msg = log_line

            log_entries.append({
                "timestamp": ts,
                "message": msg,
                "level": "error" if "✗" in msg else "success" if "✓" in msg else "info"
            })

        status_data = {
            "running": automation_status["running"],
            "current_profile": automation_status["current_profile"],
            "progress": automation_status["progress"],
            "total": automation_status["total"],
            "comments_posted": automation_status["comments_posted"],
            "completed": len(automation_status["completed"])
        }

        # Upsert to live_logs table (single row)
        supabase.table('live_logs').upsert({
            'id': '00000000-0000-0000-0000-000000000001',  # Fixed ID for singleton
            'logs': log_entries,
            'status': status_data,
            'updated_at': datetime.now().isoformat()
        }).execute()
    except:
        pass  # Silently fail - don't interrupt main process

def sync_dm_to_cloud(dm_report_entry):
    """Sync a single DM report to Supabase"""
    if not HAS_SUPABASE:
        return
    try:
        # Get screenshot filename
        screenshot = dm_report_entry.get('screenshot', '')
        screenshot_filename = os.path.basename(screenshot) if screenshot else ''

        supabase.table('dm_reports').insert({
            'timestamp': dm_report_entry.get('timestamp'),
            'profile': dm_report_entry.get('profile'),
            'username': dm_report_entry.get('username'),
            'profile_url': dm_report_entry.get('profile_url', f"https://www.tiktok.com/@{dm_report_entry.get('username', '')}"),
            'message': dm_report_entry.get('message', '')[:500],
            'status': dm_report_entry.get('status', 'unknown'),
            'screenshot': screenshot_filename
        }).execute()
    except:
        pass

def sync_post_to_cloud(post_entry):
    """Sync a single post report to Supabase"""
    if not HAS_SUPABASE:
        return
    try:
        # Format timestamp for Supabase
        ts = post_entry.get('timestamp')
        if ts and ' ' in ts:
            # Convert "2026-03-26 01:29:34" to ISO format
            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            ts = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')

        supabase.table('post_reports').insert({
            'timestamp': ts,
            'profile': post_entry.get('profile'),
            'video': post_entry.get('video', ''),
            'caption': post_entry.get('caption', '')[:500],
            'status': post_entry.get('status', 'reposted'),
            'content_type': post_entry.get('content_type', 'social')
        }).execute()
    except Exception as e:
        print(f"Error syncing repost to Supabase: {e}")

def scheduler_loop():
    """Background thread: auto-runs repost scheduler daily"""
    while scheduler_running:
        try:
            now = datetime.now()
            # Check if we should run (once per day, early morning suggested)
            today_str = now.strftime("%Y-%m-%d")
            
            if post_settings.get("enabled") and not post_status["running"]:
                # Check if we've already run today
                if post_status.get("last_run") != today_str:
                    hour = now.hour
                    # Auto-start at configured hour (default: 9 AM)
                    if hour >= 9 and hour < 22:
                        post_log(f"⏰ Scheduler: Auto-starting repost run for {today_str}")
                        post_status["next_run"] = None
                        start_repost_automation()
                else:
                    # Already ran today, calculate next run
                    tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
                    post_status["next_run"] = tomorrow.strftime("%Y-%m-%d %H:%M")
        except:
            pass
        time.sleep(60)  # Check every minute

# =============================================================================
# DM FUNCTIONS - Brand Outreach for Bump Syndicate
# =============================================================================

def load_dm_data():
    """Load DM targets, tracker and history from files"""
    global dm_targets, dm_status, dm_tracker
    
    # Load targets
    try:
        with open(DM_TARGETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dm_targets.update(data)
            print(f"✓ Loaded {len(dm_targets.get('specific_users', []))} DM targets")
            print(f"✓ Loaded {len(dm_targets.get('scraped_brands', []))} scraped brands")
    except FileNotFoundError:
        print("No DM targets file, starting fresh")
    except Exception as e:
        print(f"Error loading DM targets: {e}")
    
    # Load DM tracker (daily counts per profile)
    try:
        with open(DM_TRACKER_FILE, 'r', encoding='utf-8') as f:
            dm_tracker = json.load(f)
            print(f"✓ Loaded DM tracker ({len(dm_tracker)} profiles)")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading DM tracker: {e}")
    
    # Load history
    try:
        with open(DM_REPORT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dm_status["report"] = data.get("report", [])
            dm_status["sent_to"] = set(data.get("sent_to", []))
            dm_status["dms_sent"] = len(dm_status["report"])
            # Count today's DMs
            today = datetime.now().strftime("%Y-%m-%d")
            dm_status["dms_sent_today"] = sum(1 for r in dm_status["report"] if r.get("timestamp", "").startswith(today))
            print(f"✓ Loaded {len(dm_status['report'])} DM history ({dm_status['dms_sent_today']} today)")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading DM history: {e}")

def save_dm_data():
    """Save DM targets, tracker and history"""
    try:
        with open(DM_TARGETS_FILE, 'w', encoding='utf-8') as f:
            # Convert set to list for JSON serialization
            targets_to_save = dm_targets.copy()
            if 'scraped_brands' in targets_to_save and isinstance(targets_to_save['scraped_brands'], set):
                targets_to_save['scraped_brands'] = list(targets_to_save['scraped_brands'])
            json.dump(targets_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving DM targets: {e}")
    
    try:
        with open(DM_TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(dm_tracker, f, indent=2)
    except Exception as e:
        print(f"Error saving DM tracker: {e}")
    
    try:
        with open(DM_REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "report": dm_status["report"],
                "sent_to": list(dm_status["sent_to"]),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving DM history: {e}")

def get_dms_today(profile_name):
    """Get number of DMs sent by profile today"""
    today = datetime.now().strftime("%Y-%m-%d")
    return dm_tracker.get(profile_name, {}).get(today, 0)

def record_dm(profile_name):
    """Record a DM sent by profile"""
    today = datetime.now().strftime("%Y-%m-%d")
    if profile_name not in dm_tracker:
        dm_tracker[profile_name] = {}
    dm_tracker[profile_name][today] = dm_tracker[profile_name].get(today, 0) + 1
    save_dm_data()

def get_total_dms_today():
    """Get total DMs sent today across all profiles"""
    today = datetime.now().strftime("%Y-%m-%d")
    total = 0
    for profile_data in dm_tracker.values():
        total += profile_data.get(today, 0)
    return total

def dm_log(message):
    """Log for DM operations"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [DM] {message}"
    dm_status["logs"].append(log_entry)
    print(log_entry)
    if len(dm_status["logs"]) > 200:
        dm_status["logs"] = dm_status["logs"][-200:]

def get_dm_message(username):
    """Get the appropriate DM message for a user"""
    # Check if user is in a specific group
    for group_name, group_data in dm_targets["messages"].get("groups", {}).items():
        if username in group_data.get("users", []):
            return group_data.get("message", dm_targets["messages"]["default"])
    return dm_targets["messages"]["default"]

def search_brands_on_tiktok(page, search_query, limit=50):
    """Search TikTok for brands/businesses and collect usernames"""
    brands = []
    dm_log(f"🔍 Searching: '{search_query}'")
    
    try:
        encoded = search_query.replace(" ", "%20")
        # Search for users (accounts), not videos
        page.goto(f"https://www.tiktok.com/search/user?q={encoded}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        
        # Check if logged in
        if "login" in page.url.lower():
            dm_log(f"  ⚠ Not logged in!")
            return []
        
        # Scroll and collect users
        for scroll in range(5):
            new_brands = page.evaluate('''() => {
                const users = [];
                // Find user cards in search results
                document.querySelectorAll('[data-e2e="search-user-container"] a[href*="/@"], [class*="UserCard"] a[href*="/@"], a[href*="/@"]').forEach(a => {
                    const match = a.href.match(/@([a-zA-Z0-9_.]+)/);
                    if (match && !users.includes(match[1])) {
                        // Check if it looks like a business/brand (has certain indicators)
                        const card = a.closest('[class*="Card"], [class*="container"], [class*="Item"]');
                        if (card) {
                            const text = card.innerText.toLowerCase();
                            // Look for business indicators
                            if (text.includes('business') || text.includes('brand') || 
                                text.includes('shop') || text.includes('store') ||
                                text.includes('official') || text.includes('co.') ||
                                text.includes('llc') || text.includes('inc') ||
                                text.includes('@') || text.includes('.com') ||
                                text.includes('founder') || text.includes('ceo') ||
                                text.includes('owner') || text.length > 10) {
                                users.push(match[1]);
                            }
                        } else {
                            users.push(match[1]);
                        }
                    }
                });
                return users;
            }''')
            
            brands.extend([b for b in new_brands if b not in brands])
            
            if len(brands) >= limit:
                break
            
            # Scroll down
            page.evaluate('window.scrollBy(0, 600)')
            time.sleep(1.5)
        
        dm_log(f"  ✓ Found {len(brands)} potential brands")
        return brands[:limit]
        
    except Exception as e:
        dm_log(f"  ✗ Search error: {str(e)[:80]}")
        return []

def scrape_brands_for_dm(page, num_brands=100):
    """Scrape brands from multiple search queries"""
    all_brands = set()
    queries_to_use = random.sample(DM_BRAND_SEARCH_QUERIES, min(5, len(DM_BRAND_SEARCH_QUERIES)))
    
    dm_log(f"🎯 Scraping brands using {len(queries_to_use)} search queries...")
    
    for query in queries_to_use:
        if len(all_brands) >= num_brands:
            break
        
        brands = search_brands_on_tiktok(page, query, limit=30)
        # Filter out already contacted users
        new_brands = [b for b in brands if b not in dm_status["sent_to"]]
        all_brands.update(new_brands)
        
        # Small delay between searches
        time.sleep(random.randint(2, 4))
    
    dm_log(f"✓ Total unique brands found: {len(all_brands)}")
    return list(all_brands)[:num_brands]

def send_dm_to_user(page, username, message):
    """Send a DM to a specific user - Simple and direct approach"""
    try:
        dm_log(f"  → Going to @{username}'s profile...")
        page.goto(f"https://www.tiktok.com/@{username}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)  # Wait longer for page to fully load
        
        # STEP 1: Find and click the Message button directly (no 404 check - just try it)
        dm_log(f"  → Looking for Message button...")
        
        # Wait for buttons to appear (retry up to 3 times)
        debug_info = []
        for attempt in range(3):
            debug_info = page.evaluate('''() => {
                const btns = [];
                document.querySelectorAll('button').forEach(el => {
                    const text = (el.textContent || '').trim();
                    if (text && el.offsetParent !== null) {
                        btns.push(text.substring(0, 25));
                    }
                });
                return btns.slice(0, 6);
            }''')
            if len(debug_info) > 0:
                break
            time.sleep(2)  # Wait and retry
        
        dm_log(f"  [DEBUG] Visible buttons: {debug_info}")
        
        # Click Message button - ONLY in profile area, NOT sidebar
        msg_clicked = page.evaluate('''() => {
            // IMPORTANT: Avoid sidebar navigation! Only look in main content area
            const sidebar = document.querySelector('[class*="Sidebar"], [class*="sidebar"], [class*="SideNav"], nav[class*="Nav"]');
            const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;

            // Helper to check if element is in sidebar (left side of page)
            const isInSidebar = (el) => {
                const rect = el.getBoundingClientRect();
                // Sidebar is typically on the left (x < 300) and full height
                if (rect.left < 250 && rect.width < 300) return true;
                // Also check parent classes
                let parent = el.parentElement;
                while (parent) {
                    const cls = (parent.className || '').toLowerCase();
                    if (cls.includes('sidebar') || cls.includes('sidenav') || cls.includes('navigation')) return true;
                    parent = parent.parentElement;
                }
                return false;
            };

            // Find all buttons NOT in sidebar
            const allBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                return b.offsetParent !== null && !isInSidebar(b);
            });

            // Debug: show profile area buttons
            const profileBtnTexts = allBtns.slice(0, 10).map(b => (b.textContent || '').trim().substring(0, 20));
            console.log('Profile buttons:', profileBtnTexts);

            // METHOD 1: Find Follow button first - Message button is usually next to it
            let followBtn = null;
            let followIdx = -1;
            const followWords = ['follow', 'volgen', 'suivre', 'seguir', 'folgen', 'подписаться', 'フォロー'];
            for (let i = 0; i < allBtns.length; i++) {
                const text = (allBtns[i].textContent || '').trim().toLowerCase();
                for (let fw of followWords) {
                    if (text === fw || text === fw + 'ing') {
                        followBtn = allBtns[i];
                        followIdx = i;
                        break;
                    }
                }
                if (followBtn) break;
            }

            // If found Follow, look for sibling Message button in same container
            if (followBtn) {
                const parent = followBtn.parentElement;
                if (parent) {
                    const siblingBtns = Array.from(parent.querySelectorAll('button, div[role="button"]')).filter(b => {
                        return b !== followBtn && b.offsetParent !== null && !isInSidebar(b);
                    });
                    for (let btn of siblingBtns) {
                        const text = (btn.textContent || '').trim().toLowerCase();
                        // Skip share/more/unfollow buttons
                        if (!text.includes('share') && !text.includes('deel') && !text.includes('more') &&
                            !text.includes('meer') && !text.includes('unfollow') && !text.includes('following')) {
                            btn.scrollIntoView({block: 'center'});
                            btn.click();
                            return {success: true, text: text || 'follow-sibling', method: 'follow-sibling', debug: profileBtnTexts};
                        }
                    }
                }

                // Try button immediately after Follow in DOM
                if (followIdx + 1 < allBtns.length) {
                    const nextBtn = allBtns[followIdx + 1];
                    const text = (nextBtn.textContent || '').trim().toLowerCase();
                    if (!text.includes('share') && !text.includes('deel') && !text.includes('more')) {
                        nextBtn.scrollIntoView({block: 'center'});
                        nextBtn.click();
                        return {success: true, text: text || 'after-follow', method: 'after-follow', debug: profileBtnTexts};
                    }
                }
            }

            // METHOD 2: Look for data-e2e message button (but NOT in sidebar)
            const dataE2eBtns = document.querySelectorAll('[data-e2e*="message"], [data-e2e*="Message"]');
            for (let btn of dataE2eBtns) {
                if (btn.offsetParent !== null && !isInSidebar(btn)) {
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    return {success: true, text: 'data-e2e:message', method: 'data-e2e', debug: profileBtnTexts};
                }
            }

            // METHOD 3: Find button with message text (exact match, not in sidebar)
            const messageWords = ['message', 'berichten', 'nachricht', 'messaggio', 'mensaje', 'mensagem', 'сообщение'];
            for (let btn of allBtns) {
                const text = (btn.textContent || '').trim().toLowerCase();
                for (let word of messageWords) {
                    if (text === word) {
                        btn.scrollIntoView({block: 'center'});
                        btn.click();
                        return {success: true, text: text, method: 'text-exact', debug: profileBtnTexts};
                    }
                }
            }

            return {success: false, debug: profileBtnTexts, followFound: !!followBtn, totalBtns: allBtns.length};
        }''')
        
        if not msg_clicked.get('success'):
            dm_log(f"  ⚠ No Message button found - user may have DMs disabled")
            dm_log(f"  [DEBUG] Profile buttons found: {msg_clicked.get('debug', [])}")
            dm_log(f"  [DEBUG] Follow button found: {msg_clicked.get('followFound', False)}")
            return False, "no_dm_button"

        dm_log(f"  ✓ Clicked Message button: '{msg_clicked.get('text')}' (method: {msg_clicked.get('method')})")
        
        # STEP 2: Wait for messages page
        dm_log(f"  → Waiting for chat to open...")
        time.sleep(4)
        
        # STEP 3: Find the message input and type (with retries)
        dm_log(f"  → Finding input field...")
        
        input_found = None
        for attempt in range(5):  # Try up to 5 times
            input_found = page.evaluate('''() => {
                // Try to find and click the input
                const selectors = [
                    '[contenteditable="true"]',
                    '[class*="InputArea"] [contenteditable="true"]',
                    '[class*="DivInput"] [contenteditable="true"]',
                    '[class*="MessageInput"] [contenteditable="true"]',
                    'textarea',
                    'input[type="text"]'
                ];
                
                for (let sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        el.click();
                        el.focus();
                        return {success: true, selector: sel};
                    }
                }
                return {success: false};
            }''')
            
            if input_found.get('success'):
                break
            time.sleep(1)  # Wait and retry
        
        if not input_found.get('success'):
            dm_log(f"  ⚠ Could not find message input after retries")
            return False, "no_input"
        
        dm_log(f"  ✓ Found input field")
        time.sleep(1)
        
        # STEP 4: Type the message
        dm_log(f"  → Typing message...")
        page.keyboard.type(message, delay=30)
        time.sleep(2)
        
        # STEP 5: Send the message
        dm_log(f"  → Sending message...")
        
        # Try clicking send button first
        send_clicked = page.evaluate('''() => {
            // Find button with SVG (send icon) in the input area
            const inputArea = document.querySelector('[class*="InputArea"], [class*="DivInput"]');
            if (inputArea) {
                const btns = inputArea.querySelectorAll('button, div[role="button"]');
                for (let btn of btns) {
                    if (btn.querySelector('svg') && btn.offsetParent !== null) {
                        btn.click();
                        return {success: true, method: 'svg-button'};
                    }
                }
            }
            
            // Try any button with send-related class
            const sendBtn = document.querySelector('[class*="Send"], [data-e2e*="send"]');
            if (sendBtn && sendBtn.offsetParent !== null) {
                sendBtn.click();
                return {success: true, method: 'send-class'};
            }
            
            return {success: false};
        }''')
        
        if not send_clicked.get('success'):
            dm_log(f"  → Using Enter key to send...")
            page.keyboard.press("Enter")
        else:
            dm_log(f"  ✓ Clicked send button")
        
        # STEP 6: Wait and confirm
        time.sleep(3)
        dm_log(f"  ✓ DM sent to @{username}")
        return True, "success"
        
    except Exception as e:
        dm_log(f"  ✗ Error: {str(e)[:100]}")
        return False, str(e)

def collect_users_from_hashtag(page, hashtag, limit=100):
    """Collect usernames from a hashtag page"""
    users = set()
    dm_log(f"→ Collecting users from #{hashtag}...")
    
    try:
        page.goto(f"https://www.tiktok.com/tag/{hashtag}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        for scroll in range(10):  # Scroll multiple times
            new_users = page.evaluate('''() => {
                const users = new Set();
                // Find all user links
                document.querySelectorAll('a[href*="/@"]').forEach(a => {
                    const match = a.href.match(/@([a-zA-Z0-9_.]+)/);
                    if (match) users.add(match[1]);
                });
                return Array.from(users);
            }''')
            
            users.update(new_users)
            
            if len(users) >= limit:
                break
            
            page.keyboard.press("ArrowDown")
            page.keyboard.press("ArrowDown")
            time.sleep(1)
        
        dm_log(f"✓ Found {len(users)} users from #{hashtag}")
        return list(users)[:limit]
    except Exception as e:
        dm_log(f"✗ Error collecting from hashtag: {e}")
        return []

def collect_users_from_comments(page, video_url, limit=100):
    """Collect usernames from video comments"""
    users = set()
    dm_log(f"→ Collecting commenters from video...")
    
    try:
        page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # Open comments
        page.evaluate('''() => {
            const btn = document.querySelector('[data-e2e="comment-icon"]');
            if (btn) btn.click();
        }''')
        time.sleep(2)
        
        for scroll in range(10):
            new_users = page.evaluate('''() => {
                const users = new Set();
                document.querySelectorAll('[data-e2e="comment-username-1"], [class*="CommentUsername"], a[href*="/@"]').forEach(el => {
                    const href = el.href || '';
                    const match = href.match(/@([a-zA-Z0-9_.]+)/);
                    if (match) users.add(match[1]);
                    // Also check text content
                    const text = el.textContent.trim();
                    if (text.startsWith('@')) users.add(text.slice(1));
                });
                return Array.from(users);
            }''')
            
            users.update(new_users)
            
            if len(users) >= limit:
                break
            
            # Scroll in comments
            page.evaluate('document.querySelector("[class*=CommentList]")?.scrollBy(0, 500)')
            time.sleep(1)
        
        dm_log(f"✓ Found {len(users)} commenters")
        return list(users)[:limit]
    except Exception as e:
        dm_log(f"✗ Error collecting commenters: {e}")
        return []

def collect_followers(page, account, limit=100):
    """Collect followers from an account"""
    users = set()
    dm_log(f"→ Collecting followers of @{account}...")
    
    try:
        page.goto(f"https://www.tiktok.com/@{account}", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        # Click followers count to open list
        page.evaluate('''() => {
            const followerLink = document.querySelector('[data-e2e="followers-count"]');
            if (followerLink) followerLink.click();
        }''')
        time.sleep(2)
        
        for scroll in range(10):
            new_users = page.evaluate('''() => {
                const users = new Set();
                document.querySelectorAll('[class*="UserList"] a[href*="/@"], [class*="follower"] a[href*="/@"]').forEach(a => {
                    const match = a.href.match(/@([a-zA-Z0-9_.]+)/);
                    if (match) users.add(match[1]);
                });
                return Array.from(users);
            }''')
            
            users.update(new_users)
            
            if len(users) >= limit:
                break
            
            page.evaluate('document.querySelector("[class*=UserList]")?.scrollBy(0, 500)')
            time.sleep(1)
        
        dm_log(f"✓ Found {len(users)} followers")
        return list(users)[:limit]
    except Exception as e:
        dm_log(f"✗ Error collecting followers: {e}")
        return []

def run_dm_automation_for_profile(ws_endpoint, profile_name):
    """Run DM automation for a single profile - NEW VERSION with brand search"""
    # Check if automation was stopped
    if not dm_status["running"]:
        dm_log(f"  [{profile_name}] ⏹ Stopped")
        return 0

    if not HAS_PLAYWRIGHT:
        dm_log("✗ Playwright not installed!")
        return 0

    dms_sent = 0
    max_dms = dm_settings.get("max_dms_per_profile", 100)
    
    # Check how many DMs this profile has already sent today
    dms_already_sent = get_dms_today(profile_name)
    remaining_for_profile = max_dms - dms_already_sent
    
    if remaining_for_profile <= 0:
        dm_log(f"  ⚠ Profile already at daily limit ({max_dms} DMs)")
        return 0
    
    # Check total daily limit
    total_today = get_total_dms_today()
    max_total = dm_settings.get("max_dms_total", 2500)
    remaining_total = max_total - total_today
    
    if remaining_total <= 0:
        dm_log(f"  ⚠ Total daily limit reached ({max_total} DMs)")
        return 0
    
    # Take the minimum of profile limit and remaining total
    to_send = min(remaining_for_profile, remaining_total)
    dm_log(f"  📊 Profile limit: {remaining_for_profile} | Total remaining: {remaining_total} | Will send: {to_send}")
    
    target_users = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            
            # === GUARDRAIL: Check if logged into TikTok ===
            dm_log(f"  → Checking TikTok login...")
            try:
                page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)
                if "login" in page.url.lower():
                    dm_log(f"  ⚠ NOT LOGGED IN - Skipping profile")
                    track_not_logged_in(profile_name, source="dm")
                    browser.close()
                    return -1
                dm_log(f"  ✓ Logged in")
            except Exception as e:
                dm_log(f"  ⚠ Login check failed - Skipping")
                browser.close()
                return -1

            # Auto-detect TikTok username and save to mapping
            try:
                page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
                current_url = page.url
                if "/@" in current_url:
                    match = re.search(r'/@([^/?]+)', current_url)
                    if match:
                        detected_username = match.group(1)
                        set_tiktok_username(profile_name, detected_username)
                        dm_log(f"  📱 Account: @{detected_username}")
            except:
                pass

            # Collect target users based on mode
            mode = dm_settings.get("target_mode", "brand_search")
            
            if mode == "brand_search":
                # NEW: Scrape brands from TikTok search
                target_users = scrape_brands_for_dm(page, num_brands=to_send + 20)
            elif mode == "specific":
                target_users = [u for u in dm_targets.get("specific_users", []) if u not in dm_status["sent_to"]]
            elif mode == "hashtag":
                hashtag = dm_settings.get("target_hashtag", "").strip().replace("#", "")
                if hashtag:
                    target_users = collect_users_from_hashtag(page, hashtag, 200)
                    target_users = [u for u in target_users if u not in dm_status["sent_to"]]
            elif mode == "commenters":
                video_url = dm_settings.get("target_video_url", "").strip()
                if video_url:
                    target_users = collect_users_from_comments(page, video_url, 200)
                    target_users = [u for u in target_users if u not in dm_status["sent_to"]]
            elif mode == "followers":
                account = dm_settings.get("target_account", "").strip().replace("@", "")
                if account:
                    target_users = collect_followers(page, account, 200)
                    target_users = [u for u in target_users if u not in dm_status["sent_to"]]
            
            # Filter already contacted
            target_users = [u for u in target_users if u not in dm_status["sent_to"]]
            
            if not target_users:
                dm_log(f"  ⚠ No new users to DM")
                browser.close()
                return 0
            
            dm_log(f"  → Found {len(target_users)} potential targets, will try until {to_send} DMs sent")
            
            # Loop through ALL available users until we hit our target
            users_tried = 0
            for username in target_users:
                if not dm_status["running"]:
                    dm_log(f"  ⏹ Stopped by user")
                    break
                
                # Stop if we've sent enough DMs
                if dms_sent >= to_send:
                    dm_log(f"  ✓ Reached target: {dms_sent} DMs sent")
                    break
                
                # Check limits again during loop
                if get_total_dms_today() >= max_total:
                    dm_log(f"  ⚠ Total daily limit reached")
                    break
                
                if get_dms_today(profile_name) >= max_dms:
                    dm_log(f"  ⚠ Profile daily limit reached")
                    break
                
                users_tried += 1
                dm_status["progress"] = dms_sent + 1
                dm_status["total"] = to_send
                
                message = get_dm_message(username)
                success, result = send_dm_to_user(page, username, message)
                
                if success:
                    dms_sent += 1
                    dm_status["dms_sent"] += 1
                    dm_status["dms_sent_today"] += 1
                    dm_status["sent_to"].add(username)
                    record_dm(profile_name)

                    # Take screenshot as proof of DM
                    dm_screenshot_path = None
                    try:
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dm_screenshot_filename = f"dm_{profile_name}_{timestamp_str}_{username[:15]}.png"
                        dm_screenshot_path = os.path.join(SCREENSHOTS_FOLDER, dm_screenshot_filename)
                        page.screenshot(path=dm_screenshot_path, full_page=False)
                        dm_log(f"    📸 DM screenshot saved: {dm_screenshot_filename}")
                    except Exception as e:
                        dm_log(f"    ⚠ Screenshot failed: {e}")

                    dm_status["report"].append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "profile": profile_name,
                        "username": username,
                        "profile_url": f"https://www.tiktok.com/@{username}",
                        "message": message[:50] + "..." if len(message) > 50 else message,
                        "status": "sent",
                        "search_mode": mode,
                        "screenshot": dm_screenshot_path
                    })
                    
                    # Sync DM to cloud
                    try:
                        threading.Thread(target=sync_dm_to_cloud, args=(dm_status["report"][-1],), daemon=True).start()
                    except:
                        pass
                    
                    save_dm_data()
                    
                    # Wait between DMs
                    delay = random.randint(dm_settings["min_delay"], dm_settings["max_delay"])
                    dm_log(f"  ⏳ Waiting {delay}s... (Sent: {dms_sent}/{to_send})")
                    for _ in range(delay):
                        if not dm_status["running"]:
                            break
                        time.sleep(1)
                else:
                    # Log the failure reason
                    if result == "user_not_found":
                        dm_log(f"  ⚠ User @{username} not found or private")
                    elif result == "no_dm_button":
                        dm_log(f"  ⚠ User @{username} - DMs disabled or private account")
                    else:
                        dm_log(f"  ⚠ Failed to DM @{username}: {result}")
                    
                    # Add to sent_to to avoid retrying the same user
                    dm_status["sent_to"].add(username)
                    
                    # Short delay between failures to avoid rate limiting
                    time.sleep(2)
            
            dm_log(f"  📊 Tried {users_tried} users, sent {dms_sent} DMs")
            
            browser.close()
            dm_log(f"✓ Profile {profile_name}: Sent {dms_sent} DMs")
            return dms_sent
            
    except Exception as e:
        dm_log(f"✗ Error: {e}")
        traceback.print_exc()
        return dms_sent

def process_dm_profile(profile_id, profile_name):
    """Process a single profile for DM automation"""
    # Check if automation was stopped before opening browser
    if not dm_status["running"]:
        dm_log(f"  [{profile_name}] ⏹ Stopped before opening browser")
        return 0

    dm_log(f"▶ Starting DM: {profile_name}")
    dm_status["current_profile"] = profile_name

    # Double-check running status before opening browser
    if not dm_status["running"]:
        dm_log(f"  [{profile_name}] ⏹ Stopped")
        return 0

    browser_data = open_browser(profile_id)
    if not browser_data or browser_data == "SKIP":
        dm_log(f"  ✗ Failed to open browser - skipping")
        return 0

    try:
        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
        if not ws_endpoint:
            dm_log(f"  ✗ No WebSocket endpoint")
            return 0

        time.sleep(3)
        dms_sent = run_dm_automation_for_profile(ws_endpoint, profile_name)
    finally:
        close_browser(profile_id)
        dm_log(f"  → Browser closed")
    
    return dms_sent

def start_dm_automation(selected_profile_ids=None):
    """Start the DM automation process
    
    Features:
    - Searches TikTok for brands/businesses
    - Max 100 DMs per profile per day
    - Max 2500 DMs total per day
    - 2 profiles open at a time (parallel)
    - Only processes selected profiles
    - Continues until all selected profiles hit daily quota
    """
    if dm_status["running"]:
        return False
    
    dm_status["running"] = True
    dm_status["logs"] = []
    dm_status["progress"] = 0
    dm_status["total"] = 0
    dm_status["profiles_completed"] = []
    dm_status["dms_sent_today"] = get_total_dms_today()
    
    # Filter to only selected profiles
    if selected_profile_ids:
        selected_profiles = [p for p in profiles if p.get("user_id") in selected_profile_ids]
    else:
        selected_profiles = profiles

    # Sort profiles numerically: tt1, tt2, tt3, ... tt10, tt11, etc.
    def sort_key(p):
        name = p.get("name", p.get("user_id", ""))
        import re
        match = re.search(r'(\d+)', name)
        if match:
            return int(match.group(1))
        return 999
    selected_profiles = sorted(selected_profiles, key=sort_key)

    if not selected_profiles:
        dm_log("✗ No profiles selected!")
        dm_status["running"] = False
        return False
    
    dm_log("═" * 50)
    dm_log("🚀 Starting Brand DM Outreach")
    dm_log("═" * 50)
    dm_log(f"📊 Settings:")
    dm_log(f"   Selected profiles: {len(selected_profiles)}")
    dm_log(f"   Max per profile: {dm_settings['max_dms_per_profile']} DMs")
    dm_log(f"   Max total/day: {dm_settings['max_dms_total']} DMs")
    dm_log(f"   Parallel browsers: {dm_settings['parallel_browsers']}")
    dm_log(f"   Mode: {dm_settings['target_mode']}")
    dm_log(f"   Already sent today: {dm_status['dms_sent_today']} DMs")
    dm_log("═" * 50)
    
    # Check if we've hit total daily limit
    if dm_status["dms_sent_today"] >= dm_settings["max_dms_total"]:
        dm_log(f"✗ Already at total daily limit ({dm_settings['max_dms_total']} DMs)")
        dm_status["running"] = False
        return False
    
    def run():
        total_dms = 0
        try:
            # Sort profiles by name numerically (tt1, tt2, ... tt25)
            def sort_key(p):
                name = p.get("name", p.get("user_id", ""))
                # Extract number from name like "tt1", "tt2", etc.
                import re
                match = re.search(r'(\d+)', str(name))
                return int(match.group(1)) if match else 999
            
            sorted_profiles = sorted(selected_profiles, key=sort_key)
            parallel = dm_settings.get("parallel_browsers", 2)
            max_total = dm_settings["max_dms_total"]
            max_per_profile = dm_settings["max_dms_per_profile"]
            
            dm_log(f"📋 Processing {len(sorted_profiles)} selected profiles")
            dm_log(f"🔄 Running {parallel} profiles at a time")
            
            profile_index = 0
            
            while profile_index < len(sorted_profiles) and dm_status["running"]:
                # Check if we've hit total daily limit
                if get_total_dms_today() >= max_total:
                    dm_log(f"🎯 Total daily limit reached ({max_total} DMs)")
                    break
                
                # Get next batch of profiles (2 at a time)
                batch = sorted_profiles[profile_index:profile_index + parallel]
                dm_log(f"")
                dm_log(f"📦 Batch {profile_index // parallel + 1}: {[p.get('name', p.get('user_id')) for p in batch]}")
                
                # Process each profile in batch sequentially (but with 2 browsers concept)
                batch_has_work = False
                for profile in batch:
                    if not dm_status["running"]:
                        break
                    
                    profile_id = profile.get("user_id")
                    profile_name = profile.get("name", profile_id)
                    
                    # Skip if profile already at daily limit
                    if get_dms_today(profile_name) >= max_per_profile:
                        dm_log(f"  ⏭ {profile_name} already at limit ({max_per_profile}), skipping")
                        dm_status["profiles_completed"].append(profile_name)
                        continue
                    
                    # Skip if total limit reached
                    if get_total_dms_today() >= max_total:
                        dm_log(f"  🎯 Total daily limit reached")
                        break
                    
                    dm_status["current_profile_index"] = profile_index
                    dms_sent = process_dm_profile(profile_id, profile_name)
                    total_dms += dms_sent
                    
                    if dms_sent > 0:
                        batch_has_work = True
                    
                    # Mark as completed if at limit
                    if get_dms_today(profile_name) >= max_per_profile:
                        dm_status["profiles_completed"].append(profile_name)
                    
                    # Wait between profiles
                    if dm_status["running"] and batch.index(profile) < len(batch) - 1:
                        delay = random.randint(15, 30)
                        dm_log(f"  ⏳ Switching profile in {delay}s...")
                        for _ in range(delay):
                            if not dm_status["running"]:
                                break
                            time.sleep(1)
                
                profile_index += parallel
                
                # Wait between batches
                if dm_status["running"] and profile_index < len(sorted_profiles) and batch_has_work:
                    delay = random.randint(30, 60)
                    dm_log(f"")
                    dm_log(f"⏳ Next batch in {delay}s...")
                    for _ in range(delay):
                        if not dm_status["running"]:
                            break
                        time.sleep(1)
            
        except Exception as e:
            dm_log(f"✗ Fatal error: {e}")
            traceback.print_exc()
        finally:
            dm_status["running"] = False
            dm_status["current_profile"] = None
            dm_log("")
            dm_log("═" * 50)
            dm_log(f"✅ DM Outreach Complete!")
            dm_log(f"   Total DMs sent this session: {total_dms}")
            dm_log(f"   Total DMs sent today: {get_total_dms_today()}")
            dm_log(f"   Profiles completed: {len(dm_status['profiles_completed'])}")
            dm_log("═" * 50)
    
    threading.Thread(target=run, daemon=True).start()
    return True

def stop_dm_automation():
    """Stop the DM automation"""
    dm_status["running"] = False
    dm_log("⏹ Stopping DM automation...")

# =============================================================================
# REPOST FUNCTIONS - Auto-scrape and repost TikTok content
# Monday: Brand content (Bump Connect/Kollabsy/Bump Syndicate)
# Tue-Sun: Social media content
# Max 2 reposts per profile per day
# =============================================================================

def post_log(message):
    """Log for repost operations"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [REPOST] {message}"
    post_status["logs"].append(log_entry)
    print(log_entry)
    if len(post_status["logs"]) > 200:
        post_status["logs"] = post_status["logs"][-200:]

def load_post_data():
    """Load repost tracker and history"""
    global repost_tracker
    try:
        with open(REPOST_TRACKER_FILE, 'r', encoding='utf-8') as f:
            repost_tracker = json.load(f)
            print(f"  Loaded repost tracker ({len(repost_tracker)} profiles)")
    except FileNotFoundError:
        pass
    except:
        pass
    try:
        with open(POST_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            post_status["history"] = data.get("history", [])
            post_status["posts_made"] = len(post_status["history"])
    except FileNotFoundError:
        pass
    except:
        pass

def save_post_data():
    """Save repost tracker and history"""
    try:
        with open(REPOST_TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(repost_tracker, f, indent=2)
    except:
        pass
    try:
        with open(POST_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"history": post_status["history"], "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)
    except:
        pass

def get_reposts_today(profile_name):
    today = datetime.now().strftime("%Y-%m-%d")
    return repost_tracker.get(profile_name, {}).get(today, 0)

def record_repost(profile_name):
    today = datetime.now().strftime("%Y-%m-%d")
    if profile_name not in repost_tracker:
        repost_tracker[profile_name] = {}
    repost_tracker[profile_name][today] = repost_tracker[profile_name].get(today, 0) + 1
    save_post_data()

def get_todays_search_terms():
    """Monday = brand content, Tue-Sun = social media content"""
    day = datetime.now().weekday()
    if day == 0:
        return BRAND_SEARCH_TERMS, "brand"
    else:
        return SOCIAL_MEDIA_SEARCH_TERMS, "social"

def scrape_and_repost(page, profile_name, search_terms, content_type):
    """Scrape TikTok search results and repost videos (max 2/day)"""
    max_reposts = post_settings["max_reposts_per_day"]
    remaining = max_reposts - get_reposts_today(profile_name)
    if remaining <= 0:
        post_log(f"  Already at {max_reposts} reposts today, skipping")
        return 0

    post_log(f"  Need {remaining} repost(s) ({content_type} content)")
    reposts_made = 0
    search_term = random.choice(search_terms)

    # Get the TikTok username by navigating to profile page first
    tiktok_username = None
    try:
        post_log(f"  Getting account username...")
        # Navigate to TikTok profile page to get the username
        page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # The profile page URL will contain the username
        current_url = page.url
        if "/@" in current_url:
            match = re.search(r'/@([^/?]+)', current_url)
            if match:
                tiktok_username = match.group(1)

        # If URL doesn't have it, try extracting from page elements
        if not tiktok_username:
            tiktok_username = page.evaluate('''() => {
                // Method 1: Check canonical link (most reliable on profile page)
                const canonical = document.querySelector('link[rel="canonical"]');
                if (canonical && canonical.href.includes('/@')) {
                    const match = canonical.href.match(/\\/@([^/?]+)/);
                    if (match) return match[1];
                }
                // Method 2: Check og:url meta tag
                const ogUrl = document.querySelector('meta[property="og:url"]');
                if (ogUrl && ogUrl.content.includes('/@')) {
                    const match = ogUrl.content.match(/\\/@([^/?]+)/);
                    if (match) return match[1];
                }
                // Method 3: Look for username display element
                const usernameEl = document.querySelector('[data-e2e="user-subtitle"], [class*="SpanUniqueId"], h2[data-e2e="user-subtitle"]');
                if (usernameEl) {
                    const text = usernameEl.textContent.trim();
                    if (text.startsWith('@')) return text.substring(1);
                    return text;
                }
                // Method 4: Get from profile header
                const headerUsername = document.querySelector('[class*="ShareTitle"] span, [class*="UserTitle"]');
                if (headerUsername) return headerUsername.textContent.trim().replace('@', '');
                return null;
            }''')

        if tiktok_username:
            post_log(f"  Logged in as: @{tiktok_username}")
            # Save to mapping for future use
            set_tiktok_username(profile_name, tiktok_username)
        else:
            # Fall back to saved mapping
            tiktok_username = get_tiktok_username(profile_name)
            if tiktok_username:
                post_log(f"  Using saved username: @{tiktok_username}")
            else:
                post_log(f"  ⚠ Could not detect username (set mapping in Settings)")
    except Exception as e:
        post_log(f"  ⚠ Username detection error: {str(e)[:40]}")
        # Fall back to saved mapping on error
        tiktok_username = get_tiktok_username(profile_name)

    try:
        encoded = search_term.replace(" ", "%20")
        post_log(f"  Searching: '{search_term}'")
        page.goto(f"https://www.tiktok.com/search/video?q={encoded}", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        
        if "login" in page.url.lower():
            post_log(f"  Not logged in, skipping")
            track_not_logged_in(profile_name, source="repost")
            return 0

        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(2)
        
        video_links = page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a[href*="/video/"]').forEach(a => {
                if (a.href && !links.includes(a.href)) links.push(a.href);
            });
            return links.slice(0, 10);
        }''')
        
        # Retry with different search terms until we find videos
        retry_count = 0
        max_retries = min(3, len(search_terms))
        while not video_links and retry_count < max_retries:
            search_term = random.choice([t for t in search_terms if t != search_term])
            encoded = search_term.replace(" ", "%20")
            post_log(f"  Retrying: '{search_term}'")
            page.goto(f"https://www.tiktok.com/search/video?q={encoded}", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            page.evaluate("window.scrollBy(0, 400)")
            time.sleep(2)
            video_links = page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a[href*="/video/"]').forEach(a => {
                    if (a.href && !links.includes(a.href)) links.push(a.href);
                });
                return links.slice(0, 10);
            }''')
            retry_count += 1

        post_log(f"  Found {len(video_links)} videos")
        random.shuffle(video_links)
        
        for video_url in video_links[:remaining + 3]:
            if reposts_made >= remaining or not post_status["running"]:
                break
            try:
                post_log(f"  Opening: ...{video_url[-30:]}")
                page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)
                
                # Step 1: Click the Share button to open the share modal
                post_log(f"  → Clicking share button...")
                share_clicked = page.evaluate('''() => {
                    // Method 1: data-e2e selectors (most reliable)
                    const dataE2eSelectors = [
                        '[data-e2e="share-icon"]',
                        '[data-e2e="video-share-icon"]',
                        '[data-e2e*="share"]'
                    ];
                    for (let sel of dataE2eSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent) {
                            el.scrollIntoView({block: 'center'});
                            el.click();
                            return {ok: true, method: 'data-e2e'};
                        }
                    }

                    // Method 2: aria-label
                    const ariaSelectors = [
                        '[aria-label="Share video"]',
                        '[aria-label*="Share"]',
                        '[aria-label*="share"]',
                        '[title*="Share"]'
                    ];
                    for (let sel of ariaSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent) {
                            el.scrollIntoView({block: 'center'});
                            el.click();
                            return {ok: true, method: 'aria'};
                        }
                    }

                    // Method 3: Look for share icon in the action bar (right side of video)
                    const actionBars = document.querySelectorAll('[class*="ActionBar"], [class*="action-bar"], [class*="DivActionItemContainer"]');
                    for (let bar of actionBars) {
                        const btns = bar.querySelectorAll('button, [role="button"], span[class*="Icon"]');
                        for (let btn of btns) {
                            const svg = btn.querySelector('svg');
                            if (svg && btn.offsetParent) {
                                // Share icon usually has an arrow or is after like/comment/save
                                btn.click();
                                return {ok: true, method: 'action-bar'};
                            }
                        }
                    }

                    // Method 4: Find buttons on right side of screen with SVG icons
                    const allBtns = document.querySelectorAll('button, [role="button"]');
                    const rightBtns = Array.from(allBtns).filter(b => {
                        if (!b.offsetParent) return false;
                        const rect = b.getBoundingClientRect();
                        return rect.left > window.innerWidth * 0.6; // Right 40% of screen
                    });
                    // Share is usually 4th or 5th button (after like, comment, save, favorite)
                    for (let btn of rightBtns.slice(3, 6)) {
                        if (btn.querySelector('svg')) {
                            btn.click();
                            return {ok: true, method: 'right-side'};
                        }
                    }

                    return {ok: false};
                }''')
                
                if not share_clicked.get('ok'):
                    post_log(f"  ✗ Share button not found")
                    continue

                post_log(f"  ✓ Share clicked ({share_clicked.get('method')})")
                time.sleep(4)  # Wait for share modal to fully load

                # Step 2: Click the Repost button in the share modal
                post_log(f"  → Looking for Repost button...")

                # First debug what's in the modal
                modal_debug = page.evaluate('''() => {
                    const items = [];
                    document.querySelectorAll('[class*="Share"] span, [class*="share"] span, [role="dialog"] span').forEach(el => {
                        const t = (el.textContent || '').trim();
                        if (t && t.length < 30) items.push(t);
                    });
                    return items.slice(0, 10);
                }''')
                post_log(f"  [DEBUG] Modal items: {modal_debug}")

                repost_clicked = page.evaluate('''() => {
                    // Multi-language repost words
                    const repostWords = ['repost', 'reposten', 'republier', 'repostear', 'ripubblicare', 'opnieuw posten', 'повторить'];

                    // Method 1: data-e2e for repost
                    const repostE2e = document.querySelector('[data-e2e="share-to-repost"], [data-e2e*="repost"]');
                    if (repostE2e && repostE2e.offsetParent) {
                        repostE2e.click();
                        return {ok: true, method: 'data-e2e'};
                    }

                    // Method 2: Look for exact "Repost" text in modal
                    const modal = document.querySelector('[role="dialog"], [class*="SharePanel"], [class*="share-panel"], [class*="Modal"]');
                    if (modal) {
                        const elements = modal.querySelectorAll('button, div, span, [role="button"], [class*="Item"]');
                        for (let el of elements) {
                            const text = (el.textContent || '').trim().toLowerCase();
                            for (let word of repostWords) {
                                if (text === word || (text.includes(word) && text.length < 25)) {
                                    el.click();
                                    return {ok: true, method: 'modal-text', text: text};
                                }
                            }
                        }
                    }

                    // Method 3: Look for repost in any share-related container
                    const shareContainers = document.querySelectorAll('[class*="ShareLayoutMain"], [class*="share-layout"], [class*="ShareMenu"]');
                    for (let container of shareContainers) {
                        const items = container.querySelectorAll('[class*="ItemContainer"], [class*="item"], button, div');
                        for (let item of items) {
                            const txt = (item.textContent || '').trim().toLowerCase();
                            for (let word of repostWords) {
                                if (txt === word || (txt.includes(word) && txt.length < 25)) {
                                    item.click();
                                    return {ok: true, method: 'container-item', text: txt};
                                }
                            }
                        }
                    }

                    // Method 4: First item with circular arrow icon (repost icon)
                    const allItems = document.querySelectorAll('[class*="Share"] [class*="Item"], [role="dialog"] button');
                    if (allItems.length > 0) {
                        // Repost is usually the first action in share modal
                        const firstItem = allItems[0];
                        if (firstItem.offsetParent) {
                            firstItem.click();
                            return {ok: true, method: 'first-item'};
                        }
                    }

                    // Method 5: aria-label
                    const ariaBtn = document.querySelector('[aria-label*="Repost" i], [aria-label*="repost" i]');
                    if (ariaBtn && ariaBtn.offsetParent) {
                        ariaBtn.click();
                        return {ok: true, method: 'aria'};
                    }

                    return {ok: false};
                }''')
                
                if repost_clicked.get('ok'):
                    post_log(f"  → Clicked Repost ({repost_clicked.get('method')}), waiting for confirmation...")
                    time.sleep(3)  # Wait for confirmation/animation
                    
                    # Check if repost was successful (look for confirmation or undo button)
                    confirmed = page.evaluate('''() => {
                        const body = document.body.innerText.toLowerCase();
                        if (body.includes('reposted') || body.includes('undo')) return true;
                        // Check if modal closed
                        const modal = document.querySelector('[class*="SharePanel"], [class*="share-panel"]');
                        if (!modal || !modal.offsetParent) return true; // Modal closed = success
                        return false;
                    }''')
                    
                    if confirmed:
                        post_log(f"  ✓ Repost confirmed!")

                    reposts_made += 1
                    record_repost(profile_name)

                    # Take screenshot as proof of repost
                    post_screenshot_path = None
                    try:
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        post_screenshot_filename = f"repost_{profile_name}_{timestamp_str}.png"
                        post_screenshot_path = os.path.join(SCREENSHOTS_FOLDER, post_screenshot_filename)
                        page.screenshot(path=post_screenshot_path, full_page=False)
                        post_log(f"  📸 Repost screenshot saved")
                    except Exception as e:
                        post_log(f"  ⚠ Screenshot failed: {e}")

                    # Build repost_url - link directly to the Reposts tab on the profile
                    repost_url = f"https://www.tiktok.com/@{tiktok_username}?tab=reposts" if tiktok_username else None

                    entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "profile": profile_name,
                        "video": video_url,
                        "repost_url": repost_url,
                        "tiktok_username": tiktok_username,
                        "caption": f"Reposted {content_type}: {search_term}",
                        "status": "reposted",
                        "content_type": content_type,
                        "screenshot": post_screenshot_path,
                    }
                    post_status["history"].append(entry)
                    post_status["posts_made"] += 1
                    save_post_data()
                    try:
                        threading.Thread(target=sync_post_to_cloud, args=(entry,), daemon=True).start()
                    except:
                        pass
                    post_log(f"  ✓ Done! ({reposts_made}/{remaining})")
                    if reposts_made < remaining:
                        delay = random.randint(post_settings["min_delay"], post_settings["max_delay"])
                        post_log(f"  Waiting {delay}s...")
                        for _ in range(delay):
                            if not post_status["running"]:
                                break
                            time.sleep(1)
                else:
                    post_log(f"  ✗ Repost button not found in modal")
            except Exception as e:
                post_log(f"  Error: {str(e)[:60]}")
    except Exception as e:
        post_log(f"  Scrape error: {str(e)[:80]}")
    return reposts_made

def repost_from_source_accounts(page, profile_name):
    """Repost videos from source accounts (REPOST_SOURCE_ACCOUNTS list)"""
    max_reposts = post_settings["max_reposts_per_day"]
    remaining = max_reposts - get_reposts_today(profile_name)
    if remaining <= 0:
        post_log(f"  Already at {max_reposts} reposts today, skipping")
        return 0

    post_log(f"  Need {remaining} repost(s) from source accounts")
    reposts_made = 0

    # Get the logged-in TikTok username
    tiktok_username = get_tiktok_username(profile_name)
    if not tiktok_username:
        try:
            page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            current_url = page.url
            if "/@" in current_url:
                match = re.search(r'/@([^/?]+)', current_url)
                if match:
                    tiktok_username = match.group(1)
                    set_tiktok_username(profile_name, tiktok_username)
                    post_log(f"  Logged in as: @{tiktok_username}")
        except:
            pass

    if "login" in page.url.lower():
        post_log(f"  Not logged in, skipping")
        track_not_logged_in(profile_name, source="repost_source")
        return 0

    # Pick a random source account
    source_account = random.choice(REPOST_SOURCE_ACCOUNTS)
    post_log(f"  Source account: @{source_account}")

    try:
        # Navigate to source account's profile
        page.goto(f"https://www.tiktok.com/@{source_account}", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Scroll to load videos
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(2)

        # Get video links from their profile
        video_links = page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a[href*="/video/"]').forEach(a => {
                if (a.href && !links.includes(a.href)) links.push(a.href);
            });
            return links.slice(0, 10);
        }''')

        post_log(f"  Found {len(video_links)} videos from @{source_account}")
        random.shuffle(video_links)

        for video_url in video_links[:remaining + 3]:
            if reposts_made >= remaining or not post_status["running"]:
                break
            try:
                post_log(f"  Opening: ...{video_url[-30:]}")
                page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(4)

                # Click the Share button
                post_log(f"  → Clicking share button...")
                share_clicked = page.evaluate('''() => {
                    const selectors = [
                        '[data-e2e="share-icon"]',
                        '[data-e2e="video-share-icon"]',
                        '[data-e2e*="share"]',
                        'button[aria-label*="Share"]',
                        '[class*="ButtonShare"]',
                        '[class*="share-icon"]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }''')

                if not share_clicked:
                    post_log(f"  ✗ Share button not found")
                    continue

                time.sleep(2)

                # Click the Repost button in the share modal
                post_log(f"  → Clicking repost button...")
                repost_clicked = page.evaluate('''() => {
                    const repostSelectors = [
                        '[data-e2e="share-repost"]',
                        '[data-e2e*="repost"]',
                        'div[class*="Repost"]',
                        'button:has-text("Repost")',
                        'span:has-text("Repost")'
                    ];
                    for (const sel of repostSelectors) {
                        try {
                            const el = document.querySelector(sel);
                            if (el && el.offsetParent !== null) {
                                el.click();
                                return true;
                            }
                        } catch(e) {}
                    }
                    const allElements = document.querySelectorAll('div, button, span');
                    for (const el of allElements) {
                        if (el.textContent.trim() === 'Repost' && el.offsetParent !== null) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }''')

                if repost_clicked:
                    time.sleep(2)
                    post_log(f"  ✓ Repost clicked!")

                    reposts_made += 1
                    record_repost(profile_name)

                    # Build repost_url
                    repost_url = f"https://www.tiktok.com/@{tiktok_username}?tab=reposts" if tiktok_username else None

                    entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "profile": profile_name,
                        "video": video_url,
                        "repost_url": repost_url,
                        "tiktok_username": tiktok_username,
                        "caption": f"Reposted from @{source_account}",
                        "status": "reposted",
                        "content_type": "source_account",
                        "source_account": source_account,
                    }
                    post_status["history"].append(entry)
                    post_status["posts_made"] += 1
                    save_post_data()

                    post_log(f"  ✓ Done! ({reposts_made}/{remaining})")
                    if reposts_made < remaining:
                        delay = random.randint(post_settings["min_delay"], post_settings["max_delay"])
                        post_log(f"  Waiting {delay}s...")
                        for _ in range(delay):
                            if not post_status["running"]:
                                break
                            time.sleep(1)
                else:
                    post_log(f"  ✗ Repost button not found")
            except Exception as e:
                post_log(f"  Error: {str(e)[:60]}")
    except Exception as e:
        post_log(f"  Source account error: {str(e)[:80]}")
    return reposts_made

def run_repost_for_profile(profile_id, profile_name, use_source_accounts=False):
    """Open browser and run repost for one profile"""
    # Check if automation was stopped before opening browser
    if not post_status["running"]:
        post_log(f"  [{profile_name}] ⏹ Stopped before opening browser")
        return 0

    if use_source_accounts:
        post_log(f"[{profile_name}] Reposting from source accounts")
        content_type = "source_account"
    else:
        search_terms, content_type = get_todays_search_terms()
        day_name = datetime.now().strftime("%A")
        post_log(f"[{profile_name}] {day_name}: {content_type} content")

    post_status["current_profile"] = profile_name

    if get_reposts_today(profile_name) >= post_settings["max_reposts_per_day"]:
        post_log(f"  At daily limit, skipping")
        return 0

    # Double-check running status before opening browser
    if not post_status["running"]:
        post_log(f"  [{profile_name}] ⏹ Stopped")
        return 0

    browser_data = open_browser(profile_id)
    if not browser_data or browser_data == "SKIP":
        post_log(f"  Failed to open browser - skipping")
        return 0

    try:
        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
        if not ws_endpoint:
            post_log(f"  No WebSocket endpoint")
            return 0

        time.sleep(3)
        reposts = 0
        if HAS_PLAYWRIGHT:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.connect_over_cdp(ws_endpoint)
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                    page = context.pages[0] if context.pages else context.new_page()
                    if use_source_accounts:
                        reposts = repost_from_source_accounts(page, profile_name)
                    else:
                        reposts = scrape_and_repost(page, profile_name, search_terms, content_type)
                    browser.close()
            except Exception as e:
                post_log(f"  Playwright error: {str(e)[:80]}")
    finally:
        close_browser(profile_id)
    post_log(f"  Done. Reposts: {reposts}")
    return reposts

def start_repost_automation(use_source_accounts=False):
    """Start automated repost across all profiles"""
    if post_status["running"]:
        return False
    if not profiles:
        post_log("No profiles loaded! Sync first.")
        return False

    search_terms, content_type = get_todays_search_terms()
    day_name = datetime.now().strftime("%A")
    today_str = datetime.now().strftime("%Y-%m-%d")

    if use_source_accounts:
        content_type = "source_accounts"

    # Sort profiles numerically: tt1, tt2, tt3, ... tt10, tt11, etc.
    def sort_key(p):
        name = p.get("name", p.get("user_id", ""))
        # Extract number from name like "tt1", "tt12", etc.
        import re
        match = re.search(r'(\d+)', name)
        if match:
            return int(match.group(1))
        return 999  # Put non-numeric names at the end

    sorted_profiles = sorted(profiles, key=sort_key)

    post_status["running"] = True
    post_status["logs"] = []
    post_status["progress"] = 0
    post_status["total"] = len(sorted_profiles)

    post_log("=" * 50)
    post_log(f"Auto Repost - {day_name}, {today_str}")
    if use_source_accounts:
        post_log(f"Content: Source Accounts ({', '.join(REPOST_SOURCE_ACCOUNTS[:3])}...)")
    else:
        post_log(f"Content: {'Brand (Bump Connect/Kollabsy/Bump Syndicate)' if content_type == 'brand' else 'Social Media'}")
    post_log(f"Profiles: {len(sorted_profiles)} | Max {post_settings['max_reposts_per_day']}/profile/day")
    post_log(f"Order: {', '.join([p.get('name', p.get('user_id'))[:6] for p in sorted_profiles[:5]])}...")
    post_log("=" * 50)

    def run():
        total_reposts = 0
        try:
            for i, profile in enumerate(sorted_profiles):
                if not post_status["running"]:
                    break
                pid = profile.get("user_id")
                pname = profile.get("name", pid)
                post_status["progress"] = i + 1
                total_reposts += run_repost_for_profile(pid, pname, use_source_accounts)
                if i < len(profiles) - 1 and post_status["running"]:
                    delay = random.randint(30, 60)
                    post_log(f"Next profile in {delay}s...")
                    for _ in range(delay):
                        if not post_status["running"]:
                            break
                        time.sleep(1)
        except Exception as e:
            post_log(f"Fatal: {e}")
        finally:
            post_status["running"] = False
            post_status["current_profile"] = None
            post_status["last_run"] = today_str
            post_log("=" * 50)
            post_log(f"Done! Total reposts: {total_reposts}")
            post_log("=" * 50)
    
    threading.Thread(target=run, daemon=True).start()
    return True

def stop_post_automation():
    post_status["running"] = False
    post_log("Stopping repost automation...")

def fetch_adspower_profiles():
    """Fetch profiles from AdsPower API"""
    global profiles
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=5)
        data = response.json()
        if data.get("code") == 0:
            profiles = data.get("data", {}).get("list", [])
            log(f"✓ Loaded {len(profiles)} profiles from AdsPower")
            return True
        log(f"✗ AdsPower error: {data.get('msg')}")
    except requests.exceptions.ConnectionError:
        log("✗ Cannot connect to AdsPower - is it running?")
    except Exception as e:
        log(f"✗ Error: {e}")
    return False

def fetch_google_sheet_comments(sheet_name):
    global comments_cache
    try:
        encoded_name = sheet_name.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            reader = csv.reader(io.StringIO(response.text))
            next(reader, None)
            comments = [row[0].strip() for row in reader if row and row[0].strip()]
            comments_cache[sheet_name] = comments
            log(f"✓ Loaded {len(comments)} comments from '{sheet_name}'")
            return comments
    except Exception as e:
        log(f"✗ Error loading comments: {e}")
    return []

def open_browser(profile_id):
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=120)
        data = response.json()
        if data.get("code") == 0:
            return data.get("data", {})
        msg = data.get('msg', '')
        # Skip profiles where browser is not ready/installing
        if any(x in msg for x in ['being installed', 'not ready', 'installing', 'Too many request']):
            log(f"  ⚠ Skipping {profile_id}: {msg}")
            return "SKIP"
        log(f"  ✗ Error: {msg}")
    except requests.exceptions.Timeout:
        log(f"  ✗ Timeout opening browser {profile_id} - skipping")
        return "SKIP"
    except Exception as e:
        log(f"  ✗ Error opening browser: {e}")
    return None

def close_browser(profile_id):
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile_id}", timeout=10)
    except:
        pass

# Promotional comments - natural with website links
PROMO_COMMENTS = {
    "Bump Connect": [
        "omg this reminds me of something I saw on Bump Connect 😂 bumpconnect.com",
        "the creator community on Bump Connect would love this - bumpconnect.com",
        "giving Bump Connect vibes fr fr ✨ bumpconnect.com",
        "this is the type of content we share on Bump Connect 🔥 bumpconnect.com",
        "you should post this on Bump Connect too! bumpconnect.com",
        "I found so many creators like you on Bump Connect - check bumpconnect.com",
        "Bump Connect creators are doing stuff like this 👀 bumpconnect.com",
        "love this! the Bump Connect community needs to see this - bumpconnect.com",
        "this is why I love Bump Connect bumpconnect.com 🙌",
        "just shared this with my Bump Connect group - join at bumpconnect.com",
        "Bump Connect vibes ✨ bumpconnect.com",
        "anyone else here from Bump Connect? 🙋 bumpconnect.com",
        "this would blow up on Bump Connect - bumpconnect.com",
        "Bump Connect creators doing it right 💯 bumpconnect.com",
        "found you through Bump Connect btw! bumpconnect.com",
        "Bump Connect fam where you at 🔥 bumpconnect.com",
        "this creator gets it, Bump Connect type content - bumpconnect.com",
        "saving this for my Bump Connect friends 😂 bumpconnect.com",
        "if you're a creator check out bumpconnect.com 🚀",
        "creators supporting creators 🙌 bumpconnect.com",
    ],
    "Kollabsy": [
        "this is the collab energy we need ✨ kollabsy.xyz",
        "found amazing collabs like this on Kollabsy - kollabsy.xyz",
        "Kollabsy creators would love to collab with you! kollabsy.xyz",
        "giving me Kollabsy collab ideas rn 😂 kollabsy.xyz",
        "the Kollabsy community appreciates this 🙌 kollabsy.xyz",
        "this is what Kollabsy collabs look like - kollabsy.xyz",
        "you should check out Kollabsy for collabs! kollabsy.xyz",
        "Kollabsy energy right here ✨ kollabsy.xyz",
        "I found my collab partner on Kollabsy 🔥 kollabsy.xyz",
        "looking for collabs? check kollabsy.xyz",
        "collab with creators like this at kollabsy.xyz 🤝",
        "Kollabsy is where the real collabs happen - kollabsy.xyz",
    ],
    "Bump Syndicate": [
        "this is what we talk about in Bump Syndicate 😂 bumpsyndicate.xyz",
        "Bump Syndicate community would appreciate this - bumpsyndicate.xyz",
        "giving Bump Syndicate group chat energy 🔥 bumpsyndicate.xyz",
        "just shared this in Bump Syndicate - join at bumpsyndicate.xyz",
        "the Bump Syndicate fam needs to see this 👀 bumpsyndicate.xyz",
        "this is Bump Syndicate approved content 💯 bumpsyndicate.xyz",
        "Bump Syndicate creators doing it different - bumpsyndicate.xyz",
        "love finding content like this ✨ bumpsyndicate.xyz",
        "Bump Syndicate gang where you at 🔥 bumpsyndicate.xyz",
        "posting this to Bump Syndicate rn - bumpsyndicate.xyz",
        "join the best creator community at bumpsyndicate.xyz 🙌",
        "creator growth tips at bumpsyndicate.xyz",
    ]
}

def get_random_comment(sheet_name):
    """Get a random promotional comment for one of the brands"""
    # Pick a random brand
    brand = random.choice(list(PROMO_COMMENTS.keys()))
    comments = PROMO_COMMENTS[brand]
    
    if comments:
        comment = random.choice(comments)
        return comment, brand
    return None, None

# =============================================================================
# IMPROVED TIKTOK AUTOMATION WITH RETRY LOGIC
# =============================================================================

MAX_RETRIES = 3
RETRY_DELAY = 5

def safe_click(page, selectors, description="element", timeout=5000):
    """Safely click an element with multiple selector fallbacks"""
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=timeout):
                element.click(timeout=timeout)
                return True, selector
        except:
            continue
    return False, None

def safe_wait_for_video(page, timeout=15000):
    """Wait for video content to load with multiple strategies"""
    strategies = [
        ('video', 'video element'),
        ('[data-e2e="browse-video"]', 'browse video'),
        ('[class*="DivVideoContainer"]', 'video container'),
        ('[class*="video-card"]', 'video card'),
    ]
    
    for selector, name in strategies:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return True, name
        except:
            continue
    return False, None

def check_login_status(page):
    """Check if user is logged in to TikTok - IMPROVED to detect sidebar Log in button"""
    try:
        # Check URL for login redirect
        if "login" in page.url.lower() or "signup" in page.url.lower():
            return False

        # Check for login buttons/prompts in page (more aggressive detection)
        login_indicators = page.evaluate('''() => {
            // Method 1: Check for data-e2e login button
            if (document.querySelector('[data-e2e="login-button"]')) return true;
            if (document.querySelector('[class*="LoginModal"]')) return true;

            // Method 2: Check for "Log in" button text in sidebar or anywhere prominent
            const buttons = document.querySelectorAll('button, a, div[role="button"]');
            for (let btn of buttons) {
                const text = (btn.textContent || '').trim().toLowerCase();
                // Exact match for "log in" button (the red button in sidebar)
                if (text === 'log in' || text === 'login') {
                    // Check if it's visible and reasonably sized (not a tiny link)
                    if (btn.offsetParent !== null && btn.offsetHeight > 20) {
                        return true;
                    }
                }
            }

            // Method 3: Check sidebar specifically for Login button
            const sidebar = document.querySelector('[class*="SideNav"], [class*="Sidebar"], nav');
            if (sidebar) {
                const sidebarText = sidebar.innerText.toLowerCase();
                if (sidebarText.includes('log in') && !sidebarText.includes('log out')) {
                    return true;
                }
            }

            // Method 4: Check for login links that are prominent
            const loginLinks = document.querySelectorAll('a[href*="/login"]');
            for (let link of loginLinks) {
                if (link.offsetParent !== null && link.offsetHeight > 30) return true;
            }

            // Method 5: Check comments section for "Log in" button
            const commentSection = document.querySelector('[class*="Comment"], [data-e2e*="comment"]');
            if (commentSection) {
                const commentButtons = commentSection.querySelectorAll('button');
                for (let btn of commentButtons) {
                    const text = (btn.textContent || '').trim().toLowerCase();
                    if (text === 'log in' || text === 'login') {
                        return true;
                    }
                }
            }

            return false;
        }''')

        return not login_indicators
    except:
        return True  # Assume logged in if check fails

def click_comment_button(page):
    """Click the comment button with updated selectors for 2026 TikTok"""
    # Close any open dialogs first
    try:
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except:
        pass

    # Updated selectors for TikTok 2026
    result = page.evaluate('''() => {
        // Helper to check if element is share-related
        function isShareElement(el) {
            if (!el) return false;
            const text = (el.textContent || '').toLowerCase();
            const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
            const className = (el.className || '').toLowerCase();
            const dataE2e = (el.getAttribute('data-e2e') || '').toLowerCase();
            return text.includes('share') || ariaLabel.includes('share') ||
                   className.includes('share') || dataE2e.includes('share') ||
                   text.includes('copy') || ariaLabel.includes('copy');
        }

        // Method 1: data-e2e attribute (most reliable)
        let btn = document.querySelector('[data-e2e="comment-icon"]');
        if (btn && !isShareElement(btn)) { btn.click(); return {success: true, method: 'data-e2e-comment-icon'}; }

        // Method 2: Browse comment icon
        btn = document.querySelector('[data-e2e="browse-comment-icon"]');
        if (btn && !isShareElement(btn)) { btn.click(); return {success: true, method: 'data-e2e-browse-comment'}; }

        // Method 3: Video comment icon
        btn = document.querySelector('[data-e2e="video-comment-icon"]');
        if (btn && !isShareElement(btn)) { btn.click(); return {success: true, method: 'data-e2e-video-comment'}; }

        // Method 4: Look for comment count/number near a clickable element
        const allElements = document.querySelectorAll('button, [role="button"], span[class*="Count"], span[class*="Number"]');
        for (let el of allElements) {
            const text = el.textContent || '';
            const parent = el.closest('button, [role="button"], [class*="Comment"]');
            // Check if this looks like a comment count (numbers like 123, 1.2K, etc)
            if (/^[\\d.]+[KMB]?$/i.test(text.trim()) && parent && !isShareElement(parent)) {
                // Check if the parent container has comment-related classes
                const containerClass = (parent.className || '') + (parent.parentElement?.className || '');
                if (containerClass.toLowerCase().includes('comment')) {
                    parent.click();
                    return {success: true, method: 'comment-count'};
                }
            }
        }

        // Method 5: aria-label variations (be more specific)
        const commentLabels = ['comment', 'comments'];
        for (let label of commentLabels) {
            const elements = document.querySelectorAll('[aria-label*="' + label + '" i]');
            for (let el of elements) {
                if (el && !isShareElement(el) && !isShareElement(el.parentElement) && el.offsetParent) {
                    // Extra check: make sure it's not in a share container
                    const container = el.closest('[class*="Share"], [data-e2e*="share"]');
                    if (!container) {
                        el.click();
                        return {success: true, method: 'aria-label-' + label};
                    }
                }
            }
        }

        // Method 6: Find the comment bubble SVG specifically (chat bubble shape)
        // Comment bubble SVG usually has a tail/pointer at the bottom
        const svgs = document.querySelectorAll('svg');
        for (let svg of svgs) {
            const paths = svg.querySelectorAll('path');
            for (let path of paths) {
                const d = path.getAttribute('d') || '';
                // Comment bubble specific patterns - look for bubble with tail
                // Avoid share icon which is typically an arrow
                if (d.includes('M') && !d.includes('arrow') &&
                    (d.includes('bubble') || d.includes('chat') ||
                     (d.includes('c') && d.includes('z') && d.length > 100))) {
                    const parent = svg.closest('button, [role="button"]');
                    if (parent && parent.offsetParent && !isShareElement(parent)) {
                        parent.click();
                        return {success: true, method: 'svg-bubble'};
                    }
                }
            }
        }

        // Method 7: Action bar - find by position relative to like button
        const likeBtn = document.querySelector('[data-e2e="like-icon"], [data-e2e="browse-like-icon"], [data-e2e="video-like-icon"]');
        if (likeBtn) {
            const actionContainer = likeBtn.closest('[class*="ActionBar"], [class*="DivActionItem"], [class*="ButtonContainer"]');
            if (actionContainer) {
                const buttons = actionContainer.parentElement?.querySelectorAll('button, [role="button"]') || [];
                // Comment is typically second button after like
                for (let i = 0; i < buttons.length; i++) {
                    const btn = buttons[i];
                    const dataE2e = btn.getAttribute('data-e2e') || '';
                    if (dataE2e.includes('comment') && !isShareElement(btn)) {
                        btn.click();
                        return {success: true, method: 'action-bar-comment'};
                    }
                }
            }
        }

        return {success: false, method: 'none'};
    }''')

    return result

def find_and_focus_comment_input(page):
    """Find and focus the comment input field - updated for 2026 TikTok UI"""
    result = page.evaluate('''() => {
        // Method 1: Look for "Add comment..." placeholder (most specific)
        const placeholderSelectors = [
            '[placeholder="Add comment..."]',
            '[placeholder*="Add comment" i]',
            '[placeholder*="comment" i]',
            '[aria-placeholder*="Add comment" i]',
            '[aria-placeholder*="comment" i]'
        ];

        for (let sel of placeholderSelectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) {
                el.click();
                el.focus();
                return {success: true, method: sel};
            }
        }

        // Method 2: data-e2e attributes
        const dataE2eSelectors = [
            '[data-e2e="comment-input"]',
            '[data-e2e="comment-text-input"]',
            '[data-e2e="comment-input-container"] input',
            '[data-e2e="comment-input-container"] [contenteditable]'
        ];

        for (let sel of dataE2eSelectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) {
                el.click();
                el.focus();
                return {success: true, method: sel};
            }
        }

        // Method 3: Class-based selectors
        const classSelectors = [
            '[class*="DivInputEditorContainer"] [contenteditable="true"]',
            '[class*="CommentInput"] [contenteditable="true"]',
            '[class*="DivCommentInput"] [contenteditable="true"]',
            '[class*="DivInputContainer"] input',
            '[class*="public-DraftEditor-content"]',
            '[class*="DraftEditor-root"] [contenteditable="true"]'
        ];

        for (let sel of classSelectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) {
                el.click();
                el.focus();
                return {success: true, method: sel};
            }
        }

        // Method 4: Find by contenteditable near comment section
        const commentSection = document.querySelector('[class*="CommentList"], [data-e2e="comment-list"]');
        if (commentSection) {
            const container = commentSection.closest('[class*="Container"]') || commentSection.parentElement;
            const input = container?.querySelector('[contenteditable="true"], input[type="text"]');
            if (input && input.offsetParent !== null) {
                input.click();
                input.focus();
                return {success: true, method: 'comment-section-input'};
            }
        }

        // Method 5: Any contenteditable that looks like comment input
        const editables = document.querySelectorAll('[contenteditable="true"]');
        for (let el of editables) {
            if (el.offsetParent && el.offsetHeight > 15 && el.offsetHeight < 150) {
                // Check if it's in the comment area (right side of video)
                const rect = el.getBoundingClientRect();
                if (rect.x > window.innerWidth / 2) {
                    el.click();
                    el.focus();
                    return {success: true, method: 'contenteditable-right-side'};
                }
            }
        }

        return {success: false};
    }''')

    return result

def click_post_button(page):
    """Click the post/submit button for the comment"""
    result = page.evaluate('''() => {
        // Method 1: data-e2e
        let btn = document.querySelector('[data-e2e="comment-post"]');
        if (btn && btn.offsetParent) { btn.click(); return {success: true, method: 'data-e2e-post'}; }
        
        // Method 2: Class-based
        const classSelectors = [
            '[class*="DivPostButton"]',
            '[class*="PostButton"]',
            '[class*="CommentPost"]',
            '[class*="submit" i]'
        ];
        
        for (let sel of classSelectors) {
            btn = document.querySelector(sel);
            if (btn && btn.offsetParent) { 
                btn.click(); 
                return {success: true, method: sel}; 
            }
        }
        
        // Method 3: Find by text content
        const postWords = ['post', 'pubblica', 'publicar', 'publier', 'posten', 'enviar', 'отправить', '发布', '게시', 'send', 'submit'];
        const elements = document.querySelectorAll('button, span, div[role="button"]');
        
        for (let el of elements) {
            const text = el.textContent.toLowerCase().trim();
            if (postWords.includes(text) && el.offsetParent) {
                el.click();
                return {success: true, method: 'text-' + text};
            }
        }
        
        return {success: false};
    }''')
    
    return result

def process_single_video_with_retry(page, video_num, profile_name, target_videos):
    """Process a single video with retry logic"""
    global commented_videos
    
    for attempt in range(MAX_RETRIES):
        try:
            log(f"    📹 Video {video_num + 1}/{target_videos}" + (f" (attempt {attempt + 1})" if attempt > 0 else ""))
            
            current_url = page.url
            
            # Check for login redirect - this is called on EVERY video attempt
            if not check_login_status(page):
                log(f"    ⚠ NOT LOGGED IN - skipping this browser")
                track_not_logged_in(profile_name, source="commenter")
                return False, "login_required"
            
            # Handle hashtag/search grid view
            if "/tag/" in current_url or "/search" in current_url:
                log(f"    → Grid view detected - clicking video...")
                
                # Scroll to load more videos
                page.evaluate('window.scrollBy(0, 200)')
                time.sleep(1)
                
                # Try to click a video from the grid
                click_result = page.evaluate('''(videoIndex) => {
                    const videoSelectors = [
                        '[data-e2e="challenge-item"]',
                        '[data-e2e="search_top-item"]',
                        '[class*="DivItemCardContainer"]',
                        '[class*="DivVideoCard"]',
                        'a[href*="/video/"]'
                    ];
                    
                    for (let selector of videoSelectors) {
                        const videos = document.querySelectorAll(selector);
                        const targetIndex = videoIndex % Math.max(videos.length, 1);
                        if (videos.length > targetIndex) {
                            videos[targetIndex].click();
                            return {success: true, method: selector, count: videos.length};
                        }
                    }
                    return {success: false, count: 0};
                }''', video_num % 12)
                
                if not click_result.get('success'):
                    log(f"    ⚠ Could not find video in grid, scrolling...")
                    page.keyboard.press("ArrowDown")
                    time.sleep(2)
                    continue
                
                log(f"    ✓ Clicked video ({click_result.get('method')})")
                time.sleep(3)

                # Verify video opened - check for URL change OR modal/overlay
                video_opened = page.evaluate('''() => {
                    // Check 1: URL contains /video/
                    if (window.location.href.includes('/video/')) return true;

                    // Check 2: Video modal/overlay is visible
                    const modalSelectors = [
                        '[class*="DivBrowserModeContainer"]',
                        '[class*="DivVideoContainer"]',
                        '[data-e2e="browse-video"]',
                        '[data-e2e="video-player"]',
                        'video[src]',
                        '[class*="DivContentContainer"] video',
                        '[class*="VideoPlayer"]'
                    ];
                    for (const sel of modalSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) return true;
                    }

                    // Check 3: Comments section is visible (means video is open)
                    const commentSelectors = [
                        '[data-e2e="comment-input"]',
                        '[data-e2e="comment-icon"]',
                        '[class*="CommentInput"]',
                        '[placeholder*="comment"]'
                    ];
                    for (const sel of commentSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetParent !== null) return true;
                    }

                    return false;
                }''')

                if not video_opened:
                    log(f"    ⚠ Video didn't open, retrying...")
                    # Try pressing Escape first to close any partial modal
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                    continue
                
                # Capture the actual video URL after it loads
                current_url = page.url
            
            # If URL is still FYP/foryou, try to extract actual video URL from page
            if "/foryou" in current_url or "/video/" not in current_url:
                extracted_url = page.evaluate('''() => {
                    // Try to get video URL from current video element or URL
                    const videoLink = document.querySelector('a[href*="/video/"]');
                    if (videoLink) return videoLink.href;

                    // Try to get from share button or canonical link
                    const canonical = document.querySelector('link[rel="canonical"]');
                    if (canonical && canonical.href.includes('/video/')) return canonical.href;

                    // Try meta og:url
                    const ogUrl = document.querySelector('meta[property="og:url"]');
                    if (ogUrl && ogUrl.content.includes('/video/')) return ogUrl.content;

                    // Try to extract from any visible video ID
                    const match = document.body.innerHTML.match(/\/@[\w.]+\/video\/(\d+)/);
                    if (match) return 'https://www.tiktok.com' + match[0];

                    return null;
                }''')
                if extracted_url:
                    current_url = extracted_url
                    log(f"    📍 Extracted video URL: ...{current_url[-40:]}")

            video_id = f"video_{video_num}_{int(time.time())}"

            if video_id in commented_videos:
                log(f"    ⏭ Already commented, skipping")
                return True, "skipped"

            # Step 1: Navigate directly to video page if we have the URL
            if "/video/" in current_url and "/tag/" in page.url:
                log(f"    → Opening video page directly...")
                try:
                    page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(4)
                except:
                    pass

            # Step 2: On video page, comments should already be visible
            # Just need to find the "Add comment..." input at the bottom
            log(f"    → Looking for comment input...")

            # Check if comment input is already visible (on video page layout)
            comment_input_visible = page.evaluate('''() => {
                // Look for the "Add comment..." placeholder input
                const selectors = [
                    '[placeholder*="Add comment" i]',
                    '[placeholder*="comment" i]',
                    '[data-e2e="comment-input"]',
                    '[class*="DivCommentInput"] [contenteditable]',
                    '[class*="CommentInput"]',
                    'div[contenteditable="true"][class*="public-DraftEditor"]',
                    '[class*="DraftEditor-root"]'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {
                        return {found: true, selector: sel};
                    }
                }
                return {found: false};
            }''')

            if comment_input_visible.get('found'):
                log(f"    ✓ Comment input visible ({comment_input_visible.get('selector')})")
            else:
                # Comments not visible, try clicking the comment icon
                log(f"    → Comments not visible, clicking comment button...")
                comment_result = click_comment_button(page)

                if comment_result.get('success'):
                    log(f"    ✓ Clicked ({comment_result.get('method')})")
                    time.sleep(2)

                    # Check if share dialog opened instead
                    share_check = page.evaluate('''() => {
                        const shareIndicators = ['copy link', 'share to', 'send to', 'embed', 'whatsapp'];
                        const text = document.body.innerText.toLowerCase();
                        return shareIndicators.some(ind => text.includes(ind));
                    }''')

                    if share_check:
                        log(f"    ⚠ Share dialog opened instead, closing...")
                        page.keyboard.press("Escape")
                        time.sleep(1)
                        if attempt < MAX_RETRIES - 1:
                            continue
                        return False, "wrong_dialog"
                else:
                    log(f"    ⚠ Could not open comments")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return False, "no_comments"
            
            # Step 2: Find comment input
            log(f"    → Finding input...")
            input_result = find_and_focus_comment_input(page)
            
            if not input_result.get('success'):
                log(f"    ⚠ Comment input not found")
                page.keyboard.press("Escape")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return False, "no_input"
            
            log(f"    ✓ Input found ({input_result.get('method')})")
            time.sleep(0.5)
            
            # Step 3: Get and type comment
            comment_text, from_sheet = get_random_comment(None)
            if not comment_text:
                log(f"    ⚠ No comments available")
                return False, "no_comment_text"
            
            log(f"    → Typing ({from_sheet})...")
            
            # Clear any existing text first
            page.keyboard.press("Control+a")
            time.sleep(0.1)
            
            # Type the comment
            page.keyboard.type(comment_text, delay=random.randint(30, 70))
            time.sleep(1)
            
            # Step 4: Post comment
            log(f"    → Posting...")
            post_result = click_post_button(page)
            
            if not post_result.get('success'):
                log(f"    → Trying Enter key...")
                page.keyboard.press("Enter")
            else:
                log(f"    ✓ Clicked post ({post_result.get('method')})")
            
            time.sleep(2)

            # Take screenshot as proof of comment
            screenshot_path = None
            try:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"{profile_name}_{timestamp_str}_{video_id[-8:]}.png"
                screenshot_path = os.path.join(SCREENSHOTS_FOLDER, screenshot_filename)
                page.screenshot(path=screenshot_path, full_page=False)
                log(f"    📸 Screenshot saved: {screenshot_filename}")
            except Exception as ss_err:
                log(f"    ⚠ Screenshot failed: {str(ss_err)[:50]}")

            # Success!
            commented_videos.add(video_id)

            return True, {
                "comment": comment_text,
                "sheet": from_sheet,
                "video_url": current_url,
                "video_id": video_id,
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            log(f"    ✗ Error: {str(e)[:100]}")
            if attempt < MAX_RETRIES - 1:
                log(f"    → Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            continue
    
    return False, "max_retries"

def run_tiktok_commenter(ws_endpoint, profile_name, sheet_name):
    """Connect to browser and comment on TikTok videos - IMPROVED VERSION"""
    global commented_videos

    # Check if automation was stopped
    if not automation_status["running"]:
        log(f"  [{profile_name}] ⏹ Stopped")
        return False

    if not HAS_PLAYWRIGHT:
        log("  ✗ Playwright not installed!")
        return False

    videos_commented = 0
    target_videos = settings["videos_per_profile"]
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 5
    
    try:
        with sync_playwright() as p:
            # Connect to AdsPower browser
            log(f"  → Connecting to browser...")
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            log(f"  ✓ Connected")

            # Auto-detect TikTok username and check login status
            try:
                page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
                current_url = page.url

                # Check if redirected to login page
                if "login" in current_url.lower() or "signup" in current_url.lower():
                    log(f"  ⚠ NOT LOGGED IN - Skipping browser")
                    track_not_logged_in(profile_name, source="commenter")
                    browser.close()
                    return False

                if "/@" in current_url:
                    match = re.search(r'/@([^/?]+)', current_url)
                    if match:
                        detected_username = match.group(1)
                        set_tiktok_username(profile_name, detected_username)
                        log(f"  📱 Account: @{detected_username}")
                else:
                    # No username detected - might not be logged in
                    log(f"  ⚠ No account detected - checking login status...")
                    # Check if login button is visible
                    login_visible = page.evaluate('''() => {
                        const loginBtn = document.querySelector('[data-e2e="login-button"], a[href*="login"]');
                        return loginBtn && loginBtn.offsetParent !== null;
                    }''')
                    if login_visible:
                        log(f"  ⚠ NOT LOGGED IN - Skipping browser")
                        track_not_logged_in(profile_name, source="commenter")
                        browser.close()
                        return False
            except Exception as e:
                log(f"  ⚠ Profile check error: {str(e)[:40]}")

            # Close extra TikTok tabs only, keep AdsPower tab
            log(f"  → Cleaning up TikTok tabs...")
            pages = context.pages
            tiktok_tabs = []
            
            for p in pages:
                try:
                    if "tiktok" in p.url.lower():
                        tiktok_tabs.append(p)
                except:
                    pass
            
            # Close all TikTok tabs except keep first one (or close all if multiple)
            if len(tiktok_tabs) > 1:
                for p in tiktok_tabs[1:]:  # Keep first, close rest
                    try:
                        p.close()
                    except:
                        pass
                log(f"  ✓ Closed {len(tiktok_tabs)-1} extra TikTok tab(s)")
                page = tiktok_tabs[0]  # Use existing TikTok tab
            elif len(tiktok_tabs) == 1:
                page = tiktok_tabs[0]  # Use existing TikTok tab
            else:
                # No TikTok tab, create new one (keeps AdsPower tab open)
                page = context.new_page()
            
            # Go to TikTok - either For You or target hashtag
            target_hashtag = settings.get("target_hashtag", "").strip()
            
            if target_hashtag:
                # Clean hashtag (remove # if present)
                hashtag = target_hashtag.replace("#", "").strip()
                tiktok_url = f"https://www.tiktok.com/tag/{hashtag}"
                log(f"  → Opening TikTok #{hashtag}...")
            else:
                tiktok_url = "https://www.tiktok.com/foryou"
                log(f"  → Opening TikTok For You...")
            
            try:
                page.goto(tiktok_url, wait_until="domcontentloaded", timeout=90000)
            except Exception as e:
                log(f"  ⚠ Slow load, continuing anyway...")
            
            time.sleep(8)  # Give more time for content to load
            
            # Check if logged in
            current_url = page.url
            log(f"  📍 URL: {current_url}")
            
            # Check if redirected to login
            if "login" in current_url.lower() or "signup" in current_url.lower():
                log(f"  ⚠ NOT LOGGED IN - Closing browser automatically")
                track_not_logged_in(profile_name, source="commenter")
                browser.close()
                return False

            # Also check page content for login prompts
            try:
                login_check = page.evaluate('''() => {
                    const text = document.body.innerText.toLowerCase();
                    if (text.includes('log in') && text.includes('sign up')) return true;
                    if (document.querySelector('[data-e2e="login-button"]')) return true;
                    if (document.querySelector('a[href*="login"]')) return true;
                    return false;
                }''')
                if login_check:
                    log(f"  ⚠ LOGIN REQUIRED - Closing browser automatically")
                    track_not_logged_in(profile_name, source="commenter")
                    browser.close()
                    return False
            except:
                pass
            
            # Wait for video
            try:
                page.wait_for_selector('video', timeout=15000)
                log(f"  ✓ TikTok loaded")
            except:
                log(f"  ⚠ No video found, continuing anyway...")
            
            # Process videos using improved retry logic
            for video_num in range(target_videos):
                if not automation_status["running"]:
                    log(f"  ⏹ Stopped by user")
                    break
                
                # Check consecutive failures
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log(f"  ⚠ Too many consecutive failures ({MAX_CONSECUTIVE_FAILURES}), stopping profile")
                    break
                
                # Process video with retry
                success, result = process_single_video_with_retry(page, video_num, profile_name, target_videos)
                
                if success:
                    consecutive_failures = 0
                    
                    if isinstance(result, dict):
                        # Comment was posted successfully
                        videos_commented += 1
                        automation_status["comments_posted"] += 1
                        
                        report_entry = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "profile": profile_name,
                            "video_url": result.get("video_url", ""),
                            "video_id": result.get("video_id", ""),
                            "comment": result.get("comment", ""),
                            "sheet": result.get("sheet", "Unknown"),
                            "screenshot": result.get("screenshot", "")
                        }
                        
                        automation_status["report"].append(report_entry)
                        save_report_history()
                        
                        # Send to cloud
                        try:
                            threading.Thread(target=send_to_cloud, args=(report_entry,), daemon=True).start()
                        except:
                            pass
                        
                        log(f"    ✓ SUCCESS: {result.get('comment', '')[:40]}...")
                        
                        # Close comments and wait
                        page.keyboard.press("Escape")
                        time.sleep(1)
                        
                        delay = random.randint(settings["min_delay"], settings["max_delay"])
                        log(f"    ⏳ Waiting {delay}s...")
                        for _ in range(delay):
                            if not automation_status["running"]:
                                break
                            time.sleep(1)
                else:
                    consecutive_failures += 1
                    if result == "login_required":
                        log(f"  ⚠ Profile not logged in, stopping")
                        track_not_logged_in(profile_name, source="commenter")
                        break
                    log(f"    ⚠ Failed: {result}")
                
                # Navigate to next video
                try:
                    current_url = page.url
                    target_hashtag = settings.get("target_hashtag", "").strip()
                    
                    if "/video/" in current_url:
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
                        
                        if target_hashtag:
                            # Go back to hashtag grid
                            if "/video/" in page.url:
                                hashtag = target_hashtag.replace("#", "").strip()
                                try:
                                    page.goto(f"https://www.tiktok.com/tag/{hashtag}", wait_until="domcontentloaded", timeout=30000)
                                    time.sleep(3)
                                    # Scroll to load more
                                    for _ in range(min(video_num // 3 + 1, 5)):
                                        page.keyboard.press("ArrowDown")
                                        time.sleep(0.3)
                                except:
                                    pass
                        else:
                            page.keyboard.press("ArrowDown")
                    else:
                        page.keyboard.press("ArrowDown")
                    
                    time.sleep(1)
                except:
                    pass
                
                # Clean up extra tabs
                try:
                    current_pages = context.pages
                    tiktok_pages = [pg for pg in current_pages if "tiktok" in pg.url.lower()]
                    if len(tiktok_pages) > 1:
                        for pg in tiktok_pages:
                            if pg != page:
                                pg.close()
                except:
                    pass
            
            log(f"  ✓ Done: {videos_commented} comments posted")
            browser.close()
            return videos_commented > 0
            
    except Exception as e:
        log(f"  ✗ Error: {e}")
        log(f"  📋 {traceback.format_exc()}")
        return False

def run_single_profile(profile_id, sheet_name):
    """Run automation for a single profile - used for parallel execution"""
    # Check if automation was stopped before opening browser
    if not automation_status["running"]:
        return False

    profile = next((p for p in profiles if p.get("user_id") == profile_id), None)
    if not profile:
        return False

    profile_name = profile.get("name", profile_id)

    # Double-check running status before opening browser
    if not automation_status["running"]:
        log(f"  [{profile_name}] ⏹ Stopped before opening browser")
        return False

    log(f"\n🚀 [{profile_name}] Starting...")
    log(f"  [{profile_name}] Sheet: {sheet_name}")

    # Open browser
    browser_data = open_browser(profile_id)
    if not browser_data:
        log(f"  [{profile_name}] ✗ Failed to open browser")
        return False
    if browser_data == "SKIP":
        log(f"  [{profile_name}] ⚠ Browser not ready, skipping")
        return False

    try:
        ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
        if not ws_endpoint:
            log(f"  [{profile_name}] ✗ No WebSocket")
            return False

        # Run commenter
        success = run_tiktok_commenter(ws_endpoint, profile_name, sheet_name)
    finally:
        # Close browser
        log(f"  [{profile_name}] Closing browser...")
        close_browser(profile_id)
    
    if success:
        automation_status["completed"].append(profile_id)
        log(f"  [{profile_name}] ✓ Completed!")
    else:
        log(f"  [{profile_name}] ✗ Failed")
    
    return success

def run_automation_thread(profile_ids, sheet_mapping):
    global automation_status
    
    automation_status["running"] = True
    automation_status["progress"] = 0
    automation_status["total"] = len(profile_ids)
    automation_status["completed"] = []
    automation_status["logs"] = []
    # Keep existing report data - don't clear it!
    # comments_posted is total of ALL time

    parallel = settings.get('parallel_browsers', 2)  # Number of browsers to run at a time

    log(f"{'='*50}")
    log(f"Starting for {len(profile_ids)} profiles (Target: 25/day)")
    log(f"Running {parallel} browser{'s' if parallel != 1 else ''} at a time until all {len(profile_ids)} finished")
    log(f"Target: {settings['videos_per_profile']} videos per profile")
    if settings.get('target_hashtag'):
        log(f"🎯 Targeting: #{settings['target_hashtag'].replace('#','')}")
    else:
        log(f"🎯 Targeting: For You Page")
    log(f"📢 Promoting: Bump Connect, Kollabsy, Bump Syndicate")
    log(f"Total target: {len(profile_ids) * settings['videos_per_profile']} comments")
    log(f"{'='*50}")
    
    # Comments are built-in promotional messages
    log(f"📢 Using promotional comments for: Bump Connect, Kollabsy, Bump Syndicate")
    
    # Sort profile_ids numerically (tt1, tt2, ... tt25)
    def sort_key(pid):
        # Get profile name
        profile = next((p for p in profiles if p.get("user_id") == pid), None)
        name = profile.get("name", pid) if profile else pid
        import re
        match = re.search(r'(\d+)', str(name))
        return int(match.group(1)) if match else 999
    
    sorted_profile_ids = sorted(profile_ids, key=sort_key)
    log(f"📋 Order: {', '.join([next((p.get('name', pid) for p in profiles if p.get('user_id') == pid), pid) for pid in sorted_profile_ids[:5]])}...")
    
    # Run profiles in parallel batches of 2
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {}
        
        for profile_id in sorted_profile_ids:
            if not automation_status["running"]:
                break
            
            sheet_name = sheet_mapping.get(profile_id, SHEET_NAMES[0])
            future = executor.submit(run_single_profile, profile_id, sheet_name)
            futures[future] = profile_id
        
        # Wait for all to complete
        for future in as_completed(futures):
            if not automation_status["running"]:
                break
            
            profile_id = futures[future]
            automation_status["progress"] += 1
            
            try:
                future.result()
            except Exception as e:
                log(f"  ✗ Error for {profile_id}: {e}")
    
    automation_status["running"] = False
    automation_status["current_profile"] = None
    log(f"\n{'='*50}")
    log(f"✓ DONE! {automation_status['comments_posted']} comments")
    log(f"{'='*50}")

# =============================================================================
# WEB DASHBOARD
# =============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Commenter</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #0a0a0b; color: #e4e4e7; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 4px; }
        .subtitle { color: #71717a; font-size: 14px; margin-bottom: 24px; }
        .target-info { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid #4c1d95; border-radius: 12px; padding: 16px; margin-bottom: 20px; }
        .target-info h3 { font-size: 14px; color: #a78bfa; margin-bottom: 8px; }
        .target-stats { display: flex; gap: 32px; }
        .target-stat { text-align: center; }
        .target-stat .num { font-size: 28px; font-weight: 700; color: #fff; }
        .target-stat .lbl { font-size: 11px; color: #a1a1aa; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 20px; }
        .card-title { font-weight: 600; margin-bottom: 16px; display: flex; justify-content: space-between; }
        .btn { padding: 10px 20px; border-radius: 8px; border: none; font-size: 14px; cursor: pointer; }
        .btn-secondary { background: #27272a; color: #e4e4e7; }
        .btn-success { background: #16a34a; color: white; font-size: 16px; padding: 14px 32px; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-primary { background: #7c3aed; color: white; }
        .profile { display: flex; align-items: center; padding: 12px; background: #27272a; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
        .profile.selected { background: #4c1d95; border: 1px solid #7c3aed; }
        .profile input { margin-right: 12px; }
        .profile-list { max-height: 300px; overflow-y: auto; margin-top: 12px; }
        select { padding: 6px; background: #18181b; border: 1px solid #3f3f46; color: #e4e4e7; border-radius: 4px; }
        .stats { display: flex; gap: 24px; justify-content: center; margin: 20px 0; }
        .stat-value { font-size: 32px; font-weight: 700; color: #7c3aed; }
        .stat-label { color: #71717a; font-size: 12px; }
        .progress { width: 100%; height: 8px; background: #27272a; border-radius: 4px; margin: 16px 0; }
        .progress-fill { height: 100%; background: #7c3aed; border-radius: 4px; }
        .logs { background: #0f0f10; border-radius: 8px; padding: 16px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; }
        .settings { background: #1a1a2e; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
        .setting-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
        .setting-row label { font-size: 13px; color: #a1a1aa; min-width: 140px; }
        .setting-row input { width: 80px; padding: 8px; background: #27272a; border: 1px solid #3f3f46; color: white; border-radius: 6px; }
        .center { text-align: center; }
        .tabs { display: flex; gap: 4px; margin-bottom: 20px; background: #18181b; padding: 4px; border-radius: 10px; width: fit-content; }
        .tab { padding: 10px 20px; border-radius: 8px; cursor: pointer; }
        .tab.active { background: #7c3aed; }
        .report-table { width: 100%; font-size: 13px; }
        .report-table th { text-align: left; padding: 12px; background: #27272a; }
        .report-table td { padding: 12px; border-bottom: 1px solid #27272a; }
        .report-table a { color: #a78bfa; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 TikTok Auto Commenter</h1>
        <p class="subtitle" id="dailyTargetText">Daily target: <span id="numProfiles">0</span> browsers × <span id="numVideos">10</span> videos = <span id="totalTarget">0</span> comments</p>

        <div class="target-info">
            <h3>📊 Daily Target</h3>
            <div class="target-stats">
                <div class="target-stat"><div class="num" id="profileCount">0</div><div class="lbl">Profiles</div></div>
                <div class="target-stat"><div class="num" id="videosPerProfile">10</div><div class="lbl">Videos/Profile</div></div>
                <div class="target-stat"><div class="num" id="dailyTarget">0</div><div class="lbl">Daily Target</div></div>
                <div class="target-stat"><div class="num">2</div><div class="lbl">Parallel</div></div>
            </div>
            <div style="margin-top:12px;font-size:12px;color:#a1a1aa;">
                🎯 Promoting: <span style="color:#4ade80">Bump Connect</span> • <span style="color:#a78bfa">Kollabsy</span> • <span style="color:#fbbf24">Bump Syndicate</span>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('main')">🎮 Control</div>
            <div class="tab" onclick="showTab('dm')">💬 DM</div>
            <div class="tab" onclick="showTab('replies')">📨 Replies</div>
            <div class="tab" onclick="showTab('post')">📤 Post</div>
            <div class="tab" onclick="showTab('profiles')">👤 Profiles</div>
            <div class="tab" onclick="showTab('report')">📊 Report</div>
        </div>
        
        <div id="tab-main">
            <div class="grid">
                <div class="card">
                    <div class="card-title"><span>Profiles</span><span id="pc" style="color:#71717a">0/0 selected</span></div>
                    <div style="display:flex;gap:8px;margin-bottom:12px;">
                        <button class="btn btn-secondary" onclick="sync()">🔄 Sync</button>
                        <button class="btn btn-secondary" onclick="selAll()" id="selAllBtn">Select All</button>
                    </div>
                    <div class="profile-list" id="pl"></div>
                </div>
                <div class="card">
                    <div class="card-title">Control</div>
                    <div class="settings">
                        <div class="setting-row"><label>Target hashtag:</label><input type="text" id="hashtag" value="" placeholder="#socialmedia" style="width:150px;"></div>
                        <div style="font-size:11px;color:#71717a;margin-bottom:10px;">Leave empty for For You page, or enter hashtag like #fitness</div>
                        <div class="setting-row"><label>Min delay (s):</label><input type="number" id="mind" value="30"></div>
                        <div class="setting-row"><label>Max delay (s):</label><input type="number" id="maxd" value="60"></div>
                        <div class="setting-row"><label>Videos/profile:</label><input type="number" id="vpp" value="100"></div>
                        <div class="setting-row"><label>Parallel browsers:</label><input type="number" id="parallel" value="2" min="1" max="10"></div>
                        <div style="font-size:12px;color:#71717a;margin-top:8px;">⚡ Run 1-10 browsers at a time (2-3 recommended for stability)</div>
                    </div>
                    <div class="stats">
                        <div class="stat"><div class="stat-value" id="sp">0</div><div class="stat-label">Profiles Done</div></div>
                        <div class="stat"><div class="stat-value" id="sc-today">0</div><div class="stat-label">Today</div></div>
                        <div class="stat"><div class="stat-value" id="sc">0</div><div class="stat-label">Total</div></div>
                    </div>
                    <div class="progress"><div class="progress-fill" id="prog" style="width:0%"></div></div>
                    <p class="center" style="color:#71717a" id="st">Ready - Click Start to run 25 browsers</p>
                    <div class="center" style="margin-top:20px;">
                        <button class="btn btn-success" id="startb" onclick="start()">▶ Start Daily Run</button>
                        <button class="btn btn-danger" id="stopb" onclick="stop()" style="display:none">⏹ Stop</button>
                    </div>
                </div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>Log</span><button class="btn btn-secondary" style="padding:4px 8px" onclick="clrLog()">Clear</button></div>
                <div class="logs" id="logs">Ready - Select all 25 profiles and click Start...</div>
            </div>
        </div>
        
        <!-- DM TAB - Brand Outreach -->
        <div id="tab-dm" style="display:none">
            <div class="grid">
                <div class="card">
                    <div class="card-title"><span>👥 Select Profiles for DM</span><span id="dm-pc" style="color:#71717a">0/0</span></div>
                    <div style="display:flex;gap:8px;margin-bottom:12px;">
                        <button class="btn btn-secondary" onclick="dmSelAll()">Select All</button>
                        <button class="btn btn-secondary" onclick="dmSelNone()">Deselect All</button>
                    </div>
                    <div class="profile-list" id="dm-pl" style="max-height:200px;"></div>
                </div>
                <div class="card">
                    <div class="card-title"><span>🎯 Brand DM Outreach</span></div>
                    <div style="background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;padding:12px;margin-bottom:12px;">
                        <div style="font-size:13px;color:#c4b5fd;font-weight:bold;margin-bottom:6px;">How It Works</div>
                        <div style="font-size:12px;color:#a1a1aa;line-height:1.8;">
                            <b style="color:#4ade80;">1.</b> Select profiles above, then click Start<br>
                            <b style="color:#60a5fa;">2.</b> Searches TikTok for brands needing social media help<br>
                            <b style="color:#fbbf24;">3.</b> Max <span id="dm-limit-profile">100</span> DMs per profile, <span id="dm-limit-total">2500</span> total per day<br>
                            <b style="color:#c4b5fd;">4.</b> Processes 2 profiles at a time (tt1 → tt25)
                        </div>
                    </div>
                    <div class="settings">
                        <div class="setting-row">
                            <label>Target Mode:</label>
                            <select id="dm-mode" onchange="dmModeChange()">
                                <option value="brand_search">🔍 Auto Search Brands</option>
                                <option value="specific">Specific Users</option>
                                <option value="hashtag">From Hashtag</option>
                                <option value="commenters">Video Commenters</option>
                                <option value="followers">Account Followers</option>
                            </select>
                        </div>
                        <div id="dm-brand-info" style="background:#14532d;border:1px solid #16a34a;border-radius:6px;padding:10px;margin:8px 0;">
                            <div style="font-size:12px;color:#4ade80;margin-bottom:4px;">🔍 Search Queries (random selection):</div>
                            <div style="font-size:11px;color:#86efac;line-height:1.6;" id="dm-search-queries">small business owner, startup founder, entrepreneur life, ecommerce brand, clothing brand, beauty brand, fitness brand, restaurant owner, salon owner, real estate agent...</div>
                        </div>
                        <div id="dm-specific" class="setting-row" style="display:none">
                            <label>Usernames:</label>
                            <textarea id="dm-users" placeholder="user1, user2, user3..." style="width:100%;height:60px;background:#27272a;border:1px solid #3f3f46;color:white;border-radius:6px;padding:8px;"></textarea>
                        </div>
                        <div id="dm-hashtag" class="setting-row" style="display:none">
                            <label>Hashtag:</label>
                            <input type="text" id="dm-tag" placeholder="#fitness" style="width:150px;">
                        </div>
                        <div id="dm-video" class="setting-row" style="display:none">
                            <label>Video URL:</label>
                            <input type="text" id="dm-video-url" placeholder="https://tiktok.com/..." style="width:250px;">
                        </div>
                        <div id="dm-account" class="setting-row" style="display:none">
                            <label>Account:</label>
                            <input type="text" id="dm-acc" placeholder="@username" style="width:150px;">
                        </div>
                        <div class="setting-row">
                            <label>Max DMs/profile:</label>
                            <input type="number" id="dm-max" value="100" min="1" max="100" style="width:80px;">
                        </div>
                        <div class="setting-row">
                            <label>Max DMs/day (total):</label>
                            <input type="number" id="dm-max-total" value="2500" min="1" max="5000" style="width:80px;">
                        </div>
                        <div class="setting-row">
                            <label>Min delay (s):</label>
                            <input type="number" id="dm-mind" value="45" style="width:80px;">
                        </div>
                        <div class="setting-row">
                            <label>Max delay (s):</label>
                            <input type="number" id="dm-maxd" value="90" style="width:80px;">
                        </div>
                    </div>
                    <button class="btn btn-secondary" onclick="saveDmSettings()" style="margin-top:10px;">💾 Save Settings</button>
                </div>
                <div class="card">
                    <div class="card-title"><span>📝 DM Message</span></div>
                    <div class="settings">
                        <div style="margin-bottom:12px;">
                            <label style="font-size:13px;color:#a1a1aa;">Message to send:</label>
                            <textarea id="dm-default-msg" oninput="dmMessageEdited=true" style="width:100%;height:100px;background:#27272a;border:1px solid #3f3f46;color:white;border-radius:6px;padding:8px;margin-top:4px;">Hey! 👋 I noticed your brand and love what you're doing! We help businesses like yours grow on social media. Check out bumpsyndicate.xyz - we'd love to help you scale! 🚀</textarea>
                        </div>
                        <button class="btn btn-secondary" onclick="saveDmMessage()">💾 Save Message</button>
                    </div>
                </div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>📊 DM Status</span></div>
                <div class="stats">
                    <div class="stat"><div class="stat-value" id="dm-sent">0</div><div class="stat-label">DMs Sent (Session)</div></div>
                    <div class="stat"><div class="stat-value" id="dm-today">0</div><div class="stat-label">Sent Today</div></div>
                    <div class="stat"><div class="stat-value" id="dm-remaining">250</div><div class="stat-label">Remaining Today</div></div>
                    <div class="stat"><div class="stat-value" id="dm-profiles-done">0</div><div class="stat-label">Profiles Done</div></div>
                </div>
                <div class="progress"><div class="progress-fill" id="dm-prog" style="width:0%"></div></div>
                <p class="center" style="color:#71717a" id="dm-st">Ready - Click Start to begin brand outreach</p>
                <div class="center" style="margin-top:20px;">
                    <button class="btn btn-success" id="dm-startb" onclick="startDm()">▶ Start Brand Outreach</button>
                    <button class="btn btn-danger" id="dm-stopb" onclick="stopDm()" style="display:none">⏹ Stop</button>
                </div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>DM Log</span><button class="btn btn-secondary" style="padding:4px 8px" onclick="clrDmLog()">Clear</button></div>
                <div class="logs" id="dm-logs">Ready - Will search TikTok for brands and send DMs...</div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>DM History</span>
                    <div>
                        <button class="btn btn-primary" onclick="expDmCSV()" style="padding:4px 12px">📥 Export</button>
                        <button class="btn btn-danger" onclick="clrDmHistory()" style="padding:4px 12px">🗑️ Clear</button>
                    </div>
                </div>
                <div style="max-height:200px;overflow:auto">
                    <table class="report-table"><thead><tr><th>Time</th><th>Profile</th><th>Username</th><th>Message</th><th>Status</th></tr></thead><tbody id="dm-rb"></tbody></table>
                </div>
            </div>
        </div>
        
        <!-- REPLIES TAB - AI Reply Management -->
        <div id="tab-replies" style="display:none">
            <div class="card">
                <div class="card-title"><span>📨 AI Reply Management</span></div>
                <div style="background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;padding:12px;margin-bottom:12px;">
                    <div style="font-size:13px;color:#c4b5fd;font-weight:bold;margin-bottom:6px;">How It Works</div>
                    <div style="font-size:12px;color:#a1a1aa;line-height:1.8;">
                        <b style="color:#4ade80;">1.</b> Click "Check for Replies" to scan DM inbox for responses<br>
                        <b style="color:#60a5fa;">2.</b> AI (GPT-5.2) drafts professional replies automatically<br>
                        <b style="color:#fbbf24;">3.</b> Review and approve/edit drafts below<br>
                        <b style="color:#c4b5fd;">4.</b> Click "Send All Approved" to send replies from each profile
                    </div>
                </div>
                <div class="stats">
                    <div class="stat"><div class="stat-value" id="reply-pending">0</div><div class="stat-label">Pending Check</div></div>
                    <div class="stat"><div class="stat-value" id="reply-drafts">0</div><div class="stat-label">Drafts Ready</div></div>
                    <div class="stat"><div class="stat-value" id="reply-approved">0</div><div class="stat-label">Approved</div></div>
                    <div class="stat"><div class="stat-value" id="reply-sent">0</div><div class="stat-label">Sent</div></div>
                </div>
                <p class="center" style="color:#71717a;margin:10px 0" id="reply-status">Ready - Click "Check for Replies" to start</p>
                <div class="center" style="margin-top:15px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
                    <button class="btn btn-primary" id="btn-check-replies" onclick="checkReplies()">📥 Check for Replies</button>
                    <button class="btn btn-success" id="btn-send-approved" onclick="sendApproved()">📤 Send All Approved</button>
                    <button class="btn btn-secondary" onclick="refreshReplies()">🔄 Refresh</button>
                </div>
            </div>
            
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>🤖 AI Draft Replies (Needs Approval)</span><span style="color:#fbbf24" id="draft-count">0</span></div>
                <div id="draft-replies-container" style="max-height:400px;overflow:auto;">
                    <div style="text-align:center;color:#71717a;padding:20px;">No draft replies. Click "Check for Replies" to find new messages.</div>
                </div>
            </div>
            
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>✅ Approved Replies (Ready to Send)</span><span style="color:#4ade80" id="approved-count">0</span></div>
                <div id="approved-replies-container" style="max-height:300px;overflow:auto;">
                    <div style="text-align:center;color:#71717a;padding:20px;">No approved replies yet.</div>
                </div>
            </div>
            
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>Reply Log</span><button class="btn btn-secondary" style="padding:4px 8px" onclick="clrReplyLog()">Clear</button></div>
                <div class="logs" id="reply-logs">Ready to check for replies...</div>
            </div>
            
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>📜 Sent Reply History</span><span style="color:#71717a" id="sent-count">0</span></div>
                <div style="max-height:200px;overflow:auto">
                    <table class="report-table">
                        <thead><tr><th>Sent At</th><th>Profile</th><th>To</th><th>Their Message</th><th>Our Reply</th></tr></thead>
                        <tbody id="sent-replies-table"></tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- POST TAB (Auto Repost Scheduler) -->
        <div id="tab-post" style="display:none">
            <div class="grid">
                <div class="card">
                    <div class="card-title"><span>📤 Auto Repost Scheduler</span></div>
                    <div style="background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;padding:12px;margin-bottom:12px;">
                        <div style="font-size:13px;color:#c4b5fd;font-weight:bold;margin-bottom:6px;">Schedule Rules</div>
                        <div style="font-size:12px;color:#a1a1aa;line-height:1.8;">
                            <b style="color:#4ade80;">Monday:</b> Repost Bump Connect / Kollabsy / Bump Syndicate content<br>
                            <b style="color:#60a5fa;">Tue - Sun:</b> Repost social media / content creator content<br>
                            <b style="color:#fbbf24;">Limit:</b> Max <span id="post-limit-display">2</span> reposts per profile per day<br>
                            <b style="color:#c4b5fd;">Auto-run:</b> Scheduler starts daily at 9 AM when enabled
                        </div>
                    </div>
                    <div class="settings">
                        <div class="setting-row"><label>Max reposts/day:</label><input type="number" id="post-maxday" value="2" min="1" max="5" style="width:60px;"></div>
                        <div class="setting-row"><label>Min delay (s):</label><input type="number" id="post-mind" value="300" style="width:80px;"></div>
                        <div class="setting-row"><label>Max delay (s):</label><input type="number" id="post-maxd" value="600" style="width:80px;"></div>
                        <div style="font-size:11px;color:#71717a;margin-top:6px;">5-10 min delay between reposts to avoid detection</div>
                    </div>
                    <div class="center" style="margin-top:12px;">
                        <button class="btn btn-success" onclick="applyRepostSettings()">Save Settings</button>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title"><span>Status</span></div>
                    <div class="stats" style="margin-top:8px;">
                        <div class="stat"><div class="stat-value" id="post-done">0</div><div class="stat-label">Reposts Made</div></div>
                        <div class="stat"><div class="stat-value" id="post-today-count">0</div><div class="stat-label">Today</div></div>
                    </div>
                    <div class="progress" style="margin-top:12px;"><div class="progress-fill" id="post-prog" style="width:0%"></div></div>
                    <p class="center" style="color:#71717a;font-size:12px;" id="post-st">Ready</p>
                    <p class="center" style="color:#52525b;font-size:11px;" id="post-next">Scheduler: Waiting...</p>
                    <div class="center" style="margin-top:16px;">
                        <button class="btn btn-success" id="post-startb" onclick="startPost()">▶ Start Repost Run</button>
                        <button class="btn btn-danger" id="post-stopb" onclick="stopPost()" style="display:none">⏹ Stop</button>
                    </div>
                </div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>Repost Log</span><button class="btn btn-secondary" style="padding:4px 8px" onclick="clrPostLog()">Clear</button></div>
                <div class="logs" id="post-logs">Ready - Click Start or wait for auto-scheduler...</div>
            </div>
            <div class="card" style="margin-top:20px;">
                <div class="card-title"><span>Repost History</span>
                    <div>
                        <button class="btn btn-primary" onclick="expPostCSV()" style="padding:4px 12px">📥 Export</button>
                        <button class="btn btn-danger" onclick="clrPostHistory()" style="padding:4px 12px">Clear</button>
                    </div>
                </div>
                <div style="max-height:200px;overflow:auto">
                    <table class="report-table"><thead><tr><th>Time</th><th>Profile</th><th>Repost</th><th>Content Type</th><th>Status</th></tr></thead><tbody id="post-hist-tb"></tbody></table>
                </div>
            </div>
        </div>

        <!-- PROFILES TAB - Profile to TikTok Username Mapping -->
        <div id="tab-profiles" style="display:none">
            <div class="card">
                <div class="card-title"><span>👤 Profile to TikTok Username Mapping</span></div>
                <div style="background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;padding:12px;margin-bottom:16px;">
                    <div style="font-size:13px;color:#c4b5fd;font-weight:bold;margin-bottom:6px;">How It Works</div>
                    <div style="font-size:12px;color:#a1a1aa;line-height:1.8;">
                        <b style="color:#4ade80;">Auto-Detection:</b> Usernames are automatically detected when you run any automation (DM, Repost, Comment)<br>
                        <b style="color:#60a5fa;">Manual Entry:</b> You can also manually add/edit mappings below<br>
                        <b style="color:#fbbf24;">Repost Links:</b> Mappings are used to generate correct repost links (@username?tab=reposts)
                    </div>
                </div>
                <div style="display:flex;gap:8px;margin-bottom:16px;">
                    <button class="btn btn-primary" onclick="refreshProfileMapping()">🔄 Refresh</button>
                    <button class="btn btn-secondary" onclick="detectAllUsernames()">🔍 Detect All Usernames</button>
                </div>
                <div style="max-height:500px;overflow:auto">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th style="width:120px;">Profile (Browser)</th>
                                <th style="width:180px;">TikTok Username</th>
                                <th style="width:250px;">Repost URL</th>
                                <th style="width:100px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="profile-mapping-tb"></tbody>
                    </table>
                </div>
                <div style="margin-top:20px;padding:16px;background:#27272a;border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;margin-bottom:12px;">➕ Add New Mapping</div>
                    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
                        <select id="new-profile-select" style="padding:8px 12px;background:#18181b;border:1px solid #3f3f46;color:#e4e4e7;border-radius:6px;">
                            <option value="">Select Profile...</option>
                        </select>
                        <input type="text" id="new-tiktok-username" placeholder="@username" style="padding:8px 12px;background:#18181b;border:1px solid #3f3f46;color:#e4e4e7;border-radius:6px;width:180px;">
                        <button class="btn btn-success" onclick="addProfileMapping()">Add Mapping</button>
                    </div>
                </div>
            </div>
        </div>

        <div id="tab-report" style="display:none">
            <div class="card">
                <div class="card-title"><span>📊 All Comments History</span><span id="rc" style="color:#71717a">0 local</span></div>
                <div style="background:#14532d;border:1px solid #16a34a;border-radius:8px;padding:12px;margin-bottom:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="color:#4ade80;font-weight:bold;">☁️ Cloud Total: <span id="cloud-total-count">Loading...</span></span>
                            <span style="color:#86efac;margin-left:16px;">Local: <span id="local-count">0</span></span>
                        </div>
                        <button class="btn btn-success" onclick="loadFromCloud()" id="btn-load-cloud" style="padding:6px 16px;">📥 Load All from Cloud</button>
                    </div>
                </div>
                <div style="display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap;">
                    <button class="btn btn-primary" onclick="expCSV()">📥 Export CSV</button>
                    <button class="btn btn-secondary" onclick="syncCloud()" style="background:#4c1d95;">☁️ Sync to Cloud</button>
                    <button class="btn btn-danger" onclick="clrReport()">🗑️ Clear All</button>
                </div>
                <div style="display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap;padding:12px;background:#18181b;border-radius:8px;">
                    <span style="color:#71717a;font-size:12px;">📅 Date Range:</span>
                    <input type="date" id="startDate" onchange="applyDateRange()" style="padding:6px 10px;background:#27272a;border:1px solid #3f3f46;border-radius:6px;color:#e4e4e7;font-size:12px;">
                    <span style="color:#71717a;">to</span>
                    <input type="date" id="endDate" onchange="applyDateRange()" style="padding:6px 10px;background:#27272a;border:1px solid #3f3f46;border-radius:6px;color:#e4e4e7;font-size:12px;">
                    <button class="btn btn-secondary" onclick="clearDateRange()" style="padding:6px 12px;">Clear</button>
                    <span style="color:#3f3f46;">|</span>
                    <button class="btn btn-secondary" onclick="filterToday()">Today</button>
                    <button class="btn btn-secondary" onclick="filterWeek()">This Week</button>
                    <button class="btn btn-secondary" onclick="filterMonth()">This Month</button>
                    <button class="btn btn-secondary" onclick="filterAll()">All Time</button>
                </div>
                <div style="background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;padding:12px;margin-bottom:16px;">
                    <div style="font-size:12px;color:#a78bfa;margin-bottom:4px;">☁️ Team Dashboard</div>
                    <div style="font-size:11px;color:#71717a;">Comments are automatically synced to: <a href="https://bump-tiktok-bot.preview.emergentagent.com" target="_blank" style="color:#7c3aed;">profile-reports-sync.preview.emergentagent.com</a></div>
                </div>
                <div id="filter-info" style="font-size:12px;color:#a78bfa;margin-bottom:10px;">Showing: All time</div>
                <div style="max-height:400px;overflow:auto">
                    <table class="report-table"><thead><tr><th>Date/Time</th><th>Profile</th><th>Comment</th><th>Video</th><th>Sheet</th></tr></thead><tbody id="rb"></tbody></table>
                </div>
                <div style="margin-top:16px;padding:12px;background:#27272a;border-radius:8px;">
                    <div style="display:flex;gap:24px;justify-content:center;flex-wrap:wrap;">
                        <div style="text-align:center;padding:8px 16px;background:#1e1b4b;border:1px solid #4c1d95;border-radius:8px;"><div style="font-size:24px;font-weight:700;color:#a78bfa" id="sum-month">0</div><div style="font-size:11px;color:#71717a">This Month</div></div>
                        <div style="text-align:center;padding:8px 16px;background:#172554;border:1px solid #1d4ed8;border-radius:8px;"><div style="font-size:24px;font-weight:700;color:#60a5fa" id="sum-week">0</div><div style="font-size:11px;color:#71717a">This Week</div></div>
                        <div style="text-align:center;padding:8px 16px;background:#14532d;border:1px solid #16a34a;border-radius:8px;"><div style="font-size:24px;font-weight:700;color:#4ade80" id="sum-today">0</div><div style="font-size:11px;color:#71717a">Today</div></div>
                        <div style="text-align:center;padding:8px 16px;background:#27272a;border:1px solid #3f3f46;border-radius:8px;"><div style="font-size:24px;font-weight:700;color:#e4e4e7" id="sum-total">0</div><div style="font-size:11px;color:#71717a">All Time</div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        let profiles=[],selected=new Set(),sheetMap={},report=[],filteredReport=[];
        let currentFilter='all';
        const SHEETS=['Bump Connect','Kollabsy','Bump Syndicate'];
        setInterval(upd,1000);
        window.addEventListener('load', function(){ sync(); upd(); });
        function showTab(t){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));event.target.classList.add('active');document.getElementById('tab-main').style.display=t=='main'?'block':'none';document.getElementById('tab-dm').style.display=t=='dm'?'block':'none';document.getElementById('tab-replies').style.display=t=='replies'?'block':'none';document.getElementById('tab-post').style.display=t=='post'?'block':'none';document.getElementById('tab-profiles').style.display=t=='profiles'?'block':'none';document.getElementById('tab-report').style.display=t=='report'?'block':'none';if(t=='dm')updDm();if(t=='replies')refreshReplies();if(t=='post')updPost();if(t=='profiles')refreshProfileMapping();if(t=='report')fetchCloudStats();}
        async function sync(){const r=await fetch('/api/sync-profiles',{method:'POST'});profiles=(await r.json()).profiles||[];render();updateProfileCounts();}
        async function loadC(){const r=await fetch('/api/load-comments',{method:'POST'});const d=await r.json();alert('Loaded:\\n'+Object.entries(d.counts).map(([k,v])=>k+': '+v).join('\\n'));}
        function render(){const e=document.getElementById('pl');if(!profiles.length){e.innerHTML='<div style="text-align:center;color:#71717a;padding:40px">Click Sync to load 25 profiles</div>';return;}e.innerHTML=profiles.map(p=>'<div class="profile '+(selected.has(p.user_id)?'selected':'')+'" onclick="tog(\\''+p.user_id+'\\')"><input type="checkbox" '+(selected.has(p.user_id)?'checked':'')+' onclick="event.stopPropagation();tog(\\''+p.user_id+'\\')"><div style="flex:1"><div style="font-weight:500">'+(p.name||p.user_id)+'</div><div style="font-size:11px;color:#71717a">'+p.user_id+'</div></div></div>').join('');document.getElementById('pc').textContent=selected.size+'/'+profiles.length+' selected';}
        function tog(id){selected.has(id)?selected.delete(id):selected.add(id);render();}
        function selAll(){if(selected.size==profiles.length)selected.clear();else profiles.forEach(p=>selected.add(p.user_id));render();}
        async function start(){if(!selected.size){alert('Select profiles first');return;}await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({min_delay:+document.getElementById('mind').value,max_delay:+document.getElementById('maxd').value,videos_per_profile:+document.getElementById('vpp').value,target_hashtag:document.getElementById('hashtag').value,parallel_browsers:+document.getElementById('parallel').value})});await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile_ids:[...selected],sheet_mapping:{}})});document.getElementById('startb').style.display='none';document.getElementById('stopb').style.display='inline';}
        async function stop(){await fetch('/api/stop',{method:'POST'});}
        
        function filterToday(){currentFilter='today';applyFilter();}
        function filterWeek(){currentFilter='week';applyFilter();}
        function filterMonth(){currentFilter='month';applyFilter();}
        function filterAll(){currentFilter='all';applyFilter();}
        
        function applyFilter(){
            const now=new Date();
            const today=now.toISOString().split('T')[0];
            const weekAgo=new Date(now-7*24*60*60*1000).toISOString().split('T')[0];
            const monthAgo=new Date(now-30*24*60*60*1000).toISOString().split('T')[0];
            
            if(currentFilter=='today'){
                filteredReport=report.filter(r=>r.timestamp.startsWith(today));
                document.getElementById('filter-info').textContent='Showing: Today ('+today+')';
            }else if(currentFilter=='week'){
                filteredReport=report.filter(r=>r.timestamp>=weekAgo);
                document.getElementById('filter-info').textContent='Showing: Last 7 days';
            }else if(currentFilter=='month'){
                filteredReport=report.filter(r=>r.timestamp>=monthAgo);
                document.getElementById('filter-info').textContent='Showing: Last 30 days';
            }else{
                filteredReport=report;
                document.getElementById('filter-info').textContent='Showing: All time ('+report.length+' comments)';
            }
            renderReport();
        }
        
        function renderReport(){
            document.getElementById('rc').textContent=report.length+' total';
            document.getElementById('rb').innerHTML=filteredReport.length?filteredReport.slice().sort((a,b)=>b.timestamp.localeCompare(a.timestamp)).map(r=>'<tr><td style="white-space:nowrap">'+r.timestamp+'</td><td>'+r.profile+'</td><td title="'+r.comment.replace(/"/g,'&quot;')+'">'+r.comment.substring(0,35)+'...</td><td><a href="'+r.video_url+'" target="_blank">🔗 Open</a></td><td>'+r.sheet+'</td></tr>').join(''):'<tr><td colspan="5" style="text-align:center;color:#71717a;padding:20px">No comments for this period</td></tr>';

            const now=new Date();
            const todayStr=now.toISOString().split('T')[0];
            const weekAgo=new Date(now-7*24*60*60*1000).toISOString().split('T')[0];
            const monthAgo=new Date(now-30*24*60*60*1000).toISOString().split('T')[0];

            document.getElementById('sum-total').textContent=report.length.toLocaleString();
            document.getElementById('sum-month').textContent=report.filter(r=>r.timestamp>=monthAgo).length.toLocaleString();
            document.getElementById('sum-week').textContent=report.filter(r=>r.timestamp>=weekAgo).length.toLocaleString();
            document.getElementById('sum-today').textContent=report.filter(r=>r.timestamp.startsWith(todayStr)).length.toLocaleString();
        }

        function applyDateRange(){
            const startDate=document.getElementById('startDate').value;
            const endDate=document.getElementById('endDate').value;
            if(!startDate&&!endDate){filterAll();return;}
            filteredReport=report.filter(r=>{
                const ts=r.timestamp.split(' ')[0];
                if(startDate&&ts<startDate)return false;
                if(endDate&&ts>endDate)return false;
                return true;
            });
            let info='Showing: ';
            if(startDate&&endDate)info+=startDate+' to '+endDate;
            else if(startDate)info+='From '+startDate;
            else if(endDate)info+='Until '+endDate;
            info+=' ('+filteredReport.length+' comments)';
            document.getElementById('filter-info').textContent=info;
            currentFilter='custom';
            renderReport();
        }

        function clearDateRange(){
            document.getElementById('startDate').value='';
            document.getElementById('endDate').value='';
            filterAll();
        }
        
        async function fetchCloudStats(){
            try{
                const r=await fetch('/api/cloud-stats');
                const d=await r.json();
                if(d.ok){
                    document.getElementById('cloud-total-count').textContent=d.total.toLocaleString()+' comments';
                    document.getElementById('local-count').textContent=report.length.toLocaleString();
                }else{
                    document.getElementById('cloud-total-count').textContent='Error';
                }
            }catch(e){document.getElementById('cloud-total-count').textContent='Offline';}
        }
        
        async function upd(){try{const r=await fetch('/api/status');const d=await r.json();document.getElementById('prog').style.width=(d.total?(d.progress/d.total*100):0)+'%';document.getElementById('sp').textContent=d.completed.length;document.getElementById('sc-today').textContent=d.comments_today||0;document.getElementById('sc').textContent=d.comments_posted||0;document.getElementById('st').textContent=d.running?'Running: '+d.current_profile+' ('+d.progress+'/'+d.total+')':'Ready';if(!d.running){document.getElementById('startb').style.display='inline';document.getElementById('stopb').style.display='none';}if(d.logs.length)document.getElementById('logs').innerHTML=d.logs.map(l=>'<div style="color:'+(l.includes('✗')?'#f87171':l.includes('✓')?'#4ade80':'#a1a1aa')+'">'+l+'</div>').join('');if(d.report&&d.report.length!==report.length){report=d.report;applyFilter();}}catch(e){}}
        function clrLog(){fetch('/api/clear-logs',{method:'POST'});document.getElementById('logs').innerHTML='Cleared';}
        async function clrReport(){if(!confirm('⚠️ Delete ALL comment history forever?\\n\\nThis will remove '+report.length+' comments and cannot be undone.'))return;await fetch('/api/clear-report',{method:'POST'});report=[];filteredReport=[];renderReport();}
        function expCSV(){if(!report.length)return alert('No data');const csv='Date,Time,Profile,Comment,Video URL,Sheet\\n'+report.map(r=>{const[d,t]=r.timestamp.split(' ');return d+','+t+','+r.profile+',"'+r.comment.replace(/"/g,'""')+'",'+r.video_url+','+r.sheet;}).join('\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv]));a.download='tiktok_comments_history_'+new Date().toISOString().split('T')[0]+'.csv';a.click();}
        async function syncCloud(){if(!report.length)return alert('No reports to sync');try{const r=await fetch('/api/sync-to-cloud',{method:'POST'});const d=await r.json();alert('☁️ Synced '+d.synced+' reports to cloud dashboard!');}catch(e){alert('Sync failed: '+e.message);}}
        async function loadFromCloud(){
            const btn=document.getElementById('btn-load-cloud');
            btn.disabled=true;btn.textContent='⏳ Loading...';
            try{
                const r=await fetch('/api/load-from-cloud');
                const d=await r.json();
                if(d.ok){
                    report=d.reports||[];filteredReport=report;renderReport();
                    document.getElementById('cloud-total-count').textContent=d.cloud_total.toLocaleString()+' comments';
                    document.getElementById('local-count').textContent=report.length.toLocaleString();
                    alert('✅ Loaded '+report.length+' comments!\\n\\nCloud total: '+d.cloud_total.toLocaleString());
                }else{alert('❌ '+d.message);}
            }catch(e){alert('❌ Error: '+e.message);}
            btn.disabled=false;btn.textContent='📥 Load from Cloud (11k+)';
        }
        
        // Repost Functions
        let postStatus={running:false,posts_made:0,history:[],logs:[]};
        async function updPost(){
            try{
                const r=await fetch('/api/post/status');
                const d=await r.json();
                postStatus=d;
                document.getElementById('post-done').textContent=d.posts_made||0;
                const todayCount=d.history?d.history.filter(h=>{const t=h.timestamp||'';return t.startsWith(new Date().toISOString().split('T')[0])}).length:0;
                document.getElementById('post-today-count').textContent=todayCount;
                document.getElementById('post-prog').style.width=(d.total?(d.progress/d.total*100):0)+'%';
                const dayName=new Date().toLocaleDateString('en-US',{weekday:'long'});
                const isMonday=new Date().getDay()===1;
                const contentType=isMonday?'Brand':'Social Media';
                document.getElementById('post-st').textContent=d.running?'Reposting: '+d.current_profile+' ('+d.progress+'/'+d.total+')':'Ready ('+dayName+': '+contentType+' content)';
                document.getElementById('post-next').textContent=d.last_run?(d.last_run===new Date().toISOString().split('T')[0]?'Last run: Today':'Last run: '+d.last_run)+(d.next_run?' | Next: '+d.next_run:''):'Scheduler: Waiting for first run...';
                if(!d.running){document.getElementById('post-startb').style.display='inline';document.getElementById('post-stopb').style.display='none';}
                else{document.getElementById('post-startb').style.display='none';document.getElementById('post-stopb').style.display='inline';}
                if(d.logs&&d.logs.length)document.getElementById('post-logs').innerHTML=d.logs.map(l=>'<div style="color:'+(l.includes('Error')||l.includes('Failed')?'#f87171':l.includes('Reposted')||l.includes('Done')?'#4ade80':'#a1a1aa')+'">'+l+'</div>').join('');
                renderPostHistory(d.history||[]);
            }catch(e){}
        }
        setInterval(()=>{if(document.getElementById('tab-post').style.display!='none')updPost();},2000);
        function renderPostHistory(hist){
            document.getElementById('post-hist-tb').innerHTML=hist.length?hist.slice().sort((a,b)=>b.timestamp.localeCompare(a.timestamp)).slice(0,50).map(h=>'<tr><td>'+h.timestamp+'</td><td>'+h.profile+'</td><td>'+(h.repost_url?'<a href="'+h.repost_url+'" target="_blank" style="color:#f472b6">@'+(h.tiktok_username||'View')+'</a>':'<span style="color:#71717a">-</span>')+'</td><td style="color:'+(h.content_type=='brand'?'#4ade80':'#60a5fa')+'">'+((h.content_type||'').charAt(0).toUpperCase()+(h.content_type||'').slice(1))+'</td><td style="color:#4ade80">'+h.status+'</td></tr>').join(''):'<tr><td colspan="5" style="text-align:center;color:#71717a">No reposts yet. Click Start or wait for auto-scheduler.</td></tr>';
        }
        async function applyRepostSettings(){
            const s={max_reposts_per_day:+document.getElementById('post-maxday').value,min_delay:+document.getElementById('post-mind').value,max_delay:+document.getElementById('post-maxd').value};
            await fetch('/api/post/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(s)});
            document.getElementById('post-limit-display').textContent=s.max_reposts_per_day;
            alert('Settings saved!');
        }
        async function startPost(){await fetch('/api/post/start',{method:'POST'});document.getElementById('post-startb').style.display='none';document.getElementById('post-stopb').style.display='inline';}
        async function stopPost(){await fetch('/api/post/stop',{method:'POST'});}
        function clrPostLog(){fetch('/api/post/clear-logs',{method:'POST'});document.getElementById('post-logs').innerHTML='Cleared';}
        async function clrPostHistory(){if(!confirm('Clear all repost history?'))return;await fetch('/api/post/clear-history',{method:'POST'});updPost();}
        function expPostCSV(){window.open('/api/post/export','_blank');}
        
        // DM Functions
        let dmStatus={running:false,dms_sent:0,report:[]};
        let dmMessageEdited=false;
        // DM Profile Selection
        let dmSelected = new Set();
        
        function renderDmProfiles(){
            const e=document.getElementById('dm-pl');
            if(!profiles.length){e.innerHTML='<div style="text-align:center;color:#71717a;padding:20px">Sync profiles in Control tab first</div>';return;}
            e.innerHTML=profiles.map(p=>'<div class="profile '+(dmSelected.has(p.user_id)?'selected':'')+'" onclick="dmTog(\\''+p.user_id+'\\')"><input type="checkbox" '+(dmSelected.has(p.user_id)?'checked':'')+' onclick="event.stopPropagation();dmTog(\\''+p.user_id+'\\')"><div style="flex:1"><div style="font-weight:500">'+(p.name||p.user_id)+'</div></div></div>').join('');
            document.getElementById('dm-pc').textContent=dmSelected.size+'/'+profiles.length;
        }
        function dmTog(id){if(dmSelected.has(id))dmSelected.delete(id);else dmSelected.add(id);renderDmProfiles();}
        function dmSelAll(){profiles.forEach(p=>dmSelected.add(p.user_id));renderDmProfiles();}
        function dmSelNone(){dmSelected.clear();renderDmProfiles();}
        
        function dmModeChange(){
            const mode=document.getElementById('dm-mode').value;
            document.getElementById('dm-brand-info').style.display=mode=='brand_search'?'block':'none';
            document.getElementById('dm-specific').style.display=mode=='specific'?'block':'none';
            document.getElementById('dm-hashtag').style.display=mode=='hashtag'?'block':'none';
            document.getElementById('dm-video').style.display=mode=='commenters'?'block':'none';
            document.getElementById('dm-account').style.display=mode=='followers'?'block':'none';
        }
        async function updDm(){
            try{
                // Render DM profiles if not done
                if(profiles.length && document.getElementById('dm-pl').innerHTML.includes('Sync profiles'))renderDmProfiles();
                
                const r=await fetch('/api/dm/status');
                const d=await r.json();
                dmStatus=d;
                document.getElementById('dm-sent').textContent=d.dms_sent||0;
                document.getElementById('dm-today').textContent=d.dms_sent_today||0;
                const maxTotal=d.settings?.max_dms_total||2500;
                document.getElementById('dm-remaining').textContent=Math.max(0, maxTotal-(d.dms_sent_today||0));
                document.getElementById('dm-profiles-done').textContent=d.profiles_completed?.length||0;
                document.getElementById('dm-prog').style.width=(d.total?(d.progress/d.total*100):0)+'%';
                document.getElementById('dm-st').textContent=d.running?'🔄 Running: '+d.current_profile+' ('+d.progress+'/'+d.total+')':'Ready - Select profiles and click Start';
                if(!d.running){document.getElementById('dm-startb').style.display='inline';document.getElementById('dm-stopb').style.display='none';}
                else{document.getElementById('dm-startb').style.display='none';document.getElementById('dm-stopb').style.display='inline';}
                if(d.logs&&d.logs.length)document.getElementById('dm-logs').innerHTML=d.logs.map(l=>'<div style="color:'+(l.includes('✗')?'#f87171':l.includes('✓')?'#4ade80':l.includes('⚠')?'#fbbf24':'#a1a1aa')+'">'+l+'</div>').join('');
                if(d.report)renderDmReport(d.report);
                if(!dmMessageEdited && d.targets?.messages?.default)document.getElementById('dm-default-msg').value=d.targets.messages.default;
                // Update limit displays
                document.getElementById('dm-limit-profile').textContent=d.settings?.max_dms_per_profile||100;
                document.getElementById('dm-limit-total').textContent=d.settings?.max_dms_total||2500;
            }catch(e){}
        }
        setInterval(()=>{if(document.getElementById('tab-dm').style.display!='none')updDm();},2000);
        function renderDmReport(rep){
            document.getElementById('dm-rb').innerHTML=rep.length?rep.slice().sort((a,b)=>b.timestamp.localeCompare(a.timestamp)).slice(0,50).map(r=>'<tr><td>'+r.timestamp+'</td><td>'+r.profile+'</td><td>@'+r.username+'</td><td title="'+r.message+'">'+r.message.substring(0,30)+'...</td><td style="color:'+(r.status=='sent'?'#4ade80':'#f87171')+'">'+r.status+'</td></tr>').join(''):'<tr><td colspan="5" style="text-align:center;color:#71717a">No DMs sent yet</td></tr>';
        }
        async function saveDmSettings(){
            const mode=document.getElementById('dm-mode').value;
            const settings={
                target_mode:mode,
                max_dms_per_profile:+document.getElementById('dm-max').value,
                max_dms_total:+document.getElementById('dm-max-total').value,
                min_delay:+document.getElementById('dm-mind').value,
                max_delay:+document.getElementById('dm-maxd').value,
                target_hashtag:document.getElementById('dm-tag').value,
                target_video_url:document.getElementById('dm-video-url').value,
                target_account:document.getElementById('dm-acc').value
            };
            await fetch('/api/dm/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)});
            alert('DM settings saved!');
        }
        async function saveDmMessage(){
            const msg=document.getElementById('dm-default-msg').value;
            await fetch('/api/dm/message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
            dmMessageEdited=false;
            alert('Message saved!');
        }
        async function startDm(){
            if(!dmSelected.size){alert('Please select at least one profile');return;}
            await saveDmSettings();
            await fetch('/api/dm/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile_ids:[...dmSelected]})});
            document.getElementById('dm-startb').style.display='none';
            document.getElementById('dm-stopb').style.display='inline';
        }
        async function stopDm(){await fetch('/api/dm/stop',{method:'POST'});}
        function clrDmLog(){fetch('/api/dm/clear-logs',{method:'POST'});document.getElementById('dm-logs').innerHTML='Cleared';}
        async function clrDmHistory(){if(!confirm('Clear all DM history?'))return;await fetch('/api/dm/clear-history',{method:'POST'});dmStatus.report=[];renderDmReport([]);}
        function expDmCSV(){window.open('/api/dm/export','_blank');}
        
        // ========== REPLIES TAB FUNCTIONS ==========
        let replyData = {drafts: [], approved: [], sent: []};
        
        async function refreshReplies() {
            try {
                const r = await fetch('/api/replies/status');
                const d = await r.json();
                replyData = d;
                
                document.getElementById('reply-pending').textContent = d.pending?.length || 0;
                document.getElementById('reply-drafts').textContent = d.drafts?.length || 0;
                document.getElementById('reply-approved').textContent = d.approved?.length || 0;
                document.getElementById('reply-sent').textContent = d.sent?.length || 0;
                document.getElementById('draft-count').textContent = d.drafts?.length || 0;
                document.getElementById('approved-count').textContent = d.approved?.length || 0;
                document.getElementById('sent-count').textContent = d.sent?.length || 0;
                
                document.getElementById('reply-status').textContent = d.checking 
                    ? '🔄 ' + (d.logs?.slice(-1)[0] || 'Processing...') 
                    : 'Last check: ' + (d.last_check || 'Never');
                
                // Render draft replies
                renderDraftReplies(d.drafts || []);
                renderApprovedReplies(d.approved || []);
                renderSentReplies(d.sent || []);
                
                // Update logs
                if (d.logs && d.logs.length) {
                    document.getElementById('reply-logs').innerHTML = d.logs.map(l => 
                        '<div style="color:' + (l.includes('✗') ? '#f87171' : l.includes('✓') ? '#4ade80' : l.includes('⚠') ? '#fbbf24' : '#a1a1aa') + '">' + l + '</div>'
                    ).join('');
                }
            } catch(e) { console.error(e); }
        }
        
        function renderDraftReplies(drafts) {
            const container = document.getElementById('draft-replies-container');
            if (!drafts || drafts.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:#71717a;padding:20px;">No draft replies. Click "Check for Replies" to find new messages.</div>';
                return;
            }
            
            container.innerHTML = drafts.map((d, i) => `
                <div style="background:#27272a;border:1px solid #3f3f46;border-radius:8px;padding:12px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <div>
                            <span style="color:#4ade80;font-weight:bold;">@${d.username}</span>
                            <span style="color:#71717a;font-size:12px;margin-left:8px;">via ${d.profile}</span>
                        </div>
                        <span style="color:#71717a;font-size:11px;">${d.received_at}</span>
                    </div>
                    <div style="background:#1c1c1e;border-radius:6px;padding:8px;margin-bottom:8px;">
                        <div style="color:#71717a;font-size:11px;margin-bottom:4px;">Their message:</div>
                        <div style="color:#fbbf24;font-size:13px;">"${d.their_message}"</div>
                    </div>
                    <div style="margin-bottom:8px;">
                        <div style="color:#71717a;font-size:11px;margin-bottom:4px;">AI Draft Reply:</div>
                        <textarea id="draft-${i}" style="width:100%;height:60px;background:#18181b;border:1px solid #3f3f46;color:#4ade80;border-radius:6px;padding:8px;font-size:13px;">${d.draft_message}</textarea>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button class="btn btn-success" onclick="approveDraft(${i})" style="padding:6px 16px;">✓ Approve</button>
                        <button class="btn btn-primary" onclick="regenerateDraft(${i})" style="padding:6px 16px;">🔄 Regenerate</button>
                        <button class="btn btn-danger" onclick="rejectDraft(${i})" style="padding:6px 16px;">✗ Reject</button>
                    </div>
                </div>
            `).join('');
        }
        
        function renderApprovedReplies(approved) {
            const container = document.getElementById('approved-replies-container');
            if (!approved || approved.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:#71717a;padding:20px;">No approved replies yet.</div>';
                return;
            }
            
            container.innerHTML = approved.map((a, i) => `
                <div style="background:#14532d;border:1px solid #16a34a;border-radius:8px;padding:12px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="color:#4ade80;font-weight:bold;">@${a.username}</span>
                            <span style="color:#86efac;font-size:12px;margin-left:8px;">via ${a.profile}</span>
                        </div>
                        <button class="btn btn-secondary" onclick="unapprove(${i})" style="padding:4px 12px;font-size:12px;">Undo</button>
                    </div>
                    <div style="color:#86efac;font-size:13px;margin-top:8px;">"${a.draft_message}"</div>
                </div>
            `).join('');
        }
        
        function renderSentReplies(sent) {
            const tbody = document.getElementById('sent-replies-table');
            if (!sent || sent.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#71717a">No sent replies yet</td></tr>';
                return;
            }
            
            tbody.innerHTML = sent.slice().reverse().slice(0, 50).map(s => `
                <tr>
                    <td>${s.sent_at || ''}</td>
                    <td>${s.profile}</td>
                    <td>@${s.username}</td>
                    <td title="${s.their_message}">${s.their_message?.substring(0, 30)}...</td>
                    <td title="${s.draft_message}">${s.draft_message?.substring(0, 30)}...</td>
                </tr>
            `).join('');
        }
        
        async function checkReplies() {
            document.getElementById('btn-check-replies').disabled = true;
            document.getElementById('btn-check-replies').textContent = '⏳ Checking...';
            await fetch('/api/replies/check', {method: 'POST'});
            setTimeout(() => {
                document.getElementById('btn-check-replies').disabled = false;
                document.getElementById('btn-check-replies').textContent = '📥 Check for Replies';
            }, 5000);
        }
        
        async function approveDraft(index) {
            const editedMsg = document.getElementById('draft-' + index)?.value || replyData.drafts[index].draft_message;
            await fetch('/api/replies/approve', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index, message: editedMsg})
            });
            refreshReplies();
        }
        
        async function rejectDraft(index) {
            await fetch('/api/replies/reject', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({index: index})});
            refreshReplies();
        }
        
        async function regenerateDraft(index) {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳...';
            await fetch('/api/replies/regenerate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({index: index})});
            setTimeout(() => { btn.disabled = false; btn.textContent = '🔄 Regenerate'; refreshReplies(); }, 3000);
        }
        
        async function unapprove(index) {
            await fetch('/api/replies/unapprove', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({index: index})});
            refreshReplies();
        }
        
        async function sendApproved() {
            if (!confirm('Send all approved replies? This will open browsers and send messages.')) return;
            document.getElementById('btn-send-approved').disabled = true;
            document.getElementById('btn-send-approved').textContent = '⏳ Sending...';
            await fetch('/api/replies/send', {method: 'POST'});
            setTimeout(() => {
                document.getElementById('btn-send-approved').disabled = false;
                document.getElementById('btn-send-approved').textContent = '📤 Send All Approved';
            }, 5000);
        }
        
        function clrReplyLog() {
            fetch('/api/replies/clear-logs', {method: 'POST'});
            document.getElementById('reply-logs').innerHTML = 'Cleared';
        }
        
        // Auto-refresh replies tab
        setInterval(() => { if(document.getElementById('tab-replies').style.display != 'none') refreshReplies(); }, 3000);

        // Profile Mapping Functions
        let profileMappings = {};

        async function refreshProfileMapping() {
            try {
                // Fetch current mappings
                const r = await fetch('/api/profile-mapping');
                profileMappings = await r.json();
                renderProfileMapping();
            } catch(e) {
                console.error('Error fetching profile mapping:', e);
            }
        }

        function renderProfileMapping() {
            const tbody = document.getElementById('profile-mapping-tb');
            const select = document.getElementById('new-profile-select');

            // Build rows for all profiles
            let rows = '';
            const mappedProfiles = new Set(Object.keys(profileMappings));

            // Show all synced profiles with their mappings
            profiles.forEach(p => {
                const profileName = p.name || p.user_id;
                const username = profileMappings[profileName] || '';
                const hasMapping = !!username;
                const repostUrl = username ? 'https://www.tiktok.com/@' + username + '?tab=reposts' : '-';

                rows += '<tr>' +
                    '<td><div style="font-weight:500;">' + profileName + '</div><div style="font-size:10px;color:#71717a;">' + p.user_id + '</div></td>' +
                    '<td>' + (hasMapping ?
                        '<span style="color:#4ade80;">@' + username + '</span>' :
                        '<span style="color:#71717a;font-style:italic;">Not detected</span>') +
                    '</td>' +
                    '<td>' + (hasMapping ?
                        '<a href="' + repostUrl + '" target="_blank" style="color:#f472b6;font-size:11px;">' + repostUrl + '</a>' :
                        '<span style="color:#3f3f46;">-</span>') +
                    '</td>' +
                    '<td>' +
                        '<button class="btn btn-secondary" onclick="editProfileMapping(\\'' + profileName + '\\', \\'' + username + '\\')" style="padding:4px 8px;font-size:11px;margin-right:4px;">✏️ Edit</button>' +
                        (hasMapping ? '<button class="btn btn-danger" onclick="deleteProfileMapping(\\'' + profileName + '\\')" style="padding:4px 8px;font-size:11px;">🗑️</button>' : '') +
                    '</td>' +
                '</tr>';
            });

            // Also show any mappings for profiles not in the current list
            Object.keys(profileMappings).forEach(pname => {
                if (!profiles.find(p => (p.name || p.user_id) === pname)) {
                    const username = profileMappings[pname];
                    const repostUrl = 'https://www.tiktok.com/@' + username + '?tab=reposts';
                    rows += '<tr style="opacity:0.6;">' +
                        '<td><div style="font-weight:500;">' + pname + '</div><div style="font-size:10px;color:#71717a;">Not synced</div></td>' +
                        '<td><span style="color:#4ade80;">@' + username + '</span></td>' +
                        '<td><a href="' + repostUrl + '" target="_blank" style="color:#f472b6;font-size:11px;">' + repostUrl + '</a></td>' +
                        '<td>' +
                            '<button class="btn btn-secondary" onclick="editProfileMapping(\\'' + pname + '\\', \\'' + username + '\\')" style="padding:4px 8px;font-size:11px;margin-right:4px;">✏️ Edit</button>' +
                            '<button class="btn btn-danger" onclick="deleteProfileMapping(\\'' + pname + '\\')" style="padding:4px 8px;font-size:11px;">🗑️</button>' +
                        '</td>' +
                    '</tr>';
                }
            });

            if (!rows) {
                rows = '<tr><td colspan="4" style="text-align:center;color:#71717a;padding:40px;">No profiles synced. Click "Sync" in Control tab first, then run any automation to auto-detect usernames.</td></tr>';
            }

            tbody.innerHTML = rows;

            // Update the profile select dropdown
            let options = '<option value="">Select Profile...</option>';
            profiles.forEach(p => {
                const profileName = p.name || p.user_id;
                if (!profileMappings[profileName]) {
                    options += '<option value="' + profileName + '">' + profileName + '</option>';
                }
            });
            select.innerHTML = options;
        }

        async function addProfileMapping() {
            const profile = document.getElementById('new-profile-select').value;
            const username = document.getElementById('new-tiktok-username').value.replace('@', '').trim();

            if (!profile) { alert('Please select a profile'); return; }
            if (!username) { alert('Please enter a TikTok username'); return; }

            await fetch('/api/profile-mapping', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ [profile]: username })
            });

            document.getElementById('new-tiktok-username').value = '';
            refreshProfileMapping();
        }

        function editProfileMapping(profile, currentUsername) {
            const newUsername = prompt('Enter TikTok username for ' + profile + ':', currentUsername);
            if (newUsername === null) return;

            const cleaned = newUsername.replace('@', '').trim();
            if (!cleaned) {
                if (confirm('Remove mapping for ' + profile + '?')) {
                    deleteProfileMapping(profile);
                }
                return;
            }

            fetch('/api/profile-mapping', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ [profile]: cleaned })
            }).then(() => refreshProfileMapping());
        }

        async function deleteProfileMapping(profile) {
            if (!confirm('Remove TikTok username mapping for ' + profile + '?')) return;

            await fetch('/api/profile-mapping/' + encodeURIComponent(profile), {
                method: 'DELETE'
            });
            refreshProfileMapping();
        }

        async function detectAllUsernames() {
            if (!confirm('This will open each browser one by one to detect TikTok usernames. Continue?')) return;
            alert('Username detection runs automatically when you start any automation (DM, Repost, Comments). The usernames will be saved and appear here.');
        }

        // Update daily target counts using loaded profiles
        function updateProfileCounts() {
            const numProfiles = profiles.length;
            const videosPerProfile = parseInt(document.getElementById('vpp')?.value) || 10;
            const dailyTarget = numProfiles * videosPerProfile;
            document.getElementById('profileCount').textContent = numProfiles.toLocaleString();
            document.getElementById('numProfiles').textContent = numProfiles;
            document.getElementById('numVideos').textContent = videosPerProfile;
            document.getElementById('videosPerProfile').textContent = videosPerProfile;
            document.getElementById('totalTarget').textContent = dailyTarget.toLocaleString();
            document.getElementById('dailyTarget').textContent = dailyTarget.toLocaleString();
        }
    </script>
</body>
</html>
"""

# =============================================================================
# API ROUTES
# =============================================================================
@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    """Serve screenshot images"""
    from flask import send_from_directory
    return send_from_directory(SCREENSHOTS_FOLDER, filename)

@app.route('/api/screenshots')
def api_screenshots():
    """List all screenshots"""
    screenshots = []
    if os.path.exists(SCREENSHOTS_FOLDER):
        for f in sorted(os.listdir(SCREENSHOTS_FOLDER), reverse=True)[:100]:
            if f.endswith('.png'):
                screenshots.append({
                    "filename": f,
                    "url": f"/screenshots/{f}",
                    "timestamp": f.split('_')[1] if '_' in f else ""
                })
    return jsonify({"screenshots": screenshots})

@app.route('/api/sync-profiles', methods=['POST'])
def api_sync():
    fetch_adspower_profiles()
    return jsonify({"profiles": profiles})

@app.route('/api/load-comments', methods=['POST'])
def api_load_comments():
    counts = {}
    for sheet in SHEET_NAMES:
        comments = fetch_google_sheet_comments(sheet)
        counts[sheet] = len(comments)
    return jsonify({"counts": counts})

@app.route('/api/status')
def api_status():
    # Fetch counts from Supabase to match Vercel dashboard
    try:
        # Use UTC midnight to match Vercel (which uses browser's timezone)
        from datetime import timezone as tz
        utc_now = datetime.now(tz.utc)
        utc_midnight = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_iso = utc_midnight.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        # Fetch from Supabase
        today_result = supabase.table('comment_reports').select('id', count='exact').gte('timestamp', today_iso).execute()
        total_result = supabase.table('comment_reports').select('id', count='exact').execute()

        today_count = today_result.count or 0
        total_count = total_result.count or 0
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        # Fallback to local data
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_count = sum(1 for r in automation_status.get("report", [])
                          if r.get("timestamp", "").startswith(today_str))
        total_count = len(automation_status.get("report", []))

    response = dict(automation_status)
    response["comments_today"] = today_count
    response["comments_posted"] = total_count
    return jsonify(response)

@app.route('/api/settings', methods=['POST'])
def api_settings():
    global settings
    settings.update(request.json)
    return jsonify({"ok": True})

@app.route('/api/start', methods=['POST'])
def api_start():
    if automation_status["running"]:
        return jsonify({"error": "Running"}), 400
    data = request.json
    t = threading.Thread(target=run_automation_thread, args=(data['profile_ids'], data['sheet_mapping']))
    t.daemon = True
    t.start()
    return jsonify({"ok": True})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    automation_status["running"] = False
    return jsonify({"ok": True})

@app.route('/api/not-logged-in', methods=['GET'])
def api_get_not_logged_in():
    """Get list of browsers that are not logged in"""
    return jsonify({
        "browsers": get_not_logged_in_list(),
        "count": len(get_not_logged_in_list())
    })

@app.route('/api/not-logged-in/clear', methods=['POST'])
def api_clear_not_logged_in():
    """Clear the not logged in browsers list"""
    clear_not_logged_in()
    return jsonify({"ok": True})

@app.route('/api/clear-logs', methods=['POST'])
def api_clear_logs():
    automation_status["logs"] = []
    return jsonify({"ok": True})

@app.route('/api/sync-to-cloud', methods=['POST'])
def api_sync_to_cloud():
    """Manually sync all reports to cloud dashboard"""
    synced = sync_all_to_cloud()
    return jsonify({"ok": True, "synced": synced})

@app.route('/api/cloud-stats', methods=['GET'])
def api_cloud_stats():
    """Get cloud stats from Supabase"""
    if not HAS_SUPABASE:
        return jsonify({"ok": False, "message": "Supabase not configured"})
    try:
        total_result = supabase.table("comment_reports").select("id", count="exact").execute()
        total = total_result.count if hasattr(total_result, 'count') else 0
        return jsonify({"ok": True, "total": total})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route('/api/load-from-cloud', methods=['GET'])
def api_load_from_cloud():
    """Load comment reports from Supabase cloud"""
    if not HAS_SUPABASE:
        return jsonify({"ok": False, "message": "Supabase not configured"})
    try:
        total_result = supabase.table("comment_reports").select("id", count="exact").execute()
        cloud_total = total_result.count if hasattr(total_result, 'count') else 0
        reports_result = supabase.table("comment_reports").select("*").order("timestamp", desc=True).limit(1000).execute()
        reports = []
        for r in reports_result.data:
            reports.append({"timestamp": r.get("timestamp", ""), "profile": r.get("profile", ""), "comment": r.get("comment", ""), "video_url": r.get("video_url", ""), "sheet": r.get("sheet", "")})
        automation_status["report"] = reports
        save_report_history()
        return jsonify({"ok": True, "reports": reports, "cloud_total": cloud_total})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})

@app.route('/api/clear-report', methods=['POST'])
def api_clear_report():
    automation_status["report"] = []
    automation_status["comments_posted"] = 0
    save_report_history()
    return jsonify({"ok": True})

# =============================================================================
# DM API ROUTES
# =============================================================================

@app.route('/api/dm/status')
def api_dm_status():
    today = datetime.now().strftime("%Y-%m-%d")
    # Count DMs sent today
    dms_today = sum(1 for r in dm_status["report"] if r.get("timestamp", "").startswith(today))
    
    return jsonify({
        "running": dm_status["running"],
        "current_profile": dm_status["current_profile"],
        "current_profile_index": dm_status.get("current_profile_index", 0),
        "profiles_completed": dm_status.get("profiles_completed", []),
        "progress": dm_status["progress"],
        "total": dm_status["total"],
        "dms_sent": dm_status["dms_sent"],
        "dms_sent_today": dms_today,
        "logs": dm_status["logs"][-100:],
        "report": dm_status["report"][-50:],
        "settings": dm_settings,
        "targets": {
            "specific_users_count": len(dm_targets.get("specific_users", [])),
            "scraped_brands_count": len(dm_targets.get("scraped_brands", [])),
            "messages": dm_targets.get("messages", {}),
            "groups_count": len(dm_targets["messages"].get("groups", {}))
        },
        "search_queries": DM_BRAND_SEARCH_QUERIES[:10]
    })

@app.route('/api/dm/settings', methods=['POST'])
def api_dm_settings():
    data = request.json or {}
    dm_settings.update({
        "enabled": data.get("enabled", dm_settings["enabled"]),
        "max_dms_per_profile": min(100, data.get("max_dms_per_profile", dm_settings["max_dms_per_profile"])),
        "max_dms_total": min(5000, data.get("max_dms_total", dm_settings.get("max_dms_total", 2500))),
        "parallel_browsers": data.get("parallel_browsers", dm_settings.get("parallel_browsers", 2)),
        "min_delay": data.get("min_delay", dm_settings["min_delay"]),
        "max_delay": data.get("max_delay", dm_settings["max_delay"]),
        "target_mode": data.get("target_mode", dm_settings["target_mode"]),
        "target_hashtag": data.get("target_hashtag", dm_settings.get("target_hashtag", "")),
        "target_account": data.get("target_account", dm_settings.get("target_account", "")),
        "target_video_url": data.get("target_video_url", dm_settings.get("target_video_url", "")),
    })
    return jsonify({"ok": True, "settings": dm_settings})

@app.route('/api/dm/message', methods=['POST'])
def api_dm_message():
    data = request.json or {}
    if "message" in data:
        dm_targets["messages"]["default"] = data["message"]
        save_dm_data()
    return jsonify({"ok": True})

@app.route('/api/dm/targets', methods=['GET'])
def api_dm_targets_get():
    return jsonify(dm_targets)

@app.route('/api/dm/targets', methods=['POST'])
def api_dm_targets_set():
    data = request.json or {}
    
    if "specific_users" in data:
        # Accept list of usernames or comma-separated string
        users = data["specific_users"]
        if isinstance(users, str):
            users = [u.strip().replace("@", "") for u in users.split(",") if u.strip()]
        dm_targets["specific_users"] = users
    
    if "default_message" in data:
        dm_targets["messages"]["default"] = data["default_message"]
    
    if "groups" in data:
        dm_targets["messages"]["groups"] = data["groups"]
    
    save_dm_data()
    return jsonify({"ok": True, "targets": dm_targets})

@app.route('/api/dm/add-group', methods=['POST'])
def api_dm_add_group():
    data = request.json or {}
    group_name = data.get("name", "").strip()
    users = data.get("users", [])
    message = data.get("message", dm_targets["messages"]["default"])
    
    if not group_name:
        return jsonify({"error": "Group name required"}), 400
    
    if isinstance(users, str):
        users = [u.strip().replace("@", "") for u in users.split(",") if u.strip()]
    
    dm_targets["messages"]["groups"][group_name] = {
        "users": users,
        "message": message
    }
    
    save_dm_data()
    return jsonify({"ok": True, "group": group_name})

@app.route('/api/dm/delete-group', methods=['POST'])
def api_dm_delete_group():
    data = request.json or {}
    group_name = data.get("name", "")
    
    if group_name in dm_targets["messages"]["groups"]:
        del dm_targets["messages"]["groups"][group_name]
        save_dm_data()
    
    return jsonify({"ok": True})

@app.route('/api/dm/start', methods=['POST'])
def api_dm_start():
    if dm_status["running"]:
        return jsonify({"error": "DM automation already running"}), 400
    
    data = request.json or {}
    selected_profile_ids = data.get("profile_ids", [])
    
    success = start_dm_automation(selected_profile_ids)
    return jsonify({"ok": success})

@app.route('/api/dm/stop', methods=['POST'])
def api_dm_stop():
    stop_dm_automation()
    return jsonify({"ok": True})

@app.route('/api/dm/clear-logs', methods=['POST'])
def api_dm_clear_logs():
    dm_status["logs"] = []
    return jsonify({"ok": True})

@app.route('/api/dm/clear-history', methods=['POST'])
def api_dm_clear_history():
    dm_status["report"] = []
    dm_status["sent_to"] = set()
    dm_status["dms_sent"] = 0
    save_dm_data()
    return jsonify({"ok": True})

@app.route('/api/dm/export', methods=['GET'])
def api_dm_export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "Profile", "Username", "Message", "Status"])
    
    for r in dm_status["report"]:
        ts = r.get("timestamp", "")
        date, time_str = (ts.split(" ") + [""])[:2]
        writer.writerow([date, time_str, r.get("profile", ""), r.get("username", ""), r.get("message", ""), r.get("status", "")])
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=dm_history_{datetime.now().strftime("%Y%m%d")}.csv'
    }

# =============================================================================
# REPLY MANAGEMENT API ROUTES
# =============================================================================

@app.route('/api/replies/status')
def api_replies_status():
    return jsonify({
        "checking": reply_status["checking"],
        "last_check": reply_status["last_check"],
        "pending": reply_status["pending_replies"],
        "drafts": reply_status["draft_replies"],
        "approved": reply_status["approved_replies"],
        "sent": reply_status["sent_replies"][-50:],
        "logs": reply_status["logs"][-100:]
    })

@app.route('/api/replies/check', methods=['POST'])
def api_replies_check():
    if start_check_replies():
        return jsonify({"ok": True, "message": "Started checking for replies"})
    return jsonify({"ok": False, "message": "Already checking or error"})

@app.route('/api/replies/approve', methods=['POST'])
def api_replies_approve():
    data = request.json or {}
    index = data.get("index", 0)
    edited_message = data.get("message", "")
    
    if index < len(reply_status["draft_replies"]):
        draft = reply_status["draft_replies"][index]
        if edited_message:
            draft["draft_message"] = edited_message
        draft["status"] = "approved"
        draft["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reply_status["approved_replies"].append(draft)
        reply_status["draft_replies"].pop(index)
        save_replies_data()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "message": "Invalid index"})

@app.route('/api/replies/reject', methods=['POST'])
def api_replies_reject():
    data = request.json or {}
    index = data.get("index", 0)
    
    if index < len(reply_status["draft_replies"]):
        reply_status["draft_replies"].pop(index)
        save_replies_data()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "message": "Invalid index"})

@app.route('/api/replies/unapprove', methods=['POST'])
def api_replies_unapprove():
    data = request.json or {}
    index = data.get("index", 0)
    
    if index < len(reply_status["approved_replies"]):
        approved = reply_status["approved_replies"][index]
        approved["status"] = "draft"
        reply_status["draft_replies"].append(approved)
        reply_status["approved_replies"].pop(index)
        save_replies_data()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "message": "Invalid index"})

@app.route('/api/replies/regenerate', methods=['POST'])
def api_replies_regenerate():
    data = request.json or {}
    index = data.get("index", 0)
    
    if index < len(reply_status["draft_replies"]):
        draft = reply_status["draft_replies"][index]
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_draft = loop.run_until_complete(draft_ai_reply(
                draft["username"],
                draft["their_message"],
                draft.get("original_outreach", "")
            ))
            loop.close()
            draft["draft_message"] = new_draft
            draft["regenerated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_replies_data()
            return jsonify({"ok": True, "draft": new_draft})
        except Exception as e:
            return jsonify({"ok": False, "message": str(e)})
    return jsonify({"ok": False, "message": "Invalid index"})

@app.route('/api/replies/send', methods=['POST'])
def api_replies_send():
    if start_send_approved():
        return jsonify({"ok": True, "message": "Started sending approved replies"})
    return jsonify({"ok": False, "message": "Already sending or no replies to send"})

@app.route('/api/replies/clear-logs', methods=['POST'])
def api_replies_clear_logs():
    reply_status["logs"] = []
    return jsonify({"ok": True})

# =============================================================================
# REPOST API ROUTES
# =============================================================================

@app.route('/api/post/status')
def api_post_status():
    today = datetime.now().strftime("%Y-%m-%d")
    day_name = datetime.now().strftime("%A")
    is_monday = datetime.now().weekday() == 0
    return jsonify({
        "running": post_status["running"],
        "current_profile": post_status["current_profile"],
        "progress": post_status["progress"],
        "total": post_status["total"],
        "posts_made": post_status["posts_made"],
        "last_run": post_status.get("last_run"),
        "next_run": post_status.get("next_run"),
        "day_name": day_name,
        "content_type": "brand" if is_monday else "social",
        "max_per_day": post_settings["max_reposts_per_day"],
        "history": post_status["history"][-50:],
        "logs": post_status["logs"][-100:]
    })

@app.route('/api/post/settings', methods=['POST'])
def api_post_settings():
    data = request.json or {}
    if "min_delay" in data:
        post_settings["min_delay"] = data["min_delay"]
    if "max_delay" in data:
        post_settings["max_delay"] = data["max_delay"]
    if "max_reposts_per_day" in data:
        post_settings["max_reposts_per_day"] = max(1, min(5, data["max_reposts_per_day"]))
    return jsonify({"ok": True, "settings": post_settings})

@app.route('/api/post/start', methods=['POST'])
def api_post_start():
    if post_status["running"]:
        return jsonify({"error": "Repost automation already running"}), 400
    use_source = request.json.get("use_source_accounts", False) if request.json else False
    success = start_repost_automation(use_source_accounts=use_source)
    return jsonify({"ok": success})

@app.route('/api/post/start-source', methods=['POST'])
def api_post_start_source():
    """Start reposting from source accounts (e.g., lifeadventuresafterfifty)"""
    if post_status["running"]:
        return jsonify({"error": "Repost automation already running"}), 400
    success = start_repost_automation(use_source_accounts=True)
    return jsonify({"ok": success})

@app.route('/api/post/source-accounts', methods=['GET'])
def api_get_source_accounts():
    """Get list of source accounts for reposting"""
    return jsonify({"accounts": REPOST_SOURCE_ACCOUNTS})

@app.route('/api/post/stop', methods=['POST'])
def api_post_stop():
    stop_post_automation()
    return jsonify({"ok": True})

@app.route('/api/post/clear-logs', methods=['POST'])
def api_post_clear_logs():
    post_status["logs"] = []
    return jsonify({"ok": True})

@app.route('/api/post/clear-history', methods=['POST'])
def api_post_clear_history():
    post_status["history"] = []
    post_status["posts_made"] = 0
    save_post_data()
    return jsonify({"ok": True})

@app.route('/api/post/export', methods=['GET'])
def api_post_export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "Profile", "Video", "Content Type", "Status"])
    for r in post_status["history"]:
        ts = r.get("timestamp", "")
        date, time_str = (ts.split(" ") + [""])[:2]
        writer.writerow([date, time_str, r.get("profile", ""), r.get("video", ""), r.get("content_type", ""), r.get("status", "")])
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=repost_history_{datetime.now().strftime("%Y%m%d")}.csv'
    }

# =============================================================================
# PROFILE MAPPING API - Map profile names to TikTok usernames
# =============================================================================

@app.route('/api/profile-mapping', methods=['GET'])
def api_get_profile_mapping():
    """Get all profile to TikTok username mappings"""
    return jsonify(profile_usernames)

@app.route('/api/profile-mapping', methods=['POST'])
def api_set_profile_mapping():
    """Set profile to TikTok username mappings"""
    global profile_usernames
    data = request.json or {}
    # Update mappings (remove @ prefix if present)
    for profile, username in data.items():
        if username:
            profile_usernames[profile] = username.replace("@", "")
        elif profile in profile_usernames:
            del profile_usernames[profile]
    save_profile_mapping()
    return jsonify({"ok": True, "mappings": profile_usernames})

@app.route('/api/profile-mapping/<profile>', methods=['PUT'])
def api_set_single_profile_mapping(profile):
    """Set TikTok username for a single profile"""
    data = request.json or {}
    username = data.get("username", "").replace("@", "")
    if username:
        set_tiktok_username(profile, username)
    elif profile in profile_usernames:
        del profile_usernames[profile]
        save_profile_mapping()
    return jsonify({"ok": True, "profile": profile, "username": username})

@app.route('/api/profile-mapping/<profile>', methods=['DELETE'])
def api_delete_profile_mapping(profile):
    """Delete TikTok username mapping for a profile"""
    global profile_usernames
    if profile in profile_usernames:
        del profile_usernames[profile]
        save_profile_mapping()
        return jsonify({"ok": True, "message": f"Mapping for {profile} deleted"})
    return jsonify({"ok": False, "message": f"No mapping found for {profile}"})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9000, help='Port to run on (default: 9000)')
    args = parser.parse_args()
    PORT = args.port
    print("=" * 50)
    print(f"  TikTok Commenter - http://localhost:{PORT}")
    print("=" * 50)
    load_report_history()  # Load past runs
    load_dm_data()  # Load DM data
    load_post_data()  # Load post queue and history
    load_replies_data()  # Load reply tracking data
    fetch_adspower_profiles()  # Auto-load AdsPower profiles on startup
    # Start background scheduler thread
    sched_thread = threading.Thread(target=scheduler_loop, daemon=True)
    sched_thread.start()
    print("  Scheduler running (checks scheduled posts every 30s)")
    # Auto-open browser after short delay
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)
