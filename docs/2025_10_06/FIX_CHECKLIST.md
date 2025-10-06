# STAGING DEPLOYMENT FIX - IMMEDIATE ACTION CHECKLIST

**Date:** 2025-10-06
**Issue:** Staging service not deploying new code with psycopg2 driver fix
**Status:** Code is ready, deployment configuration issue

---

## ✅ VERIFICATION COMPLETED

- ✅ Code is on staging branch (commit: 3396375)
- ✅ Local and remote branches in sync
- ✅ Diagnostic logging present in code
- ✅ render.yaml configured for staging branch
- ❌ **Render is NOT deploying the new code**

---

## 🎯 ROOT CAUSE (90% Confident)

**Render Dashboard branch setting is NOT set to 'staging'**

The staging service was likely created **manually** (not from blueprint), which means:
- render.yaml settings are **IGNORED**
- Dashboard branch setting controls what gets deployed
- Dashboard is probably deploying from `main` instead of `staging`

---

## 🔧 FIX INSTRUCTIONS - FOLLOW EXACTLY

### Step 1: Open Render Dashboard

1. Go to: **https://dashboard.render.com**
2. Log in with your credentials
3. Find service: **marketedge-platform-staging**
4. Click on the service to open it

---

### Step 2: Check Branch Setting

1. Click the **"Settings"** tab (top navigation)
2. Scroll to **"Build & Deploy"** section
3. Look for field labeled **"Branch"**

**What you're looking for:**
```
Branch: [current-value-here]
```

---

### Step 3: Identify the Problem

**IF Branch shows:** `staging`
→ Branch is correct, proceed to Step 4 (cache issue)

**IF Branch shows:** `main` or anything else
→ **THIS IS THE PROBLEM!** This explains why new code isn't deploying

---

### Step 4: Fix the Branch Setting

1. Click **"Edit"** or directly in the Branch field
2. Change value to: **`staging`**
3. Click **"Save Changes"** button

**IMPORTANT:** This will trigger an automatic deployment!

---

### Step 5: Clear Build Cache

Even if branch was correct, we need to clear the build cache:

1. Look for **"Manual Deploy"** button (usually top right)
2. Click **"Manual Deploy"**
3. Select option: **"Clear build cache & deploy"**
4. Confirm the deployment

---

### Step 6: Monitor Deployment Logs

1. Click **"Logs"** tab in Render Dashboard
2. Watch the deployment logs in real-time
3. **Look for these EXACT lines** (within first 30 seconds):

```
[DATABASE-INIT] Starting database initialization, DATABASE_URL scheme: postgres
[SCHEME-FIX] original=postgres async=postgresql+asyncpg
[SCHEME-FIX-DETAILS] Transformation applied: postgres -> postgresql+asyncpg
```

---

### Step 7: Verify Success

**✅ SUCCESS if you see:**
- All three diagnostic log lines above
- NO `ModuleNotFoundError: No module named 'psycopg2'` error
- Message: `Application startup complete.`

**❌ STILL BROKEN if you see:**
- Old error: `ModuleNotFoundError: No module named 'psycopg2'`
- NO diagnostic log lines
- Deployment using wrong commit SHA

---

## 🚨 IF FIX DOESN'T WORK

### Alternative Fix: Force Empty Commit

Run from your local terminal:

```bash
cd /Users/matt/Sites/MarketEdge
git checkout staging
git commit --allow-empty -m "chore: force rebuild - emergency deployment fix"
git push origin staging
```

Then in Render Dashboard:
- Click "Manual Deploy" → "Clear build cache & deploy"

---

## 📊 EXPECTED SUCCESSFUL LOGS

When deployment succeeds, Render logs should show:

```
[Build Phase]
-----> Installing dependencies
       Successfully installed asyncpg==0.29.0 psycopg2-binary==2.9.9

[Startup Phase]
🚀 MarketEdge Platform Starting...
🔧 Environment: staging
🔄 STAGING/PREVIEW ENVIRONMENT DETECTED
[DATABASE-INIT] Starting database initialization, DATABASE_URL scheme: postgres
[SCHEME-FIX] original=postgres async=postgresql+asyncpg
[SCHEME-FIX-DETAILS] Transformation applied: postgres -> postgresql+asyncpg
✅ Schema validation passed
🟢 Starting FastAPI application...
INFO:     Application startup complete.
```

**NO psycopg2 errors anywhere!**

---

## 🎯 WHAT TO REPORT BACK

After completing the fix, please report:

1. **What was the Branch setting before fix?**
   - [ ] It was `main` (this was the problem)
   - [ ] It was `staging` (branch was correct, cache issue)
   - [ ] It was something else: `___________`

2. **Did the fix work?**
   - [ ] ✅ YES - I see all three diagnostic log lines
   - [ ] ❌ NO - Still seeing psycopg2 error
   - [ ] ❓ UNCLEAR - Logs are confusing

3. **Commit SHA shown in Render build logs:**
   - Expected: `339637588a09c00077e7512cf4498aaf31760842`
   - Actual: `___________`

---

## 📞 IF YOU NEED HELP

If none of this works:

1. Take screenshots of:
   - Render Dashboard "Settings" page (showing Branch field)
   - Render "Logs" page (showing deployment logs)
   - Any error messages

2. Report:
   - What branch setting was shown
   - Whether changing it triggered a deployment
   - What the logs show after deployment

---

## ⏱️ EXPECTED TIMELINE

- **Step 1-4:** 2 minutes (navigate and change branch)
- **Step 5:** 30 seconds (trigger cache clear)
- **Step 6-7:** 5-8 minutes (watch deployment complete)

**Total:** ~10 minutes to full resolution

---

**Generated:** 2025-10-06
**Agent:** DevOps (Maya)
**Priority:** 🚨 CRITICAL
**Business Impact:** £925K Zebra Associates opportunity blocked until fixed
