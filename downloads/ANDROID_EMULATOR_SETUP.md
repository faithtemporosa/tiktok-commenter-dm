# Android Emulator TikTok Automation Setup

Complete guide to running TikTok commenting automation on Android emulators.

---

## Prerequisites

### 1. Install Android Emulator

Choose one:

**BlueStacks (Recommended)**
- Download: https://www.bluestacks.com/
- Easy setup, good performance
- Multi-instance manager built-in

**NOX Player**
- Download: https://www.bignox.com/
- Lightweight, fast
- Good for multiple instances

**Android Studio AVD**
- Download: https://developer.android.com/studio
- Most authentic Android experience
- Requires more setup

### 2. Install Dependencies

```bash
# Install Python packages
pip install appium-python-client selenium requests supabase

# Install Appium (Node.js required)
npm install -g appium

# Install UiAutomator2 driver
appium driver install uiautomator2

# Install ADB (if not already installed)
# Mac: brew install android-platform-tools
# Windows: Download from https://developer.android.com/studio/releases/platform-tools
```

---

## Setup Steps

### 1. Configure Emulator

**Enable ADB in your emulator:**

**BlueStacks:**
1. Settings → Advanced → Enable Android Debug Bridge (ADB)
2. Note the port (usually 5555)

**NOX:**
1. Settings → Enable root mode
2. ADB is enabled by default on port 62001

**Android Studio AVD:**
1. ADB is enabled by default

### 2. Install TikTok on Emulator

1. Open emulator
2. Open Google Play Store
3. Search for "TikTok"
4. Install TikTok app
5. Login to your TikTok account

### 3. Verify ADB Connection

```bash
# Check connected devices
adb devices

# Should show something like:
# emulator-5554    device
# emulator-5556    device
```

### 4. Start Appium Server

```bash
# Start Appium on default port 4723
appium

# Or specify port
appium -p 4723

# You should see:
# [Appium] Welcome to Appium v2.x.x
# [Appium] Appium REST http interface listener started on 0.0.0.0:4723
```

### 5. Configure Emulators

Edit `emulator_configs.json`:

```json
{
  "emulators": [
    {
      "name": "Emulator-1",
      "udid": "emulator-5554",
      "tiktok_account": "your_account_1",
      "device_name": "Android Emulator"
    },
    {
      "name": "Emulator-2",
      "udid": "emulator-5556",
      "tiktok_account": "your_account_2",
      "device_name": "Android Emulator"
    }
  ]
}
```

**Finding UDID:**
```bash
adb devices
# The left column shows the UDID (e.g., emulator-5554)
```

---

## Running the Script

### Basic Usage

```bash
cd /Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads

# Make sure Appium is running first
appium

# In another terminal, run the script
python3 comment_target_emulator.py
```

### What It Does

1. Connects to each configured emulator
2. Opens TikTok app
3. Searches for target accounts
4. Views latest 2 videos per account
5. Posts natural comments
6. Tracks commented videos (no duplicates)
7. Syncs stats to Supabase

### Expected Output

```
============================================================
Android Emulator TikTok Commenter
============================================================
✓ Appium server running at http://localhost:4723

Connected devices: 2
  - emulator-5554
  - emulator-5556

Configured emulators: 2
Target accounts: 7
  - @flockboynation
  - @happyandyaya
  - @catalyst_supps
  ...

============================================================
Emulator: Emulator-1 (emulator-5554)
============================================================
Connecting to Emulator-1...

[1/7] @flockboynation
  Searching for @flockboynation...
  Found 2 videos
  Video 1: Watching video for 5s...
  Posting comment: 'Love the gains content!'
  ✓ Comment posted
  Video 2: Watching video for 4s...
  Posting comment: 'Great tips! Been looking for this'
  ✓ Comment posted

[2/7] @happyandyaya
  ...

Emulator-1 Summary:
  Total comments: 14
```

---

## Configuration

### Target Accounts

Edit in `comment_target_emulator.py`:

```python
TARGET_ACCOUNTS = [
    'flockboynation',
    'happyandyaya',
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]
```

### Settings

```python
COMMENTS_PER_ACCOUNT = 2  # Videos to comment on per account
PARALLEL_EMULATORS = 2    # Run 2 emulators at once
APPIUM_SERVER = 'http://localhost:4723'
```

### Comments

Customize comments by niche in the script:

