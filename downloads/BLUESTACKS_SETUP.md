# Bluestacks + ADB Automation Setup (Mac)

## Step 1: Install Bluestacks

1. Download Bluestacks for Mac:
   ```
   https://www.bluestacks.com/download.html
   ```

2. Install and launch Bluestacks

3. Complete Google account setup

4. Install TikTok from Play Store:
   - Open Play Store in Bluestacks
   - Search "TikTok"
   - Install
   - Open and log in to your TikTok account

## Step 2: Install ADB Tools

```bash
# Install ADB via Homebrew
brew install android-platform-tools

# Verify installation
adb version
```

## Step 3: Connect ADB to Bluestacks

```bash
# Bluestacks runs on localhost:5555 by default
adb connect 127.0.0.1:5555

# Verify connection
adb devices
# Should show: 127.0.0.1:5555   device
```

## Step 4: Get TikTok Package Name

```bash
# List all installed apps
adb shell pm list packages | grep tiktok

# Should show: package:com.zhiliaoapp.musically
```

## Step 5: Run Automation Script

```bash
python3 downloads/bluestacks_tiktok_automation.py
```

## Troubleshooting

### Bluestacks not connecting?
```bash
# Check if Bluestacks is running
adb devices

# If empty, try:
adb kill-server
adb start-server
adb connect 127.0.0.1:5555
```

### Find Bluestacks port:
- Check Bluestacks Settings → Advanced → Android Debug Bridge (ADB)
- Port is usually 5555 or 5037

### Enable ADB in Bluestacks:
1. Open Bluestacks
2. Settings → Advanced
3. Enable "Android Debug Bridge (ADB)"
4. Restart Bluestacks
