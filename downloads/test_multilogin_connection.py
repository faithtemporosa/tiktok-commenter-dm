#!/usr/bin/env python3
"""
Multilogin Connection Test
===========================
Quick script to test your Multilogin API connection and list available profiles.

USAGE:
    python test_multilogin_connection.py
"""

import json
import os
from multilogin_api import MultiloginClient


def load_config():
    """Load configuration from JSON file"""
    config_file = "multilogin_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None


def test_connection():
    """Test Multilogin API connection"""
    print("=" * 60)
    print("  Multilogin Connection Test")
    print("=" * 60)
    print()

    # Load config
    config = load_config()
    if not config:
        print("❌ multilogin_config.json not found!")
        print("   Create this file with your Multilogin credentials.")
        return False

    email = config.get("email", "")
    password = config.get("password", "")
    automation_token = config.get("automation_token", "")

    if not email and not automation_token:
        print("❌ No credentials found in multilogin_config.json")
        print("   Please add your email/password or automation_token")
        return False

    # Initialize client
    print("🔌 Connecting to Multilogin...")
    client = MultiloginClient(
        email=email,
        password=password,
        automation_token=automation_token
    )

    # Test authentication
    print("🔐 Authenticating...")
    if not client.authenticate():
        print("❌ Authentication failed!")
        print("   Check your credentials in multilogin_config.json")
        return False

    print("✅ Authentication successful!")
    print()

    # Get folders
    print("📁 Fetching folders...")
    folders = client.get_folders()

    if folders:
        print(f"✅ Found {len(folders)} folders:")
        print()
        for i, folder in enumerate(folders[:10], 1):
            folder_id = folder.get("id", "N/A")
            folder_name = folder.get("name", "Unnamed")
            print(f"   {i}. {folder_name}")
            print(f"      ID: {folder_id}")
        print()

        if len(folders) > 10:
            print(f"   ... and {len(folders) - 10} more folders")
            print()
    else:
        print("⚠️  No folders found")
        print()

    # Get profiles
    print("👤 Fetching browser profiles...")
    folder_id = config.get("folder_id")

    if folder_id:
        print(f"   Filtering by folder: {folder_id}")

    profiles = client.get_profiles(folder_id=folder_id, limit=100)

    if profiles:
        print(f"✅ Found {len(profiles)} profiles:")
        print()
        for i, profile in enumerate(profiles[:10], 1):
            profile_id = profile.get("id", "N/A")
            profile_name = profile.get("name", "Unnamed")
            browser_type = profile.get("browser_type", "N/A")
            print(f"   {i}. {profile_name}")
            print(f"      ID: {profile_id}")
            print(f"      Browser: {browser_type}")
            print()

        if len(profiles) > 10:
            print(f"   ... and {len(profiles) - 10} more profiles")
            print()
    else:
        print("⚠️  No profiles found")
        print()

    # Summary
    print("=" * 60)
    print("✅ CONNECTION TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  • Folders: {len(folders)}")
    print(f"  • Profiles: {len(profiles)}")
    print()
    print("Next steps:")
    print("  1. Run: python multilogin_tiktok_signup.py")
    print("  2. Open: http://localhost:9006")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_connection()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹  Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