```python
NICHE_COMMENTS = {
    'fitness': [
        'Love the gains content!',
        'Great tips! Been looking for this',
        ...
    ],
    'adventure': [
        'What an amazing journey!',
        ...
    ]
}
```

---

## Multiple Emulators

### BlueStacks Multi-Instance

1. Open BlueStacks Multi-Instance Manager
2. Click "Instance" → "Fresh Instance"
3. Create 2-5 instances
4. Start all instances
5. Each will have a unique port (5555, 5556, 5557, etc.)

### NOX Multi-Instance

1. Open Multi-Drive
2. Click "Add Emulator"
3. Create multiple instances
4. Start all
5. Ports: 62001, 62025, 62026, etc.

### Get All UDIDs

```bash
adb devices

# Output:
# emulator-5554    device  <- BlueStacks Instance 1
# emulator-5556    device  <- BlueStacks Instance 2
# 127.0.0.1:62001  device  <- NOX Instance 1
```

Add each to `emulator_configs.json`.

---

## Troubleshooting

### Appium Server Not Running

```bash
# Check if running
curl http://localhost:4723/status

# If not, start it
appium
```

### Emulator Not Detected

```bash
# Restart ADB
adb kill-server
adb start-server

# Check devices
adb devices

# Connect manually (if needed)
adb connect 127.0.0.1:5555  # BlueStacks
adb connect 127.0.0.1:62001  # NOX
```

### TikTok App Not Opening

```bash
# Check if TikTok is installed
adb -s emulator-5554 shell pm list packages | grep musically

# Should show:
# package:com.zhiliaoapp.musically

# If not, install TikTok via Play Store
```

### Element Not Found Errors

- TikTok UI changes frequently
- Update selectors in script if needed
- Check if you're logged into TikTok on emulator

### Connection Timeout

- Increase wait timeouts in script
- Check emulator performance (allocate more RAM)
- Ensure Appium server is running

---

## Performance Tips

### 1. Emulator Resources

**BlueStacks:**
- Settings → Performance
- CPU: 4 cores
- RAM: 4GB
- Performance mode: High

**NOX:**
- Settings → Advanced
- CPU: 2-4 cores
- RAM: 2-4GB

### 2. Parallel Processing

```python
# Run 2-3 emulators at once for best performance
PARALLEL_EMULATORS = 2  # Adjust based on your CPU
```

### 3. Background Running

```bash
# Run in background
nohup python3 comment_target_emulator.py > emulator.log 2>&1 &

# Check output
tail -f emulator.log
```

---

## Automation Best Practices

### 1. Natural Behavior

The script includes:
- Random delays between actions
- Human-like swipe gestures
- Variable video watch times (3-7 seconds)
- Natural typing speed

### 2. Daily Limits

Start conservative:
- 2-5 comments per account per day
- Run once daily
- Monitor for shadowbans

### 3. Account Safety

- Use different TikTok accounts per emulator
- Don't run 24/7
- Take breaks between sessions
- Monitor account health

---

## Files Created

| File | Purpose |
|------|---------|
| `emulator_configs.json` | Emulator configurations |
| `emulator_commented_videos.json` | Tracks commented videos (no duplicates) |
| `emulator_daily_activity.json` | Daily activity tracking |
| `target_accounts_stats.json` | Analytics & stats |

---

## Comparison: Desktop vs Emulator

| Feature | Desktop (AdsPower) | Emulator (This Script) |
|---------|-------------------|------------------------|
| Platform | Chrome browser | TikTok mobile app |
| Detection Risk | Medium | Lower (native app) |
| Setup | AdsPower profiles | Emulator instances |
| Cost | AdsPower license | Free (emulator) |
| Scalability | 100+ browsers | 5-10 emulators (CPU limited) |
| Performance | Fast | Moderate |
| Authenticity | Web fingerprint | Real mobile app |

**Recommendation:**
- **Desktop:** For scale (100+ accounts)
- **Emulator:** For authenticity (5-10 high-value accounts)
- **Both:** Use emulators for important accounts, desktop for volume

---

## Next Steps

1. ✓ Install emulator & dependencies
2. ✓ Configure emulators in JSON
3. ✓ Start Appium server
4. ✓ Run script: `python3 comment_target_emulator.py`
5. Monitor results in logs
6. Scale up with more emulators

---

**Built for mobile. Runs naturally. Comments authentically.**

Last updated: 2026-04-20
