# LDPlayer 40 Instances Setup

**All scripts needed to run 40 LDPlayer instances on Windows Server with 128GB RAM**

---

## Prerequisites (Do These First!)

### 1. Install LDPlayer

```
Download from: https://www.ldplayer.net/
Install to default location: C:\Program Files\LDPlayer\LDPlayer9
Open LDPlayer once to complete initial setup
```

### 2. Install Python

```powershell
# Download from https://www.python.org/downloads/
# Or via winget:
winget install Python.Python.3.12

# Verify:
python --version
```

### 3. Install Node.js

```powershell
# Download from https://nodejs.org/
# Or via winget:
winget install OpenJS.NodeJS

# Verify:
node --version
```

### 4. Verify ADB (Android Debug Bridge)

```powershell
# Usually comes with LDPlayer
# Or download from: https://developer.android.com/studio/releases/platform-tools

# Verify:
adb version
```

### Quick Install All (PowerShell as Admin):

```powershell
# Install dependencies
winget install Python.Python.3.12
winget install OpenJS.NodeJS

# Restart PowerShell after installing, then verify:
python --version
node --version
adb version
```

### Prerequisites Checklist:

| Step | Action | Verify |
|------|--------|--------|
| 1 | Install LDPlayer | Open LDPlayer app |
| 2 | Install Python | `python --version` |
| 3 | Install Node.js | `node --version` |
| 4 | Verify ADB | `adb version` |

---

## Quick Start

```powershell
# 1. Download this folder to your Windows Server
# 2. Install LDPlayer from https://www.ldplayer.net/
# 3. Open PowerShell as Administrator
# 4. Navigate to this folder and run:

.\SETUP_MASTER.ps1
```

---

## Files in This Folder

### PowerShell Scripts (Run in Order)

| Script | Purpose |
|--------|---------|
| `SETUP_MASTER.ps1` | **Run this first** - Automates entire setup |
| `setup_40_ldplayers.ps1` | Creates 40 LDPlayer instances |
| `start_all_ldplayers.ps1` | Starts all 40 instances |
| `connect_all_adb.ps1` | Connects all instances to ADB |
| `install_tiktok_all.ps1` | Installs TikTok on all instances |

### Python Scripts

| Script | Purpose |
|--------|---------|
| `comment_target_emulator.py` | Main automation - comments on target accounts |
| `generate_ldplayer_configs.py` | Auto-generates emulator_configs.json |

### Configuration

| File | Purpose |
|------|---------|
| `emulator_configs.json` | Configuration for all 40 emulators |

### Documentation

| File | Purpose |
|------|---------|
| `SERVER_SETUP_40_INSTANCES.md` | Complete step-by-step guide |
| `ANDROID_EMULATOR_SETUP.md` | General emulator setup guide |

---

## Server Requirements

- **OS:** Windows Server 2022
- **RAM:** 128GB
- **CPU:** 24+ cores
- **Storage:** 100GB free

---

## Setup Steps

1. Install LDPlayer
2. Run `.\SETUP_MASTER.ps1`
3. Download TikTok APK
4. Run `.\install_tiktok_all.ps1`
5. Login to TikTok on each instance (manual)
6. Install dependencies: `pip install appium-python-client selenium requests`
7. Start Appium: `appium`
8. Run automation: `python comment_target_emulator.py`

---

## Expected Results

- 40 TikTok accounts running
- 7 target accounts
- 560 comments/day (40 accounts x 7 targets x 2 comments)
- 16,800+ comments/month

---

**See SERVER_SETUP_40_INSTANCES.md for complete documentation**
