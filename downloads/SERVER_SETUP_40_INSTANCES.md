# 40 LDPlayer Instances Setup Guide
## Windows Server 2022 - 128GB RAM - 24 Cores

Complete guide to setting up 40 LDPlayer instances for TikTok automation at scale.

---

## Server Specs

- **OS:** Windows Server 2022
- **RAM:** 128GB
- **CPU:** AMD EPYC 9224 (24 cores)
- **IP:** 5.189.172.196
- **Purpose:** Run 40 TikTok accounts simultaneously

---

## Resource Allocation

| Resource | Total | Per Instance | 40 Instances | Overhead |
|----------|-------|--------------|--------------|----------|
| RAM | 128 GB | 2 GB | 80 GB | 48 GB |
| CPU | 24 cores | 2 cores | Shared | N/A |
| Storage | - | 2 GB | 80 GB | - |

---

## Step-by-Step Setup

### 1. Initial Server Setup

**After RDP into server:**

```powershell
# Update Windows
Install-Module PSWindowsUpdate
Get-WindowsUpdate
Install-WindowsUpdate -AcceptAll -AutoReboot

# Install Chocolatey (package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install tools
choco install git python nodejs adb -y

# Verify installations
python --version
node --version
adb version
```

---

### 2. Install LDPlayer

1. Download LDPlayer: https://www.ldplayer.net/
2. Run installer
3. Install to: `C:\Program Files\LDPlayer\LDPlayer9`
4. Open LDPlayer once to complete setup

---

### 3. Upload Project Files

**From your Mac:**

```bash
# Copy project to server
scp -r /Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads Administrator@5.189.172.196:C:/TikTokAutomation/
```

**Or use RDP file transfer:**
1. Copy files on your Mac
2. Paste in RDP session

---

### 4. Create 40 LDPlayer Instances

**On server, open PowerShell as Administrator:**

```powershell
cd C:\TikTokAutomation\downloads

# Create all 40 instances (takes ~10 minutes)
.\setup_40_ldplayers.ps1
```

**What it does:**
- Creates 40 instances: `TikTok-1` through `TikTok-40`
- Configures each: 2GB RAM, 2 CPU cores, 1080x1920 resolution
- Enables root access
- Sets 60 FPS

**Expected output:**
```
========================================
LDPlayer Mass Instance Creator
Creating 40 instances...
========================================

[1/40] Creating TikTok-1...
  Configuring TikTok-1...
  ✓ TikTok-1 created and configured

[2/40] Creating TikTok-2...
  ...
```

---

### 5. Start All Instances

```powershell
# Start all 40 instances in batches (takes ~5 minutes)
.\start_all_ldplayers.ps1
```

**Starts in batches:**
- Batch 1: Instances 1-5
- Wait 30 seconds
- Batch 2: Instances 6-10
- ... continues until all 40 are running

**Monitor resource usage:**
- Task Manager → Performance
- Should see RAM climbing to ~80-90GB
- CPU usage will spike then stabilize

---

### 6. Connect All to ADB

```powershell
# Connect all instances to ADB
.\connect_all_adb.ps1

# Verify all connected
adb devices
```

**Expected output:**
```
List of devices attached
127.0.0.1:5555    device
127.0.0.1:5557    device
127.0.0.1:5559    device
...
127.0.0.1:5633    device  (40th instance)
```

---

### 7. Install TikTok on All Instances

**Download TikTok APK:**
1. Visit: https://apkpure.com/tiktok/com.zhiliaoapp.musically
2. Download latest APK
3. Save as: `C:\TikTokAutomation\downloads\tiktok.apk`

**Install on all instances:**

```powershell
.\install_tiktok_all.ps1
```

**Takes ~5 minutes for all 40.**

---

### 8. Login to TikTok (Manual Step)

**Option A: Manual (Recommended for first setup)**

For each instance 1-40:
1. Click on instance in LDPlayer
2. Open TikTok app
3. Login with your account credentials
4. Complete any verification

**Option B: Semi-automated (Advanced)**

Create CSV with login credentials, then use ADB input commands to automate login flow.

---

### 9. Install Python Dependencies

```powershell
# Install Appium
npm install -g appium

# Install Appium driver
appium driver install uiautomator2

# Install Python packages
pip install appium-python-client selenium requests supabase
```

---

### 10. Generate Configuration

```powershell
# Auto-generate emulator_configs.json for all 40 instances
python generate_ldplayer_configs.py
```

**Creates:**
```json
{
  "emulators": [
    {
      "name": "TikTok-1",
      "udid": "127.0.0.1:5555",
      "tiktok_account": "your_account_1",
      ...
    },
    ...
    {
      "name": "TikTok-40",
      "udid": "127.0.0.1:5633",
      "tiktok_account": "your_account_40",
      ...
    }
  ],
  "settings": {
    "parallel_emulators": 5
  }
}
```

**Edit the file:**
- Update `tiktok_account` fields with actual usernames
- Adjust `parallel_emulators` (5-10 recommended)

---

### 11. Start Appium Server

```powershell
# Start Appium
appium

# Should see:
# [Appium] Welcome to Appium v2.x.x
# [Appium] Appium REST http interface listener started on 0.0.0.0:4723
```

