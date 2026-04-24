#!/usr/bin/env python3
"""
Multilogin API Client
=====================
Python client for Multilogin X API with support for browser profile management
and Selenium/Puppeteer automation.

DOCUMENTATION:
    https://documenter.getpostman.com/view/28533318/2s946h9Cv9

SETUP:
    pip install requests selenium

USAGE:
    from multilogin_api import MultiloginClient

    client = MultiloginClient(email="your@email.com", password="yourpassword")
    client.authenticate()

    # Start a profile with Selenium
    driver = client.start_profile(
        folder_id="your_folder_id",
        profile_id="your_profile_id",
        automation_type="selenium"
    )

    # Use the driver
    driver.get("https://tiktok.com")

    # Stop the profile
    client.stop_profile(profile_id="your_profile_id")
"""

import requests
import hashlib
import time
from typing import Optional, Dict, List, Any
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


class MultiloginClient:
    """Client for interacting with Multilogin X API"""

    # API endpoints
    MLX_BASE = "https://api.multilogin.com"
    MLX_LAUNCHER = "https://launcher.mlx.yt:45001/api/v1"
    MLX_LAUNCHER_V2 = "https://launcher.mlx.yt:45001/api/v2"
    LOCALHOST = "http://127.0.0.1"

    def __init__(self, email: str = "", password: str = "", automation_token: str = ""):
        """
        Initialize Multilogin client

        Args:
            email: Multilogin account email
            password: Multilogin account password (plain text)
            automation_token: Optional pre-generated automation token (higher rate limits)
        """
        self.email = email
        self.password = password
        self.automation_token = automation_token
        self.token = None
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def authenticate(self) -> bool:
        """
        Authenticate with Multilogin API and get access token

        Returns:
            bool: True if authentication successful, False otherwise
        """
        if self.automation_token:
            self.token = self.automation_token
            self.headers["Authorization"] = f"Bearer {self.automation_token}"
            return True

        try:
            payload = {
                "email": self.email,
                "password": hashlib.md5(self.password.encode()).hexdigest()
            }

            response = requests.post(
                f"{self.MLX_BASE}/user/signin",
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                self.token = data.get("token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                print(f"✓ Authenticated successfully")
                return True
            else:
                print(f"✗ Authentication failed: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False

    def get_folders(self) -> List[Dict[str, Any]]:
        """
        Get list of all folders

        Returns:
            List of folder objects
        """
        try:
            response = requests.get(
                f"{self.MLX_BASE}/folder/list",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"✗ Error getting folders: {response.text}")
                return []

        except Exception as e:
            print(f"✗ Error: {e}")
            return []

    def get_profiles(self, folder_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of browser profiles

        Args:
            folder_id: Optional folder ID to filter profiles
            limit: Maximum number of profiles to return

        Returns:
            List of profile objects
        """
        try:
            url = f"{self.MLX_BASE}/profile"
            params = {"limit": limit}

            if folder_id:
                params["folderId"] = folder_id

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"✗ Error getting profiles: {response.text}")
                return []

        except Exception as e:
            print(f"✗ Error: {e}")
            return []

    def create_profile(
        self,
        name: str,
        folder_id: str,
        browser_type: str = "mimic",
        os_type: str = "windows",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new browser profile

        Args:
            name: Profile name
            folder_id: Folder ID to create profile in
            browser_type: "mimic" or "stealthfox"
            os_type: Operating system ("windows", "macos", "linux")
            **kwargs: Additional profile parameters (user_agent, proxy, etc.)

        Returns:
            Profile object if successful, None otherwise
        """
        try:
            payload = {
                "name": name,
                "folder_id": folder_id,
                "browser_type": browser_type,
                "os_type": os_type,
                **kwargs
            }

            response = requests.post(
                f"{self.MLX_BASE}/profile",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 201]:
                print(f"✓ Profile '{name}' created successfully")
                return response.json().get("data")
            else:
                print(f"✗ Error creating profile: {response.text}")
                return None

        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def start_profile(
        self,
        folder_id: str,
        profile_id: str,
        automation_type: str = "selenium",
        headless: bool = False
    ) -> Optional[webdriver.Remote]:
        """
        Start a browser profile and return Selenium WebDriver

        Args:
            folder_id: Folder ID containing the profile
            profile_id: Profile ID to start
            automation_type: "selenium" or "puppeteer"
            headless: Run browser in headless mode

        Returns:
            Selenium WebDriver instance if successful, None otherwise
        """
        try:
            url = f"{self.MLX_LAUNCHER_V2}/profile/f/{folder_id}/p/{profile_id}/start"
            params = {
                "automation_type": automation_type,
                "headless_mode": str(headless).lower()
            }

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=60
            )

            if response.status_code != 200:
                print(f"✗ Error starting profile: {response.text}")
                return None

            data = response.json().get("data", {})
            selenium_port = data.get("port")

            if not selenium_port:
                print(f"✗ No port returned from API")
                return None

            # Connect Selenium to the launched browser
            if automation_type == "selenium":
                # For Mimic browser (Chromium-based)
                options = ChromiumOptions()
                driver = webdriver.Remote(
                    command_executor=f"{self.LOCALHOST}:{selenium_port}",
                    options=options
                )
                print(f"✓ Profile started on port {selenium_port}")
                return driver
            else:
                print(f"✗ Only selenium automation_type is supported in this client")
                return None

        except Exception as e:
            print(f"✗ Error starting profile: {e}")
            return None

    def stop_profile(self, profile_id: str) -> bool:
        """
        Stop a running browser profile

        Args:
            profile_id: Profile ID to stop

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.MLX_LAUNCHER}/profile/stop/p/{profile_id}",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Profile stopped")
                return True
            else:
                print(f"✗ Error stopping profile: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def create_quick_profile(
        self,
        name: str = "Quick Profile",
        browser_type: str = "mimic",
        automation_type: str = "selenium"
    ) -> Optional[webdriver.Remote]:
        """
        Create and start a quick profile (temporary profile)

        Args:
            name: Profile name
            browser_type: "mimic" or "stealthfox"
            automation_type: "selenium" or "puppeteer"

        Returns:
            Selenium WebDriver instance if successful, None otherwise
        """
        try:
            payload = {
                "name": name,
                "browser_type": browser_type,
                "automation_type": automation_type
            }

            response = requests.post(
                f"{self.MLX_LAUNCHER_V2}/profile/quick",
                json=payload,
                headers=self.headers,
                timeout=60
            )

            if response.status_code != 200:
                print(f"✗ Error creating quick profile: {response.text}")
                return None

            data = response.json().get("data", {})
            selenium_port = data.get("port")
            profile_id = data.get("profile_id")

            if not selenium_port:
                print(f"✗ No port returned from API")
                return None

            # Connect Selenium to the launched browser
            options = ChromiumOptions()
            driver = webdriver.Remote(
                command_executor=f"{self.LOCALHOST}:{selenium_port}",
                options=options
            )

            # Store profile_id on driver for later cleanup
            driver.multilogin_profile_id = profile_id

            print(f"✓ Quick profile created on port {selenium_port}")
            return driver

        except Exception as e:
            print(f"✗ Error creating quick profile: {e}")
            return None

    def update_profile(
        self,
        profile_id: str,
        **kwargs
    ) -> bool:
        """
        Update an existing profile

        Args:
            profile_id: Profile ID to update
            **kwargs: Profile parameters to update (name, proxy, etc.)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.patch(
                f"{self.MLX_BASE}/profile/{profile_id}",
                json=kwargs,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                print(f"✓ Profile updated successfully")
                return True
            else:
                print(f"✗ Error updating profile: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a profile

        Args:
            profile_id: Profile ID to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.MLX_BASE}/profile/{profile_id}",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Profile deleted")
                return True
            else:
                print(f"✗ Error deleting profile: {response.text}")
                return False

        except Exception as e:
            print(f"✗ Error: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = MultiloginClient(
        email="your-email@example.com",
        password="your-password"
    )

    # Authenticate
    if not client.authenticate():
        print("Failed to authenticate")
        exit(1)

    # Get folders
    folders = client.get_folders()
    if folders:
        print(f"\nFound {len(folders)} folders:")
        for folder in folders[:5]:
            print(f"  - {folder.get('name')} (ID: {folder.get('id')})")

    # Get profiles
    profiles = client.get_profiles(limit=10)
    if profiles:
        print(f"\nFound {len(profiles)} profiles:")
        for profile in profiles[:5]:
            print(f"  - {profile.get('name')} (ID: {profile.get('id')})")

    # Example: Start a profile
    # driver = client.start_profile(
    #     folder_id="your_folder_id",
    #     profile_id="your_profile_id"
    # )
    # if driver:
    #     driver.get("https://multilogin.com")
    #     time.sleep(5)
    #     client.stop_profile(profile_id="your_profile_id")

    print("\n✓ Done!")
