#!/usr/bin/env python3
"""
AdsPower Rebotou Automation Dashboard
=====================================
Automates adding comments and running Rebotou across all AdsPower browsers.

SETUP:
    pip install requests flask pyautogui pyperclip

RUN:
    python adspower_dashboard.py

Open http://localhost:9000 in your browser.
"""

import requests
import time
import json
import csv
import io
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.3
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("ERROR: Install pyautogui: pip install pyautogui")

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
    print("WARNING: Install pyperclip for clipboard: pip install pyperclip")

# =============================================================================
# CONFIGURATION
# =============================================================================
ADSPOWER_API = "http://localhost:50325"
GOOGLE_SHEET_ID = "1cgjxB09nXSsKMEFwNxQlDzl8xVDyQgT0o8aKm6YOJ-o"
SHEET_NAMES = ["Bump Connect", "Bump Syndicate", "Kollabsy"]

# =============================================================================
# GLOBAL STATE
# =============================================================================
app = Flask(__name__)
profiles = []
comments_cache = {}

# Click positions - calibrate these for your screen
click_positions = {
    "extension_x": 1350,      # Rebotou extension icon X
    "extension_y": 45,        # Rebotou extension icon Y
    "task_x": 400,            # Task row X (click to edit)
    "task_y": 330,            # Task row Y
    "comment_box_x": 550,     # Kommentarinhalt textarea X
    "comment_box_y": 580,     # Kommentarinhalt textarea Y
    "save_btn_x": 550,        # Speichern button X
    "save_btn_y": 850,        # Speichern button Y
    "close_x": 1060,          # X close button
    "close_y": 180,           # X close button Y
    "run_all_x": 115,         # Run All button X
    "run_all_y": 115,         # Run All button Y
}

automation_status = {
    "running": False,
    "current_profile": None,
    "progress": 0,
    "total": 0,
    "logs": [],
    "completed": []
}

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    automation_status["logs"].append(log_entry)
    print(log_entry)
    if len(automation_status["logs"]) > 150:
        automation_status["logs"] = automation_status["logs"][-150:]

def fetch_adspower_profiles():
    global profiles
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=100", timeout=5)
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
            next(reader, None)  # Skip header
            comments = [row[0].strip() for row in reader if row and row[0].strip()]
            comments_cache[sheet_name] = comments
            log(f"✓ Loaded {len(comments)} comments from '{sheet_name}'")
            return comments
    except Exception as e:
        log(f"✗ Error loading comments: {e}")
    return []

def open_browser(profile_id):
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/browser/start?user_id={profile_id}", timeout=60)
        data = response.json()
        if data.get("code") == 0:
            return True
        log(f"  ✗ Error: {data.get('msg')}")
    except Exception as e:
        log(f"  ✗ Error opening browser: {e}")
    return False

def close_browser(profile_id):
    try:
        requests.get(f"{ADSPOWER_API}/api/v1/browser/stop?user_id={profile_id}", timeout=10)
    except:
        pass

