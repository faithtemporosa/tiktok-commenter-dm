# Multilogin Anti-Detection Setup for TikTok

## 🚨 Current Problems Causing Detection

### 1. ❌ Temp Email Addresses (mail.tm)
**Problem:** TikTok blacklists temp email domains
- mail.tm is widely known and blocked
- TikTok checks email domain reputation
- Temp emails = instant ban

**Solution:** Use real email providers
- Gmail (best)
- Outlook/Hotmail
- Yahoo
- ProtonMail
- Custom domain emails

### 2. ❌ No Proxy Configuration
**Problem:** All accounts share same IP address
- TikTok links accounts by IP
- Multiple accounts from one IP = ban
- Your M2 Mac IP is fingerprinted

**Solution:** Unique residential proxy per account
- 1 account = 1 unique residential IP
- Rotating proxies don't work well (TikTok detects)
- Sticky residential proxies recommended

### 3. ❌ Same Browser Fingerprint
**Problem:** Default Multilogin profiles might share fingerprints
- Need unique Canvas fingerprint per profile
- Different screen resolution, GPU, fonts
- Timezone must match proxy location

**Solution:** Configure each profile with unique fingerprint

### 4. ❌ Behavior Patterns
**Problem:** Automation is too fast/robotic
- Creating accounts too quickly
- Same actions in same order
- No human-like delays

**Solution:** Random delays, warm-up period

---

## ✅ Proper Anti-Detection Setup

### Step 1: Get Residential Proxies

**Recommended Proxy Providers:**
1. **Bright Data** (Luminati) - Best quality, expensive
2. **Smartproxy** - Good balance of price/quality
3. **IPRoyal** - Affordable residential proxies
4. **Proxy-Seller** - Budget option
5. **922 S5 Proxy** - Popular for multi-accounting

**What you need:**
- Residential proxies (NOT datacenter)
- Sticky sessions (same IP for 10-30 minutes)
- Geographic targeting (match your target region)
- 1 unique proxy per TikTok account

**Cost:** ~$5-15 per GB, ~$1-3 per account/month

### Step 2: Configure Multilogin Profiles Properly

Each profile needs:

```javascript
{
  "name": "TikTok_Account_01",
  "folder_id": "your_folder_id",
  "browser_type": "mimic",  // Chromium-based
  "os_type": "windows",      // or "macos"

  // PROXY (CRITICAL!)
  "proxy": {
    "type": "http",
    "host": "proxy.example.com",
    "port": 12345,
    "username": "your_username",
    "password": "your_password"
  },

  // FINGERPRINT RANDOMIZATION
  "parameters": {
    "fingerprint": {
      // Canvas fingerprint - unique per profile
      "canvas_noise": true,
      "canvas_mode": "noise",

      // WebGL fingerprint
      "webgl_noise": true,
      "webgl_vendor_noise": true,

      // Audio context fingerprint
      "audio_noise": true,

      // Fonts - vary per profile
      "fonts_list": "random",

      // Screen resolution - vary per profile
      "screen": {
        "width": 1920,   // randomize: 1366, 1440, 1920
        "height": 1080   // randomize: 768, 900, 1080
      },

      // Timezone - MUST match proxy location!
      "timezone": "America/New_York",  // Match proxy city

      // Geolocation - MUST match proxy
      "geolocation": {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "accuracy": 100
      },

      // WebRTC - prevent IP leaking
      "webrtc": {
        "mode": "altered",  // or "disabled"
        "public_ip": "proxy_ip_here"
      },

      // Language - match location
      "navigator": {
        "language": "en-US",
        "languages": ["en-US", "en"]
      }
    }
  }
}
```

### Step 3: Use Real Email Addresses

**Option A: Gmail (Recommended)**
- Create Gmail accounts (use phone verification)
- 1 Gmail = 1 TikTok account
- Cost: Free (need phone numbers)
- Can buy aged Gmail accounts: $0.50-2 each

**Option B: Outlook/Hotmail**
- Microsoft accounts
- Easier to create without phone
- Less trusted than Gmail but works

**Option C: Buy Accounts**
- Pre-made Gmail accounts: ~$0.50-2/account
- Aged accounts (6+ months old) are better
- Sites: PVA Creator, AccsMarket, etc.

**Email Tips:**
```
✅ Use real email providers
✅ One unique email per account
✅ Don't use patterns (tt1@..., tt2@..., etc.)
✅ Random names: john.smith.2847@gmail.com
❌ No temp email services
❌ No disposable domains
❌ No email forwarding services
```

### Step 4: Account Warming Strategy

**Don't create and immediately automate!**

**Day 1: Account Creation**
- Create account with real email
- Use unique proxy
- Complete profile (photo, bio, username)
- DON'T follow anyone yet
- Browse For You page for 5-10 minutes
- Watch 3-5 videos
- Close browser

**Day 2-3: Light Activity**
- Login (same proxy!)
- Browse For You for 10-15 minutes
- Watch 5-10 videos
- Like 2-3 videos
- Maybe follow 1-2 accounts
- Close browser

**Day 4-7: Build Trust**
- Login daily
- Watch 10-15 videos
- Like 5-8 videos
- Follow 3-5 accounts
- Maybe leave 1-2 comments
- Search for content

