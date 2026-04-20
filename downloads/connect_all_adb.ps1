# PowerShell Script: Connect All LDPlayer Instances to ADB
# Connects all 40 instances to ADB for automation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Connecting All LDPlayers to ADB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Port range for 40 instances
$startPort = 5555
$numInstances = 40

$connected = 0
$failed = 0

Write-Host "`nConnecting $numInstances instances...`n" -ForegroundColor Yellow

for ($i = 0; $i -lt $numInstances; $i++) {
    $port = $startPort + ($i * 2)
    $address = "127.0.0.1:$port"

    Write-Host "[$($i+1)/$numInstances] Connecting to $address..." -ForegroundColor Gray

    # Connect via ADB
    $result = adb connect $address 2>&1

    if ($result -match "connected") {
        Write-Host "  ✓ Connected" -ForegroundColor Green
        $connected++
    } else {
        Write-Host "  ✗ Failed: $result" -ForegroundColor Red
        $failed++
    }

    Start-Sleep -Milliseconds 500
}

# Show summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ADB CONNECTION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total instances: $numInstances" -ForegroundColor White
Write-Host "Connected: $connected" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "Failed: $failed" -ForegroundColor Red
    Write-Host "`nNote: Failed instances may not be running yet." -ForegroundColor Yellow
    Write-Host "Start them with: .\start_all_ldplayers.ps1" -ForegroundColor Yellow
}

# Verify with adb devices
Write-Host "`nVerifying connections..." -ForegroundColor Yellow
adb devices

Write-Host "`n✓ Done!" -ForegroundColor Green
