# New TikTok Account Setup Guide

**Complete step-by-step process for setting up and warming up new TikTok accounts with stealth mode.**

---

## ⚡ Quick Overview

| Timeline | Action | Duration |
|----------|--------|----------|
| **Day 0** | Setup proxies | One-time (15 min) |
| **Days 1-7** | Daily warmup | 7 days × 15 min/day |
| **Day 7** | Test one account | 10 min |
| **Day 8+** | Start automation | Ongoing |

**Total setup time:** ~2 hours 30 minutes over 8 days
**Critical requirement:** DO NOT skip the warmup period

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ AdsPower installed and running (port 50325)
- ✅ Browser profiles created in AdsPower
- ✅ TikTok accounts created (via email)
- ✅ Proxy list (webshare_proxies_fresh.txt)
- ✅ Python dependencies installed

### Install Dependencies

```bash
pip install requests playwright
playwright install chromium

# Optional: For Gmail verification
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 🚀 Step-by-Step Setup Process

### **Day 0: Initial Setup**

#### Step 1.1: Assign Unique Proxies (One-Time)

**Why:** Each browser needs its own unique IP to avoid TikTok's mass ban detection.

```bash
cd downloads
python3 assign_unique_proxies_fast.py
```

**What happens:**
- Loads 2,500 proxies from `webshare_proxies_fresh.txt`
- Filters out 250 known datacenter IPs
- Assigns 1 unique proxy to each browser
- No proxy sharing = lower detection risk

**Expected output:**
```
✓ [1/100] tt505 → 198.23.128.182:5810
✓ [2/100] tt504 → 154.6.121.247:6214
...
COMPLETE: 100 updated, 0 failed
Unique proxies used: 100
```

**Time required:** 5-10 minutes

---

#### Step 1.2: Verify Stealth Mode (Optional but Recommended)

**Why:** Confirm that automation is properly hidden from TikTok's detection.

```bash
python3 test_stealth.py
```

**What to check:**
- Browser opens to `bot.sannysoft.com`
- Look for **GREEN** indicators (= not detected)
- `navigator.webdriver` should show as `undefined`
- Most tests should pass

**If you see RED:**
- Stealth mode may not be working
- Check that stealth_browsing.py is in the same folder
- Try restarting the script

**Time required:** 2-3 minutes

---

### **Days 1-7: Critical Warmup Period**

⚠️ **THIS IS THE MOST IMPORTANT STEP - DO NOT SKIP**

#### Why Warmup is Critical

TikTok's algorithm flags:
- ❌ New IPs that immediately start commenting
- ❌ Accounts that don't browse organically first
- ❌ Sudden activity spikes from fresh accounts

Warmup makes your accounts look like real users by:
- ✅ Browsing For You page naturally
- ✅ Watching full videos
- ✅ Scrolling with human-like patterns
- ✅ Building trust with TikTok's algorithm

---

#### Daily Warmup Routine

**Days 1-3:** Light warmup
```bash
cd downloads
python3 warmup_accounts.py
```

**When prompted:**
- How many browsers? `20-30` (start small)
- Videos per browser? `10`

**Days 4-7:** Heavier warmup
```bash
python3 warmup_accounts.py
```

**When prompted:**
- How many browsers? `50-100` (increase gradually)
- Videos per browser? `15-20`

---

#### What Warmup Does

For each browser:
1. Opens TikTok with stealth mode enabled
2. Checks login status
3. Browses For You page naturally:
   - Watches 10-20 videos
   - Scrolls naturally (not mechanical)
   - Random mouse movements
   - Natural pauses between videos
4. Sometimes visits trending page (random behavior)
5. Logs activity to `warmup_log.json`

**Time per session:** 10-20 minutes
**Frequency:** DAILY for 7 days minimum

---

#### Warmup Best Practices

✅ **DO:**
- Run at different times each day (e.g., 10am, 2pm, 8pm)
- Vary the number of browsers (20-30 one day, 50-60 next)
- Let browsers run completely (don't interrupt)
- Check warmup_log.json to track progress

❌ **DON'T:**
- Skip days (breaks the trust-building)
- Run all 100 browsers at once (too suspicious)
- Comment, like, or follow during warmup
- Close browsers mid-session

---

### **Day 7: Test One Account**

Before starting automation on all accounts, test ONE browser manually.

#### Manual Testing Process

1. **Open ONE browser in AdsPower**
   ```bash
   # Find a browser that completed all 7 days of warmup
   # Example: tt406, tt407, etc.
   ```

2. **Navigate to TikTok**
   - Go to a target account (e.g., @catalyst_supps)
   - Click on their latest video

3. **Test Commenting**
   - Try to leave a comment manually
   - Press the Post button

4. **Check for Issues**

   **✅ GOOD SIGNS:**
   - Comment posts successfully
   - No "server error" message
   - No forced logout
   - Account feels responsive

   **❌ BAD SIGNS:**
   - "Something went wrong with the server" error
   - Account logs out automatically
   - Can't click comment button
   - Page doesn't load properly

   **If you see bad signs:**
   - Continue warmup for 3-5 MORE days
   - Account needs more trust-building time
   - Consider getting better proxies (residential)

5. **Check View Counts (24h later)**
   - After 24 hours, check if the video view registered
   - Go to your profile → check engagement stats
   - If views don't register = need more warmup

---

### **Day 8+: Start Light Automation**

Once manual test passes, begin VERY light automation.

#### Week 1: Ultra-Light Activity

```bash
cd downloads
python3 comment_target_accounts.py
```

**Settings for Week 1:**
- Run EVERY 2-3 DAYS (not daily!)
- Process only 10-20 browsers per run
- Monitor for "server error" messages

**Current script settings:**
```python
COMMENTS_PER_ACCOUNT = 1  # 1 comment per target per day
NEW_ACCOUNT_DAILY_COMMENTS = 2  # Max 2 comments total per day for new accounts
```

**What this means:**
- Each browser comments on max 2 target accounts per day
- Each target gets 1 comment per browser per day
- New accounts automatically limited by script

---

#### Week 2+: Gradual Increase

If Week 1 goes well (no bans, views register):

```bash
# Run daily instead of every 2-3 days
python3 comment_target_accounts.py
```

**Gradually increase:**
- Week 2: Run daily
- Week 3: Process 30-50 browsers per run
- Week 4+: Process all 100 browsers

**Monitor for:**
- "Server error" messages = account flagged
- Views not registering = IP not trusted
- Forced logouts = account banned

---

## 📊 Your Account Status

### Current Setup
- **Total accounts in CSV:** 509
- **Active (created):** 383
- **Browsers with unique IPs:** 100
- **Proxy pool:** 2,500 (65% residential, 35% datacenter)

### Recommended Approach

#### Option 1: Focus on 100 Browsers (Recommended)
1. Warmup all 100 browsers (Days 1-7)
2. Start automation with these 100 (Day 8+)
3. Monitor which accounts perform best
4. Phase out underperforming accounts
5. Scale the working 100 accounts

#### Option 2: Full 383 Accounts (Advanced)
1. Get 283 more unique residential IPs
2. Assign to remaining browsers
3. Warmup in batches of 50-100
4. Gradually roll out automation

**Our recommendation:** Start with Option 1 (100 browsers)

---

## 🎯 Target Accounts

The script currently targets these accounts:

```python
TARGET_ACCOUNTS = [
    'catalyst_supps',
    'aisoiq',
    'lifeadventuresafterfifty',
    'ventur_3',
    'thehouseofgracehuxley'
]
```

**Behavior:**
- Each browser comments on each target ONCE per day
- Comments on latest video only
- Natural delays between actions
- Stealth mode enabled throughout

---

## ⚙️ Configuration Options

### Adjust Comment Frequency

Edit `comment_target_accounts.py`:

```python
# Line 45-47: New account limits
NEW_ACCOUNT_DAYS = 30  # Days to treat account as "new"
NEW_ACCOUNT_DAILY_FOLLOWS = 2  # Max follows per day for new accounts
NEW_ACCOUNT_DAILY_COMMENTS = 2  # Max comments per day for new accounts

