# PowerShell Script: Setup 40 LDPlayer Instances
# Run this on your Windows Server 2022

# Configuration
$NUM_INSTANCES = 40
$RAM_PER_INSTANCE = 2048  # MB
$CPU_PER_INSTANCE = 2
$RESOLUTION = "1080x1920"
$DPI = 240
$STARTING_PORT = 5555

# LDPlayer paths (adjust if needed)
$LDPLAYER_PATH = "C:\Program Files\LDPlayer\LDPlayer9"
$LDCONSOLE = "$LDPLAYER_PATH\ldconsole.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LDPlayer Mass Instance Creator" -ForegroundColor Cyan
Write-Host "Creating $NUM_INSTANCES instances..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if LDPlayer is installed
if (-not (Test-Path $LDCONSOLE)) {
    Write-Host "ERROR: LDPlayer not found at $LDPLAYER_PATH" -ForegroundColor Red
    Write-Host "Please install LDPlayer first from https://www.ldplayer.net/" -ForegroundColor Yellow
    exit 1
}

# Get existing instances
Write-Host "`nChecking existing instances..." -ForegroundColor Yellow
$existingInstances = & $LDCONSOLE list2

# Create instances
Write-Host "`nCreating $NUM_INSTANCES instances..." -ForegroundColor Green

for ($i = 1; $i -le $NUM_INSTANCES; $i++) {
    $instanceName = "TikTok-$i"

    Write-Host "[$i/$NUM_INSTANCES] Creating $instanceName..." -ForegroundColor Cyan

    # Create instance
    & $LDCONSOLE add --name $instanceName

    Start-Sleep -Seconds 2

    # Configure instance
    Write-Host "  Configuring $instanceName..." -ForegroundColor Gray

    # Set RAM
    & $LDCONSOLE modify --name $instanceName --memory $RAM_PER_INSTANCE

    # Set CPU
    & $LDCONSOLE modify --name $instanceName --cpu $CPU_PER_INSTANCE

    # Set resolution
    & $LDCONSOLE modify --name $instanceName --resolution $RESOLUTION --dpi $DPI

    # Enable root
    & $LDCONSOLE modify --name $instanceName --root 1

    # Set frame rate
    & $LDCONSOLE modify --name $instanceName --fps 60

    Write-Host "  ✓ $instanceName created and configured" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Created: $NUM_INSTANCES instances" -ForegroundColor White
Write-Host "RAM per instance: $RAM_PER_INSTANCE MB" -ForegroundColor White
Write-Host "CPU per instance: $CPU_PER_INSTANCE cores" -ForegroundColor White
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Start all instances: .\start_all_ldplayers.ps1" -ForegroundColor White
Write-Host "2. Install TikTok on each instance" -ForegroundColor White
Write-Host "3. Generate config: python generate_ldplayer_configs.py" -ForegroundColor White
Write-Host "4. Run automation: python comment_target_emulator.py" -ForegroundColor White
