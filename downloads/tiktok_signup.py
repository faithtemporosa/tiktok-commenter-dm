#!/usr/bin/env python3
"""
TikTok Auto Signup
==================
Creates new TikTok accounts for profiles that are not logged in.
Uses temp email (mail.tm) for verification.

SETUP:
    pip install requests flask playwright
    playwright install chromium

RUN:
    python tiktok_signup.py

Open http://localhost:9005
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import requests
import time
import json
import random
import string
import threading
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("ERROR: Install playwright: pip install playwright && playwright install chromium")

try:
    from supabase import create_client
    SUPABASE_URL = "https://gisbdbbsvwjcjwovwklg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdpc2JkYmJzdndqY2p3b3Z3a2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTk5NzQsImV4cCI6MjA4NTM3NTk3NH0.uIKtftzl9ssaP2rXfXgHr3NFcA2PFYAUcSzQu_6ZIcI"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("Note: Install supabase for cloud sync: pip install supabase")

# =============================================================================
# CONFIGURATION
# =============================================================================
ADSPOWER_API = "http://localhost:50325"
LOCAL_BOT_API = "http://localhost:9000"

# =============================================================================
# GLOBAL STATE
# =============================================================================
app = Flask(__name__)

signup_status = {
    "running": False,
    "current_profile": None,
    "progress": 0,
    "total": 0,
    "logs": [],
    "completed": [],
    "failed": [],
    "created_accounts": []
}

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    signup_status["logs"].append(entry)
    try:
        print(entry)
    except UnicodeEncodeError:
        print(entry.encode('ascii', errors='replace').decode('ascii'))
    if len(signup_status["logs"]) > 300:
        signup_status["logs"] = signup_status["logs"][-300:]

# =============================================================================
# TEMP EMAIL (mail.tm)
# =============================================================================
MAILTM_API = "https://api.mail.tm"

def create_temp_email():
    """Create a temporary email using mail.tm API"""
    try:
        # Get available domains
        r = requests.get(f"{MAILTM_API}/domains", timeout=10)
        domains = r.json().get("hydra:member", [])
        if not domains:
            return None, None, None
        domain = domains[0]["domain"]

        # Generate random address
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        email = f"{username}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        # Create account
        r = requests.post(f"{MAILTM_API}/accounts", json={"address": email, "password": password}, timeout=10)
        if r.status_code in (200, 201):
            log(f"  ✓ Temp email created: {email}")
            return email, password, None
        else:
            log(f"  ✗ Failed to create email: {r.text[:100]}")
            return None, None, None
    except Exception as e:
        log(f"  ✗ Email creation error: {e}")
        return None, None, None

def get_mailtm_token(email, password):
    """Get auth token for mail.tm"""
    try:
        r = requests.post(f"{MAILTM_API}/token", json={"address": email, "password": password}, timeout=10)
        if r.status_code == 200:
            return r.json().get("token")
    except:
        pass
    return None

def wait_for_verification_code(email, password, timeout=120):
    """Poll mail.tm inbox for TikTok verification code"""
    log(f"  ⏳ Waiting for verification email (max {timeout}s)...")
    token = get_mailtm_token(email, password)
    if not token:
        log("  ✗ Could not get mail.tm token")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{MAILTM_API}/messages", headers=headers, timeout=10)
            messages = r.json().get("hydra:member", [])
            for msg in messages:
                subject = msg.get("subject", "").lower()
                if "tiktok" in subject or "verify" in subject or "code" in subject:
                    # Get full message
                    msg_r = requests.get(f"{MAILTM_API}/messages/{msg['id']}", headers=headers, timeout=10)
                    body = msg_r.json().get("text", "") or msg_r.json().get("html", "")
                    # Extract 6-digit code
                    import re
                    codes = re.findall(r'\b\d{6}\b', body)
                    if codes:
                        log(f"  ✓ Got verification code: {codes[0]}")
                        return codes[0]
        except Exception as e:
            pass
        time.sleep(5)

    log("  ✗ Verification code timeout")
    return None

# =============================================================================
# HELPERS
# =============================================================================
def generate_password():
    """Generate a strong password"""
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=14))

def generate_birthday():
    """Generate a random birthday for an 18-25 year old"""
    today = datetime.now()
    age_days = random.randint(18 * 365, 25 * 365)
    bday = today - timedelta(days=age_days)
    return bday.strftime("%Y-%m-%d"), bday.month, bday.day, bday.year

def generate_username(profile_name):
    """Generate a TikTok username based on profile name"""
    base = profile_name.lower().replace('tt', 'user')
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{base}{suffix}"

def open_browser(profile_id):
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=120)
        data = response.json()
        if data.get("code") == 0:
            return data.get("data", {})
        msg = data.get('msg', '')
        if any(x in msg for x in ['being installed', 'not ready', 'installing', 'Too many request']):
            log(f"  ⚠ Skipping {profile_id}: {msg}")
            return "SKIP"
        log(f"  ✗ AdsPower error: {msg}")
    except requests.exceptions.Timeout:
        log(f"  ✗ Timeout opening browser {profile_id}")
        return "SKIP"
    except Exception as e:
        log(f"  ✗ Error opening browser: {e}")
    return None

def close_browser(profile_id):
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile_id}", timeout=10)
    except:
        pass

def get_profile_id(profile_name):
    """Get AdsPower user_id from profile name"""
    try:
        r = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1000", timeout=10)
        data = r.json()
        if data.get("code") == 0:
            for p in data.get("data", {}).get("list", []):
                if p.get("name") == profile_name:
                    return p.get("user_id")
    except Exception as e:
        log(f"  ✗ Error fetching profiles: {e}")
    return None

def save_account_to_supabase(profile_name, browser_num, email, password, username, birthdate):
    """Save created account to Supabase"""
    if not HAS_SUPABASE:
        return
    try:
        supabase.table('tiktok_accounts').upsert({
            'browser_num': browser_num,
            'email': email,
            'password': password,
            'username': username,
            'birthdate': birthdate,
            'status': 'active'
        }).execute()
        log(f"  ✓ Saved account to Supabase: {username}")
    except Exception as e:
        log(f"  ✗ Supabase save error: {e}")

def clear_not_logged_in(profile_name):
    """Remove profile from not-logged-in list"""
    try:
        requests.post(f"{LOCAL_BOT_API}/api/not-logged-in/clear",
                      json={"profile": profile_name}, timeout=5)
    except:
        pass

# =============================================================================
# SIGNUP AUTOMATION
# =============================================================================
def run_signup_for_profile(profile_name, profile_id):
    """Run TikTok signup flow for a single profile"""
    log(f"\n{'='*40}")
    log(f"  Starting signup for: {profile_name}")

    # Create temp email
    email, email_pass, _ = create_temp_email()
    if not email:
        log(f"  ✗ Could not create temp email for {profile_name}")
        return False

    tiktok_password = generate_password()
    birthdate_str, bday_month, bday_day, bday_year = generate_birthday()
    username = generate_username(profile_name)

    # Open AdsPower browser
    browser_data = open_browser(profile_id)
    if not browser_data or browser_data == "SKIP":
        log(f"  ✗ Could not open browser for {profile_name}")
        return False

    ws_endpoint = browser_data.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        log(f"  ✗ No WebSocket endpoint for {profile_name}")
        close_browser(profile_id)
        return False

    success = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            log(f"  → Navigating to TikTok signup...")
            page.goto("https://www.tiktok.com/signup", timeout=30000)
            time.sleep(3)

            # Click "Use phone or email"
            try:
                phone_email_btn = page.locator('text=Use phone or email').first
                if phone_email_btn.is_visible():
                    phone_email_btn.click()
                    time.sleep(1)
            except:
                pass

            # Click "Sign up with email or username" if shown
            try:
                email_btn = page.locator('text=Sign up with email or username').first
                if email_btn.is_visible():
                    email_btn.click()
                    time.sleep(1)
            except:
                pass

            # Fill in birthday
            log(f"  → Filling birthday: {bday_month}/{bday_day}/{bday_year}")
            try:
                month_sel = page.locator('select[name="month"], [placeholder*="Month"], .month-select').first
                if month_sel.is_visible():
                    month_sel.select_option(str(bday_month))
                    time.sleep(0.5)
            except:
                pass
            try:
                day_sel = page.locator('select[name="day"], [placeholder*="Day"], .day-select').first
                if day_sel.is_visible():
                    day_sel.select_option(str(bday_day))
                    time.sleep(0.5)
            except:
                pass
            try:
                year_sel = page.locator('select[name="year"], [placeholder*="Year"], .year-select').first
                if year_sel.is_visible():
                    year_sel.select_option(str(bday_year))
                    time.sleep(0.5)
            except:
                pass

            # Click Next/Continue after birthday
            try:
                next_btn = page.locator('button:has-text("Next"), button:has-text("Continue")').first
                if next_btn.is_visible():
                    next_btn.click()
                    time.sleep(2)
            except:
                pass

            # Fill in email
            log(f"  → Entering email: {email}")
            try:
                email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first
                if email_input.is_visible():
                    email_input.fill(email)
                    time.sleep(0.5)
            except Exception as e:
                log(f"  ✗ Could not fill email: {e}")

            # Click Send Code / Next
            try:
                send_btn = page.locator('button:has-text("Send code"), button:has-text("Next"), button:has-text("Continue")').first
                if send_btn.is_visible():
                    send_btn.click()
                    time.sleep(2)
            except:
                pass

            # Wait for verification code
            code = wait_for_verification_code(email, email_pass, timeout=120)
            if not code:
                log(f"  ✗ No verification code received for {profile_name}")
                return False

            # Enter verification code
            log(f"  → Entering verification code: {code}")
            try:
                code_input = page.locator('input[placeholder*="code" i], input[name="code"], input[type="number"]').first
                if code_input.is_visible():
                    code_input.fill(code)
                    time.sleep(0.5)
            except Exception as e:
                log(f"  ✗ Could not fill code: {e}")

            # Enter password
            log(f"  → Setting password...")
            try:
                pw_input = page.locator('input[type="password"]').first
                if pw_input.is_visible():
                    pw_input.fill(tiktok_password)
                    time.sleep(0.5)
            except Exception as e:
                log(f"  ✗ Could not fill password: {e}")

            # Submit signup
            try:
                submit_btn = page.locator('button[type="submit"], button:has-text("Sign up"), button:has-text("Create")').first
                if submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(5)
            except:
                pass

            # Check if signed up
            time.sleep(3)
            current_url = page.url
            if "login" not in current_url.lower() and "signup" not in current_url.lower():
                log(f"  ✓ Signup successful for {profile_name}!")
                success = True

                # Save to Supabase
                browser_num = int(''.join(filter(str.isdigit, profile_name)) or 0)
                save_account_to_supabase(profile_name, browser_num, email, tiktok_password, username, birthdate_str)

                # Save locally
                signup_status["created_accounts"].append({
                    "profile": profile_name,
                    "email": email,
                    "password": tiktok_password,
                    "username": username,
                    "birthdate": birthdate_str,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Remove from not-logged-in list
                clear_not_logged_in(profile_name)
            else:
                log(f"  ✗ Signup may not have completed for {profile_name} (URL: {current_url[:60]})")

    except Exception as e:
        log(f"  ✗ Error during signup: {e}")
        traceback.print_exc()
    finally:
        close_browser(profile_id)

    return success

def run_signup_thread(profiles_to_signup):
    """Run signup for all not-logged-in profiles"""
    signup_status["running"] = True
    signup_status["progress"] = 0
    signup_status["total"] = len(profiles_to_signup)
    signup_status["completed"] = []
    signup_status["failed"] = []

    log(f"Starting signup for {len(profiles_to_signup)} profiles...")

    for i, profile_name in enumerate(profiles_to_signup):
        if not signup_status["running"]:
            log("Stopped by user")
            break

        signup_status["current_profile"] = profile_name
        signup_status["progress"] = i + 1

        # Get AdsPower profile ID
        profile_id = get_profile_id(profile_name)
        if not profile_id:
            log(f"  ✗ Could not find AdsPower ID for {profile_name}")
            signup_status["failed"].append(profile_name)
            continue

        success = run_signup_for_profile(profile_name, profile_id)

        if success:
            signup_status["completed"].append(profile_name)
        else:
            signup_status["failed"].append(profile_name)

        # Delay between profiles
        if i < len(profiles_to_signup) - 1 and signup_status["running"]:
            delay = random.randint(10, 20)
            log(f"  Waiting {delay}s before next profile...")
            time.sleep(delay)

    signup_status["running"] = False
    signup_status["current_profile"] = None
    log(f"\nDone! {len(signup_status['completed'])} succeeded, {len(signup_status['failed'])} failed")

# =============================================================================
# FLASK ROUTES
# =============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>TikTok Signup Bot</title>
<meta charset="utf-8">
<style>
  body { background:#09090b; color:#e4e4e7; font-family:sans-serif; margin:0; padding:20px; }
  h1 { color:#fff; font-size:22px; }
  .card { background:#18181b; border:1px solid #27272a; border-radius:12px; padding:20px; margin:12px 0; }
  .btn { padding:8px 18px; border-radius:8px; border:none; cursor:pointer; font-size:13px; font-weight:600; }
  .btn-start { background:#22c55e; color:#000; }
  .btn-stop { background:#ef4444; color:#fff; }
  .btn-refresh { background:#3f3f46; color:#fff; }
  .logs { background:#09090b; border:1px solid #27272a; border-radius:8px; padding:12px; height:300px; overflow-y:auto; font-family:monospace; font-size:12px; }
  .stat { display:inline-block; margin:0 16px 0 0; }
  .stat .num { font-size:28px; font-weight:700; color:#a78bfa; }
  .stat .lbl { font-size:11px; color:#71717a; }
  .profile-list { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
  .profile-tag { background:#27272a; border-radius:6px; padding:4px 10px; font-size:12px; }
  .profile-tag.done { background:#14532d; color:#86efac; }
  .profile-tag.failed { background:#450a0a; color:#fca5a5; }
  .accounts-table { width:100%; border-collapse:collapse; font-size:12px; margin-top:8px; }
  .accounts-table th { background:#27272a; padding:8px; text-align:left; }
  .accounts-table td { padding:8px; border-bottom:1px solid #27272a; }
  .progress { background:#27272a; border-radius:4px; height:6px; margin:8px 0; }
  .progress-fill { background:#a78bfa; height:6px; border-radius:4px; transition:width 0.3s; }
</style>
</head>
<body>
<h1>TikTok Signup Bot</h1>
<div class="card">
  <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;">
    <div class="stat"><div class="num" id="total">0</div><div class="lbl">Total</div></div>
    <div class="stat"><div class="num" id="done" style="color:#22c55e">0</div><div class="lbl">Done</div></div>
    <div class="stat"><div class="num" id="failed" style="color:#ef4444">0</div><div class="lbl">Failed</div></div>
    <div class="stat"><div class="num" id="current" style="color:#fbbf24;font-size:14px">-</div><div class="lbl">Current</div></div>
  </div>
  <div class="progress"><div class="progress-fill" id="prog" style="width:0%"></div></div>
  <div style="margin-top:12px;display:flex;gap:8px;">
    <button class="btn btn-start" onclick="startSignup()">▶ Start Signup</button>
    <button class="btn btn-stop" onclick="stopSignup()">■ Stop</button>
    <button class="btn btn-refresh" onclick="loadProfiles()">↻ Refresh Not-Logged-In List</button>
  </div>
</div>
<div class="card">
  <b>Not Logged In Profiles</b>
  <div class="profile-list" id="profile-list">Loading...</div>
</div>
<div class="card">
  <b>Live Logs</b>
  <div class="logs" id="logs"></div>
</div>
<div class="card" id="accounts-card" style="display:none">
  <b>Created Accounts</b>
  <table class="accounts-table">
    <thead><tr><th>Profile</th><th>Email</th><th>Password</th><th>Username</th><th>Birthday</th><th>Created</th></tr></thead>
    <tbody id="accounts-body"></tbody>
  </table>
</div>
<script>
  let notLoggedIn = [];
  setInterval(updateStatus, 2000);

  async function loadProfiles() {
    try {
      const r = await fetch('/api/not-logged-in');
      const d = await r.json();
      notLoggedIn = d.browsers || [];
      const el = document.getElementById('profile-list');
      el.innerHTML = notLoggedIn.map(b =>
        `<span class="profile-tag">${b.profile}</span>`
      ).join('') || '<span style="color:#71717a">None</span>';
      document.getElementById('total').textContent = notLoggedIn.length;
    } catch(e) { console.error(e); }
  }

  async function startSignup() {
    if (!notLoggedIn.length) { alert('No profiles to sign up. Click Refresh first.'); return; }
    await fetch('/api/start', { method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ profiles: notLoggedIn.map(b => b.profile) }) });
  }

  async function stopSignup() {
    await fetch('/api/stop', { method: 'POST' });
  }

  async function updateStatus() {
    try {
      const r = await fetch('/api/status');
      const d = await r.json();
      document.getElementById('done').textContent = d.completed.length;
      document.getElementById('failed').textContent = d.failed.length;
      document.getElementById('current').textContent = d.current_profile || '-';
      if (d.total > 0) {
        document.getElementById('prog').style.width = (d.progress / d.total * 100) + '%';
      }
      if (d.logs.length) {
        const logsEl = document.getElementById('logs');
        logsEl.innerHTML = d.logs.slice(-100).map(l =>
          `<div style="color:${l.includes('✗')?'#f87171':l.includes('✓')?'#4ade80':'#a1a1aa'}">${l}</div>`
        ).join('');
        logsEl.scrollTop = logsEl.scrollHeight;
      }
      if (d.created_accounts.length) {
        document.getElementById('accounts-card').style.display = 'block';
        document.getElementById('accounts-body').innerHTML = d.created_accounts.map(a =>
          `<tr><td>${a.profile}</td><td>${a.email}</td><td><code>${a.password}</code></td><td>@${a.username}</td><td>${a.birthdate}</td><td>${a.created_at}</td></tr>`
        ).join('');
      }
      // Update profile list tags with status
      document.querySelectorAll('.profile-tag').forEach(el => {
        const name = el.textContent.trim();
        if (d.completed.includes(name)) el.className = 'profile-tag done';
        else if (d.failed.includes(name)) el.className = 'profile-tag failed';
      });
    } catch(e) {}
  }

  loadProfiles();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/not-logged-in')
def api_not_logged_in():
    """Fetch not-logged-in profiles from the main bot"""
    try:
        r = requests.get(f"{LOCAL_BOT_API}/api/not-logged-in", timeout=5)
        return r.json()
    except:
        return jsonify({"browsers": [], "count": 0})

@app.route('/api/status')
def api_status():
    return jsonify(signup_status)

@app.route('/api/start', methods=['POST'])
def api_start():
    if signup_status["running"]:
        return jsonify({"error": "Already running"}), 400
    data = request.json
    profiles_to_signup = data.get("profiles", [])
    if not profiles_to_signup:
        return jsonify({"error": "No profiles provided"}), 400
    t = threading.Thread(target=run_signup_thread, args=(profiles_to_signup,), daemon=True)
    t.start()
    return jsonify({"ok": True, "total": len(profiles_to_signup)})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    signup_status["running"] = False
    return jsonify({"ok": True})

@app.route('/api/accounts')
def api_accounts():
    return jsonify(signup_status["created_accounts"])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9005)
    args = parser.parse_args()
    print("=" * 50)
    print(f"  TikTok Signup Bot - http://localhost:{args.port}")
    print("=" * 50)
    import webbrowser
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()
    app.run(host="0.0.0.0", port=args.port, debug=False)