**Keep this terminal open.**

---

### 12. Run Automation

**Open new PowerShell window:**

```powershell
cd C:\TikTokAutomation\downloads

# Run the commenter
python comment_target_emulator.py
```

**Expected output:**
```
============================================================
Android Emulator TikTok Commenter
============================================================
✓ Appium server running at http://localhost:4723

Connected devices: 40
  - 127.0.0.1:5555
  - 127.0.0.1:5557
  ...

Configured emulators: 40
Target accounts: 7
  - @flockboynation
  - @happyandyaya
  ...

Parallel emulators: 5

============================================================
Emulator: TikTok-1 (127.0.0.1:5555)
============================================================
[1/7] @flockboynation
  Searching for @flockboynation...
  Found 2 videos
  Watching video for 5s...
  Posting comment: 'Love the gains content!'
  ✓ Comment posted
...
```

---

## Performance Optimization

### LDPlayer Settings (Per Instance)

**Graphics:**
- Rendering: OpenGL
- Frame rate: 60 FPS
- Resolution: 1080x1920

**Performance:**
- RAM: 2048 MB
- CPU: 2 cores
- Enable high performance mode

### Server Settings

**Power Plan:**
```powershell
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # High performance
```

**Disable Windows animations:**
- System → Advanced → Performance → Adjust for best performance

**Increase virtual memory:**
- System → Advanced → Performance Settings → Advanced → Virtual Memory
- Set to 50GB minimum, 100GB maximum

---

## Running at Scale

### Batch Processing

Edit `emulator_configs.json`:

```json
{
  "settings": {
    "parallel_emulators": 10  // Run 10 at once
  }
}
```

**Processing batches:**
- 40 emulators ÷ 10 parallel = 4 batches
- Each batch takes ~5-10 minutes
- Total time: 20-40 minutes for all 40

### Scheduling

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 9:00 AM
4. Action: Start Program
   - Program: `python`
   - Arguments: `comment_target_emulator.py`
   - Start in: `C:\TikTokAutomation\downloads`

---

## Monitoring

### Resource Monitor

```powershell
# Watch resource usage
while ($true) {
    Clear-Host
    Get-Process ldplayer* | Measure-Object -Property WorkingSet -Sum | Select-Object @{Name="RAM (GB)";Expression={[math]::Round($_.Sum/1GB,2)}}
    Start-Sleep -Seconds 5
}
```

### Log Files

```powershell
# Run with logging
python comment_target_emulator.py > automation.log 2>&1

# Watch logs
Get-Content automation.log -Wait -Tail 50
```

---

## Troubleshooting

### Instance Won't Start

```powershell
# Check instance status
& "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe" list2

# Restart specific instance
& "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe" reboot --name TikTok-5
```

### ADB Connection Lost

```powershell
# Restart ADB
adb kill-server
adb start-server

# Reconnect all
.\connect_all_adb.ps1
```

### High RAM Usage

```powershell
# Reduce RAM per instance
& "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe" modify --name TikTok-1 --memory 1536

# Or reduce parallel processing
# Edit emulator_configs.json: "parallel_emulators": 3
```

### Appium Errors

```powershell
# Reinstall Appium driver
appium driver uninstall uiautomator2
appium driver install uiautomator2

# Restart Appium
# Ctrl+C to stop, then: appium
```

---

## Maintenance

### Daily Checklist

```powershell
# 1. Check all instances running
& "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe" list2

# 2. Verify ADB connections
adb devices

# 3. Check Appium server
curl http://localhost:4723/status

# 4. Run automation
python comment_target_emulator.py
```

### Weekly Tasks

- Restart all instances (prevent memory leaks)
- Update TikTok app
- Check for Windows updates
- Review automation logs

---

## Scaling Beyond 40

**For 80+ instances:**
- Upgrade to 256GB RAM server
- Use multiple Appium servers (load balancing)
- Distribute across multiple physical servers

**Current setup supports:**
- 40 TikTok accounts
- 7 target accounts
- 2 comments per target = 560 comments/day
- At scale: 20,000+ comments/month

---

## Quick Reference Commands

```powershell
# Create instances
.\setup_40_ldplayers.ps1

# Start all
.\start_all_ldplayers.ps1

# Connect ADB
.\connect_all_adb.ps1

# Install TikTok
.\install_tiktok_all.ps1

# Generate config
python generate_ldplayer_configs.py

# Start Appium
appium

# Run automation
python comment_target_emulator.py

# Stop all instances
& "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe" quitall
```

---

## Support Files Created

| File | Purpose |
|------|---------|
| `setup_40_ldplayers.ps1` | Create 40 instances |
| `start_all_ldplayers.ps1` | Start all instances |
| `connect_all_adb.ps1` | Connect all to ADB |
| `install_tiktok_all.ps1` | Install TikTok APK |
| `generate_ldplayer_configs.py` | Generate config JSON |
| `comment_target_emulator.py` | Main automation script |
| `emulator_configs.json` | Configuration file |

---

**Ready to scale TikTok automation to 40 accounts!**

Last updated: 2026-04-20
