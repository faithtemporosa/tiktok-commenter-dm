# Multilogin Integration for TikTok Automation

This folder contains Multilogin-based alternatives to your AdsPower automation scripts. Multilogin provides advanced browser fingerprinting and multi-accounting capabilities.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Available Scripts](#available-scripts)
- [Migration from AdsPower](#migration-from-adspower)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

Multilogin is a professional anti-detect browser platform that allows you to:

- Create multiple browser profiles with unique fingerprints
- Manage separate browser sessions for multi-accounting
- Automate browsers using Selenium/Puppeteer
- Avoid detection and account bans

**Key Differences from AdsPower:**
- More advanced fingerprinting technology
- Better API documentation and support
- Higher rate limits with automation tokens
- Support for both Chromium (Mimic) and Firefox (Stealthfox) browsers

## ✅ Prerequisites

1. **Multilogin Account**
   - Sign up at [https://multilogin.com](https://multilogin.com)
   - Purchase a subscription (Solo, Team, or Custom Plan)
   - Download and install Multilogin X application

2. **Multilogin X Application**
   - Install the Multilogin X desktop app
   - Make sure it's running (local API runs on `https://launcher.mlx.yt:45001`)
   - Create at least one folder and browser profile

3. **Python Dependencies**
   ```bash
   pip install requests selenium flask supabase
   ```

## 🚀 Installation

1. **Install Python packages:**
   ```bash
   cd downloads
   pip install requests selenium flask supabase
   ```

2. **Configure your credentials:**
   Edit `multilogin_config.json` with your Multilogin credentials:
   ```json
   {
     "email": "your-email@example.com",
     "password": "your-password",
     "automation_token": "",
     "folder_id": ""
   }
   ```

3. **Get your Folder ID (optional):**
   - Run the test script to see your folders:
   ```bash
   python multilogin_api.py
   ```
   - Copy the folder ID you want to use and add it to `multilogin_config.json`

## ⚙️ Configuration

### multilogin_config.json

| Field | Description | Required |
|-------|-------------|----------|
| `email` | Your Multilogin account email | Yes (unless using token) |
| `password` | Your Multilogin account password | Yes (unless using token) |
| `automation_token` | Optional automation token for higher rate limits | No |
| `folder_id` | Filter profiles from specific folder | No |

### Getting an Automation Token

For higher API rate limits, generate an automation token:

1. Open Multilogin X application
2. Go to Settings → API
3. Generate a new automation token
4. Copy and paste it into `multilogin_config.json`

**Note:** Automation tokens have higher rate limits than regular bearer tokens.

## 📁 Available Scripts

### 1. multilogin_api.py

**Purpose:** Core API client library for Multilogin

**Features:**
- Authentication with email/password or automation token
- Profile management (create, update, delete, list)
- Start/stop browser profiles with Selenium
- Create quick profiles (temporary profiles)

**Usage:**
```python
from multilogin_api import MultiloginClient

# Initialize client
client = MultiloginClient(
    email="your@email.com",
    password="yourpassword"
)

# Authenticate
client.authenticate()

# Get profiles
profiles = client.get_profiles()

# Start a profile
driver = client.start_profile(
    folder_id="folder_id",
    profile_id="profile_id"
)

# Use the driver
driver.get("https://tiktok.com")

# Stop the profile
client.stop_profile(profile_id="profile_id")
```

### 2. multilogin_tiktok_signup.py

**Purpose:** Automated TikTok account creation using Multilogin profiles

**Features:**
- Web dashboard at http://localhost:9006
- Select multiple profiles to create TikTok accounts
- Automatic temp email creation (mail.tm)
- Verification code retrieval
- Supabase integration for account storage

**Run:**
```bash
python multilogin_tiktok_signup.py
```

Then open http://localhost:9006 in your browser.

**Workflow:**
1. Click "Sync Profiles" to load your Multilogin profiles
2. Select profiles you want to create TikTok accounts for
3. Click "Start Signup"
4. Watch the automation create accounts automatically
5. View created accounts in the table at the bottom

## 🔄 Migration from AdsPower

### Key Differences

| Feature | AdsPower | Multilogin |
|---------|----------|------------|
| API Base URL | `http://localhost:50325` | `https://launcher.mlx.yt:45001` |
| Profile ID | `user_id` | `id` |
| Folder System | Groups | Folders with `folder_id` |
| Start Endpoint | `/api/v1/browser/start?user_id=X` | `/api/v2/profile/f/{folder_id}/p/{profile_id}/start` |
| Authentication | No auth required (local) | Bearer token required |

### Migration Checklist

- [ ] Install Multilogin X application
- [ ] Create browser profiles in Multilogin
- [ ] Update `multilogin_config.json` with credentials
- [ ] Test connection: `python multilogin_api.py`
- [ ] Run TikTok signup: `python multilogin_tiktok_signup.py`
- [ ] Migrate any custom scripts using the new API

### Code Conversion Example

**AdsPower (Old):**
```python
import requests

# Start browser
response = requests.get(
    "http://localhost:50325/api/v1/browser/start?user_id=abc123"
)
```

**Multilogin (New):**
```python
from multilogin_api import MultiloginClient

client = MultiloginClient(email="...", password="...")
client.authenticate()

# Start browser
driver = client.start_profile(
    folder_id="folder_123",
    profile_id="profile_abc"
)
```

## 📚 API Documentation

### Official Multilogin Docs

- **API Reference:** [https://documenter.getpostman.com/view/28533318/2s946h9Cv9](https://documenter.getpostman.com/view/28533318/2s946h9Cv9)
- **Beginner's Guide:** [https://multilogin.com/help/en_US/multilogin-x-api-beginners-guide](https://multilogin.com/help/en_US/multilogin-x-api-beginners-guide)
- **Selenium Examples:** [https://multilogin.com/help/en_US/api/selenium-automation-example](https://multilogin.com/help/en_US/api/selenium-automation-example)

### Core Endpoints

#### 1. Authentication
```http
POST https://api.multilogin.com/user/signin
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "md5_hashed_password"
}
```

**Response:**
```json
{
  "data": {
    "token": "bearer_token_here"
  }
}
```

#### 2. List Profiles
```http
GET https://api.multilogin.com/profile?limit=100
Authorization: Bearer {token}
```

#### 3. Start Profile (Selenium)
```http
GET https://launcher.mlx.yt:45001/api/v2/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium&headless_mode=false
Authorization: Bearer {token}
```

**Response:**
```json
{
  "data": {
    "port": 34567
  }
}
```

#### 4. Stop Profile
```http
GET https://launcher.mlx.yt:45001/api/v1/profile/stop/p/{profile_id}
Authorization: Bearer {token}
```

## 🐛 Troubleshooting

### Error: "Cannot connect to Multilogin"

**Solution:**
- Make sure Multilogin X application is running
- Check that the local API is accessible at `https://launcher.mlx.yt:45001`
- Verify your firewall allows connections to this port

### Error: "Authentication failed"

**Solution:**
- Double-check email and password in `multilogin_config.json`
- Try generating an automation token instead
- Make sure your Multilogin subscription is active

### Error: "No port returned from API"

**Solution:**
- The profile might already be running - stop it first
- Check that you have enough browser slots in your subscription
- Verify the folder_id and profile_id are correct

### Error: "Profile failed to start"

**Solution:**
- Make sure the profile exists in Multilogin X
- Check that the folder_id is correct
- Verify your Multilogin app is up to date
- Try stopping all running profiles and try again

### TikTok signup fails

**Solution:**
- Check if TikTok changed their signup flow
- Verify the temp email service (mail.tm) is working
- Try running manually first to see the flow
- Check the Selenium selectors are still valid

## 💡 Tips & Best Practices

1. **Use Automation Tokens** for production to avoid rate limits
2. **Create separate folders** for different account types (e.g., "TikTok Accounts", "Test Profiles")
3. **Always stop profiles** after use to free up browser slots
4. **Monitor your rate limits** - Multilogin has API rate limits per minute
5. **Use headless mode** (`headless=True`) for faster automation
6. **Test with one profile** before running bulk operations
7. **Keep Multilogin X updated** for latest API features

## 🔗 Related Resources

- [Multilogin Official Website](https://multilogin.com)
- [Multilogin Help Center](https://multilogin.com/help)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)

## 📝 License

These scripts are part of your TikTok automation project. Use responsibly and in accordance with TikTok's Terms of Service and Multilogin's acceptable use policy.

---

**Need Help?** Check the official Multilogin documentation or reach out to their support team.
