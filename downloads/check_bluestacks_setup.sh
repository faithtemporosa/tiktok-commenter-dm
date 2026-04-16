#!/bin/bash
# Check if Bluestacks automation is ready

echo "======================================================================"
echo "  Bluestacks Setup Checker"
echo "======================================================================"
echo ""

# Check if adb is installed
echo "1. Checking if ADB is installed..."
if command -v adb &> /dev/null; then
    echo "   ✓ ADB is installed"
    adb version | head -1
else
    echo "   ✗ ADB not found"
    echo "   Install with: brew install android-platform-tools"
    exit 1
fi
echo ""

# Check if Bluestacks is running
echo "2. Checking if Bluestacks is connected..."
adb devices | grep "127.0.0.1:5555"
if [ $? -eq 0 ]; then
    echo "   ✓ Bluestacks is connected"
else
    echo "   ✗ Bluestacks not connected"
    echo "   Connecting..."
    adb connect 127.0.0.1:5555
    sleep 2
    adb devices | grep "127.0.0.1:5555"
    if [ $? -eq 0 ]; then
        echo "   ✓ Connected!"
    else
        echo "   ✗ Connection failed"
        echo ""
        echo "   Make sure:"
        echo "     1. Bluestacks is running"
        echo "     2. Enable ADB in Bluestacks Settings → Advanced"
        echo "     3. Restart Bluestacks"
        exit 1
    fi
fi
echo ""

# Check if TikTok is installed
echo "3. Checking if TikTok is installed in Bluestacks..."
adb -s 127.0.0.1:5555 shell pm list packages | grep "com.zhiliaoapp.musically"
if [ $? -eq 0 ]; then
    echo "   ✓ TikTok is installed"
else
    echo "   ✗ TikTok not installed"
    echo "   Install TikTok from Play Store in Bluestacks"
    exit 1
fi
echo ""

echo "======================================================================"
echo "  ✓ SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "You can now run the automation script:"
echo "  python3 downloads/bluestacks_tiktok_automation.py"
echo ""
