# Staging Environment Variables Diagnostic Guide

**Date:** 2025-10-06
**Issue:** Database error during authentication on staging
**Author:** Maya (DevOps)

## 🚨 CRITICAL FINDING: Auth0 Client ID Mismatch

The `render.yaml` has **INCORRECT** Auth0 Client ID for staging!

### Configuration Discrepancy Found

| Variable | render.yaml (WRONG) | Should Be (CORRECT) | Source |
|----------|-------------------|-------------------|---------|
| AUTH0_CLIENT_ID | wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6 | 9FRjf82esKN4fx3iY337CT1jpvNVFbAP | STAGING_ENV_VARS.env |
| Comment | "PlatformWrapper-dev (Option A)" | "PlatformWrapper-Staging (Option B)" | Staging-specific |

**CRITICAL:** render.yaml is using the **development** Auth0 Client ID instead of the **staging** one!

## Environment Variables Required for Staging

### 1. Database Configuration

```bash
DATABASE_URL
# Should be: Internal Database URL from Render staging database
# Format: postgres://[user]:[password]@[host]/[database]
# Example: postgres://marketedge_staging_user:xxxxx@dpg-xxxxx-a/marketedge_staging
# NOTE: Use INTERNAL URL (ends with -a), not external URL

RUN_MIGRATIONS=true
# Ensures migrations run on deployment
```

### 2. Auth0 Configuration (CRITICAL - MUST BE CORRECTED)

```bash
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
# Auth0 tenant domain

AUTH0_CLIENT_ID=9FRjf82esKN4fx3iY337CT1jpvNVFbAP
# CRITICAL: Must be staging-specific Client ID (NOT wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6)

AUTH0_CLIENT_SECRET=xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7
# Staging-specific secret (different from production)

AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
# CRITICAL: Required for JWT validation

AUTH0_CALLBACK_URL=https://staging.zebra.associates/callback
# Staging callback URL

AUTH0_ACTION_SECRET=0mSkHhYYz8PcB_MylserTVm9DXuZJSCrM77KCKxlY5U
# Used for webhook validation (same as production)
```

### 3. JWT Configuration

```bash
JWT_SECRET_KEY=pu1PUYs3-1DtNcMTaECe9KBihlzC7FPZa4FHmJ9Ou9r2-IHIKApIoO1mLTtxF1Ge
# Can be same as production for token continuity during migration
# Or use staging-specific: 9ee849a61260d50a6d23bb11d41a04d844706507abcd0c5b5d019430e75c9d70

JWT_ALGORITHM=HS256
JWT_ISSUER=market-edge-platform
JWT_AUDIENCE=market-edge-api
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Environment & CORS

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

CORS_ORIGINS=https://staging.zebra.associates,https://*.vercel.app,http://localhost:3000
# Note: Can be JSON array or comma-separated

COOKIE_DOMAIN=.zebra.associates
# Domain for cookie scope
```

### 5. Redis Configuration

```bash
REDIS_URL=redis://[redis-host]:6379
# Optional: Can share with production or use separate instance
```

### 6. Server Configuration

```bash
PORT=8000
FASTAPI_PORT=8000
```

## 🔍 Step-by-Step Verification in Render Dashboard

### Step 1: Navigate to Service Settings
1. Go to https://dashboard.render.com/
2. Click on "marketedge-platform-staging" service
3. Click on "Environment" tab

### Step 2: Critical Variables to Check

#### ❌ HIGHEST PRIORITY - MUST FIX IMMEDIATELY:
- [ ] **AUTH0_CLIENT_ID** = `9FRjf82esKN4fx3iY337CT1jpvNVFbAP` (NOT wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6)

#### ✅ Database Connection:
- [ ] **DATABASE_URL** exists and is not empty
- [ ] Verify it's the INTERNAL URL (should end with `-a`)
- [ ] Format: `postgres://user:password@dpg-xxxxx-a/database_name`