# Line 241-244: General settings
COMMENTS_PER_ACCOUNT = 1  # Comments per video
PARALLEL_BROWSERS = 3  # Concurrent browsers
```

### Change Target Accounts

Edit `comment_target_accounts.py` line 233-238:

```python
TARGET_ACCOUNTS = [
    'your_target_1',
    'your_target_2',
    'your_target_3',
]
```

### Customize Comments

Edit `comment_target_accounts.py` line 247+:

```python
NICHE_COMMENTS = {
    'fitness': [
        'Love the gains content!',
        'Great workout tips!',
    ],
    'default': [
        'Love this!',
        'Great content!',
    ]
}
```

---

## 🔍 Troubleshooting

### Issue: "Something wrong with the server" error

**Cause:** Account is flagged/shadowbanned
**Solution:**
1. Stop automation for that account
2. Rest for 1-2 weeks
3. Resume with lighter activity (1 comment every 3-4 days)

---

### Issue: Views not registering

**Cause:** IP not trusted yet
**Solution:**
1. Continue warmup for 3-5 more days
2. Wait 24-48 hours after warmup
3. Consider upgrading to residential proxies

---

### Issue: Accounts logging out automatically

**Cause:** TikTok detecting automation
**Solution:**
1. Verify stealth mode is working (`test_stealth.py`)
2. Ensure warmup was completed (7 days)
3. Check proxy quality (datacenter IPs more likely to be flagged)
4. Consider getting residential proxies

---

### Issue: "Failed to open browser"

**Cause:** AdsPower not running or browser not found
**Solution:**
1. Check AdsPower is running (port 50325)
2. Verify browser profile exists
3. Try restarting AdsPower

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `warmup_log.json` | Tracks warmup sessions per browser |
| `daily_target_comments.json` | Tracks comments per target per day |
| `target_commented_videos.json` | Prevents duplicate comments |
| `account_creation_dates.json` | Determines new vs established accounts |
| `daily_activity_tracker.json` | Tracks daily comment/follow counts |

**Location:** All files are created in the `downloads/` folder

---

## ⚠️ Critical Rules

### For New Accounts (< 30 days old):

✅ **ALWAYS:**
- Complete 7-day warmup before commenting
- Start with 1 comment every 2-3 days
- Use unique IPs (no sharing)
- Monitor for "server error"
- Rest flagged accounts 1-2 weeks

❌ **NEVER:**
- Skip warmup period
- Comment immediately after creating account
- Share IPs between browsers
- Ignore warning messages
- Run automation without testing first

---

## 🎓 Advanced Tips

### Maximizing Account Longevity

1. **Diversify Activity**
   - Occasionally browse without commenting
   - Watch full videos sometimes
   - Mix up comment times

2. **Proxy Quality Matters**
   - Residential > Datacenter
   - Consider upgrading from Webshare
   - Philippines residential IPs ideal (if using PH phones)

3. **Account Age Helps**
   - Older accounts = more trusted
   - Let accounts age naturally
   - Don't rush to max volume

4. **Monitor and Adapt**
   - Track which accounts work best
   - Phase out problematic ones
   - Focus on high-performers

---

## 📈 Success Metrics

### Week 1 Goals
- ✅ All 100 browsers complete warmup
- ✅ Test account posts successfully
- ✅ No "server error" messages
- ✅ Views register within 24-48h

### Month 1 Goals
- ✅ 70-80% of accounts commenting successfully
- ✅ Views consistently registering
- ✅ No mass bans or logouts
- ✅ Accounts building engagement

### Long-Term Goals
- ✅ Stable automation for months
- ✅ Consistent comment delivery
- ✅ Low ban rate (<5%)
- ✅ Natural-looking engagement

---

## 📞 Quick Reference Commands

```bash
# Setup (Day 0)
python3 assign_unique_proxies_fast.py
python3 test_stealth.py

