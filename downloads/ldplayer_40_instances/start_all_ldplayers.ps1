# PowerShell Script: Start All LDPlayer Instances
# Starts instances in batches to avoid overload

param(
    [int]$BatchSize = 5,  # Start 5 at a time
    [int]$DelayBetweenBatches = 30  # 30 seconds between batches
)

$LDCONSOLE = "C:\Program Files\LDPlayer\LDPlayer9\ldconsole.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting All LDPlayer Instances" -ForegroundColor Cyan
Write-Host "Batch size: $BatchSize" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

# Get all instances
$instances = & $LDCONSOLE list2 | Select-String "TikTok-" | ForEach-Object {
    ($_ -split ',')[1]
}

$totalInstances = $instances.Count
Write-Host "Found $totalInstances instances`n" -ForegroundColor Green

$batchNumber = 1
$started = 0

for ($i = 0; $i -lt $totalInstances; $i += $BatchSize) {
    $batch = $instances[$i..([Math]::Min($i + $BatchSize - 1, $totalInstances - 1))]

    Write-Host "Batch $batchNumber (instances $($i+1)-$([Math]::Min($i + $BatchSize, $totalInstances))):" -ForegroundColor Yellow

    foreach ($instance in $batch) {
        if ($instance) {
            Write-Host "  Starting $instance..." -ForegroundColor Gray
            & $LDCONSOLE launch --name $instance
            $started++
        }
    }

    Write-Host "  ✓ Batch $batchNumber started ($started/$totalInstances)" -ForegroundColor Green

    if ($i + $BatchSize -lt $totalInstances) {
        Write-Host "  Waiting $DelayBetweenBatches seconds before next batch...`n" -ForegroundColor Cyan
        Start-Sleep -Seconds $DelayBetweenBatches
    }

    $batchNumber++
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ALL INSTANCES STARTED!" -ForegroundColor Green
Write-Host "Total: $started instances" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
