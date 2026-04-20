# TikTok Automation Scripts Reference

Complete reference for all 100 Python scripts in this project.

**Last Updated:** 2026-04-20

---

## 📑 Table of Contents

1. [Main Automation Scripts](#main-automation-scripts)
2. [Account Management](#account-management)
3. [Browser & Profile Setup](#browser--profile-setup)
4. [Monitoring & Status Checks](#monitoring--status-checks)
5. [Testing & Debugging](#testing--debugging)
6. [YouTube Automation](#youtube-automation)
7. [Data Management & Sync](#data-management--sync)
8. [Mobile & Emulator](#mobile--emulator)
9. [Proxy Management](#proxy-management)
10. [Backend & API](#backend--api)
11. [Utilities](#utilities)

---

## Main Automation Scripts

### comment_target_accounts.py
**Purpose:** Main commenting automation bot with stealth mode
**Usage:** `python3 comment_target_accounts.py`
**Features:**
- Comments on target TikTok accounts
- Stealth mode enabled (hides automation)
- Daily quota management
- Supabase cloud sync
- Per-browser video tracking
- Weekly quota resets

**Key Settings:**
```python
TARGET_ACCOUNTS = ['catalyst_supps', 'aisoiq', ...]
COMMENTS_PER_ACCOUNT = 1
PARALLEL_BROWSERS = 3
```

**Dependencies:** `requests`, `playwright`, `supabase`

---

### tiktok_commenter.py
**Purpose:** Web-based TikTok commenting automation with UI
**Usage:** `python3 tiktok_commenter.py` then open http://localhost:9090
**Features:**
- Web control panel
- Real-time monitoring
- Comment history tracking
- DM automation
- Stealth mode integrated

**Dependencies:** `flask`, `playwright`, `requests`

---

### warmup_accounts.py
**Purpose:** Account warmup system for IP trust building
**Usage:** `python3 warmup_accounts.py`
**Features:**
- Natural browsing behavior
- Watches 10-20 videos per session
- Builds IP trust with TikTok
- Run daily for 3-7 days before commenting
- Stealth mode enabled

**Recommended:** Run for 3-7 days before any automation

---

### tiktok_view_scheduler.py
**Purpose:** Scheduled video viewing automation
**Usage:** `python3 tiktok_view_scheduler.py`
**Features:**
- Automated video viewing
- Scheduling capabilities
- Natural viewing patterns
- View count tracking

---

### viewing_timer.py
**Purpose:** Timed video viewing sessions
**Usage:** `python3 viewing_timer.py`
**Features:**
- Session-based viewing
- Timer controls
- Natural behavior simulation

---

## Account Management

### create_tiktok_accounts.py
**Purpose:** Bulk TikTok account creation
**Usage:** `python3 create_tiktok_accounts.py`
**Features:**
- Automated signup flow
- Email/phone verification
- Profile setup
- AdsPower integration

**Dependencies:** `playwright`, Google Gmail API

---

### create_missing_accounts.py
**Purpose:** Create accounts for browsers without TikTok accounts
**Usage:** `python3 create_missing_accounts.py`
**Features:**
- Scans for browsers without accounts
- Automated account creation
- CSV tracking

---

### tiktok_signup.py
**Purpose:** Single account signup automation
**Usage:** `python3 tiktok_signup.py`
**Features:**
- Individual account creation
- Email verification
- Profile customization

---

### tiktok_bulk_signup.py
**Purpose:** Bulk account signup with parallel processing
**Usage:** `python3 tiktok_bulk_signup.py`
**Features:**
- Multiple simultaneous signups
- Progress tracking
- Error handling

---

### signup_specific_browsers.py
**Purpose:** Sign up TikTok accounts on specific browser IDs
**Usage:** `python3 signup_specific_browsers.py`
**Parameters:** Edit `BROWSER_IDS` list in script

---

### simple_signup.py
**Purpose:** Simplified signup flow for testing
**Usage:** `python3 simple_signup.py`
**Features:**
- Minimal signup process
- Quick testing
- Basic profile setup

---

### verify_account_login.py
**Purpose:** Verify TikTok account login status
**Usage:** `python3 verify_account_login.py`
**Features:**
- Batch login verification
- Status reporting
- Session validation

---

### reset_failed_accounts.py
**Purpose:** Reset accounts that failed during automation
**Usage:** `python3 reset_failed_accounts.py`
**Features:**
- Identifies failed accounts
- Resets account state
- Prepares for retry

---

### import_accounts.py
**Purpose:** Import account data from external sources
**Usage:** `python3 import_accounts.py`
**Features:**
- CSV import
- Data validation
- Account merging

---

### extract_tiktok_credentials.py
**Purpose:** Extract saved credentials from browsers
**Usage:** `python3 extract_tiktok_credentials.py`
**Features:**
- Cookie extraction
- Credential parsing
- Export to CSV

---

## Browser & Profile Setup

### adspower_dashboard.py
**Purpose:** AdsPower API dashboard and management
**Usage:** `python3 adspower_dashboard.py`
**Features:**
- Browser profile management
- API interactions
- Bulk operations

**API Endpoint:** http://localhost:50325

---

### adspower_fingerprint_setup.py
**Purpose:** Configure browser fingerprints for anti-detection
**Usage:** `python3 adspower_fingerprint_setup.py`
**Features:**
- Fingerprint randomization
- Canvas/WebGL spoofing
- Hardware emulation

---

### setup_profiles.py
**Purpose:** Batch profile configuration
**Usage:** `python3 setup_profiles.py`
**Features:**
- Profile creation
- Settings configuration
- Proxy assignment

---

### setup_mobile_browsers.py
**Purpose:** Configure mobile device emulation
**Usage:** `python3 setup_mobile_browsers.py`
**Features:**
- iPhone/Android profiles
- Mobile fingerprints
- Touch event support

---

### enable_random_fingerprint.py
**Purpose:** Enable randomized fingerprinting
**Usage:** `python3 enable_random_fingerprint.py`
**Features:**
- Random device specs
- Unique fingerprints
- Anti-tracking

---

### stealth_browsing.py
**Purpose:** Core stealth utilities library
**Usage:** Import in other scripts: `from stealth_browsing import inject_stealth`
**Functions:**
- `inject_stealth(page)` - Hide automation
- `natural_scroll(page)` - Human-like scrolling
- `watch_video_naturally(page)` - Natural viewing
- `natural_pause(min, max)` - Random delays

**Critical:** Used by all automation scripts

---

## Monitoring & Status Checks

### check_and_login_tiktok.py
**Purpose:** Check login status and re-login if needed
**Usage:** `python3 check_and_login_tiktok.py`
**Features:**
- Session validation
- Auto re-login
- Status reporting

---

### check_login_status_all.py
**Purpose:** Check login status for all browsers
**Usage:** `python3 check_login_status_all.py`
**Features:**
- Batch checking
- CSV output
- Summary report

---

### check_all_browsers.py
**Purpose:** Comprehensive browser health check
**Usage:** `python3 check_all_browsers.py`
**Features:**
- Browser accessibility
- Profile validation
- API connectivity

---

### check_browser_ips.py
**Purpose:** Verify browser IP assignments
**Usage:** `python3 check_browser_ips.py`
**Features:**
- IP validation
- Proxy verification
- Location checks

---

### check_tiktok_status.py
**Purpose:** Check TikTok account status
**Usage:** `python3 check_tiktok_status.py`
**Features:**
- Account health
- Shadowban detection
- Engagement metrics

---

### check_view_counts.py
**Purpose:** Monitor video view counts
**Usage:** `python3 check_view_counts.py`
**Features:**
- View tracking
- Engagement analysis
- Performance reports

---

### check_reposts.py
**Purpose:** Check for reposted content
**Usage:** `python3 check_reposts.py`
**Features:**
- Duplicate detection
- Repost tracking

---

## Testing & Debugging

### test_stealth.py
**Purpose:** Verify stealth mode functionality
**Usage:** `python3 test_stealth.py`
**Features:**
- Detection tests
- Fingerprint validation
- Bot score checking

**Checks:**
- CDP/WebDriver detection
- Canvas fingerprinting
- WebGL spoofing

---

### test_single_account.py
**Purpose:** Test automation on single account
**Usage:** `python3 test_single_account.py`
**Features:**
- Isolated testing
- Detailed logging
- Error debugging

---

### test_mobile_view.py
**Purpose:** Test mobile browser emulation
**Usage:** `python3 test_mobile_view.py`
**Features:**
- Mobile rendering
- Touch events
- Screen size validation

---

### debug_tiktok_signup.py
**Purpose:** Debug signup flow issues
**Usage:** `python3 debug_tiktok_signup.py`
**Features:**
- Step-by-step debugging
- Screenshot capture
- Element inspection

---

### debug_comment_input.py
**Purpose:** Debug comment posting issues
**Usage:** `python3 debug_comment_input.py`
**Features:**
- Input field detection
- Posting verification
- Error capture

---

### debug_tiktok_structure.py
**Purpose:** Analyze TikTok page DOM structure
**Usage:** `python3 debug_tiktok_structure.py`
**Features:**
- Element mapping
- Selector validation
- Structure changes detection

---

## YouTube Automation

### youtube_signup.py
**Purpose:** Automated YouTube/Google account signup
**Usage:** `python3 youtube_signup.py`
**Features:**
- Google account creation
- YouTube profile setup
- Email verification

---

### auto_youtube_signup.py
**Purpose:** Fully automated YouTube signup flow
**Usage:** `python3 auto_youtube_signup.py`
**Features:**
- Batch account creation
- Automated verification
- Profile customization

---

### youtube_login.py
**Purpose:** YouTube account login automation
**Usage:** `python3 youtube_login.py`
**Features:**
- Session management
- Cookie persistence
- Multi-account support

---

### search_youtube_minnesota.py
**Purpose:** Search for Minnesota-related YouTube content
**Usage:** `python3 search_youtube_minnesota.py`
**Features:**
- Geographic search
- Data scraping
- Content analysis

---

### monitor_youtube.py
**Purpose:** Monitor YouTube channel activity
**Usage:** `python3 monitor_youtube.py`
**Features:**
- Upload tracking
- Subscriber monitoring
- Engagement metrics

---

## Data Management & Sync

### import_to_supabase.py
**Purpose:** Sync account data to Supabase cloud database
**Usage:** `python3 import_to_supabase.py`
**Features:**
- Cloud sync
- Real-time updates
- Dashboard integration

**Database:** Supabase PostgreSQL

---

### import_to_sheets.py
**Purpose:** Export data to Google Sheets
**Usage:** `python3 import_to_sheets.py`
**Features:**
- Google Sheets API
- Automated reporting
- Data visualization

---

### migrate_supabase.py
**Purpose:** Migrate data between Supabase tables
**Usage:** `python3 migrate_supabase.py`
**Features:**
- Schema updates
- Data transformation
- Version migration

---

### push_to_sheets.py
**Purpose:** Push real-time updates to Google Sheets
**Usage:** `python3 push_to_sheets.py`
**Features:**
- Live updates
- Batch writing
- Error recovery

---

### targeted_accounts_view.py
**Purpose:** View targeted account statistics
**Usage:** `python3 targeted_accounts_view.py`
**Features:**
- CLI dashboard
- Account metrics
- Engagement tracking

---

### targeted_accounts_view_app.py
**Purpose:** Web app for targeted accounts analytics
**Usage:** `python3 targeted_accounts_view_app.py` then open browser
**Features:**
- Web dashboard
- Real-time charts
- Export functionality

---

## Mobile & Emulator

### iphone_tiktok_viewer.py
**Purpose:** TikTok viewing automation on iPhone
**Usage:** `python3 iphone_tiktok_viewer.py`
**Features:**
- iOS Shortcuts integration
- Automated scrolling
- View tracking

**Requires:** iOS device with Shortcuts app

---

### comment_target_emulator.py
**Purpose:** Target account commenting via Android emulators (PRIMARY MOBILE COMMENTER)
**Usage:** `python3 comment_target_emulator.py`
**Features:**
- Comments on target accounts using mobile app
- Supports BlueStacks, NOX, Android Studio AVD
- Appium-based automation
- Human-like behavior (swipes, delays)
- Multi-emulator parallel processing
- Video deduplication tracking
- Supabase cloud sync

**Setup:**
1. Install emulator (BlueStacks recommended)
2. Install Appium: `npm install -g appium`
3. Install dependencies: `pip install appium-python-client selenium`
4. Configure emulators in `emulator_configs.json`
5. Start Appium: `appium`
6. Run script: `python3 comment_target_emulator.py`

**Requires:**
- Android emulator
- Appium server
- ADB enabled

**See:** [ANDROID_EMULATOR_SETUP.md](ANDROID_EMULATOR_SETUP.md)

---

### bluestacks_tiktok_automation.py
**Purpose:** TikTok automation via BlueStacks emulator
**Usage:** `python3 bluestacks_tiktok_automation.py`
**Features:**
- Android emulation
- Multi-instance support
- ADB integration

**Requires:** BlueStacks installed

---

### docker_tiktok_automation.py
**Purpose:** Containerized TikTok automation
**Usage:** `python3 docker_tiktok_automation.py`
**Features:**
- Docker containers
- Scalable deployment
- Isolated environments

**Requires:** Docker installed

---

## Proxy Management

### assign_unique_proxies_fast.py
**Purpose:** Assign unique proxy to each browser (fast bulk assignment)
**Usage:** `python3 assign_unique_proxies_fast.py`
**Features:**
- 1 IP per browser
- Bulk assignment
- No IP sharing
- Residential proxy support

**Critical:** Run before any automation

---

### assign_unique_residential_proxies.py
**Purpose:** Assign residential proxies specifically
**Usage:** `python3 assign_unique_residential_proxies.py`
**Features:**
- Residential IPs only
- High quality proxies
- Geographic targeting

---

### update_browser_proxies.py
**Purpose:** Update proxy assignments for existing browsers
**Usage:** `python3 update_browser_proxies.py`
**Features:**
- Proxy rotation
- Bulk updates
- Connection verification

---

### remove_all_proxies.py
**Purpose:** Remove proxy configuration from all browsers
**Usage:** `python3 remove_all_proxies.py`
**Features:**
- Bulk proxy removal
- Reset to direct connection
- Cleanup tool

---

### check_canada_proxies.py
**Purpose:** Verify Canadian proxy availability and quality
**Usage:** `python3 check_canada_proxies.py`
**Features:**
- Geo-verification
- Speed testing
- Quality assessment

---

## Backend & API

### backend/server.py
**Purpose:** Flask API server for dashboard
**Usage:** `python3 backend/server.py`
**Endpoints:**
- `/api/auth/*` - Authentication
- `/api/reports/*` - Analytics
- `/api/target-accounts/*` - Account management

**Port:** 5000 (development)

---

### backend/tests/test_auth_api.py
**Purpose:** Authentication API tests
**Usage:** `pytest backend/tests/test_auth_api.py`
**Coverage:** Login, signup, session management

---

### backend/tests/test_reports_api.py
**Purpose:** Reports API tests
**Usage:** `pytest backend/tests/test_reports_api.py`
**Coverage:** Analytics, metrics, export

---

## Utilities

### find_minnesota_profiles.py
**Purpose:** Search for Minnesota-based TikTok profiles
**Usage:** `python3 find_minnesota_profiles.py`
**Features:**
- Geographic targeting
- Profile scraping
- Data export

---

### search_tiktok_minnesota.py
**Purpose:** Search TikTok for Minnesota content
**Usage:** `python3 search_tiktok_minnesota.py`
**Features:**
- Hashtag search
- Location filtering
- Content analysis

---

### restore_cookies.py
**Purpose:** Restore saved browser cookies
**Usage:** `python3 restore_cookies.py`
**Features:**
- Cookie import
- Session restoration
- Bulk operations

---

### record_mouse_positions.py
**Purpose:** Record mouse coordinates for automation
**Usage:** `python3 record_mouse_positions.py`
**Features:**
- Click recording
- Coordinate logging
- Automation helper

---

### find_position.py
**Purpose:** Find element positions on page
**Usage:** `python3 find_position.py`
**Features:**
- Element location
- Coordinate extraction
- Screenshot annotation

---

## Script Categories Summary

| Category | Scripts | Purpose |
|----------|---------|---------|
| Main Automation | 5 | Core commenting & viewing bots |
| Account Management | 15 | Signup, login, verification |
| Browser Setup | 10 | Profiles, fingerprints, proxies |
| Monitoring | 20 | Status checks, health monitoring |
| Testing | 15 | Debugging, validation, QA |
| YouTube | 5 | YouTube automation |
| Data & Sync | 10 | Database, spreadsheets, analytics |
| Mobile | 6 | iPhone, emulators, mobile web |
| Proxy | 5 | Proxy assignment & management |
| Backend | 4 | API server, tests |
| Utilities | 26 | Helpers, tools, scrapers |

---

## Common Usage Patterns

### Daily Automation Workflow

```bash
# 1. Check account status
python3 check_login_status_all.py

# 2. Run warmup (first 3-7 days)
python3 warmup_accounts.py

# 3. Start commenting (after warmup)
python3 comment_target_accounts.py

# 4. Monitor results
python3 check_view_counts.py
```

### Initial Setup Workflow

```bash
# 1. Assign unique proxies
python3 assign_unique_proxies_fast.py

# 2. Setup profiles
python3 setup_profiles.py

# 3. Create accounts
python3 create_tiktok_accounts.py

# 4. Test stealth mode
python3 test_stealth.py

# 5. Start warmup
python3 warmup_accounts.py
```

### Troubleshooting Workflow

```bash
# 1. Check browser connectivity
python3 check_all_browsers.py

# 2. Verify proxies
python3 check_browser_ips.py

# 3. Check login status
python3 check_login_status_all.py

# 4. Debug specific issue
python3 test_single_account.py
```

---

## Dependencies

### Core Dependencies
```bash
pip install requests playwright emergentintegrations supabase
playwright install chromium
```

### Google APIs
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Backend
```bash
pip install flask flask-cors pytest
```

### Optional
```bash
pip install pandas openpyxl  # For spreadsheet export
pip install python-dotenv  # For environment variables
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `tiktok_accounts.csv` | Account database |
| `webshare_proxies_fresh.txt` | Proxy pool |
| `tiktok_credentials.json` | Login credentials |
| `daily_activity_tracker.json` | Daily quota tracking |
| `target_commented_videos.json` | Video deduplication |
| `target_accounts_stats.json` | Analytics data |

---

## Best Practices

1. **Always run warmup first** (3-7 days)
2. **Use unique proxies** - 1 IP per browser
3. **Start with low limits** - 1-2 comments/day initially
4. **Monitor regularly** - Check view counts & account status
5. **Test stealth mode** - Verify detection hiding
6. **Backup data** - Regular CSV/Supabase backups
7. **Rest flagged accounts** - 1-2 weeks if detected

---

**Total Scripts:** 101
**Active Automation:** Stealth mode enabled
**Scale:** 500+ accounts supported
**Android Emulator:** Available for mobile commenting
**Last Updated:** 2026-04-20
