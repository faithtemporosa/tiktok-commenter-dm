# Master Setup Script - Run All Setup Steps
# Complete automated setup for 40 LDPlayer instances

param(
    [switch]$SkipInstanceCreation,
    [switch]$SkipTikTokInstall
)

$ErrorActionPreference = "Continue"

Write-Host @"

========================================
40 LDPLAYER INSTANCES - MASTER SETUP
========================================
Server: Windows Server 2022
RAM: 128GB
CPU: 24 cores
Target: 40 TikTok accounts

This script will:
1. Create 40 LDPlayer instances
2. Start all instances
3. Connect all to ADB
4. Install TikTok (if APK available)
5. Generate configuration

Press Ctrl+C to cancel, or wait 5 seconds to continue...

"@ -ForegroundColor Cyan

Start-Sleep -Seconds 5

# Check prerequisites
Write-Host "`n=== Checking Prerequisites ===" -ForegroundColor Yellow

# Check LDPlayer
$LDPLAYER_PATH = "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe"
if (Test-Path $LDPLAYER_PATH) {
    Write-Host "✓ LDPlayer installed" -ForegroundColor Green
} else {
    Write-Host "✗ LDPlayer not found" -ForegroundColor Red
    Write-Host "Install from: https://www.ldplayer.net/" -ForegroundColor Yellow
    exit 1
}

# Check ADB
try {
    $null = adb version
    Write-Host "✓ ADB available" -ForegroundColor Green
} catch {
    Write-Host "✗ ADB not found" -ForegroundColor Red
    Write-Host "Install: choco install adb" -ForegroundColor Yellow
    exit 1
}

# Check Python
try {
    $null = python --version
    Write-Host "✓ Python installed" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found" -ForegroundColor Red
    Write-Host "Install from: https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Step 1: Create Instances
if (-not $SkipInstanceCreation) {
    Write-Host "`n=== Step 1/5: Creating 40 Instances ===" -ForegroundColor Yellow
    Write-Host "This will take ~10 minutes...`n" -ForegroundColor Gray

    & .\setup_40_ldplayers.ps1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nError creating instances. Exiting." -ForegroundColor Red
        exit 1
    }

    Write-Host "`n✓ Instances created" -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "`n=== Step 1/5: Skipping Instance Creation ===" -ForegroundColor Gray
}

# Step 2: Start All Instances
Write-Host "`n=== Step 2/5: Starting All Instances ===" -ForegroundColor Yellow
Write-Host "This will take ~5 minutes...`n" -ForegroundColor Gray

& .\start_all_ldplayers.ps1

Write-Host "`n✓ Instances started" -ForegroundColor Green
Write-Host "Waiting 2 minutes for instances to fully boot..." -ForegroundColor Gray
Start-Sleep -Seconds 120

# Step 3: Connect to ADB
Write-Host "`n=== Step 3/5: Connecting All to ADB ===" -ForegroundColor Yellow

& .\connect_all_adb.ps1

$devices = (adb devices | Select-String "127.0.0.1").Count
Write-Host "`n✓ Connected $devices devices to ADB" -ForegroundColor Green
Start-Sleep -Seconds 3

# Step 4: Install TikTok
if (-not $SkipTikTokInstall) {
    Write-Host "`n=== Step 4/5: Installing TikTok ===" -ForegroundColor Yellow

    if (Test-Path ".\tiktok.apk") {
        Write-Host "Found tiktok.apk, installing on all instances...`n" -ForegroundColor Gray

        & .\install_tiktok_all.ps1

        Write-Host "`n✓ TikTok installed" -ForegroundColor Green
    } else {
        Write-Host "⚠ tiktok.apk not found" -ForegroundColor Yellow
        Write-Host "Download from: https://apkpure.com/tiktok/com.zhiliaoapp.musically" -ForegroundColor Gray
        Write-Host "Skipping TikTok installation..." -ForegroundColor Gray
    }
} else {
    Write-Host "`n=== Step 4/5: Skipping TikTok Installation ===" -ForegroundColor Gray
}

Start-Sleep -Seconds 3

# Step 5: Generate Configuration
Write-Host "`n=== Step 5/5: Generating Configuration ===" -ForegroundColor Yellow

python generate_ldplayer_configs.py

Write-Host "`n✓ Configuration generated" -ForegroundColor Green

# Final Summary
Write-Host @"

========================================
SETUP COMPLETE!
========================================

Created: 40 LDPlayer instances
Running: $devices instances
Config: emulator_configs.json

NEXT STEPS:

1. MANUAL: Login to TikTok on each instance
   - Open each LDPlayer instance
   - Login to TikTok
   - Complete verification

2. UPDATE CONFIG:
   - Edit emulator_configs.json
   - Set 'tiktok_account' for each instance

3. INSTALL DEPENDENCIES:
   npm install -g appium
   appium driver install uiautomator2
   pip install appium-python-client selenium requests supabase

4. START APPIUM:
   appium

5. RUN AUTOMATION:
   python comment_target_emulator.py

========================================
FULL GUIDE: SERVER_SETUP_40_INSTANCES.md
========================================

"@ -ForegroundColor Green

# Open config file
if (Test-Path "emulator_configs.json") {
    Write-Host "Opening configuration file..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
    notepad emulator_configs.json
}
