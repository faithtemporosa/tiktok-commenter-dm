# Setup TikTok App Automation for iOS

Follow these steps in order:

## 1. Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## 2. Install Required Tools

```bash
# Install Node.js
brew install node

# Install tools to detect iPhone
brew install libimobiledevice

# Install Appium
npm install -g appium

# Install iOS driver
appium driver install xcuitest

# Install Python client
pip3 install Appium-Python-Client
```

## 3. Connect Your iPhone

1. Connect iPhone to Mac via USB cable
2. Unlock your iPhone
3. Tap "Trust This Computer" when prompted
4. Enter your iPhone passcode

## 4. Get Your iPhone Details

Run this command and copy the output:

```bash
idevice_id -l
```

This gives you your iPhone's UDID (a long string like: 00008030-001A25E02262402E)

Also check your iOS version:
- On iPhone: Settings → General → About → Software Version
- Note the version (e.g., 17.4, 16.5, etc.)

## 5. Update the Script

I'll do this part - just tell me:
- Your UDID from step 4
- Your iOS version from step 4

## 6. Setup WebDriverAgent (One-time setup)

```bash
# This will open Xcode
appium driver run xcuitest open-wda
```

In Xcode:
1. Select **WebDriverAgentRunner** target (top left dropdown)
2. Click on **WebDriverAgentRunner** in the left sidebar
3. Go to **Signing & Capabilities** tab
4. ✓ Check "Automatically manage signing"
5. Select your **Team** (use your Apple ID if you don't have a developer account)
6. Change **Bundle Identifier** to: `com.yourname.WebDriverAgentRunner` (replace yourname with your actual name)
7. At the top bar, select your iPhone as destination
8. Click **Product** → **Build** (or press Cmd+B)
9. Wait for build to complete

On your iPhone:
1. Go to **Settings** → **General** → **VPN & Device Management**
2. Tap your Apple ID
3. Tap **Trust**

## 7. Run the Automation

Open TWO Terminal windows:

**Terminal 1:**
```bash
appium
```
(Keep this running - you should see "Appium REST http interface listener started on 0.0.0.0:4723")

**Terminal 2:**
```bash
cd /Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads
python3 targeted_accounts_view_app.py
```

## Troubleshooting

**Error: "Could not find device"**
- Make sure iPhone is unlocked and connected
- Run: `idevice_id -l` to verify it's detected

**Error: "WebDriverAgent not found"**
- Redo step 6 (WebDriverAgent setup)

**Error: "TikTok app not found"**
- Make sure TikTok is installed and you're logged in

**Error: "Permission denied"**
- Make sure you trusted the developer certificate on iPhone (Step 6, on iPhone part)

---

## What the Script Does

Once running, it will:
1. Connect to your iPhone's TikTok app
2. Search for each target account (@flockboynation, @happyandyaya, etc.)
3. Open their profile
4. Watch 10 videos per account (8-18 seconds each)
5. Use natural swipe gestures (just like you would manually)
6. Save stats to `target_accounts_view_stats_app.json`

Total: ~7 accounts × 10 videos = 70 videos viewed
Time: ~30-45 minutes
