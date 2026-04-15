# TikTok Automation Stealth Mode

Complete stealth solution to bypass TikTok's bot detection.

## 🎯 Problem Solved

TikTok was detecting and blocking automation because of:
1. ❌ CDP/WebDriver detection
2. ❌ Unnatural behavior (mechanical scrolling, fixed delays)
3. ❌ New IP addresses without warmup
4. ❌ Datacenter proxies being flagged

## ✅ Solution

This suite of scripts fixes all 4 issues:

### 📁 Files Overview

| File | Purpose |
|------|---------|
| **stealth_browsing.py** | Core stealth utilities - hides automation fingerprints |
| **warmup_accounts.py** | Daily warmup script - builds IP trust over 3-7 days |
| **comment_target_accounts.py** | Main commenter with stealth mode integrated |
| **tiktok_commenter.py** | Web UI commenter with stealth mode |
| **assign_unique_proxies_fast.py** | Assigns unique IPs to each browser |
| **test_stealth.py** | Tests if stealth mode is working |

---

## 🚀 Quick Start

### Step 1: Assign Unique Proxies (One-Time Setup)

Ensure each browser has its own unique IP:

```bash
cd downloads
python3 assign_unique_proxies_fast.py
```

**What it does:**
- Assigns 1 unique proxy per browser (no sharing)
- Filters out known datacenter IPs
- Updates all 100+ browsers automatically

---

### Step 2: Test Stealth Mode

Verify that automation is hidden:

```bash
python3 test_stealth.py
```

**Expected result:**
- Opens bot detection site
- Should show GREEN indicators (= not detected)
- `navigator.webdriver` should be `undefined`

---

### Step 3: Warmup Accounts (3-7 Days)

**IMPORTANT:** Run this daily for 3-7 days BEFORE commenting.

```bash
python3 warmup_accounts.py
```

**What it does:**
- Browses TikTok naturally (no commenting yet)
- Watches 10-20 videos per browser
- Uses stealth mode to hide automation
- Builds trust with TikTok for new IPs

**Schedule:**
- Day 1-3: Run daily (10 videos per browser)
- Day 4-7: Run daily (15 videos per browser)
- After Day 7: Ready for commenting automation

---

### Step 4: Run Commenting (After Warmup)

Once accounts are warmed up:

```bash
python3 comment_target_accounts.py
```

**Settings:**
- 1 comment per target account per day
- Natural behavior (scrolling, watching, typing)
- Stealth mode hides automation
- Daily limits for new accounts

---

## 🔧 How Stealth Mode Works

### stealth_browsing.py

Core utilities that hide automation:

```python
from stealth_browsing import inject_stealth, natural_scroll, watch_video_naturally

# Hide CDP/WebDriver detection
inject_stealth(page)

# Natural scrolling (not mechanical)
natural_scroll(page, 'down', distance=random.randint(800, 1200))

# Natural video watching with mouse movements
watch_video_naturally(page, video_duration_seconds=20)
```

**Features:**
- ✅ Hides `navigator.webdriver`
- ✅ Fakes plugins and languages
- ✅ Removes CDP runtime indicators
- ✅ Natural mouse movements
- ✅ Human-like scrolling patterns
- ✅ Random typing speeds
- ✅ Natural pauses between actions

---

## 📊 Recommended Strategy

### Phase 1: Setup (Day 0)
1. Run `assign_unique_proxies_fast.py` (one-time)
2. Verify with `test_stealth.py`

### Phase 2: Warmup (Days 1-7)
```bash
# Run daily
python3 warmup_accounts.py
```
- Day 1-3: 10 videos per browser
- Day 4-7: 15-20 videos per browser

### Phase 3: Light Automation (Days 8+)
```bash
# Start very light
python3 comment_target_accounts.py
```
- Week 1: 1 comment every 2-3 days per account
- Week 2+: 1 comment per day per account

---

## 🛡️ Anti-Detection Features

| Feature | Status |
|---------|--------|
| CDP Hidden | ✅ inject_stealth() |
| Natural Scrolling | ✅ natural_scroll() |
| Natural Typing | ✅ Random delays 50-150ms |
| Natural Mouse Movement | ✅ Curved movements |
| Natural Video Watching | ✅ watch_video_naturally() |
| Random Pauses | ✅ natural_pause() |
| Unique IPs | ✅ 1 proxy per browser |
| IP Warmup | ✅ warmup_accounts.py |

---

## ⚠️ Important Notes

1. **Patience is Key**
   - Don't rush warmup period
   - TikTok needs 3-7 days to trust new IPs
   - Start with very light activity

2. **Proxy Quality Matters**
   - Residential > Datacenter
   - Current pool is ~65% residential
   - Consider upgrading to full residential

3. **Account Flags**
   - If you see "server error" when posting = account is flagged
   - Stop automation for that account
   - Let it rest for 1-2 weeks

4. **View Counts**
   - Views may not register immediately
   - Can take 24-48 hours after warmup
   - Focus on account health over metrics

---

## 🔍 Troubleshooting

### Views Not Registering
- ✅ Ensure warmup completed (3-7 days)
- ✅ Check stealth mode is working (test_stealth.py)
- ✅ Verify unique proxies assigned
- ⏳ Wait 24-48 hours after warmup

### "Server Error" When Commenting
- Account is flagged/shadowbanned
- Stop automation for that account
- Rest for 1-2 weeks
- Resume with lighter activity

### Accounts Getting Logged Out
- Datacenter IPs being detected
- Need better proxies (residential)
- Warmup period may be insufficient

---

## 📝 Development

All scripts use:
- **Playwright** for browser automation
- **AdsPower API** for multi-account management
- **Stealth techniques** to hide automation
- **Natural behavior patterns** to mimic humans

---

## 🎓 Best Practices

1. **Always warmup first** (3-7 days)
2. **Use unique IPs** (1 per account)
3. **Start light** (1 action every 2-3 days)
4. **Monitor results** (view counts, flags)
5. **Rest flagged accounts** (1-2 weeks)
6. **Gradually increase** (after account trust is built)

---

## 📞 Support

For issues or questions, check:
- README files in each script
- Code comments
- Test scripts for verification

---

**Built with stealth. Operates naturally. Stays undetected.**
