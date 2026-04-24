#!/usr/bin/env python3
"""
Multilogin TikTok Auto Signup
==============================
Creates new TikTok accounts using Multilogin browser profiles.
Uses temp email (mail.tm) for verification.

SETUP:
    pip install requests flask selenium

CONFIGURATION:
    Edit multilogin_config.json with your Multilogin credentials

RUN:
    python multilogin_tiktok_signup.py

Open http://localhost:9006
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import os
import random
import requests
import string
import threading
import time
import traceback
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from multilogin_api import MultiloginClient

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("ERROR: Install selenium: pip install selenium")

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
CONFIG_FILE = "multilogin_config.json"

def load_config():
    """Load configuration from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "email": "",
        "password": "",
        "automation_token": "",
        "folder_id": ""
    }

config = load_config()

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

multilogin_client = None
profiles_cache = []

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
        r = requests.post(
            f"{MAILTM_API}/accounts",
            json={"address": email, "password": password},
            timeout=10
        )

        if r.status_code == 201:
            return email, password, None
        else:
            log(f"  ✗ Email creation failed: {r.text}")
            return None, None, None

    except Exception as e:
        log(f"  ✗ Email error: {e}")
        return None, None, None

def get_verification_code(email, password, max_wait=120):
    """Get TikTok verification code from temp email"""
    try:
        # Login to mail.tm
        r = requests.post(
            f"{MAILTM_API}/token",
            json={"address": email, "password": password},
            timeout=10
        )
        if r.status_code != 200:
            return None

        token = r.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # Poll for messages
        start_time = time.time()
        while time.time() - start_time < max_wait:
            r = requests.get(f"{MAILTM_API}/messages", headers=headers, timeout=10)
            if r.status_code == 200:
                messages = r.json().get("hydra:member", [])
                for msg in messages:
                    if "tiktok" in msg.get("subject", "").lower():
                        # Get message details
                        msg_id = msg.get("id")
                        r2 = requests.get(f"{MAILTM_API}/messages/{msg_id}", headers=headers, timeout=10)
                        if r2.status_code == 200:
                            text = r2.json().get("text", "")
                            # Extract verification code (usually 6 digits)
                            import re
                            codes = re.findall(r'\b\d{6}\b', text)
                            if codes:
                                return codes[0]

            time.sleep(5)

        return None

    except Exception as e:
        log(f"  ✗ Error getting code: {e}")
        return None

# =============================================================================
# MULTILOGIN FUNCTIONS
# =============================================================================
def initialize_multilogin():
    """Initialize Multilogin client"""
    global multilogin_client

    if not config.get("email") and not config.get("automation_token"):
        log("✗ Multilogin credentials not configured. Edit multilogin_config.json")
        return False

    multilogin_client = MultiloginClient(
        email=config.get("email", ""),
        password=config.get("password", ""),
        automation_token=config.get("automation_token", "")
    )

    if multilogin_client.authenticate():
        log("✓ Multilogin authenticated successfully")
        return True
    else:
        log("✗ Multilogin authentication failed")
        return False

def fetch_profiles():
    """Fetch browser profiles from Multilogin"""
    global profiles_cache

    if not multilogin_client:
        if not initialize_multilogin():
            return []

    folder_id = config.get("folder_id")
    profiles_cache = multilogin_client.get_profiles(folder_id=folder_id, limit=100)

    log(f"✓ Loaded {len(profiles_cache)} profiles from Multilogin")
    return profiles_cache

