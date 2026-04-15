# TikTok Automation Suite with Stealth Mode

Multi-account TikTok automation platform with anti-detection features.

## 🚨 Recent Updates (Latest)

**Stealth Mode Integration** - All automation scripts now include:
- ✅ CDP/WebDriver detection hidden
- ✅ Natural behavior patterns (scrolling, typing, watching)
- ✅ Unique proxy assignment (1 IP per browser)
- ✅ Account warmup system (3-7 day IP trust building)

See [downloads/README_STEALTH.md](downloads/README_STEALTH.md) for complete stealth documentation.

---

## 📁 Project Structure

```
tiktok-commenter-dm/
├── downloads/
│   ├── stealth_browsing.py          # Core stealth utilities
│   ├── warmup_accounts.py           # Daily warmup script
│   ├── comment_target_accounts.py   # Main commenter (stealth enabled)
│   ├── tiktok_commenter.py          # Web UI commenter (stealth enabled)
│   ├── assign_unique_proxies_fast.py # Proxy assignment
│   ├── test_stealth.py              # Stealth verification
│   └── README_STEALTH.md            # Stealth mode documentation
├── tiktok_accounts.csv              # Account database
├── webshare_proxies_fresh.txt       # Proxy pool (2500 proxies)
└── README.md                        # This file
```

---

## 🎯 Main Features

### 1. Multi-Account Management
- Manage 100+ TikTok accounts via AdsPower
- Each account has unique browser profile
- Unique IP assignment (no sharing)

### 2. Automated Commenting
- Target specific TikTok accounts
- Natural comment patterns
- Daily limits for new accounts
- Video deduplication

### 3. Stealth Mode (NEW)
- Hides automation fingerprints
- Natural human-like behavior
- IP warmup system
- Anti-detection measures

### 4. Proxy Management
- 2,500 proxy pool (Webshare)
- ~65% residential, ~35% datacenter
- Automatic assignment
- IP rotation support

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install requests playwright emergentintegrations
playwright install chromium

# Install Google API (for Gmail verification)
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Install Supabase (optional, for cloud sync)
pip install supabase
```

### Setup

1. **Configure AdsPower**
   - Install AdsPower on your machine
   - Import browser profiles
   - Ensure API is running on port 50325

2. **Assign Unique Proxies**
   ```bash
   cd downloads
   python3 assign_unique_proxies_fast.py
   ```

3. **Warmup Accounts (3-7 days)**
   ```bash
   python3 warmup_accounts.py
   ```
   Run this daily for 3-7 days before commenting

4. **Start Commenting**
   ```bash
   python3 comment_target_accounts.py
   ```

---

## 📖 Usage

### Warmup Script (Daily for 3-7 days)

```bash
cd downloads
python3 warmup_accounts.py
```

Warms up accounts by:
- Browsing For You page naturally
- Watching 10-20 videos per session
- Building IP trust with TikTok
- Using stealth mode throughout

### Comment Script (After warmup)

```bash
python3 comment_target_accounts.py
```

Comments on target accounts with:
- 1 comment per target per day
- Natural behavior patterns
- Stealth mode enabled
- Daily limits for new accounts

### Web UI Commenter

```bash
python3 tiktok_commenter.py
```

Then open: http://localhost:9090

Features:
- Web-based control panel
- Real-time monitoring
- Comment history
- DM automation

---

## 🛡️ Stealth Features

### What's Protected

- ✅ CDP/WebDriver detection hidden
- ✅ Natural scrolling (not mechanical)
- ✅ Human-like typing speeds
- ✅ Natural mouse movements
- ✅ Random pauses between actions
- ✅ Full video watching behavior
- ✅ Unique IP per browser
- ✅ IP warmup period

### How It Works

```python
# Automatically applied in all scripts
inject_stealth(page)  # Hides automation
natural_scroll(page)  # Human-like scrolling
watch_video_naturally(page)  # Natural viewing
natural_pause(1, 3)  # Random delays
```

See [downloads/README_STEALTH.md](downloads/README_STEALTH.md) for details.

---

## ⚙️ Configuration

### Target Accounts

Edit in `comment_target_accounts.py`:

```python
TARGET_ACCOUNTS = [
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]
```

### Settings

```python
COMMENTS_PER_ACCOUNT = 1  # Comments per video
PARALLEL_BROWSERS = 3     # Concurrent browsers
NEW_ACCOUNT_DAILY_COMMENTS = 2  # Daily limit for new accounts
```

---

## 📊 Account Status

- **Total Accounts**: 509 in CSV
- **Active (Created)**: 383 accounts
- **Browsers Setup**: 100+ with unique IPs
- **Proxy Pool**: 2,500 (65% residential)

---

## 🔧 Troubleshooting

### Accounts Getting Logged Out
- **Cause**: TikTok detecting automation
- **Fix**: Use stealth mode + warmup (3-7 days)

### Views Not Registering
- **Cause**: IP not trusted yet
- **Fix**: Complete warmup period, wait 24-48h

### "Server Error" When Posting
- **Cause**: Account is shadowbanned/flagged
- **Fix**: Stop automation, rest account 1-2 weeks

---

## 🎓 Best Practices

1. **Always warmup first** - 3-7 days of natural browsing
2. **Use unique IPs** - 1 proxy per browser (already done)
3. **Start light** - 1 comment every 2-3 days initially
4. **Monitor results** - Check view counts, account status
5. **Rest flagged accounts** - Stop automation for 1-2 weeks
6. **Upgrade proxies** - Consider full residential for best results

---

**Built for scale. Operates with stealth. Stays undetected.**

Last updated: 2026-04-16 (Stealth Mode Integration)