# Warmup (Days 1-7)
python3 warmup_accounts.py

# Automation (Day 8+)
python3 comment_target_accounts.py
```

---

## 🎯 Your 2-Week Action Plan

| Day | Task | Command | Notes |
|-----|------|---------|-------|
| 0 | Setup proxies | `assign_unique_proxies_fast.py` | One-time setup |
| 0 | Test stealth | `test_stealth.py` | Verify automation hidden |
| 1 | Warmup (light) | `warmup_accounts.py` | 20-30 browsers, 10 videos |
| 2 | Warmup (light) | `warmup_accounts.py` | 20-30 browsers, 10 videos |
| 3 | Warmup (light) | `warmup_accounts.py` | 30-50 browsers, 10 videos |
| 4 | Warmup (medium) | `warmup_accounts.py` | 50-70 browsers, 15 videos |
| 5 | Warmup (medium) | `warmup_accounts.py` | 50-70 browsers, 15 videos |
| 6 | Warmup (heavy) | `warmup_accounts.py` | 70-100 browsers, 20 videos |
| 7 | Warmup + TEST | `warmup_accounts.py` + manual test | 100 browsers, 20 videos |
| 8 | Light automation | `comment_target_accounts.py` | 10-20 browsers only |
| 10 | Light automation | `comment_target_accounts.py` | 10-20 browsers |
| 12 | Light automation | `comment_target_accounts.py` | 20-30 browsers |
| 14 | Light automation | `comment_target_accounts.py` | 30-50 browsers |
| 15+ | Regular automation | `comment_target_accounts.py` | Daily, all browsers |

---

## ✅ Success Checklist

Before starting automation, verify:

- [ ] All browsers have unique proxies assigned
- [ ] Stealth mode test passed (green indicators)
- [ ] Completed 7 days of daily warmup
- [ ] Manual test on 1 account succeeded
- [ ] No "server error" when posting manually
- [ ] Views registered within 24-48h on test
- [ ] Accounts not logging out automatically
- [ ] warmup_log.json shows 7 sessions per browser

If ALL boxes checked → Ready for automation ✅
If ANY box unchecked → Continue warmup ⏸️

---

**Remember:** Patience is key. The 7-day warmup period is the difference between accounts that last months vs accounts that get banned in days.

**Built with patience. Operated with stealth. Sustained for months.**
