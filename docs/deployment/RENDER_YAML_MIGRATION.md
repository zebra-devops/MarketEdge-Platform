# render.yaml Migration Guide

**Document Version:** 1.0
**Date:** 2025-10-02
**Prepared By:** Maya (DevOps Engineer)
**Purpose:** Migrate from dashboard-managed env vars to render.yaml blueprint

---

## Executive Summary

This guide provides a safe migration path from manually configuring environment variables in the Render Dashboard to using render.yaml as the single source of truth for infrastructure configuration.

**Key Changes:**
1. ✅ **AUTH0_AUDIENCE added** (CRITICAL FIX)
2. ✅ **CORS_ORIGINS updated** with Vercel wildcard domains
3. ✅ **Staging service added** for UAT gate
4. ✅ **Preview environment variables** properly configured
5. ✅ **Database resources defined** (preview and staging databases)

**Migration Strategy:** Additive-only changes, no removal of existing configuration. Production service continues to work with existing dashboard settings.

---

## Table of Contents

1. [Current State](#current-state)
2. [Target State](#target-state)
3. [What Changes](#what-changes)
4. [What Stays the Same](#what-stays-the-same)
5. [Migration Steps](#migration-steps)
6. [Testing Procedure](#testing-procedure)
7. [Rollback Plan](#rollback-plan)
8. [Post-Migration Validation](#post-migration-validation)

---

## Current State

### Current render.yaml Configuration

**File:** `/render.yaml` (before migration)

```yaml
previews:
  generation: automatic
  expireAfterDays: 7

envVarGroups:
  - name: production-env

services:
  - type: web
    name: marketedge-platform
    env: python-3.11
    plan: free
    envVars:
      - fromGroup: production-env
      # Environment variables defined with sync: false
      # Rely on manual dashboard configuration
```

**Issues with Current Approach:**
- ❌ AUTH0_AUDIENCE not defined anywhere (CRITICAL)
- ❌ CORS_ORIGINS incomplete (missing Vercel domains)
- ❌ No staging service definition
- ❌ No database resource definitions
- ❌ Preview environment variables not explicitly defined
- ❌ Secrets must be manually pasted in dashboard for every change
- ❌ No infrastructure-as-code for staging environment

### Current Dashboard Configuration

**Location:** Render Dashboard → marketedge-platform → Environment

**Production Environment Variables (Dashboard-Managed):**
```
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET=<secret>
AUTH0_ACTION_SECRET=<secret>
AUTH0_AUDIENCE=<MISSING - CRITICAL>
DATABASE_URL=<production-db-connection-string>
REDIS_URL=<redis-connection-string>
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com
JWT_SECRET_KEY=<secret>
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
...
```

**Problems:**
1. No version control for environment variables
2. Easy to misconfigure or forget variables
3. No way to preview changes before applying
4. No infrastructure-as-code for staging
5. Manual work required for every new environment

---

## Target State

### New render.yaml Configuration

**File:** `/render.yaml` (after migration)

```yaml
previews:
  generation: automatic
  expireAfterDays: 7

envVarGroups:
  - name: production-env
  - name: staging-env

# NEW: Database resources defined
databases:
  - name: marketedge-preview-db
    databaseName: marketedge_preview
    plan: free

  - name: marketedge-staging-db
    databaseName: marketedge_staging
    plan: free

services:
  # Production service (enhanced configuration)
  - type: web
    name: marketedge-platform
    runtime: python
    plan: free
    region: oregon
    buildCommand: "..."
    startCommand: ./render-startup.sh

    # NEW: Explicit preview configuration
    previews:
      generation: automatic
      envVars:
        - key: ENVIRONMENT
          value: preview
        - key: DEBUG
          value: "true"
        - key: CORS_ORIGINS
          value: "https://*.onrender.com,https://*.vercel.app,http://localhost:3000"
        # ... more preview-specific vars

    envVars:
      - fromGroup: production-env

      # CRITICAL FIX #1: AUTH0_AUDIENCE
      - key: AUTH0_AUDIENCE
        value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
        sync: false

      # CRITICAL FIX #2: CORS_ORIGINS (updated)
      - key: CORS_ORIGINS
        value: "https://platform.marketedge.co.uk,...,https://*.vercel.app"
        previewValue: "https://*.onrender.com,https://*.vercel.app,..."

      # All other environment variables defined explicitly
      - key: AUTH0_DOMAIN
        value: dev-g8trhgbfdq2sk2m8.us.auth0.com
        sync: false
      # ... complete list

  # NEW: Staging service
  - type: web
    name: marketedge-platform-staging
    runtime: python
    plan: free
    region: oregon
    branch: staging  # Deploy only from staging branch
    buildCommand: "..."
    startCommand: ./render-startup.sh

    envVars:
      - fromGroup: staging-env

      # Staging-specific configuration
      - key: ENVIRONMENT
        value: staging

      - key: DATABASE_URL
        fromDatabase:
          name: marketedge-staging-db
          property: connectionString

      # ... complete staging configuration
```

**Benefits of New Approach:**
1. ✅ **Version-controlled infrastructure** - All config in git
2. ✅ **Explicit configuration** - No hidden dashboard settings
3. ✅ **Preview environments properly configured** - Explicit preview envVars
4. ✅ **Staging service defined** - Infrastructure-as-code for UAT gate
5. ✅ **Database resources defined** - Automatic database provisioning
6. ✅ **CRITICAL FIXES applied** - AUTH0_AUDIENCE and CORS_ORIGINS
7. ✅ **Environment-specific values** - Production vs preview vs staging

---

## What Changes

### 1. Production Service Configuration

**Changes:**
- ✅ **Added AUTH0_AUDIENCE** (CRITICAL) - enables JWT token generation
- ✅ **Updated CORS_ORIGINS** - added `https://*.vercel.app` wildcard
- ✅ **Explicit preview configuration** - preview envVars defined in render.yaml
- ✅ **All environment variables listed** - no reliance on hidden dashboard config
- ✅ **Runtime changed** from `env: python-3.11` to `runtime: python`

**Secrets (sync: false) - Still Dashboard-Managed:**
- AUTH0_CLIENT_SECRET
- AUTH0_ACTION_SECRET
- JWT_SECRET_KEY
- DATABASE_URL (production)
- REDIS_URL
- SENTRY_DSN

These secrets MUST still be manually configured in Render Dashboard (one-time setup).

### 2. Preview Environment Configuration

**New Feature: Explicit Preview EnvVars**

Previously, preview environments inherited production environment variables with no way to customize. Now:

```yaml
previews:
  generation: automatic
  envVars:
    - key: ENVIRONMENT
      value: preview

    - key: DEBUG
      value: "true"

    - key: CORS_ORIGINS
      value: "https://*.onrender.com,https://*.vercel.app,http://localhost:3000"

    # ... more preview-specific overrides
```

**Impact:** Preview environments now have proper configuration without polluting production settings.

### 3. Staging Service (NEW)

**Completely New Addition:**

```yaml
services:
  - type: web
    name: marketedge-platform-staging
    branch: staging  # Deploy only from staging branch
    envVars:
      - key: ENVIRONMENT
        value: staging

      - key: DATABASE_URL
        fromDatabase:
          name: marketedge-staging-db
          property: connectionString

      # ... complete staging configuration
```

**Impact:** Staging environment now defined in infrastructure-as-code. No manual dashboard setup required (except secrets).

### 4. Database Resources (NEW)

**New Database Definitions:**

```yaml
databases:
  # Preview database (shared by all PR previews)
  - name: marketedge-preview-db
    databaseName: marketedge_preview
    plan: free

  # Staging database (dedicated)
  - name: marketedge-staging-db
    databaseName: marketedge_staging
    plan: free
```

**Impact:**
- Preview databases automatically provisioned
- Staging database automatically provisioned
- No manual database creation required

---

## What Stays the Same

### 1. Production Service Name

**Unchanged:** `marketedge-platform`

**Impact:** Existing production service continues to work. No downtime or service recreation.

### 2. Production Secrets

**Unchanged:** All secrets remain in Render Dashboard

**Location:** Dashboard → marketedge-platform → Environment

**Secrets to Keep:**
- AUTH0_CLIENT_SECRET
- AUTH0_ACTION_SECRET
- JWT_SECRET_KEY
- DATABASE_URL (production)
- REDIS_URL
- SENTRY_DSN

**Impact:** No need to reconfigure secrets. They continue to work.

### 3. Preview Environment Behavior

**Unchanged:** PR previews still automatically created on PR open

**Location:** Render automatically creates preview on PR creation

**Impact:** PR previews continue to work as before, but now have proper configuration.

### 4. Production Deployment Trigger

**Unchanged:** Production still deploys from `main` branch (for now)

**Note:** Can be changed to tag-based deployment later (Phase 3 of staging gate implementation).

---

## Migration Steps

### Step 0: Pre-Migration Validation

**Before starting migration:**

- [ ] **Validate render.yaml syntax**
  ```bash
  # Run validation script to check for configuration errors
  ./scripts/validate-render-yaml.sh

  # Expected output:
  # ✅ YAML syntax is valid
  # ✅ No value + sync conflicts found
  # ✅ Secret configuration looks good
  # ✅ No duplicate environment variables
  # ✅ Service configuration valid
  # =========================================
  # ✅ Validation PASSED
  # render.yaml is ready for deployment
  ```

  **CRITICAL:** Do not proceed if validation fails. Fix any errors first.

### Step 0.1: Pre-Migration Checklist

**Before starting migration:**

- [ ] **Backup current configuration**
  ```bash
  # Document current Render Dashboard environment variables
  # Take screenshots of all environment variables
  # Save to: /docs/deployment/backup/render-env-vars-backup.txt
  ```

- [ ] **Verify current production service working**
  ```bash
  curl https://marketedge-platform.onrender.com/health
  # Should return: {"status": "healthy"}
  ```

- [ ] **Notify team of upcoming changes**
  - Post in #engineering channel
  - Mention: "Migrating to render.yaml blueprint, no downtime expected"

- [ ] **Review new render.yaml**
  ```bash
  cat /Users/matt/Sites/MarketEdge/render.yaml
  # Verify all configuration looks correct
  ```

---

### Step 1: Update render.yaml (Safe - No Immediate Impact)

**Action:** Commit new render.yaml to repository

```bash
cd /Users/matt/Sites/MarketEdge

# Verify new render.yaml is in place
cat render.yaml | head -20

# Commit to git
git add render.yaml
git commit -m "config: migrate to comprehensive render.yaml blueprint

- Add AUTH0_AUDIENCE (CRITICAL FIX)
- Update CORS_ORIGINS with Vercel wildcard domains
- Add staging service definition
- Add database resource definitions
- Add explicit preview environment configuration
- Infrastructure-as-code for preview and staging environments

Refs: /docs/deployment/RENDER_YAML_MIGRATION.md"

git push origin test/trigger-zebra-smoke
```

**Impact:** None yet. render.yaml is updated in git but not yet applied to Render.

**Time:** 5 minutes

---

### Step 2: Configure Critical Production Secrets (REQUIRED)

**Action:** Add missing AUTH0_AUDIENCE to production dashboard

**Location:** Render Dashboard → marketedge-platform → Environment

```bash
# Login to: https://dashboard.render.com
# Navigate to: marketedge-platform → Environment tab
# Click: Add Environment Variable

Name: AUTH0_AUDIENCE
Value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# Click: Save Changes
# Service will automatically redeploy
```

**Impact:**
- ✅ Auth0 will now return JWT tokens instead of opaque tokens
- ✅ Authentication will work correctly
- ⚠️ Service will redeploy (2-3 minutes downtime)

**Time:** 5 minutes + 3 minutes deploy time

**CRITICAL:** Do not skip this step. AUTH0_AUDIENCE is required for authentication.

---

### Step 3: Update Production CORS Configuration

**Action:** Update CORS_ORIGINS in production dashboard

**Location:** Render Dashboard → marketedge-platform → Environment

```bash
# Navigate to: Environment tab
# Find: CORS_ORIGINS variable
# Click: Edit

# OLD VALUE:
# CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com

# NEW VALUE:
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app

# Click: Save Changes
# Service will automatically redeploy
```

**Impact:**
- ✅ Frontend requests from Vercel domains will work
- ✅ Staging frontend can communicate with backend
- ⚠️ Service will redeploy (2-3 minutes downtime)

**Time:** 5 minutes + 3 minutes deploy time

---

### Step 4: Apply render.yaml to Render (Safe - Additive Only)

**Action:** Render automatically picks up render.yaml changes on next deploy

**Method 1: Automatic (Recommended)**
```bash
# Render detects render.yaml in repository root
# Next deployment will use new render.yaml
# No manual action required
```

**Method 2: Force Apply (If Needed)**
```bash
# Use Render CLI (if installed)
render blueprint apply

# Or trigger manual deploy in Render Dashboard
# Dashboard → marketedge-platform → Manual Deploy
```

**Impact:**
- ✅ New render.yaml configuration applied
- ✅ Preview environments get explicit configuration
- ✅ Database resources created (if not exist)
- ⚠️ Staging service created (new service)

**Time:** Automatic on next deploy

---

### Step 5: Create Staging Service (NEW)

**Action:** Render automatically creates staging service from render.yaml

**Expected Behavior:**
- Render reads render.yaml
- Finds new service: `marketedge-platform-staging`
- Creates new web service
- Provisions staging database: `marketedge-staging-db`
- Waits for `staging` branch to exist

**Manual Verification:**
```bash
# Check if staging service created
# Navigate to: Render Dashboard
# Should see: marketedge-platform-staging (new service)

# Check if staging database created
# Navigate to: Render Dashboard → Databases
# Should see: marketedge-staging-db (new database)
```

**Impact:**
- ✅ New staging service created (free tier)
- ✅ New staging database created (free tier)
- ⚠️ Staging service will be in "pending" state until staging branch exists
- 💰 Additional cost: $0/month (free tier) or $14/month (starter tier)

**Time:** Automatic (5-10 minutes for provisioning)

---

### Step 6: Configure Staging Secrets (REQUIRED)

**Action:** Configure secrets for staging service in dashboard

**Location:** Render Dashboard → marketedge-platform-staging → Environment

**Secrets to Add:**
```bash
# Auth0 Secrets (same as production or staging-specific)
AUTH0_CLIENT_SECRET=<same-as-production-or-staging-specific>
AUTH0_ACTION_SECRET=<same-as-production>

# JWT Secret (MUST BE DIFFERENT from production for security)
JWT_SECRET_KEY=<generate-new-secret-for-staging>

# Redis URL (can share with production or separate)
REDIS_URL=<redis-connection-string>

# Sentry (optional)
SENTRY_DSN=<staging-sentry-dsn-or-empty>
```

**Generate New JWT Secret:**
```bash
# Generate staging JWT secret (different from production)
openssl rand -hex 32
# Copy output and paste into Render Dashboard
```

**Impact:**
- ✅ Staging service can authenticate users
- ✅ Staging service can connect to Redis
- ✅ JWT tokens work in staging

**Time:** 10 minutes

---

### Step 7: Create Staging Branch (REQUIRED)

**Action:** Create staging branch so staging service can deploy

**IMPORTANT:** The staging branch MUST exist before applying render.yaml, otherwise Render will fail with "branch staging could not be found" error.

```bash
cd /Users/matt/Sites/MarketEdge

# Ensure main is up to date
git checkout main
git pull origin main

# Create staging branch
git checkout -b staging
git push -u origin staging

# Verify branch exists remotely
git branch -a | grep staging
# Should show: remotes/origin/staging

# Return to current branch
git checkout test/trigger-zebra-smoke
```

**Impact:**
- ✅ Staging branch exists
- ✅ Staging service will deploy from staging branch
- ✅ Render staging service transitions from "pending" to "deploying"

**Time:** 5 minutes

---

### Step 8: Verify Staging Service Deployment

**Action:** Wait for staging service to deploy and verify health

**Steps:**
```bash
# Wait for staging deployment to complete (5-10 minutes)
# Check: Render Dashboard → marketedge-platform-staging → Logs

# Verify staging health endpoint
curl https://marketedge-platform-staging.onrender.com/health

# Expected response:
# {
#   "status": "healthy",
#   "environment": "staging",
#   "database": "connected",
#   "redis": "connected"
# }
```

**Troubleshooting:**
- If deployment fails: Check logs in Render Dashboard
- Common issue: Missing secret (AUTH0_CLIENT_SECRET, JWT_SECRET_KEY, REDIS_URL)
- Solution: Add missing secret in Dashboard → Environment tab

**Impact:**
- ✅ Staging service fully operational
- ✅ Ready for UAT testing

**Time:** 10 minutes (5 min deploy + 5 min verification)

---

### Step 9: Test Preview Environment Configuration

**Action:** Create test PR to verify preview environment configuration

```bash
# Create test branch
git checkout -b test/render-yaml-preview

# Make trivial change
echo "# Test preview environment" >> README.md

# Commit and push
git add README.md
git commit -m "test: verify preview environment configuration"
git push origin test/render-yaml-preview

# Create PR on GitHub
# Verify preview environment created with correct configuration
```

**Verification Steps:**
```bash
# After preview created, check health endpoint
curl https://marketedge-platform-pr-XXX.onrender.com/health

# Expected response:
# {
#   "status": "healthy",
#   "environment": "preview",  # ← NEW: explicit preview environment
#   "debug": true,
#   "cors_origins": "https://*.onrender.com,https://*.vercel.app,..."
# }
```

**Impact:**
- ✅ Preview environments have explicit configuration
- ✅ CORS wildcard domains work
- ✅ Debug mode enabled in preview

**Time:** 10 minutes (5 min create PR + 5 min verify)

---

### Step 10: Post-Migration Validation

**Action:** Comprehensive validation of all environments

**Validation Checklist:**

**Production:**
- [ ] Production health endpoint returns 200 OK
  ```bash
  curl https://marketedge-platform.onrender.com/health
  ```
- [ ] Production authentication works
  - Open: https://app.zebra.associates
  - Login with: matt.lindop@zebra.associates
  - Verify: Super admin panel accessible
- [ ] Production CORS headers present
  ```bash
  curl -H "Origin: https://app.zebra.associates" -I \
    https://marketedge-platform.onrender.com/health
  # Should include: Access-Control-Allow-Origin header
  ```

**Staging:**
- [ ] Staging health endpoint returns 200 OK
  ```bash
  curl https://marketedge-platform-staging.onrender.com/health
  ```
- [ ] Staging database connected
- [ ] Staging Redis connected
- [ ] Staging environment="staging" in health response

**Preview:**
- [ ] Preview environment created for test PR
- [ ] Preview health endpoint returns 200 OK
- [ ] Preview environment="preview" in health response
- [ ] Preview CORS wildcard domains work

**Infrastructure:**
- [ ] Preview database exists: marketedge-preview-db
- [ ] Staging database exists: marketedge-staging-db
- [ ] Staging service exists: marketedge-platform-staging
- [ ] Production service unchanged: marketedge-platform

**Time:** 20 minutes

---

## Testing Procedure

### Test 1: Production Service (No Regression)

**Objective:** Verify production service continues to work exactly as before

**Steps:**
```bash
# 1. Health check
curl https://marketedge-platform.onrender.com/health
# Expected: {"status": "healthy", "environment": "production"}

# 2. Authentication test
curl -X POST https://marketedge-platform.onrender.com/api/v1/auth/auth0-url \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "https://app.zebra.associates/callback"}'
# Expected: Auth0 URL with audience parameter

# 3. CORS test
curl -H "Origin: https://app.zebra.associates" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://marketedge-platform.onrender.com/api/v1/auth/login
# Expected: Access-Control-Allow-Origin header present

# 4. JWT token test (manual)
# Login via frontend → Verify JWT token in Network tab
# Token should be JWT format (not opaque)
```

**Success Criteria:**
- ✅ All tests pass
- ✅ No errors in production logs
- ✅ Production authentication works end-to-end

---

### Test 2: Preview Environment Configuration

**Objective:** Verify preview environments have explicit configuration

**Steps:**
```bash
# 1. Create test PR (done in Step 9)
# 2. Wait for preview creation
# 3. Check preview health

curl https://marketedge-platform-pr-XXX.onrender.com/health
# Expected: {"environment": "preview", "debug": true}

# 4. Check preview CORS
curl -H "Origin: https://test-branch.vercel.app" \
     -I https://marketedge-platform-pr-XXX.onrender.com/health
# Expected: Access-Control-Allow-Origin header present (wildcard support)

# 5. Check preview logs
# Render Dashboard → Preview Service → Logs
# Expected: LOG_LEVEL=DEBUG (verbose logging)
```

**Success Criteria:**
- ✅ Preview environment explicitly configured
- ✅ Debug mode enabled
- ✅ CORS wildcard domains work
- ✅ Preview environment isolated from production

---

### Test 3: Staging Service

**Objective:** Verify staging service operational and isolated

**Steps:**
```bash
# 1. Health check
curl https://marketedge-platform-staging.onrender.com/health
# Expected: {"status": "healthy", "environment": "staging"}

# 2. Database check
# Verify staging database has separate schema
psql $STAGING_DATABASE_URL -c "\dt"
# Expected: Tables exist (from migrations)

# 3. Redis check
# Verify staging Redis connection
redis-cli -u $STAGING_REDIS_URL ping
# Expected: PONG

# 4. Authentication test
curl -X POST https://marketedge-platform-staging.onrender.com/api/v1/auth/auth0-url \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "https://staging.zebra.associates/callback"}'
# Expected: Auth0 URL with correct callback

# 5. Isolation test
# Verify staging JWT tokens don't work in production
# (JWT_SECRET_KEY different between environments)
```

**Success Criteria:**
- ✅ Staging service healthy
- ✅ Staging database separate from production
- ✅ Staging authentication configured correctly
- ✅ JWT tokens isolated (staging tokens don't work in production)

---

### Test 4: Database Resources

**Objective:** Verify databases automatically provisioned

**Steps:**
```bash
# 1. Check Render Dashboard
# Navigate to: Dashboard → Databases
# Expected:
# - marketedge-preview-db (new)
# - marketedge-staging-db (new)
# - <production-db> (existing)

# 2. Verify preview database connection
# Create test PR → Check preview service logs
# Expected: "Database connected" in logs

# 3. Verify staging database connection
# Check staging service logs
# Expected: "Database connected" in logs

# 4. Verify database isolation
# Staging database != Production database
# Preview database != Production database
```

**Success Criteria:**
- ✅ All databases provisioned
- ✅ Databases isolated (separate connection strings)
- ✅ Migrations run successfully in all databases

---

## Rollback Plan

### Scenario 1: Migration Causes Production Issues

**Symptoms:**
- Production service fails to deploy
- Authentication broken in production
- CORS errors in production

**Immediate Rollback:**
```bash
# 1. Revert render.yaml to previous version
git checkout HEAD~1 -- render.yaml

# 2. Commit rollback
git add render.yaml
git commit -m "rollback: revert to previous render.yaml"
git push origin test/trigger-zebra-smoke

# 3. Trigger manual redeploy in Render Dashboard
# Dashboard → marketedge-platform → Manual Deploy

# 4. Verify production health
curl https://marketedge-platform.onrender.com/health
```

**Time to Rollback:** 10 minutes

**Impact:** Production restored to previous state

---

### Scenario 2: Staging Service Creation Fails

**Symptoms:**
- Staging service fails to deploy
- Staging database not created
- Staging secrets missing

**Resolution (No Rollback Needed):**
```bash
# Staging service failure does NOT affect production
# Production continues to work

# Fix staging issues without impacting production:
# 1. Check staging service logs
# 2. Add missing secrets
# 3. Retry staging deployment
```

**Impact:** Production unaffected, staging can be fixed independently

---

### Scenario 3: Preview Environments Broken

**Symptoms:**
- Preview environments fail to create
- Preview CORS not working
- Preview database connection fails

**Resolution:**
```bash
# Option 1: Fix preview configuration in render.yaml
# Edit render.yaml → Fix preview envVars → Commit

# Option 2: Temporarily disable preview generation
# Render Dashboard → Production Service → Settings
# Disable: "Preview Environments"

# Option 3: Rollback render.yaml (Scenario 1)
```

**Impact:** Preview environments can be fixed without affecting production

---

### Scenario 4: Complete Rollback (Nuclear Option)

**When to Use:** All else fails, need to restore to pre-migration state

**Steps:**
```bash
# 1. Revert render.yaml
git revert <migration-commit-hash>
git push origin test/trigger-zebra-smoke

# 2. Delete staging service (if created)
# Render Dashboard → marketedge-platform-staging → Settings → Delete Service

# 3. Delete staging database (if created)
# Render Dashboard → Databases → marketedge-staging-db → Delete

# 4. Delete preview database (if created)
# Render Dashboard → Databases → marketedge-preview-db → Delete

# 5. Remove AUTH0_AUDIENCE from production (if causing issues)
# Dashboard → marketedge-platform → Environment → Delete AUTH0_AUDIENCE

# 6. Restore original CORS_ORIGINS
# Dashboard → marketedge-platform → Environment → Edit CORS_ORIGINS

# 7. Verify production restored
curl https://marketedge-platform.onrender.com/health
```

**Time to Complete Rollback:** 30 minutes

**Impact:** System restored to exact pre-migration state

---

## Post-Migration Validation

### Validation Checklist

**Production Validation:**
- [ ] Production health endpoint returns 200 OK
- [ ] Production authentication works (matt.lindop@zebra.associates can login)
- [ ] Production CORS headers present for all allowed origins
- [ ] Production logs show no errors
- [ ] Production JWT tokens are JWT format (not opaque)
- [ ] Production performance unchanged (no regression)

**Staging Validation:**
- [ ] Staging service exists and healthy
- [ ] Staging database provisioned and migrated
- [ ] Staging Redis connected
- [ ] Staging authentication configured correctly
- [ ] Staging environment isolated from production

**Preview Validation:**
- [ ] Preview environments auto-create for new PRs
- [ ] Preview environments have explicit configuration (environment=preview)
- [ ] Preview CORS wildcard domains work
- [ ] Preview databases automatically provisioned
- [ ] Preview cleanup works (7 days after PR close)

**Infrastructure Validation:**
- [ ] All services visible in Render Dashboard
- [ ] All databases visible in Render Dashboard
- [ ] render.yaml is source of truth for configuration
- [ ] Secrets remain in Dashboard (not in render.yaml)

**Cost Validation:**
- [ ] Staging service cost: $0/month (free tier)
- [ ] Staging database cost: $0/month (free tier)
- [ ] Preview database cost: $0/month (free tier, shared)
- [ ] Total additional cost: $0-14/month (within budget)

---

## Troubleshooting

### Issue 1: AUTH0_AUDIENCE Not Working

**Symptoms:**
- Auth0 still returns opaque tokens
- JWT verification fails
- "Invalid token" errors

**Diagnosis:**
```bash
# Check Auth0 URL includes audience parameter
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback"

# Look for: &audience=https%3A%2F%2Fdev-g8trhgbfdq2sk2m8.us.auth0.com%2Fapi%2Fv2%2F
```

**Solution:**
```bash
# Verify AUTH0_AUDIENCE set in Render Dashboard
# Navigate to: Dashboard → marketedge-platform → Environment
# Check: AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# If missing or incorrect:
# Add/Update variable → Save → Redeploy
```

---

### Issue 2: CORS Errors After Migration

**Symptoms:**
- Browser shows "No 'Access-Control-Allow-Origin'" error
- API requests blocked by CORS policy
- Frontend cannot connect to backend

**Diagnosis:**
```bash
# Check CORS headers
curl -H "Origin: https://staging.zebra.associates" \
     -I https://marketedge-platform.onrender.com/health

# Expected: Access-Control-Allow-Origin header present
# If missing: CORS configuration incorrect
```

**Solution:**
```bash
# Verify CORS_ORIGINS in Render Dashboard
# Navigate to: Dashboard → marketedge-platform → Environment
# Check: CORS_ORIGINS includes all required domains

# Update if needed:
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app

# Save → Redeploy
```

---

### Issue 3: Staging Service Won't Deploy

**Symptoms:**
- Staging service stuck in "pending" state
- Staging deployment fails
- Staging service logs show errors

**Common Causes:**

**A. Staging branch doesn't exist**
```bash
# This is the most common cause of staging deployment failure
# Error: "branch staging could not be found"

# Check if staging branch exists
git branch -a | grep staging

# If not, create it:
git checkout main
git pull origin main
git checkout -b staging
git push -u origin staging

# Verify it exists remotely
git branch -a | grep staging
# Should show: remotes/origin/staging
```

**B. Missing secrets in staging service**
```bash
# Check Render Dashboard → marketedge-platform-staging → Environment
# Required secrets:
# - AUTH0_CLIENT_SECRET
# - AUTH0_ACTION_SECRET
# - JWT_SECRET_KEY (must be different from production)
# - REDIS_URL

# Add missing secrets in Dashboard
```

**C. Database connection issues**
```bash
# Check if staging database provisioned
# Dashboard → Databases → marketedge-staging-db

# If missing: Render should auto-create from render.yaml
# If exists but connection fails: Check DATABASE_URL in staging service
```

---

### Issue 4: Preview Environments Not Created

**Symptoms:**
- New PRs don't trigger preview creation
- Preview environments fail to deploy
- "Preview creation disabled" message

**Solution:**
```bash
# Check preview generation enabled
# Dashboard → marketedge-platform → Settings → Previews
# Ensure: "Generate preview environments for pull requests" is enabled

# Check render.yaml
# Verify: previews.generation = automatic

# If still not working:
# Trigger manual deploy → Should pick up render.yaml changes
```

---

### Issue 5: Database Not Provisioned

**Symptoms:**
- Staging database missing in Dashboard
- Preview database missing in Dashboard
- Services can't connect to database

**Solution:**
```bash
# Render should auto-provision databases from render.yaml
# If not provisioned:

# Option 1: Wait (can take 10-15 minutes)
# Check: Dashboard → Databases → Refresh page

# Option 2: Trigger manual provision
# Edit render.yaml → Add comment → Commit → Push
# Render will re-read render.yaml and provision missing resources

# Option 3: Manual database creation
# Dashboard → New → PostgreSQL
# Name: marketedge-staging-db (must match render.yaml)
# Plan: Free
```

---

## Success Criteria

### Migration Successful When:

**Production:**
- ✅ Production service continues to work without regression
- ✅ Production authentication works with JWT tokens
- ✅ Production CORS includes Vercel wildcard domains
- ✅ Zero production downtime during migration

**Staging:**
- ✅ Staging service deployed and healthy
- ✅ Staging database provisioned and migrated
- ✅ Staging environment isolated from production
- ✅ Staging ready for UAT testing

**Preview:**
- ✅ Preview environments auto-create for PRs
- ✅ Preview environments have explicit configuration
- ✅ Preview CORS wildcard domains work
- ✅ Preview cleanup works (7 days)

**Infrastructure:**
- ✅ render.yaml is single source of truth
- ✅ All configuration version-controlled
- ✅ Secrets remain in Dashboard (proper security)
- ✅ No manual dashboard configuration required (except secrets)

**Cost:**
- ✅ Additional cost within budget ($0-14/month)
- ✅ Free tier resources utilized where possible
- ✅ No unexpected cost overruns

---

## Next Steps

After successful migration:

1. **Phase 2: Infrastructure Setup (STAGING_GATE_IMPLEMENTATION_PLAN.md)**
   - Configure staging custom domains
   - Set up staging frontend (Vercel)
   - End-to-end staging stack validation

2. **Phase 3: CI/CD Workflows**
   - Create staging deployment workflow
   - Create production deployment workflow (tag-based)
   - Create rollback workflow

3. **Phase 4: Testing & Validation**
   - End-to-end flow testing (PR → Staging → Production)
   - Rollback procedure testing
   - Team training

4. **Phase 5: Production Cutover**
   - Enable staging gate requirement
   - Disable direct production deployment
   - Switch to tag-based production releases

---

## Support

**Issues During Migration:**
- Slack: #engineering channel
- DevOps Lead: [Contact]
- Render Support: support@render.com

**Documentation:**
- render.yaml Reference: /docs/deployment/RENDER_YAML_REFERENCE.md
- Environment Configuration: /docs/deployment/ENVIRONMENT_CONFIGURATION.md
- Staging Gate Implementation: /docs/deployment/STAGING_GATE_IMPLEMENTATION_PLAN.md

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Status:** ✅ Ready for Use
**Maintained By:** Maya (DevOps Engineer)