**Week 2+: Normal Automation**
- Now safe to automate
- Start commenting
- Start posting
- Engage naturally

### Step 5: Automation Best Practices

```python
# Random delays between actions
import random
import time

def human_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

# Example automation flow
driver.get("https://www.tiktok.com/@username")
human_delay(3, 7)  # Wait for page load

# Scroll like human
for i in range(random.randint(2, 5)):
    driver.execute_script("window.scrollBy(0, 300)")
    human_delay(1, 3)

# Click like button
like_button.click()
human_delay(2, 4)

# Type comment like human
comment_text = "Great video!"
for char in comment_text:
    comment_box.send_keys(char)
    time.sleep(random.uniform(0.05, 0.15))

human_delay(1, 2)
submit_button.click()
```

---

## 🛠️ Updated Multilogin Script with Proxies

Here's how to configure proxies in your Multilogin profiles:

### When Creating Profile via API:

```python
from multilogin_api import MultiloginClient

client = MultiloginClient(email="...", password="...")
client.authenticate()

# Create profile with proxy
profile = client.create_profile(
    name="TikTok_Account_01",
    folder_id="your_folder_id",
    browser_type="mimic",
    os_type="windows",

    # PROXY CONFIGURATION
    parameters={
        "proxy": {
            "type": "http",  # or "socks5"
            "host": "residential.proxy.com",
            "port": 12345,
            "username": "proxy_user",
            "password": "proxy_pass"
        },
        "fingerprint": {
            "canvas_noise": True,
            "webgl_noise": True,
            "timezone": "America/New_York",  # Match proxy location!
            "geolocation": {
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }
    }
)
```

### Or Configure Manually in Multilogin X:

1. Open Multilogin X app
2. Create new profile
3. Go to **Proxy** tab
4. Select **HTTP** or **SOCKS5**
5. Enter proxy details:
   - Host: `proxy.example.com`
   - Port: `12345`
   - Username: `your_username`
   - Password: `your_password`
6. Click **Check Proxy** to verify
7. Go to **Advanced** tab
8. Enable **Canvas noise**
9. Enable **WebGL noise**
10. Set **Timezone** to match proxy location
11. Set **Geolocation** to match proxy city
12. Save profile

---

## 📊 Cost Breakdown for 40 Accounts

| Item | Cost per Account | Total (40 accounts) |
|------|------------------|---------------------|
| Gmail Account | $0.50 - $2 | $20 - $80 |
| Residential Proxy | $1 - $3/month | $40 - $120/month |
| Multilogin Subscription | ~$25/month (Team plan) | $100/month (400 profiles) |
| **Total Setup** | **$0.50 - $2** | **$20 - $80** |
| **Total Monthly** | **$1 - $3** | **$40 - $120** |

**Compare to LDPlayer:**
- LDPlayer: Free software, but needs powerful Windows PC
- 40 instances: ~$2,000+ for hardware
- Electricity: Higher costs
- Proxies: Still need them ($40-120/month)

---

## 🔍 How to Test if Detection is Fixed

### Test 1: IP Check
```python
driver.get("https://ipinfo.io")
# Should show proxy IP, not your real Mac IP
```

### Test 2: WebRTC Leak Test
```python
driver.get("https://browserleaks.com/webrtc")
# Should show proxy IP, not your real IP
```

### Test 3: Fingerprint Uniqueness
```python
driver.get("https://browserleaks.com/canvas")
# Each profile should have different fingerprint
```

### Test 4: TikTok Account Creation
- Create 1 account
- Wait 24 hours
- Create another account
- If both survive 7 days = setup is good
- If banned quickly = still detectable

---

## ❓ FAQ

**Q: Can I use free proxies?**
A: No. TikTok detects and blocks free/datacenter proxies immediately.

**Q: Can I reuse proxies across accounts?**
A: Not recommended. 1 proxy = 1 account for best results.

**Q: What if my proxy location doesn't match my timezone?**
A: TikTok will detect this. Always match timezone to proxy location.

**Q: Can I create all 40 accounts in one day?**
A: No. Create 2-3 per day maximum. Mass creation = red flag.

**Q: Do I need different payment methods for Multilogin?**
A: No, Multilogin subscription is separate. But if buying proxies, use different payment methods.

**Q: Can I share fingerprints if using different proxies?**
A: No. Each account needs unique fingerprint + unique proxy.

---

## 🎯 Summary Checklist

Before creating TikTok accounts, ensure:

- [ ] Multilogin X installed and running
- [ ] Residential proxies purchased (1 per account)
- [ ] Each profile configured with:
  - [ ] Unique proxy
  - [ ] Timezone matching proxy location
  - [ ] Geolocation matching proxy city
  - [ ] Canvas/WebGL noise enabled
  - [ ] WebRTC set to altered/disabled
- [ ] Real email addresses ready (Gmail preferred)
- [ ] Account warming strategy planned (7-14 days)
- [ ] Random delays in automation scripts
- [ ] Creating max 2-3 accounts per day
- [ ] Each account has unique behavior pattern

**If all checked: Your detection rate should drop to near zero.**
