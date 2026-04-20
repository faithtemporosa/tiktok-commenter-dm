# PowerShell Script: Install TikTok on All LDPlayer Instances
# Installs TikTok APK on all 40 instances

param(
    [string]$ApkPath = ".\tiktok.apk"  # Path to TikTok APK
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Install TikTok on All Instances" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if APK exists
if (-not (Test-Path $ApkPath)) {
    Write-Host "ERROR: TikTok APK not found at $ApkPath" -ForegroundColor Red
    Write-Host "`nDownload TikTok APK:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://apkpure.com/tiktok/com.zhiliaoapp.musically" -ForegroundColor White
    Write-Host "2. Download latest APK" -ForegroundColor White
    Write-Host "3. Save as tiktok.apk in this folder" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host "✓ Found APK: $ApkPath`n" -ForegroundColor Green

# Get connected devices
$devices = adb devices | Select-String "127.0.0.1" | ForEach-Object {
    ($_ -split '\s+')[0]
}

$totalDevices = $devices.Count
Write-Host "Found $totalDevices connected devices`n" -ForegroundColor Yellow

if ($totalDevices -eq 0) {
    Write-Host "ERROR: No devices connected" -ForegroundColor Red
    Write-Host "Run: .\connect_all_adb.ps1" -ForegroundColor Yellow
    exit 1
}

$installed = 0
$failed = 0

foreach ($device in $devices) {
    $index = $installed + 1
    Write-Host "[$index/$totalDevices] Installing on $device..." -ForegroundColor Cyan

    # Install APK
    $result = adb -s $device install -r $ApkPath 2>&1

    if ($result -match "Success") {
        Write-Host "  ✓ Installed" -ForegroundColor Green
        $installed++
    } else {
        Write-Host "  ✗ Failed: $result" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total devices: $totalDevices" -ForegroundColor White
Write-Host "Installed: $installed" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Failed: $failed" -ForegroundColor Red
}

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Manually login to TikTok on each instance" -ForegroundColor White
Write-Host "2. Update emulator_configs.json with account usernames" -ForegroundColor White
Write-Host "3. Run automation: python comment_target_emulator.py" -ForegroundColor White