#### ✅ Auth0 Configuration:
- [ ] **AUTH0_DOMAIN** = `dev-g8trhgbfdq2sk2m8.us.auth0.com`
- [ ] **AUTH0_CLIENT_SECRET** = `xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7`
- [ ] **AUTH0_AUDIENCE** = `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/`
- [ ] **AUTH0_ACTION_SECRET** = `0mSkHhYYz8PcB_MylserTVm9DXuZJSCrM77KCKxlY5U`

#### ✅ JWT Configuration:
- [ ] **JWT_SECRET_KEY** exists (64+ characters)
- [ ] **JWT_ALGORITHM** = `HS256`

#### ✅ Environment Settings:
- [ ] **ENVIRONMENT** = `staging`
- [ ] **RUN_MIGRATIONS** = `true`

### Step 3: Check Environment Groups
- [ ] Verify "staging-env" environment group is linked
- [ ] Check if any variables are overridden in the group

## 🐛 Common Misconfigurations & Solutions

### Issue 1: Wrong AUTH0_CLIENT_ID (MOST LIKELY CAUSE)
**Symptom:** Authentication fails, JWT tokens invalid
**Current Wrong Value:** wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
**Correct Value:** 9FRjf82esKN4fx3iY337CT1jpvNVFbAP
**Fix:** Update in Render Dashboard immediately

### Issue 2: Using External Database URL
**Symptom:** Connection timeouts, "database error"
**Wrong:** postgres://user:pass@dpg-xxxxx.oregon-postgres.render.com/db
**Correct:** postgres://user:pass@dpg-xxxxx-a/db
**Fix:** Use Internal Database URL from Render

### Issue 3: Missing AUTH0_AUDIENCE
**Symptom:** JWT validation fails
**Fix:** Set to `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/`

### Issue 4: Empty or Placeholder Values
**Symptom:** Various authentication/database errors
**Fix:** Ensure all sync:false variables are set with actual values

## 📝 Diagnostic Python Script

Create and run this script on the staging server to verify environment:

```python
#!/usr/bin/env python3
# diagnostic.py - Run this on staging to check environment

import os
import sys
from urllib.parse import urlparse

def check_env():
    print("=== MarketEdge Staging Environment Diagnostic ===\n")

    # Check critical variables
    critical_vars = {
        "DATABASE_URL": "Database connection",
        "AUTH0_DOMAIN": "Auth0 domain",
        "AUTH0_CLIENT_ID": "Auth0 client ID",
        "AUTH0_CLIENT_SECRET": "Auth0 client secret",
        "AUTH0_AUDIENCE": "Auth0 audience",
        "JWT_SECRET_KEY": "JWT secret",
        "ENVIRONMENT": "Environment setting"
    }

    errors = []
    warnings = []

    for var, desc in critical_vars.items():
        value = os.getenv(var, "NOT SET")

        if value == "NOT SET":
            errors.append(f"❌ {var}: Missing ({desc})")
            print(f"❌ {var}: NOT SET")
        elif var == "DATABASE_URL":
            # Check if using internal URL
            parsed = urlparse(value)
            if parsed.hostname and "-a" in parsed.hostname:
                print(f"✅ {var}: Set (Internal URL detected)")
            elif parsed.hostname and "render.com" in parsed.hostname:
                warnings.append(f"⚠️  {var}: Using external URL (should use internal)")
                print(f"⚠️  {var}: External URL - should use internal")
            else:
                print(f"✅ {var}: Set ({parsed.hostname[:20]}...)")
        elif var == "AUTH0_CLIENT_ID":
            if value == "wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6":
                errors.append(f"❌ {var}: Wrong value (using dev instead of staging)")
                print(f"❌ {var}: WRONG - using dev client ID")
            elif value == "9FRjf82esKN4fx3iY337CT1jpvNVFbAP":
                print(f"✅ {var}: Correct staging value")
            else:
                warnings.append(f"⚠️  {var}: Unknown value")
                print(f"⚠️  {var}: Unknown value ({value[:10]}...)")
        elif var == "ENVIRONMENT":
            if value == "staging":
                print(f"✅ {var}: {value}")
            else:
                warnings.append(f"⚠️  {var}: Expected 'staging', got '{value}'")
                print(f"⚠️  {var}: {value} (expected 'staging')")
        elif "SECRET" in var or "KEY" in var:
            print(f"✅ {var}: Set ({len(value)} chars)")
        else:
            print(f"✅ {var}: {value}")

    # Check optional variables
    print("\n--- Optional Variables ---")
    optional_vars = ["REDIS_URL", "RUN_MIGRATIONS", "CORS_ORIGINS", "DEBUG"]

    for var in optional_vars:
        value = os.getenv(var, "NOT SET")
        if value != "NOT SET":
            if "REDIS" in var and value:
                print(f"✅ {var}: Set")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️  {var}: Not set (optional)")

    # Summary
    print("\n=== DIAGNOSTIC SUMMARY ===")
    if errors:
        print(f"\n❌ CRITICAL ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")

    if not errors and not warnings:
        print("\n✅ All environment variables configured correctly!")

    return len(errors) == 0

if __name__ == "__main__":
    success = check_env()
    sys.exit(0 if success else 1)
```

