# iOS Shortcut for TikTok Auto-Viewing
## No Xcode, No Mac Needed - Just Your iPhone

---

## What This Does

Automatically views TikTok videos on your iPhone:
- Opens TikTok app
- Scrolls through videos automatically
- Watches each video for 15-20 seconds
- Repeats for 30-50 videos
- Works with all 3 of your TikTok accounts

---

## Setup Instructions (5 Minutes)

### Step 1: Open Shortcuts App

1. On your iPhone, find the **Shortcuts** app (blue icon with white shortcuts symbol)
2. If you don't see it, swipe down and search "Shortcuts"
3. Tap to open

### Step 2: Create New Shortcut

1. Tap the **"+"** button (top right)
2. Tap **"Add Action"**

### Step 3: Add Actions (Follow Exactly)

**Action 1: Open TikTok**
1. In search bar, type: **"Open App"**
2. Tap **"Open App"**
3. Tap **"App"** and select **"TikTok"**
4. Tap **"Choose"**

**Action 2: Wait for TikTok to Load**
1. Tap the **"+"** button at bottom
2. Search: **"Wait"**
3. Tap **"Wait"**
4. Change time to **3 seconds**

**Action 3: Create Loop for Viewing Videos**
1. Tap the **"+"** button
2. Search: **"Repeat"**
3. Tap **"Repeat"**
4. Change number to **30** (will watch 30 videos)

**Action 4: Watch Video**
1. Inside the Repeat block, tap **"+"**
2. Search: **"Wait"**
3. Tap **"Wait"**
4. Change to **15 seconds** (watch time per video)

**Action 5: Swipe to Next Video**
1. Still inside Repeat, tap **"+"**
2. Search: **"Nothing"** (we'll use a workaround)
3. Actually, search: **"Wait"**
4. Add another **"Wait"** for **1 second**

Note: iOS Shortcuts can't directly swipe, so we'll use AssistiveTouch instead (see below)

### Step 4: Save Shortcut

1. Tap **"Done"** (top right)
2. Name it: **"TikTok Auto View"**
3. Tap **"Done"**

---

## Alternative: Better Method Using AssistiveTouch

Since iOS Shortcuts can't swipe, use this better method:

### Setup AssistiveTouch for Auto-Swipe

**Step 1: Enable AssistiveTouch**
1. Settings → Accessibility → Touch → AssistiveTouch
2. Toggle **ON**
3. A floating button appears on screen

**Step 2: Create Custom Gesture**
1. In AssistiveTouch settings, tap **"Create New Gesture"**
2. **Swipe up** on the screen (bottom to top)
3. Tap **"Stop"**
4. Tap **"Save"**
5. Name it: **"Swipe Up"**

**Step 3: Record Actions**
1. In AssistiveTouch settings, go to **"Custom Actions"**
2. Tap **"Single-Tap"**
3. Select **"Custom"** → **"Swipe Up"** (the gesture you just created)

---

## Even Simpler: Switch Control (Recommended)

This is actually the BEST method for your use case:

### Step 1: Enable Switch Control

1. **Settings** → **Accessibility** → **Switch Control**
2. Toggle **ON**
3. Tap **"Switches"**
4. Tap **"Add New Switch"**
5. Select **"Screen"**
6. Select **"Full Screen"**
7. Tap **"Select Item"**

### Step 2: Create Recipe

1. Go back to **Switch Control** settings
2. Tap **"Recipes"**
3. Tap **"Create New Recipe"**
4. Name it: **"TikTok Viewer"**

### Step 3: Record Your Actions

1. Tap **"Assign a Switch"**
2. Select **"Full Screen"**
3. Tap **"Launch Recipe at Point"**
4. Now you'll record:
   - Tap to select first video
   - Wait 15 seconds
   - Swipe up
   - Repeat

### Step 4: Set Auto-Repeat

1. In Recipe settings, set **"Auto-repeat"** to **ON**
2. Set **"Repeat Count"** to **30**

---

## EASIEST METHOD: Just Use TikTok's Auto-Play

Actually, here's the SIMPLEST approach that requires NO setup:

### Manual Semi-Automation

**For Each of Your 3 TikTok Accounts:**

1. **Open TikTok** on iPhone
2. **Search** for target account (e.g., @charlidamelio)
3. **Tap first video**
4. **Let videos auto-play** (TikTok automatically plays next video)
5. **Watch for 15-20 minutes** (TikTok will auto-play ~30-50 videos)
6. **Repeat** for each target account

TikTok already auto-plays videos if you don't swipe! Just let it run.

**Time per account:**
- Search account: 30 seconds
- Let it auto-play: 15-20 minutes
- Total: ~20 minutes per account

**For 3 accounts:**
- Total time: ~60 minutes
- Total views: 90-150 videos

---

## Workflow for Your 3 Accounts

### Account 1 (Morning)
1. Open TikTok
2. Switch to Account 1
3. Search: @charlidamelio
4. Tap first video
5. **Put phone down, let it auto-play for 20 mins**
6. Switch to @addisonre
7. Repeat
8. Switch to @bellapoarch
9. Repeat

### Account 2 (Afternoon)
Repeat same process with Account 2

### Account 3 (Evening)
Repeat same process with Account 3

---

## Summary of Options

```
┌─────────────────────┬──────────┬────────────┬─────────────┐
│ Method              │ Setup    │ Automation │ Effort/Run  │
├─────────────────────┼──────────┼────────────┼─────────────┤
│ iOS Shortcuts       │ 5 min    │ Partial    │ Medium      │
│ Switch Control      │ 10 min   │ High       │ Low         │
│ Manual Auto-Play    │ 0 min    │ None       │ Very Low    │
│ Appium (needs Xcode)│ 2 hrs    │ Full       │ Very Low    │
└─────────────────────┴──────────┴────────────┴─────────────┘
```

---

## My Recommendation

**Just use Manual Auto-Play method:**

1. No setup needed
2. TikTok auto-plays videos anyway
3. You just need to:
   - Search target account
   - Tap first video
   - Put phone down for 20 mins
   - Come back, switch to next account

**This gives you 90-150 views per day with minimal effort.**

---

## Daily Routine (30-60 Minutes Total)

**Morning (20 mins):**
- Account 1 → View @charlidamelio, @addisonre, @bellapoarch
- Put phone down, let auto-play

**Afternoon (20 mins):**
- Account 2 → Same targets
- Put phone down, let auto-play

**Evening (20 mins):**
- Account 3 → Same targets
- Put phone down, let auto-play

**Total:** 90-150 views per day across all targets

---

## Want to Track Progress?

I can create a simple Python script on your Mac that:
- Reminds you when to run each account
- Tracks daily view counts
- Schedules the routine

Would you like me to create that?
