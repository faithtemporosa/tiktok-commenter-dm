#!/bin/bash
# Setup iPhone TikTok Automation
# This installs everything needed to control your iPhone from Mac

echo "=========================================="
echo "  iPhone TikTok Automation Setup"
echo "=========================================="
echo ""
echo "This will install:"
echo "  • Node.js (for Appium)"
echo "  • Appium (iPhone automation server)"
echo "  • XCUITest driver (iOS automation)"
echo "  • libimobiledevice (iPhone connection)"
echo "  • Python packages (Appium client)"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo ""
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew already installed"
fi

# Install Node.js
echo ""
echo "Installing Node.js..."
if ! command -v node &> /dev/null; then
    brew install node
else
    echo "✓ Node.js already installed ($(node --version))"
fi

# Install libimobiledevice (for iPhone connection)
echo ""
echo "Installing libimobiledevice..."
if ! command -v idevice_id &> /dev/null; then
    brew install libimobiledevice
else
    echo "✓ libimobiledevice already installed"
fi

# Install Appium
echo ""
echo "Installing Appium..."
if ! command -v appium &> /dev/null; then
    npm install -g appium
else
    echo "✓ Appium already installed ($(appium --version))"
fi

# Install XCUITest driver
echo ""
echo "Installing XCUITest driver..."
appium driver install xcuitest

# Install Python packages
echo ""
echo "Installing Python packages..."
pip3 install Appium-Python-Client

# Check if iPhone is connected
echo ""
echo "=========================================="
echo "  Checking iPhone Connection"
echo "=========================================="
echo ""

if command -v idevice_id &> /dev/null; then
    UDID=$(idevice_id -l)
    if [ -n "$UDID" ]; then
        echo "✓ iPhone connected!"
        echo "  UDID: $UDID"

        # Get iPhone name
        if command -v ideviceinfo &> /dev/null; then
            DEVICE_NAME=$(ideviceinfo -k DeviceName)
            echo "  Name: $DEVICE_NAME"
        fi
    else
        echo "⚠ No iPhone detected"
        echo ""
        echo "Please:"
        echo "  1. Connect iPhone via USB cable"
        echo "  2. Unlock your iPhone"
        echo "  3. Tap 'Trust This Computer' if prompted"
        echo "  4. Run this script again"
    fi
else
    echo "⚠ Cannot detect iPhone (idevice_id not found)"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure your iPhone is connected via USB"
echo ""
echo "2. Enable Developer Mode on iPhone:"
echo "   Settings → Privacy & Security → Developer Mode → ON"
echo ""
echo "3. Start Appium server in one terminal:"
echo "   appium"
echo ""
echo "4. Run automation in another terminal:"
echo "   python3 downloads/iphone_tiktok_viewer.py"
echo ""
echo "For your 3 accounts setup:"
echo "   python3 downloads/iphone_3_accounts_viewer.py"
echo ""