## 🚀 Quick Fix Commands

### Fix Auth0 Client ID in Render Dashboard:

1. Go to Environment tab
2. Find AUTH0_CLIENT_ID
3. Change from: `wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6`
4. Change to: `9FRjf82esKN4fx3iY337CT1jpvNVFbAP`
5. Click "Save Changes"
6. Service will auto-redeploy

### Verify Database Connection:

```bash
# SSH to staging server or run in Render Shell
psql $DATABASE_URL -c "SELECT current_database(), current_user, version();"
```

### Test Auth0 Configuration:

```bash
# Test Auth0 endpoint is reachable
curl -I https://dev-g8trhgbfdq2sk2m8.us.auth0.com/.well-known/jwks.json
```

## 📊 Expected vs Actual Comparison

| Variable | Expected (from STAGING_ENV_VARS.env) | Likely Current (from render.yaml) | Action Required |
|----------|--------------------------------------|-----------------------------------|-----------------|
| AUTH0_CLIENT_ID | 9FRjf82esKN4fx3iY337CT1jpvNVFbAP | wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6 | **UPDATE NOW** |
| AUTH0_CLIENT_SECRET | xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7 | Not set (sync: false) | Set in Dashboard |
| DATABASE_URL | Internal Render DB URL | From marketedge-staging-db | Verify internal |
| JWT_SECRET_KEY | pu1PUYs3-1DtNcMTaECe9KBihlzC7FPZa4FHmJ9Ou9r2... | Not set (sync: false) | Set in Dashboard |
| ENVIRONMENT | staging | staging | ✅ Correct |

## 🎯 Immediate Action Items

1. **CRITICAL - Fix Auth0 Client ID:**
   - Current wrong value: wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
   - Must change to: 9FRjf82esKN4fx3iY337CT1jpvNVFbAP

2. **Verify Database URL:**
   - Must use internal URL (ends with -a)
   - Test connection with psql

3. **Set Missing Secrets:**
   - AUTH0_CLIENT_SECRET
   - JWT_SECRET_KEY
   - AUTH0_ACTION_SECRET

4. **Run Diagnostic Script:**
   - Deploy diagnostic.py to staging
   - Run to verify all variables

5. **Test Authentication:**
   - After fixing Auth0 Client ID
   - Try login flow again

## 🔄 After Fixing Variables

1. Service should auto-redeploy
2. Monitor logs for errors
3. Test login flow
4. Verify database connections
5. Check /health endpoint

## 📞 Support & Escalation

If issues persist after fixing Auth0 Client ID:
1. Check Render logs for specific error messages
2. Verify Auth0 application settings match
3. Confirm database is accessible
4. Check if migrations have run

---

**Most Likely Root Cause:** AUTH0_CLIENT_ID mismatch between render.yaml and required staging configuration.

**Immediate Fix Required:** Update AUTH0_CLIENT_ID in Render Dashboard to `9FRjf82esKN4fx3iY337CT1jpvNVFbAP`