# =============================================================================
# TIKTOK SIGNUP AUTOMATION
# =============================================================================
def signup_tiktok_account(profile_id, profile_name, folder_id):
    """
    Create a TikTok account using Multilogin profile

    Returns:
        dict: Account info if successful, None otherwise
    """
    if not HAS_SELENIUM:
        log("  ✗ Selenium not installed")
        return None

    driver = None

    try:
        # Start browser profile
        log(f"  Starting profile: {profile_name}")
        driver = multilogin_client.start_profile(
            folder_id=folder_id,
            profile_id=profile_id,
            automation_type="selenium",
            headless=False
        )

        if not driver:
            log(f"  ✗ Failed to start profile")
            return None

        log(f"  ✓ Profile started")

        # Create temp email
        log(f"  Creating temp email...")
        email, email_password, _ = create_temp_email()

        if not email:
            log(f"  ✗ Failed to create temp email")
            return None

        log(f"  ✓ Email: {email}")

        # Navigate to TikTok signup
        log(f"  Navigating to TikTok...")
        driver.get("https://www.tiktok.com/signup/phone-or-email/email")
        time.sleep(3)

        # Fill signup form
        log(f"  Filling signup form...")

        # Generate random birthday (18-35 years old)
        birth_year = random.randint(1989, 2006)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)

        # Month dropdown
        try:
            month_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select[aria-label='Month']"))
            )
            month_select.click()
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, f"option[value='{birth_month}']").click()
            time.sleep(0.5)
        except Exception as e:
            log(f"  ✗ Error selecting month: {e}")

        # Day dropdown
        try:
            day_select = driver.find_element(By.CSS_SELECTOR, "select[aria-label='Day']")
            day_select.click()
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, f"option[value='{birth_day}']").click()
            time.sleep(0.5)
        except Exception as e:
            log(f"  ✗ Error selecting day: {e}")

        # Year dropdown
        try:
            year_select = driver.find_element(By.CSS_SELECTOR, "select[aria-label='Year']")
            year_select.click()
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, f"option[value='{birth_year}']").click()
            time.sleep(0.5)
        except Exception as e:
            log(f"  ✗ Error selecting year: {e}")

        # Email input
        try:
            email_input = driver.find_element(By.CSS_SELECTOR, "input[type='text'][placeholder*='Email']")
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(1)
        except Exception as e:
            log(f"  ✗ Error entering email: {e}")

        # Password (random strong password)
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%", k=16))

        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
        except Exception as e:
            log(f"  ✗ Error entering password: {e}")

        # Click "Send code" button
        log(f"  Requesting verification code...")
        try:
            send_code_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Send code')]")
            send_code_btn.click()
            time.sleep(5)
        except Exception as e:
            log(f"  ✗ Error clicking send code: {e}")

        # Get verification code from email
        log(f"  Waiting for verification code...")
        code = get_verification_code(email, email_password, max_wait=120)

        if not code:
            log(f"  ✗ No verification code received")
            return None

        log(f"  ✓ Code received: {code}")

        # Enter verification code
        try:
            code_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'][maxlength='1']")
            for i, digit in enumerate(code):
                if i < len(code_inputs):
                    code_inputs[i].send_keys(digit)
                    time.sleep(0.2)
            time.sleep(2)
        except Exception as e:
            log(f"  ✗ Error entering code: {e}")

        # Generate username
        username = f"user_{random.randint(1000, 9999)}_{random.choice(['tt', 'tok', 'vibe'])}"

        # Enter username (if prompted)
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Username']"))
            )
            username_input.clear()
            username_input.send_keys(username)
            time.sleep(1)
        except:
            pass  # Username might not be required

        # Click signup/next button
        try:
            signup_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign up') or contains(text(), 'Next')]")
            signup_btn.click()
            time.sleep(5)
        except Exception as e:
            log(f"  ✗ Error clicking signup: {e}")

        # Check if signup was successful
        time.sleep(3)
        current_url = driver.current_url

        if "tiktok.com" in current_url and "signup" not in current_url:
            log(f"  ✓ Account created successfully!")

            account_info = {
                "profile_id": profile_id,
                "profile_name": profile_name,
                "email": email,
                "email_password": email_password,
                "password": password,
                "username": username,
                "birth_date": f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
                "created_at": datetime.now().isoformat()
            }

            # Save to Supabase
            if HAS_SUPABASE:
                try:
                    supabase.table("tiktok_accounts").insert({
                        "browser_id": profile_id,
                        "browser_name": profile_name,
                        "email": email,
                        "password": password,
                        "username": username,
                        "platform": "multilogin",
                        "status": "active",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    log(f"  ✓ Saved to Supabase")
                except Exception as e:
                    log(f"  ⚠ Supabase error: {e}")

            return account_info

        else:
            log(f"  ✗ Signup may have failed (URL: {current_url})")
            return None

    except Exception as e:
        log(f"  ✗ Error during signup: {e}")
        log(f"  Traceback: {traceback.format_exc()}")
        return None

    finally:
        # Stop the profile
        if driver and multilogin_client:
            log(f"  Stopping profile...")
            try:
                multilogin_client.stop_profile(profile_id=profile_id)
                log(f"  ✓ Profile stopped")
            except Exception as e:
                log(f"  ⚠ Error stopping profile: {e}")

# =============================================================================
# AUTOMATION THREAD
# =============================================================================
def run_signup_thread(profile_ids):
    global signup_status

    signup_status["running"] = True
    signup_status["progress"] = 0
    signup_status["total"] = len(profile_ids)
    signup_status["completed"] = []
    signup_status["failed"] = []
    signup_status["created_accounts"] = []

    log(f"{'='*50}")
    log(f"Starting TikTok signup for {len(profile_ids)} profiles")
    log(f"{'='*50}")

    folder_id = config.get("folder_id", "")

    for i, profile_id in enumerate(profile_ids):
        if not signup_status["running"]:
            log("⏹ Stopped by user")
            break

        profile = next((p for p in profiles_cache if p.get("id") == profile_id), None)
        if not profile:
            continue

        profile_name = profile.get("name", profile_id)
        signup_status["current_profile"] = profile_name
        signup_status["progress"] = i + 1

        log(f"\n[{i+1}/{len(profile_ids)}] {profile_name}")

        account = signup_tiktok_account(profile_id, profile_name, folder_id)

        if account:
            signup_status["completed"].append(profile_id)
            signup_status["created_accounts"].append(account)
        else:
            signup_status["failed"].append(profile_id)

        # Wait between profiles
        if i < len(profile_ids) - 1 and signup_status["running"]:
            log("  Waiting 10s before next profile...")
            time.sleep(10)

    signup_status["running"] = False
    signup_status["current_profile"] = None
    log(f"\n{'='*50}")
    log(f"✓ DONE! {len(signup_status['completed'])}/{len(profile_ids)} successful")
    log(f"{'='*50}")

# =============================================================================
# WEB DASHBOARD
# =============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Multilogin TikTok Signup</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #0a0a0b; color: #e4e4e7; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 4px; }
        .subtitle { color: #71717a; font-size: 14px; margin-bottom: 24px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card { background: #18181b; border: 1px solid #27272a; border-radius: 10px; padding: 16px; }
        .card-title { font-weight: 600; margin-bottom: 12px; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; font-size: 13px; cursor: pointer; transition: all 0.15s; }
        .btn:hover { opacity: 0.9; }
        .btn-sm { padding: 5px 10px; font-size: 11px; }
        .btn-secondary { background: #27272a; color: #e4e4e7; }
        .btn-success { background: #16a34a; color: white; font-size: 15px; padding: 12px 28px; }
        .btn-danger { background: #dc2626; color: white; }
        .profile { display: flex; align-items: center; padding: 10px; background: #27272a; border-radius: 6px; margin-bottom: 6px; cursor: pointer; }
        .profile:hover { background: #3f3f46; }
        .profile.selected { background: #4c1d95; border: 1px solid #7c3aed; }
        .profile input[type="checkbox"] { margin-right: 10px; width: 16px; height: 16px; }
        .profile-info { flex: 1; }
        .profile-name { font-weight: 500; font-size: 13px; }
        .profile-id { color: #71717a; font-size: 11px; }
        .profile-list { max-height: 400px; overflow-y: auto; margin-top: 10px; }
        .stats { display: flex; gap: 20px; justify-content: center; margin: 16px 0; }
        .stat { text-align: center; }
        .stat-value { font-size: 28px; font-weight: 700; color: #7c3aed; }
        .stat-label { color: #71717a; font-size: 11px; }
        .progress { width: 100%; height: 6px; background: #27272a; border-radius: 3px; margin: 12px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a855f7); border-radius: 3px; transition: width 0.3s; }
        .logs { background: #0f0f10; border-radius: 6px; padding: 12px; height: 300px; overflow-y: auto; font-family: 'SF Mono', Monaco, monospace; font-size: 11px; line-height: 1.6; }
        .log-entry { color: #a1a1aa; white-space: pre-wrap; }
        .log-entry.error { color: #f87171; }
        .log-entry.success { color: #4ade80; }
        .actions { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
        .center { text-align: center; }
        .accounts-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }
        .accounts-table th { background: #27272a; padding: 8px; text-align: left; }
        .accounts-table td { padding: 8px; border-top: 1px solid #27272a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Multilogin TikTok Signup</h1>
        <p class="subtitle">Automated TikTok account creation using Multilogin profiles</p>

        <div class="grid">
            <div class="card">
                <div class="card-title">Multilogin Profiles</div>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="syncProfiles()">🔄 Sync Profiles</button>
                    <button class="btn btn-secondary btn-sm" onclick="selectAll()">Select All</button>
                </div>
                <div class="profile-list" id="profile-list">
                    <div style="text-align:center; color:#71717a; padding:40px;">
                        Click "Sync Profiles" to load from Multilogin
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Control Panel</div>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value" id="stat-total">0</div>
                        <div class="stat-label">Total</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="stat-selected">0</div>
                        <div class="stat-label">Selected</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="stat-done">0</div>
                        <div class="stat-label">Done</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="stat-failed">0</div>
                        <div class="stat-label">Failed</div>
                    </div>
                </div>

                <div class="progress"><div class="progress-fill" id="progress" style="width:0%"></div></div>
                <p class="center" style="color:#71717a; font-size:12px;" id="status-text">Ready to start</p>

                <div class="center" style="margin-top:16px;">
                    <button class="btn btn-success" id="start-btn" onclick="startSignup()">▶ Start Signup</button>
                    <button class="btn btn-danger" id="stop-btn" onclick="stopSignup()" style="display:none;">⏹ Stop</button>
                </div>
            </div>
        </div>

        <div class="card" style="margin-top:20px;">
            <div class="card-title">📋 Activity Log</div>
            <div class="logs" id="logs">Waiting to start...</div>
        </div>

        <div class="card" style="margin-top:20px;">
            <div class="card-title">✓ Created Accounts (<span id="account-count">0</span>)</div>
            <table class="accounts-table" id="accounts-table">
                <thead>
                    <tr>
                        <th>Profile</th>
                        <th>Email</th>
                        <th>Username</th>
                        <th>Password</th>
                    </tr>
                </thead>
                <tbody id="accounts-body">
                    <tr><td colspan="4" style="text-align:center;color:#71717a;">No accounts created yet</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let profiles = [];
        let selected = new Set();

        setInterval(updateStatus, 1000);

        async function syncProfiles() {
            const res = await fetch('/api/sync-profiles', {method: 'POST'});
            const data = await res.json();
            profiles = data.profiles || [];
            renderProfiles();
        }

        function renderProfiles() {
            const el = document.getElementById('profile-list');
            if (!profiles.length) {
                el.innerHTML = '<div style="text-align:center;color:#71717a;padding:40px;">No profiles found</div>';
                updateStats();
                return;
            }
            el.innerHTML = profiles.map(p => `
                <div class="profile ${selected.has(p.id) ? 'selected' : ''}" onclick="toggle('${p.id}')">
                    <input type="checkbox" ${selected.has(p.id) ? 'checked' : ''} onclick="event.stopPropagation();toggle('${p.id}')">
                    <div class="profile-info">
                        <div class="profile-name">${p.name || p.id}</div>
                        <div class="profile-id">${p.id}</div>
                    </div>
                </div>
            `).join('');
            updateStats();
        }

        function toggle(id) {
            selected.has(id) ? selected.delete(id) : selected.add(id);
            renderProfiles();
        }

        function selectAll() {
            if (selected.size === profiles.length) {
                selected.clear();
            } else {
                profiles.forEach(p => selected.add(p.id));
            }
            renderProfiles();
        }

        function updateStats() {
            document.getElementById('stat-total').textContent = profiles.length;
            document.getElementById('stat-selected').textContent = selected.size;
        }

        async function startSignup() {
            if (!selected.size) { alert('Select at least one profile'); return; }
            await fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ profile_ids: Array.from(selected) })
            });
            document.getElementById('start-btn').style.display = 'none';
            document.getElementById('stop-btn').style.display = 'inline';
        }

        async function stopSignup() {
            await fetch('/api/stop', {method: 'POST'});
        }

        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                const pct = data.total ? (data.progress / data.total * 100) : 0;
                document.getElementById('progress').style.width = pct + '%';
                document.getElementById('stat-done').textContent = data.completed.length;
                document.getElementById('stat-failed').textContent = data.failed.length;

                if (data.running) {
                    document.getElementById('status-text').textContent = `Running: ${data.current_profile} (${data.progress}/${data.total})`;
                    document.getElementById('start-btn').style.display = 'none';
                    document.getElementById('stop-btn').style.display = 'inline';
                } else {
                    document.getElementById('start-btn').style.display = 'inline';
                    document.getElementById('stop-btn').style.display = 'none';
                    if (data.progress > 0) {
                        document.getElementById('status-text').textContent = `Done: ${data.completed.length} created, ${data.failed.length} failed`;
                    }
                }

                if (data.logs.length) {
                    const logsEl = document.getElementById('logs');
                    logsEl.innerHTML = data.logs.map(l => {
                        let cls = 'log-entry';
                        if (l.includes('✗') || l.includes('Error')) cls += ' error';
                        if (l.includes('✓') || l.includes('DONE')) cls += ' success';
                        return `<div class="${cls}">${l}</div>`;
                    }).join('');
                    logsEl.scrollTop = logsEl.scrollHeight;
                }

                if (data.created_accounts.length) {
                    document.getElementById('account-count').textContent = data.created_accounts.length;
                    const tbody = document.getElementById('accounts-body');
                    tbody.innerHTML = data.created_accounts.map(a => `
                        <tr>
                            <td>${a.profile_name}</td>
                            <td>${a.email}</td>
                            <td>${a.username}</td>
                            <td>${a.password}</td>
                        </tr>
                    `).join('');
                }
            } catch(e) {}
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

@app.route('/api/sync-profiles', methods=['POST'])
def api_sync():
    profiles = fetch_profiles()
    return jsonify({"profiles": profiles})

@app.route('/api/status')
def api_status():
    return jsonify(signup_status)

@app.route('/api/start', methods=['POST'])
def api_start():
    if signup_status["running"]:
        return jsonify({"error": "Already running"}), 400

    data = request.json
    profile_ids = data.get("profile_ids", [])

    t = threading.Thread(target=run_signup_thread, args=(profile_ids,))
    t.daemon = True
    t.start()

    return jsonify({"ok": True})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    signup_status["running"] = False
    log("⏹ Stop requested")
    return jsonify({"ok": True})

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Multilogin TikTok Auto Signup")
    print("  Open: http://localhost:9006")
    print("=" * 60)
    print()

    if not HAS_SELENIUM:
        print("⚠️  Install: pip install selenium")
    if not HAS_SUPABASE:
        print("⚠️  Install: pip install supabase")

    # Initialize Multilogin
    if initialize_multilogin():
        print("✓ Ready!")
    else:
        print("⚠️  Configure multilogin_config.json first")

    print()
    app.run(host="0.0.0.0", port=9006, debug=False)