def click(x, y, description=""):
    """Click at position with logging"""
    if description:
        log(f"  → Clicking {description} at ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(0.5)

def paste_text(text):
    """Paste text using clipboard"""
    if HAS_PYPERCLIP:
        pyperclip.copy(text)
        # Cmd+V on Mac, Ctrl+V on Windows/Linux
        pyautogui.hotkey('command', 'v')
    else:
        # Fallback: type it (slower)
        pyautogui.typewrite(text, interval=0.02)

def run_rebotou_automation(profile_name, sheet_name):
    """Full automation: add comments and run Rebotou"""
    if not HAS_PYAUTOGUI:
        log("  ✗ pyautogui not installed!")
        return False
    
    comments = comments_cache.get(sheet_name, [])
    
    try:
        # Wait for browser to fully load
        log(f"  Waiting for browser to load...")
        time.sleep(5)
        
        # Step 1: Click extension icon
        click(click_positions["extension_x"], click_positions["extension_y"], "extension icon")
        time.sleep(2)
        
        # Step 2: Click on the task row to edit
        click(click_positions["task_x"], click_positions["task_y"], "task row")
        time.sleep(1.5)
        
        # Step 3: Click on comment textarea
        click(click_positions["comment_box_x"], click_positions["comment_box_y"], "comment textarea")
        time.sleep(0.5)
        
        # Step 4: Select all existing text (Cmd+A) and delete
        log(f"  → Clearing existing comments...")
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        pyautogui.press('backspace')
        time.sleep(0.3)
        
        # Step 5: Paste new comments from Google Sheets
        if comments:
            # Format comments for Rebotou spin syntax: {comment1|comment2|comment3}
            # This makes Rebotou pick a random comment each time
            comments_text = "{" + "|".join(comments[:50]) + "}"  # First 50 comments
            log(f"  → Pasting {min(50, len(comments))} comments...")
            paste_text(comments_text)
            time.sleep(0.5)
        else:
            log(f"  ⚠ No comments found for {sheet_name}")
        
        # Step 6: Click Save button (Speichern)
        click(click_positions["save_btn_x"], click_positions["save_btn_y"], "Save button")
        time.sleep(1)
        
        # Step 7: Click X to close dialog (or it auto-closes)
        # click(click_positions["close_x"], click_positions["close_y"], "close dialog")
        # time.sleep(0.5)
        
        # Step 8: Click Run All button
        click(click_positions["run_all_x"], click_positions["run_all_y"], "Run All")
        time.sleep(2)
        
        log(f"  ✓ Rebotou started for {profile_name}!")
        
        # Step 9: Wait for Rebotou to finish
        wait_time = 180  # 3 minutes
        log(f"  ⏳ Waiting {wait_time}s for completion...")
        
        for i in range(wait_time // 15):
            if not automation_status["running"]:
                log("  ⏹ Stopped by user")
                return False
            time.sleep(15)
            elapsed = (i + 1) * 15
            log(f"  ⏳ Running... ({elapsed}s / {wait_time}s)")
        
        log(f"  ✓ Completed: {profile_name}")
        return True
        
    except Exception as e:
        log(f"  ✗ Error: {e}")
        return False

def run_automation_thread(profile_ids, sheet_mapping):
    global automation_status
    
    automation_status["running"] = True
    automation_status["progress"] = 0
    automation_status["total"] = len(profile_ids)
    automation_status["completed"] = []
    automation_status["logs"] = []
    
    log(f"{'='*50}")
    log(f"Starting automation for {len(profile_ids)} profiles")
    log(f"{'='*50}")
    
    # Pre-load all comments
    for sheet in set(sheet_mapping.values()):
        if sheet not in comments_cache:
            fetch_google_sheet_comments(sheet)
    
    for i, profile_id in enumerate(profile_ids):
        if not automation_status["running"]:
            log("⏹ Stopped by user")
            break
        
        profile = next((p for p in profiles if p.get("user_id") == profile_id), None)
        if not profile:
            continue
        
        profile_name = profile.get("name", profile_id)
        sheet_name = sheet_mapping.get(profile_id, SHEET_NAMES[0])
        
        automation_status["current_profile"] = profile_name
        automation_status["progress"] = i + 1
        
        log(f"\n[{i+1}/{len(profile_ids)}] {profile_name}")
        log(f"  Sheet: {sheet_name}")
        
        # Open browser
        log(f"  Opening browser...")
        if not open_browser(profile_id):
            log(f"  ✗ Failed to open browser, skipping...")
            continue
        
        log(f"  ✓ Browser opened")
        
        # Run automation
        success = run_rebotou_automation(profile_name, sheet_name)
        
        # Close browser
        log(f"  Closing browser...")
        close_browser(profile_id)
        log(f"  ✓ Browser closed")
        
        if success:
            automation_status["completed"].append(profile_id)
        
        # Wait between profiles
        if i < len(profile_ids) - 1 and automation_status["running"]:
            log("  Waiting 5s before next profile...")
            time.sleep(5)
    
    automation_status["running"] = False
    automation_status["current_profile"] = None
    log(f"\n{'='*50}")
    log(f"✓ DONE! {len(automation_status['completed'])}/{len(profile_ids)} completed")
    log(f"{'='*50}")

# =============================================================================
# WEB DASHBOARD
# =============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AdsPower Rebotou Automation</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, system-ui, sans-serif; background: #0a0a0b; color: #e4e4e7; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 22px; margin-bottom: 4px; }
        .subtitle { color: #71717a; font-size: 14px; margin-bottom: 24px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card { background: #18181b; border: 1px solid #27272a; border-radius: 10px; padding: 16px; }
        .card-title { font-weight: 600; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; font-size: 13px; cursor: pointer; transition: all 0.15s; }
        .btn:hover { opacity: 0.9; }
        .btn-sm { padding: 5px 10px; font-size: 11px; }
        .btn-secondary { background: #27272a; color: #e4e4e7; }
        .btn-success { background: #16a34a; color: white; font-size: 15px; padding: 12px 28px; }
        .btn-danger { background: #dc2626; color: white; }
        .btn-primary { background: #7c3aed; color: white; }
        .profile { display: flex; align-items: center; padding: 10px; background: #27272a; border-radius: 6px; margin-bottom: 6px; cursor: pointer; transition: all 0.15s; }
        .profile:hover { background: #3f3f46; }
        .profile.selected { background: #4c1d95; border: 1px solid #7c3aed; }
        .profile input[type="checkbox"] { margin-right: 10px; width: 16px; height: 16px; }
        .profile-info { flex: 1; }
        .profile-name { font-weight: 500; font-size: 13px; }
        .profile-id { color: #71717a; font-size: 11px; }
        .profile-list { max-height: 300px; overflow-y: auto; margin-top: 10px; }
        select { padding: 4px 8px; background: #18181b; border: 1px solid #3f3f46; color: #e4e4e7; border-radius: 4px; font-size: 11px; }
        .stats { display: flex; gap: 20px; justify-content: center; margin: 16px 0; }
        .stat { text-align: center; }
        .stat-value { font-size: 28px; font-weight: 700; color: #7c3aed; }
        .stat-label { color: #71717a; font-size: 11px; }
        .progress { width: 100%; height: 6px; background: #27272a; border-radius: 3px; margin: 12px 0; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a855f7); border-radius: 3px; transition: width 0.3s; }
        .logs { background: #0f0f10; border-radius: 6px; padding: 12px; height: 250px; overflow-y: auto; font-family: 'SF Mono', Monaco, monospace; font-size: 11px; line-height: 1.6; }
        .log-entry { color: #a1a1aa; white-space: pre-wrap; }
        .log-entry.error { color: #f87171; }
        .log-entry.success { color: #4ade80; }
        .actions { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
        .calibration { background: #1e1b4b; border: 1px solid #4c1d95; border-radius: 8px; padding: 14px; margin-bottom: 14px; }
        .calibration h4 { font-size: 13px; margin-bottom: 10px; color: #a78bfa; }
        .cal-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .cal-row { display: flex; align-items: center; gap: 6px; }
        .cal-row label { font-size: 11px; color: #a1a1aa; min-width: 90px; }
        .cal-row input { width: 55px; padding: 4px 6px; background: #27272a; border: 1px solid #3f3f46; color: white; border-radius: 4px; font-size: 11px; }
        .center { text-align: center; }
        .mouse-pos { position: fixed; bottom: 10px; right: 10px; background: #18181b; border: 1px solid #3f3f46; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-family: monospace; z-index: 999; }
        .help-text { font-size: 10px; color: #71717a; margin-top: 8px; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AdsPower Rebotou Automation</h1>
        <p class="subtitle">Add comments from Google Sheets and run Rebotou on all browsers</p>
        
        <div class="grid">
            <!-- Left: Profiles -->
            <div class="card">
                <div class="card-title">
                    <span>Browser Profiles</span>
                    <span id="profile-count" style="color:#71717a; font-weight:normal; font-size:12px;">0 profiles</span>
                </div>
                <div class="actions">
                    <button class="btn btn-secondary" onclick="syncProfiles()">🔄 Sync Profiles</button>
                    <button class="btn btn-secondary" onclick="loadComments()">📄 Load Comments</button>
                    <button class="btn btn-secondary btn-sm" onclick="selectAll()">Select All</button>
                </div>
                <div class="profile-list" id="profile-list">
                    <div style="text-align:center; color:#71717a; padding:40px;">
                        Click "Sync Profiles" to load from AdsPower
                    </div>
                </div>
            </div>
            
            <!-- Right: Control -->
            <div class="card">
                <div class="card-title">Control Panel</div>
                
                <!-- Calibration -->
                <div class="calibration">
                    <h4>📍 Click Position Calibration</h4>
                    <p class="help-text">Move your mouse to find positions. The coordinates show at bottom-right.</p>
                    <div class="cal-grid">
                        <div class="cal-row">
                            <label>Extension icon:</label>
                            <input type="number" id="pos-extension_x" value="1350">
                            <input type="number" id="pos-extension_y" value="45">
                        </div>
                        <div class="cal-row">
                            <label>Task row:</label>
                            <input type="number" id="pos-task_x" value="400">
                            <input type="number" id="pos-task_y" value="330">
                        </div>
                        <div class="cal-row">
                            <label>Comment box:</label>
                            <input type="number" id="pos-comment_box_x" value="550">
                            <input type="number" id="pos-comment_box_y" value="580">
                        </div>
                        <div class="cal-row">
                            <label>Save button:</label>
                            <input type="number" id="pos-save_btn_x" value="550">
                            <input type="number" id="pos-save_btn_y" value="850">
                        </div>
                        <div class="cal-row">
                            <label>Run All btn:</label>
                            <input type="number" id="pos-run_all_x" value="115">
                            <input type="number" id="pos-run_all_y" value="115">
                        </div>
                    </div>
                    <div style="margin-top:10px; display:flex; gap:8px;">
                        <button class="btn btn-sm btn-primary" onclick="savePositions()">💾 Save Positions</button>
                        <button class="btn btn-sm btn-secondary" onclick="testClick('extension')">Test Ext</button>
                        <button class="btn btn-sm btn-secondary" onclick="testClick('task')">Test Task</button>
                        <button class="btn btn-sm btn-secondary" onclick="testClick('comment')">Test Comment</button>
                        <button class="btn btn-sm btn-secondary" onclick="testClick('save')">Test Save</button>
                        <button class="btn btn-sm btn-secondary" onclick="testClick('run')">Test Run</button>
                    </div>
                </div>
                
                <!-- Stats -->
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
                </div>
                
                <div class="progress"><div class="progress-fill" id="progress" style="width:0%"></div></div>
                <p class="center" style="color:#71717a; font-size:12px;" id="status-text">Ready to start</p>
                
                <div class="center" style="margin-top:16px;">
                    <button class="btn btn-success" id="start-btn" onclick="startAutomation()">▶ Run Selected Profiles</button>
                    <button class="btn btn-danger" id="stop-btn" onclick="stopAutomation()" style="display:none;">⏹ Stop</button>
                </div>
            </div>
        </div>
        
        <!-- Logs -->
        <div class="card" style="margin-top:20px;">
            <div class="card-title">
                <span>📋 Activity Log</span>
                <button class="btn btn-secondary btn-sm" onclick="clearLogs()">Clear</button>
            </div>
            <div class="logs" id="logs">Waiting to start...</div>
        </div>
    </div>
    
    <div class="mouse-pos">Mouse: <span id="mouse-coords">(0, 0)</span></div>
    
    <script>
        let profiles = [];
        let selected = new Set();
        let sheetMap = {};
        const SHEETS = ['Bump Connect', 'Bump Syndicate', 'Kollabsy'];
        const POS_KEYS = ['extension_x', 'extension_y', 'task_x', 'task_y', 'comment_box_x', 'comment_box_y', 'save_btn_x', 'save_btn_y', 'run_all_x', 'run_all_y'];
        
        // Track mouse position
        document.addEventListener('mousemove', (e) => {
            document.getElementById('mouse-coords').textContent = `(${e.screenX}, ${e.screenY})`;
        });
        
        setInterval(updateStatus, 1000);
        
        async function syncProfiles() {
            const res = await fetch('/api/sync-profiles', {method: 'POST'});
            const data = await res.json();
            profiles = data.profiles || [];
            renderProfiles();
        }
        
        async function loadComments() {
            const res = await fetch('/api/load-comments', {method: 'POST'});
            const data = await res.json();
            alert('Comments loaded:\\n' + Object.entries(data.counts).map(([k,v]) => k + ': ' + v).join('\\n'));
        }
        
        function renderProfiles() {
            const el = document.getElementById('profile-list');
            if (!profiles.length) {
                el.innerHTML = '<div style="text-align:center;color:#71717a;padding:40px;">No profiles found. Is AdsPower running?</div>';
                updateStats();
                return;
            }
            el.innerHTML = profiles.map(p => `
                <div class="profile ${selected.has(p.user_id) ? 'selected' : ''}" onclick="toggle('${p.user_id}')">
                    <input type="checkbox" ${selected.has(p.user_id) ? 'checked' : ''} onclick="event.stopPropagation();toggle('${p.user_id}')">
                    <div class="profile-info">
                        <div class="profile-name">${p.name || p.user_id}</div>
                        <div class="profile-id">${p.user_id}</div>
                    </div>
                    <select onclick="event.stopPropagation()" onchange="sheetMap['${p.user_id}']=this.value">
                        ${SHEETS.map(s => `<option value="${s}" ${sheetMap[p.user_id]===s?'selected':''}>${s}</option>`).join('')}
                    </select>
                </div>
            `).join('');
            document.getElementById('profile-count').textContent = profiles.length + ' profiles';
            updateStats();
        }
        
        function toggle(id) {
            selected.has(id) ? selected.delete(id) : selected.add(id);
            if (!sheetMap[id]) sheetMap[id] = SHEETS[0];
            renderProfiles();
        }
        
        function selectAll() {
            if (selected.size === profiles.length) {
                selected.clear();
            } else {
                profiles.forEach(p => { selected.add(p.user_id); sheetMap[p.user_id] = sheetMap[p.user_id] || SHEETS[0]; });
            }
            renderProfiles();
        }
        
        function updateStats() {
            document.getElementById('stat-total').textContent = profiles.length;
            document.getElementById('stat-selected').textContent = selected.size;
        }
        
        function getPositions() {
            const pos = {};
            POS_KEYS.forEach(k => { pos[k] = parseInt(document.getElementById('pos-' + k).value) || 0; });
            return pos;
        }
        
        async function savePositions() {
            await fetch('/api/set-positions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(getPositions())
            });
            alert('Positions saved!');
        }
        
        async function testClick(type) {
            await savePositions();
            await fetch('/api/test-click?type=' + type, {method: 'POST'});
        }
        
        async function startAutomation() {
            if (!selected.size) { alert('Select at least one profile'); return; }
            await savePositions();
            await fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ profile_ids: Array.from(selected), sheet_mapping: sheetMap })
            });
            document.getElementById('start-btn').style.display = 'none';
            document.getElementById('stop-btn').style.display = 'inline';
        }
        
        async function stopAutomation() {
            await fetch('/api/stop', {method: 'POST'});
        }
        
        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                const pct = data.total ? (data.progress / data.total * 100) : 0;
                document.getElementById('progress').style.width = pct + '%';
                document.getElementById('stat-done').textContent = data.completed.length;
                
                if (data.running) {
                    document.getElementById('status-text').textContent = `Running: ${data.current_profile} (${data.progress}/${data.total})`;
                    document.getElementById('start-btn').style.display = 'none';
                    document.getElementById('stop-btn').style.display = 'inline';
                } else {
                    document.getElementById('start-btn').style.display = 'inline';
                    document.getElementById('stop-btn').style.display = 'none';
                    if (data.progress > 0) {
                        document.getElementById('status-text').textContent = `Done: ${data.completed.length}/${data.total} completed`;
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
            } catch(e) {}
        }
        
        function clearLogs() {
            fetch('/api/clear-logs', {method:'POST'});
            document.getElementById('logs').innerHTML = 'Logs cleared';
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

@app.route('/api/check-adspower')
def api_check_adspower():
    """Check if AdsPower is running"""
    try:
        response = requests.get(f"{ADSPOWER_API}/api/v1/user/list?page_size=1", timeout=3)
        return jsonify({"connected": response.status_code == 200})
    except:
        return jsonify({"connected": False})

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
    return jsonify(automation_status)

@app.route('/api/set-positions', methods=['POST'])
def api_set_positions():
    global click_positions
    data = request.json
    click_positions.update(data)
    log(f"Updated click positions")
    return jsonify({"ok": True})

@app.route('/api/test-click', methods=['POST'])
def api_test_click():
    click_type = request.args.get('type', 'extension')
    if not HAS_PYAUTOGUI:
        return jsonify({"error": "pyautogui not installed"}), 400
    
    pos_map = {
        'extension': ('extension_x', 'extension_y'),
        'task': ('task_x', 'task_y'),
        'comment': ('comment_box_x', 'comment_box_y'),
        'save': ('save_btn_x', 'save_btn_y'),
        'run': ('run_all_x', 'run_all_y'),
    }
    
    if click_type in pos_map:
        x_key, y_key = pos_map[click_type]
        x, y = click_positions[x_key], click_positions[y_key]
        log(f"Test click: {click_type} at ({x}, {y})")
        pyautogui.click(x, y)
    
    return jsonify({"ok": True})

@app.route('/api/start', methods=['POST'])
def api_start():
    if automation_status["running"]:
        return jsonify({"error": "Already running"}), 400
    data = request.json
    t = threading.Thread(target=run_automation_thread, args=(data['profile_ids'], data['sheet_mapping']))
    t.daemon = True
    t.start()
    return jsonify({"ok": True})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    automation_status["running"] = False
    log("⏹ Stop requested")
    return jsonify({"ok": True})

@app.route('/api/clear-logs', methods=['POST'])
def api_clear_logs():
    automation_status["logs"] = []
    return jsonify({"ok": True})

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  AdsPower Rebotou Automation Dashboard")
    print("  Open: http://localhost:9000")
    print("=" * 50)
    print()
    
    if not HAS_PYAUTOGUI:
        print("⚠️  Install: pip install pyautogui")
    if not HAS_PYPERCLIP:
        print("⚠️  Install: pip install pyperclip")
    print()
    
    app.run(host="0.0.0.0", port=9000, debug=False)
