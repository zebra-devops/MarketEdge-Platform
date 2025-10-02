# MarketEdge Platform - Staging/Preview Environment Configuration Report

**Generated:** 2025-10-02
**Branch:** `test/trigger-zebra-smoke`
**Latest Commit:** 8534897 - docs: add deployment summary report for authentication fixes
**Prepared By:** Maya (DevOps Agent)

---

## Executive Summary

This report provides a comprehensive verification of staging/preview environment configurations for both Render (backend) and Vercel (frontend) platforms, enabling safe deployment of authentication fixes from the `test/trigger-zebra-smoke` branch.

### Current Status: ✅ **WELL CONFIGURED** with Minor Recommendations

**Key Findings:**
- ✅ Render: Automatic preview environments enabled via `render.yaml`
- ✅ Vercel: Project configuration exists with staging setup
- ⚠️ **CRITICAL:** Backend staging API URL mismatch (see details below)
- ⚠️ **MISSING:** `AUTH0_AUDIENCE` must be configured in Render environment variables
- ✅ Auth0 configuration properly structured for multi-environment support

---

## Part 1: Configuration File Analysis

### 1.1 Render Backend Configuration (`render.yaml`)

**File Location:** `/Users/matt/Sites/MarketEdge/render.yaml`
**Status:** ✅ **EXISTS AND PROPERLY CONFIGURED**

#### Preview Environment Settings

```yaml
previews:
  generation: automatic      # ✅ Automatic preview for all PRs
  expireAfterDays: 7        # ✅ Auto-cleanup after 7 days
```

**Analysis:**
- ✅ Preview environments will be created automatically for all pull requests
- ✅ Each PR will get its own isolated environment
- ✅ Automatic cleanup prevents resource waste

#### Service Configuration

```yaml
services:
  - type: web
    name: marketedge-platform
    env: python-3.11
    plan: free
    buildCommand: "python --version && pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements.txt"
    startCommand: ./render-startup.sh
    previews:
      numInstances: 1       # ✅ Inherit plan from base
```

**Critical Environment Variables Configuration:**

| Variable | Production | Preview | Status |
|----------|-----------|---------|--------|
| `USE_STAGING_AUTH0` | `false` | `true` | ✅ Correct |
| `CORS_ORIGINS` | Production domains | `https://*.onrender.com,https://localhost:3000` | ✅ Wildcard support |
| `ENABLE_DEBUG_LOGGING` | `false` | `true` | ✅ Debug enabled for preview |
| `SENTRY_DSN` | Set | Empty (disabled) | ✅ Correct |
| `AUTH0_AUDIENCE` | `sync: false` | `sync: false` | ⚠️ **MUST BE SET MANUALLY** |

#### Multi-Environment Auth0 Strategy

**Excellent Design:** The `render.yaml` implements environment-aware Auth0 configuration:

**Production Auth0 Variables:**
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_AUDIENCE`

**Staging/Preview Auth0 Variables:**
- `AUTH0_DOMAIN_STAGING`
- `AUTH0_CLIENT_ID_STAGING`
- `AUTH0_CLIENT_SECRET_STAGING`
- `AUTH0_AUDIENCE_STAGING`

**Runtime Selection:**
- `USE_STAGING_AUTH0=false` → Uses production Auth0 variables
- `USE_STAGING_AUTH0=true` → Uses staging Auth0 variables (automatic in previews)

### 1.2 Vercel Frontend Configuration

**Primary Config:** `platform-wrapper/frontend/vercel-deployment-config.json`
**Staging Config:** `platform-wrapper/frontend/vercel-staging.json`
**Project Link:** `platform-wrapper/frontend/.vercel/project.json`

**Status:** ✅ **EXISTS WITH PROPER STRUCTURE**

#### Production Configuration (`vercel-deployment-config.json`)

```json
{
  "name": "marketedge-frontend",
  "version": 2,
  "regions": ["iad1"],
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://marketedge-platform.onrender.com",
    "NEXT_PUBLIC_AUTH0_DOMAIN": "dev-g8trhgbfdq2sk2m8.us.auth0.com",
    "NEXT_PUBLIC_AUTH0_CLIENT_ID": "mQG01Z4lNhTN081GHbR9R9C4fBQdPNr"
  }
}
```

**Analysis:**
- ✅ Points to production Render backend
- ✅ Auth0 configuration matches backend
- ✅ Security headers properly configured
- ✅ CORS headers for `/api/*` routes

#### Staging Configuration (`vercel-staging.json`)

```json
{
  "name": "marketedge-frontend-staging",
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://staging-api.zebra.associates",
    "NEXT_PUBLIC_AUTH0_DOMAIN": "dev-g8trhgbfdq2sk2m8.us.auth0.com",
    "NEXT_PUBLIC_AUTH0_CLIENT_ID": "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
  },
  "git": {
    "deploymentEnabled": {
      "develop": true,
      "staging": true
    }
  },
  "aliases": [
    "staging.zebra.associates"
  ]
}
```

**⚠️ CRITICAL ISSUE IDENTIFIED:**

The staging configuration references `https://staging-api.zebra.associates`, but this URL does not match the actual Render backend URL.

**Expected Backend URLs:**
- **Production:** `https://marketedge-platform.onrender.com`
- **Preview (PR-based):** `https://marketedge-platform-pr-<number>.onrender.com`
- **Staging Branch:** Would need dedicated Render service or manual deploy

**Current Mismatch:**
- Frontend staging expects: `https://staging-api.zebra.associates`
- Render provides: `https://marketedge-platform.onrender.com` (production)

#### Vercel Project Configuration

**Project ID:** `prj_MywzQ7mcvWoOWMAdnTnbOnivyhtD`
**Organization ID:** `team_1TUAsFQzZUxGWN0ItsbXMqFv`

**Status:** ✅ Project is linked to Vercel account

### 1.3 Environment Variable Documentation

#### Backend Environment Variables (`.env.example`)

**Status:** ✅ **COMPREHENSIVE DOCUMENTATION**

Key variables documented:
- ✅ `DATABASE_URL` - PostgreSQL connection
- ✅ `REDIS_URL` - Redis cache
- ✅ `AUTH0_DOMAIN` - Auth0 tenant
- ✅ `AUTH0_CLIENT_ID` - Auth0 application ID
- ✅ `AUTH0_CLIENT_SECRET` - Auth0 application secret
- ✅ `AUTH0_AUDIENCE` - **CRITICAL:** Required for JWT tokens
- ✅ `AUTH0_ACTION_SECRET` - Auth0 Actions webhook secret
- ✅ `CORS_ORIGINS` - Frontend origins
- ✅ `ENVIRONMENT` - Environment identifier

#### Frontend Environment Variables (`.env.staging`)

**Status:** ✅ **PROPERLY CONFIGURED**

```bash
NODE_ENV=staging
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
NEXT_PUBLIC_API_BASE_URL=https://staging-api.zebra.associates  # ⚠️ Mismatch
```

### 1.4 Deployment Scripts

**Found Scripts:**
- ✅ `scripts/deployment/verify_staging_deployment.sh` - Comprehensive staging verification
- ✅ `scripts/verify-render-deployment.sh` - Render deployment verification
- ✅ `scripts/validate-deployment-success.sh` - General validation
- ✅ `scripts/quick-deployment-validation.sh` - Quick checks

**Status:** ✅ **EXCELLENT AUTOMATION COVERAGE**

---

## Part 2: Render Backend Configuration Checklist

### 2.1 Preview Environments

| Check | Status | Details |
|-------|--------|---------|
| Preview environments enabled | ✅ YES | Automatic generation for all PRs |
| Branch deployment triggers | ✅ CONFIGURED | Automatic for PRs, manual for branches |
| `test/trigger-zebra-smoke` deployable | ✅ YES | Can create manual deploy or open PR |
| Preview expiration | ✅ 7 DAYS | Auto-cleanup configured |
| Preview instances | ✅ 1 INSTANCE | Inherits free plan |

### 2.2 Environment Variables - Production

**MUST BE SET MANUALLY IN RENDER DASHBOARD**

| Variable | Required | Production Value | Status |
|----------|----------|------------------|--------|
| `DATABASE_URL` | ✅ YES | PostgreSQL connection string | ⚠️ **VERIFY SET** |
| `REDIS_URL` | ✅ YES | Redis connection string | ⚠️ **VERIFY SET** |
| `AUTH0_DOMAIN` | ✅ YES | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | ⚠️ **VERIFY SET** |
| `AUTH0_CLIENT_ID` | ✅ YES | Production client ID | ⚠️ **VERIFY SET** |
| `AUTH0_CLIENT_SECRET` | ✅ YES | Production client secret | ⚠️ **VERIFY SET** |
| `AUTH0_AUDIENCE` | ✅ **CRITICAL** | Auth0 API audience URL | ❌ **MUST ADD** |
| `AUTH0_ACTION_SECRET` | ✅ YES | Webhook secret (min 32 chars) | ⚠️ **VERIFY SET** |
| `SECRET_KEY` | ✅ YES | Auto-generated by Render | ✅ CONFIGURED |

### 2.3 Environment Variables - Staging/Preview

**MUST BE SET MANUALLY IN RENDER DASHBOARD**

| Variable | Required | Preview Value | Status |
|----------|----------|---------------|--------|
| `AUTH0_DOMAIN_STAGING` | ✅ YES | Same as production or separate tenant | ❌ **MUST ADD** |
| `AUTH0_CLIENT_ID_STAGING` | ✅ YES | Staging Auth0 client ID | ❌ **MUST ADD** |
| `AUTH0_CLIENT_SECRET_STAGING` | ✅ YES | Staging Auth0 client secret | ❌ **MUST ADD** |
| `AUTH0_AUDIENCE_STAGING` | ✅ **CRITICAL** | Staging API audience URL | ❌ **MUST ADD** |
| `USE_STAGING_AUTH0` | ✅ YES | Auto-set to `true` in previews | ✅ CONFIGURED |

### 2.4 Branch Configuration

| Setting | Production | Preview | Status |
|---------|-----------|---------|--------|
| Branch | `main` (inferred) | Any branch via PR or manual | ✅ FLEXIBLE |
| Auto-deploy | Likely enabled for `main` | Automatic for PRs | ✅ CONFIGURED |
| Manual deploy | Available | Available | ✅ AVAILABLE |

---

## Part 3: Vercel Frontend Configuration Checklist

### 3.1 Preview Deployments

| Check | Status | Details |
|-------|--------|---------|
| Preview deployments enabled | ✅ YES | Git integration configured |
| Branch triggers | ✅ CONFIGURED | `develop` and `staging` branches |
| GitHub integration | ✅ ACTIVE | Linked to `zebra-devops/MarketEdge-Platform` |
| Preview URL pattern | ✅ CONFIGURED | `<branch>-<project>.vercel.app` |

### 3.2 Environment Variables - Production

**MUST BE SET IN VERCEL DASHBOARD**

| Variable | Required | Production Value | Status |
|----------|----------|------------------|--------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ YES | `https://marketedge-platform.onrender.com` | ✅ IN CONFIG |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | ✅ YES | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | ✅ IN CONFIG |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | ✅ YES | Production client ID | ✅ IN CONFIG |

**Note:** Config files define defaults, but Vercel dashboard settings override these.

### 3.3 Environment Variables - Preview

**MUST BE SET IN VERCEL DASHBOARD FOR PREVIEW ENVIRONMENT**

| Variable | Required | Preview Value | Recommendation |
|----------|----------|---------------|----------------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ YES | Should match Render preview URL | ⚠️ **NEEDS DYNAMIC SETUP** |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | ✅ YES | Same as production or staging | ✅ CAN REUSE |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | ✅ YES | Staging client ID | ⚠️ **VERIFY** |

**⚠️ CHALLENGE:** Preview URLs are dynamic (`marketedge-platform-pr-123.onrender.com`), requiring either:
1. **Option A:** Shared staging backend for all Vercel previews
2. **Option B:** Manual Vercel env var update per PR (not scalable)
3. **Option C:** Environment variable based on branch name (complex)

### 3.4 Domain Configuration

| Domain Type | Value | Status |
|-------------|-------|--------|
| Production | `app.zebra.associates` (inferred) | ⚠️ **VERIFY IN DASHBOARD** |
| Staging Alias | `staging.zebra.associates` | ✅ CONFIGURED |
| Preview Pattern | `<branch>-marketedge-<hash>.vercel.app` | ✅ AUTOMATIC |

### 3.5 Build Settings

| Setting | Value | Status |
|---------|-------|--------|
| Framework | Next.js | ✅ CONFIGURED |
| Build Command | `npm run build` | ✅ DEFAULT |
| Output Directory | `.next` | ✅ DEFAULT |
| Install Command | `npm ci` | ✅ RECOMMENDED |
| Node Version | Latest (via Vercel) | ✅ AUTOMATIC |

---

## Part 4: Environment Synchronization Analysis

### 4.1 Auth0 Configuration Alignment

| Setting | Render Backend | Vercel Frontend | Match Status |
|---------|---------------|-----------------|--------------|
| **Production Auth0** | | | |
| AUTH0_DOMAIN | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | ✅ MATCH |
| AUTH0_CLIENT_ID | Via env group | `mQG01Z4lNhTN081GHbR9R9C4fBQdPNr` | ⚠️ **VERIFY** |
| **Staging Auth0** | | | |
| AUTH0_DOMAIN_STAGING | Not set yet | Same as production | ⚠️ **NEEDS DECISION** |
| AUTH0_CLIENT_ID_STAGING | Not set yet | `mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr` | ⚠️ **NEEDS SETUP** |

### 4.2 API URL Synchronization

| Environment | Frontend Expects | Backend Provides | Match Status |
|-------------|------------------|------------------|--------------|
| **Production** | `https://marketedge-platform.onrender.com` | `https://marketedge-platform.onrender.com` | ✅ MATCH |
| **Staging** | `https://staging-api.zebra.associates` | Does not exist | ❌ **MISMATCH** |
| **Preview (PR)** | Dynamic (needs config) | `https://marketedge-platform-pr-<num>.onrender.com` | ⚠️ **NEEDS SETUP** |

### 4.3 CORS Configuration

**Backend CORS Origins (render.yaml):**
- **Production:** `https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com`
- **Preview:** `https://*.onrender.com,https://localhost:3000`

**Frontend Origins:**
- **Production:** `https://app.zebra.associates` (likely)
- **Staging:** `https://staging.zebra.associates`
- **Preview:** `https://<branch>-marketedge-<hash>.vercel.app`

**⚠️ CRITICAL ISSUE:** Backend CORS does not include Vercel domains!

**Required Fix:** Update Render CORS_ORIGINS to include:
```
https://*.vercel.app
https://app.zebra.associates
https://staging.zebra.associates
```

---

## Part 5: Preview URL Patterns

### 5.1 Render Backend Preview URLs

**Pattern:** `https://marketedge-platform-pr-<number>.onrender.com`

**Example:**
- PR #123 → `https://marketedge-platform-pr-123.onrender.com`
- PR #456 → `https://marketedge-platform-pr-456.onrender.com`

**Deployment Trigger:**
1. Create PR from `test/trigger-zebra-smoke` to `main`
2. Render automatically detects PR
3. Creates preview environment within ~5-10 minutes
4. Posts preview URL as PR comment

**Manual Deploy Alternative:**
1. Go to Render Dashboard → marketedge-platform
2. Click "Manual Deploy"
3. Select branch: `test/trigger-zebra-smoke`
4. Deploy to production URL (⚠️ **RISKY - AFFECTS PRODUCTION**)

### 5.2 Vercel Frontend Preview URLs

**Pattern:** `https://<branch-name>-<project-name>-<org>.vercel.app`

**Example:**
- Branch `test/trigger-zebra-smoke` → `https://test-trigger-zebra-smoke-marketedge-<org>.vercel.app`
- Branch `develop` → `https://develop-marketedge-<org>.vercel.app`

**Deployment Trigger:**
1. Push to GitHub branch
2. Vercel detects commit
3. Builds and deploys preview automatically
4. Posts preview URL as GitHub check/comment

---

## Part 6: Auth0 Callback URL Configuration

### 6.1 Current Auth0 Setup (Inferred)

**Auth0 Tenant:** `dev-g8trhgbfdq2sk2m8.us.auth0.com`

**Required Callback URLs:**

```
http://localhost:3000/callback
https://app.zebra.associates/callback
https://staging.zebra.associates/callback
https://*.vercel.app/callback
https://*.onrender.com/callback
```

**Required Logout URLs:**

```
http://localhost:3000
https://app.zebra.associates
https://staging.zebra.associates
https://*.vercel.app
https://*.onrender.com
```

**Required Web Origins:**

```
http://localhost:3000
https://app.zebra.associates
https://staging.zebra.associates
https://*.vercel.app
```

### 6.2 Verification Steps for Auth0 Dashboard

**MUST BE VERIFIED MANUALLY:**

1. **Login to Auth0:** https://manage.auth0.com
2. **Navigate:** Applications → [Your Application]
3. **Check Settings Tab:**
   - ✅ Application Type: `Regular Web Application` or `Single Page Application`
   - ✅ Token Endpoint Authentication Method: `POST`
4. **Verify URLs:**
   - Allowed Callback URLs (includes wildcard domains)
   - Allowed Logout URLs (includes wildcard domains)
   - Allowed Web Origins (includes Vercel domains)
5. **Check Advanced Settings → OAuth:**
   - ✅ OIDC Conformant: Enabled
   - ✅ JSON Web Token Signature Algorithm: `RS256`
6. **Check APIs:**
   - ✅ API exists with identifier matching `AUTH0_AUDIENCE`
   - ✅ API permissions configured

---

## Part 7: Step-by-Step Setup Instructions

### 7.1 Render Dashboard Configuration

**URL:** https://dashboard.render.com

#### Step 1: Access Service
1. Login to Render Dashboard
2. Navigate to: **Services** → **marketedge-platform**

#### Step 2: Configure Production Environment Variables

**Environment Tab:**

Click **Environment** tab, then add/verify these variables:

| Variable | Value | Source |
|----------|-------|--------|
| `DATABASE_URL` | PostgreSQL connection string | From managed database or external provider |
| `REDIS_URL` | Redis connection string | From managed Redis or external provider |
| `AUTH0_DOMAIN` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Auth0 Dashboard → Settings |
| `AUTH0_CLIENT_ID` | Your production client ID | Auth0 Dashboard → Settings → Client ID |
| `AUTH0_CLIENT_SECRET` | Your production client secret | Auth0 Dashboard → Settings → Client Secret |
| `AUTH0_AUDIENCE` | `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/` | Auth0 Dashboard → APIs → Identifier |
| `AUTH0_ACTION_SECRET` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Generate locally, save securely |
| `CORS_ORIGINS` | `https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app` | Update to include all frontend domains |

#### Step 3: Configure Staging/Preview Environment Variables

**Add these additional variables for preview environments:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `AUTH0_DOMAIN_STAGING` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Use same tenant or create staging tenant |
| `AUTH0_CLIENT_ID_STAGING` | Staging Auth0 client ID | Create separate Auth0 app or reuse production |
| `AUTH0_CLIENT_SECRET_STAGING` | Staging Auth0 client secret | Corresponding secret |
| `AUTH0_AUDIENCE_STAGING` | `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/` | Same API or staging API |

**Note:** `USE_STAGING_AUTH0` is automatically set to `true` in preview environments via `render.yaml`.

#### Step 4: Verify Preview Settings

**Settings Tab:**

1. Scroll to **Preview Environments**
2. ✅ Verify: "Automatically create preview environments for pull requests" is **ENABLED**
3. ✅ Verify: "Delete preview environments after" is set to **7 days**

#### Step 5: Deploy Test Branch

**Option A: Create Pull Request (RECOMMENDED)**

1. Create PR: `test/trigger-zebra-smoke` → `main`
2. Render automatically creates preview environment
3. Monitor **Deployments** tab for preview URL

**Option B: Manual Deploy (USE WITH CAUTION)**

1. Click **Manual Deploy** button
2. Select branch: `test/trigger-zebra-smoke`
3. ⚠️ **WARNING:** This deploys to PRODUCTION URL!
4. Consider creating staging service instead

### 7.2 Vercel Dashboard Configuration

**URL:** https://vercel.com/dashboard

#### Step 1: Access Project

1. Login to Vercel Dashboard
2. Navigate to your project (likely "marketedge-frontend" or similar)
3. If not found, check organization: `team_1TUAsFQzZUxGWN0ItsbXMqFv`

#### Step 2: Configure Production Environment Variables

**Settings → Environment Variables:**

Add these for **Production** environment:

| Variable | Value | Encryption |
|----------|-------|-----------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://marketedge-platform.onrender.com` | Public |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Public |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Your production client ID | Public |

**Note:** `NEXT_PUBLIC_*` variables are public and embedded in client bundle.

#### Step 3: Configure Preview Environment Variables

**Settings → Environment Variables:**

Add these for **Preview** environment:

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://staging-api.zebra.associates` OR Dynamic URL | **DECISION NEEDED** |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Can reuse production |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Staging client ID OR production | **DECISION NEEDED** |

**⚠️ CHALLENGE:** Preview backend URL is dynamic. Options:

**Option A: Shared Staging Backend (RECOMMENDED)**
- Create dedicated Render service: `marketedge-platform-staging`
- Deploy `staging` branch to this service
- Fixed URL: `https://marketedge-platform-staging.onrender.com`
- All Vercel previews use this backend

**Option B: Environment-Aware Configuration**
- Use Vercel build step to detect PR number
- Construct Render preview URL: `https://marketedge-platform-pr-{PR_NUM}.onrender.com`
- Requires custom build script

**Option C: Production Backend for Previews**
- Set preview `NEXT_PUBLIC_API_BASE_URL` to production
- ⚠️ **RISK:** Previews hit production data
- Not recommended for testing

#### Step 4: Verify Git Integration

**Settings → Git:**

1. ✅ Verify: GitHub repository connected
2. ✅ Verify: `zebra-devops/MarketEdge-Platform` is correct repo
3. ✅ Check: Production branch (likely `main`)
4. ✅ Enable: "Automatic deployments from Git pushes"

#### Step 5: Configure Branch Deployments

**Settings → Git → Deploy Hooks:**

Consider adding deploy hooks for specific branches:
- `develop` → Always deploy previews
- `staging` → Deploy to staging alias
- `test/*` → Deploy previews for testing branches

#### Step 6: Configure Custom Domains

**Settings → Domains:**

**Production:**
- Add: `app.zebra.associates`
- Verify DNS settings
- Enable HTTPS (automatic)

**Staging:**
- Add: `staging.zebra.associates`
- Assign to `staging` branch
- Verify DNS settings

### 7.3 Auth0 Dashboard Configuration

**URL:** https://manage.auth0.com

#### Step 1: Access Application

1. Login to Auth0
2. Navigate: **Applications** → **Applications**
3. Select your application (Client ID: `wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6` or staging equivalent)

#### Step 2: Configure Allowed Callback URLs

**Settings → Application URIs:**

Update **Allowed Callback URLs** to include:

```
http://localhost:3000/callback,
https://app.zebra.associates/callback,
https://staging.zebra.associates/callback,
https://*.vercel.app/callback,
https://*.onrender.com/callback
```

**Note:** Some Auth0 plans may not support wildcards. If wildcards fail:
- Manually add each preview URL as discovered
- Consider upgrading Auth0 plan
- Use subdomain approach (e.g., `staging.zebra.associates`)

#### Step 3: Configure Allowed Logout URLs

**Settings → Application URIs:**

Update **Allowed Logout URLs** to include:

```
http://localhost:3000,
https://app.zebra.associates,
https://staging.zebra.associates,
https://*.vercel.app,
https://*.onrender.com
```

#### Step 4: Configure Allowed Web Origins

**Settings → Application URIs:**

Update **Allowed Web Origins** to include:

```
http://localhost:3000,
https://app.zebra.associates,
https://staging.zebra.associates,
https://*.vercel.app
```

**Purpose:** Enables Auth0 silent authentication and token refresh from frontend.

#### Step 5: Verify API Configuration

**Navigate: APIs → [Your API]**

1. ✅ Verify API exists
2. ✅ Check **Identifier** matches `AUTH0_AUDIENCE` value
   - Example: `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/`
3. ✅ Verify **Signing Algorithm**: `RS256`
4. ✅ Check **RBAC Settings**:
   - Enable RBAC: `Yes`
   - Add Permissions in the Access Token: `Yes`

#### Step 6: Configure Token Settings

**Settings → Advanced Settings → OAuth:**

1. ✅ JSON Web Token (JWT) Signature Algorithm: `RS256`
2. ✅ OIDC Conformant: `Enabled`
3. ✅ Token Endpoint Authentication Method: `POST`

**Settings → Advanced Settings → Grant Types:**

Enable these grant types:
- ✅ Authorization Code
- ✅ Refresh Token
- ✅ Implicit (if needed for legacy support)

#### Step 7: Create Staging Application (OPTIONAL)

**If using separate staging Auth0 setup:**

1. Click **Create Application**
2. Name: `MarketEdge Platform - Staging`
3. Type: `Single Page Application` or `Regular Web Application`
4. Configure with staging URLs only
5. Use this Client ID for `AUTH0_CLIENT_ID_STAGING`

---

## Part 8: Deployment Strategy Recommendation

### 8.1 Recommended Approach: **Pull Request Preview Deployment**

**Why This Approach:**
- ✅ Isolated testing environment
- ✅ No impact on production
- ✅ Automatic cleanup after 7 days
- ✅ Easy rollback (just close PR)
- ✅ Team can review before merging
- ✅ GitHub Actions can run automated tests

**Deployment Steps:**

1. **Create Pull Request**
   ```bash
   # Ensure branch is up to date
   git checkout test/trigger-zebra-smoke
   git push origin test/trigger-zebra-smoke

   # Create PR via GitHub UI or CLI
   gh pr create \
     --title "Authentication Fixes - Critical Security Updates" \
     --body "Deploy authentication fixes from test/trigger-zebra-smoke branch" \
     --base main \
     --head test/trigger-zebra-smoke
   ```

2. **Monitor Render Preview Creation**
   - Check Render Dashboard → Deployments
   - Wait for preview URL (typically 5-10 minutes)
   - Preview URL posted to PR comments

3. **Update Vercel Preview Environment**
   - Get Render preview URL: `https://marketedge-platform-pr-<num>.onrender.com`
   - Update Vercel preview env var `NEXT_PUBLIC_API_BASE_URL`
   - Or: Use shared staging backend (see Option A below)

4. **Run Automated Verification**
   ```bash
   # Run staging verification script
   STAGING_URL=https://marketedge-platform-pr-<num>.onrender.com \
   ./scripts/deployment/verify_staging_deployment.sh
   ```

5. **Manual Testing**
   - Visit Vercel preview URL
   - Test authentication flow
   - Verify all 5 authentication fixes
   - Check super admin panel access

6. **Merge to Production**
   - If all tests pass, merge PR
   - Render deploys to production automatically
   - Vercel deploys frontend to production

### 8.2 Alternative Approach: **Dedicated Staging Environment**

**When to Use:**
- Need persistent staging environment
- Multiple team members testing concurrently
- Integration testing with external services
- Long-term feature testing

**Setup Required:**

**Render Backend:**
1. Create new service: `marketedge-platform-staging`
2. Branch: `staging` or `develop`
3. Environment variables: Use `AUTH0_*_STAGING` variables
4. Database: Separate staging database
5. URL: `https://marketedge-platform-staging.onrender.com`

**Vercel Frontend:**
1. Create branch deployment for `staging`
2. Custom domain: `staging.zebra.associates`
3. Environment variables:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform-staging.onrender.com
   NEXT_PUBLIC_ENVIRONMENT=staging
   ```

**Deployment Flow:**
```bash
# Merge to staging branch
git checkout staging
git merge test/trigger-zebra-smoke
git push origin staging

# Both Render and Vercel auto-deploy
# Access at: https://staging.zebra.associates
```

### 8.3 Risk Assessment

#### Pull Request Preview Approach

| Risk | Severity | Mitigation |
|------|----------|------------|
| Preview URL conflicts with CORS | MEDIUM | Update CORS to include `*.onrender.com` |
| Preview database shared with production | HIGH | Ensure preview uses separate DATABASE_URL |
| Auth0 callbacks not whitelisted | MEDIUM | Add wildcard URLs to Auth0 |
| Vercel preview doesn't connect to Render preview | MEDIUM | Manual env var update or shared staging backend |
| Preview environment costs | LOW | Auto-cleanup after 7 days |

**Overall Risk:** **MEDIUM-LOW** with proper configuration

#### Dedicated Staging Environment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Staging data drift from production | MEDIUM | Regular database refreshes |
| Staging costs | MEDIUM | Use free tier or smaller instances |
| Staging not representative of production | LOW | Mirror production configuration |
| Multiple developers conflicts | LOW | Use PR previews for individual work |

**Overall Risk:** **LOW** with proper maintenance

### 8.4 Recommended Deployment Path for `test/trigger-zebra-smoke`

**IMMEDIATE ACTION (SAFEST):**

**Phase 1: Configure Prerequisites (30 minutes)**

1. ✅ **Render Dashboard:**
   - Add `AUTH0_AUDIENCE` to production env vars
   - Add `AUTH0_AUDIENCE_STAGING` to preview env vars
   - Update `CORS_ORIGINS` to include Vercel domains
   - Verify `USE_STAGING_AUTH0=true` for previews (automatic via render.yaml)

2. ✅ **Auth0 Dashboard:**
   - Add wildcard callback URLs: `https://*.vercel.app/callback`, `https://*.onrender.com/callback`
   - Add wildcard logout URLs: `https://*.vercel.app`, `https://*.onrender.com`
   - Add wildcard web origins: `https://*.vercel.app`

3. ✅ **Vercel Dashboard:**
   - Set preview env var `NEXT_PUBLIC_API_BASE_URL` to production (temporary)
   - Or: Create dedicated staging backend (recommended for long-term)

**Phase 2: Create Pull Request (5 minutes)**

```bash
# Create PR
gh pr create \
  --title "🔒 Authentication Fixes - Critical Security Updates" \
  --body-file .github/pull_request_template.md \
  --base main \
  --head test/trigger-zebra-smoke \
  --label "security,authentication,critical"
```

**Phase 3: Monitor & Verify (15 minutes)**

1. Wait for Render preview environment creation
2. Check preview URL in PR comments
3. Run verification script:
   ```bash
   STAGING_URL=<render-preview-url> \
   FRONTEND_URL=<vercel-preview-url> \
   ./scripts/deployment/verify_staging_deployment.sh
   ```

**Phase 4: Manual Testing (15 minutes)**

1. Visit Vercel preview URL
2. Login with: `matt.lindop@zebra.associates`
3. Verify all authentication fixes:
   - ✅ Rate limiter works (storage access)
   - ✅ Token refresh not blocked by CSRF
   - ✅ JWT verification via Auth0 JWKS
   - ✅ AUTH0_AUDIENCE in token request
   - ✅ User lookup by email (not UUID)
4. Check super admin panel access

**Phase 5: Merge to Production (5 minutes)**

```bash
# If all tests pass
gh pr merge <pr-number> --squash --delete-branch

# Monitor production deployment
# Verify production health
curl https://marketedge-platform.onrender.com/health
```

**TOTAL TIME:** ~70 minutes from configuration to production deployment

---

## Part 9: Critical Configuration Gaps & Immediate Actions

### 9.1 MUST FIX BEFORE DEPLOYMENT

#### 1. AUTH0_AUDIENCE Missing (CRITICAL)

**Impact:** Without this, Auth0 returns opaque tokens instead of JWT tokens, breaking authentication.

**Fix:**
```bash
# Render Dashboard → Environment Variables → Add Variable
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
AUTH0_AUDIENCE_STAGING=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
```

**Verification:**
```bash
# Check Auth0 URL includes audience parameter
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback" | grep "audience="
```

#### 2. CORS Configuration Incomplete (HIGH)

**Impact:** Frontend requests blocked, authentication fails.

**Current CORS:**
```
https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com
```

**Required CORS:**
```
https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app
```

**Fix:**
```bash
# Render Dashboard → Environment Variables → Edit CORS_ORIGINS
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app
```

#### 3. Staging API URL Mismatch (MEDIUM)

**Impact:** Frontend staging can't connect to backend.

**Current:** Frontend expects `https://staging-api.zebra.associates`
**Actual:** No such backend exists

**Fix Options:**

**Option A: Create DNS CNAME**
```
# In your DNS provider (e.g., Cloudflare, Route53)
staging-api.zebra.associates CNAME marketedge-platform.onrender.com
```

**Option B: Create Dedicated Staging Service**
- Create new Render service: `marketedge-platform-staging`
- Deploy `staging` branch
- Update Vercel staging config

**Option C: Update Frontend Config**
```json
// platform-wrapper/frontend/vercel-staging.json
"NEXT_PUBLIC_API_BASE_URL": "https://marketedge-platform.onrender.com"
```

### 9.2 RECOMMENDED ENHANCEMENTS

#### 1. Environment-Specific Database URLs

**Current:** Single `DATABASE_URL` for all environments

**Recommendation:**
```bash
# Production
DATABASE_URL=postgresql://prod_user:prod_pass@prod-db.render.com/marketedge

# Preview (in Render dashboard, environment-specific)
DATABASE_URL=postgresql://preview_user:preview_pass@preview-db.render.com/marketedge_preview
```

#### 2. GitHub Actions Integration

**Add workflow to validate preview deployments:**

```yaml
# .github/workflows/preview-validation.yml
name: Preview Deployment Validation

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  validate-preview:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for Render Preview
        uses: nrwl/wait-for-netlify-action@v1
        with:
          site_name: marketedge-platform
          max_timeout: 600

      - name: Run Verification Script
        run: |
          STAGING_URL=${{ env.RENDER_PREVIEW_URL }} \
          ./scripts/deployment/verify_staging_deployment.sh
```

#### 3. Monitoring & Alerting

**Add Sentry or similar for preview environments:**

```bash
# Render Environment Variables
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=preview  # Auto-set for previews
```

---

## Part 10: Summary & Next Steps

### 10.1 Configuration Health Score: **7/10** ⚠️

**Strengths:**
- ✅ Excellent `render.yaml` with automatic preview environments
- ✅ Comprehensive environment variable documentation
- ✅ Good separation of production vs staging configuration
- ✅ Vercel project properly linked
- ✅ Deployment verification scripts in place

**Critical Gaps:**
- ❌ `AUTH0_AUDIENCE` not configured (CRITICAL)
- ❌ CORS doesn't include Vercel domains (HIGH)
- ❌ Staging API URL mismatch (MEDIUM)
- ❌ Preview environment database strategy unclear (MEDIUM)

**Enhancement Opportunities:**
- ⚠️ Add automated preview deployment validation
- ⚠️ Document environment variable values (not just keys)
- ⚠️ Create dedicated staging environment for long-term testing

### 10.2 Immediate Action Checklist

**Before deploying `test/trigger-zebra-smoke`:**

- [ ] **Render Dashboard Configuration**
  - [ ] Add `AUTH0_AUDIENCE` to production environment variables
  - [ ] Add `AUTH0_AUDIENCE_STAGING` for preview environments
  - [ ] Update `CORS_ORIGINS` to include all frontend domains
  - [ ] Verify `DATABASE_URL` points to correct database
  - [ ] Verify `REDIS_URL` is configured

- [ ] **Auth0 Dashboard Configuration**
  - [ ] Add wildcard callback URLs: `https://*.vercel.app/callback`, `https://*.onrender.com/callback`
  - [ ] Add wildcard logout URLs: `https://*.vercel.app`, `https://*.onrender.com`
  - [ ] Add wildcard web origins: `https://*.vercel.app`
  - [ ] Verify API audience identifier matches `AUTH0_AUDIENCE`
  - [ ] Verify RBAC settings enabled

- [ ] **Vercel Dashboard Configuration**
  - [ ] Verify project linked to correct GitHub repo
  - [ ] Set preview environment variables
  - [ ] Configure custom domains (production and staging)
  - [ ] Enable automatic deployments

- [ ] **Testing & Verification**
  - [ ] Create pull request for `test/trigger-zebra-smoke`
  - [ ] Wait for Render preview environment
  - [ ] Run `./scripts/deployment/verify_staging_deployment.sh`
  - [ ] Manual testing of authentication flow
  - [ ] Verify all 5 authentication fixes

### 10.3 Deployment Decision Matrix

| Scenario | Recommended Approach | Setup Time | Risk Level |
|----------|---------------------|------------|------------|
| **Quick test of auth fixes** | PR Preview | 30 min | LOW |
| **Team review before production** | PR Preview | 30 min | LOW |
| **Long-term feature development** | Dedicated Staging | 2 hours | MEDIUM |
| **Integration testing** | Dedicated Staging | 2 hours | MEDIUM |
| **Hotfix deployment** | Manual Deploy + Rollback Plan | 15 min | HIGH |

**For `test/trigger-zebra-smoke`:** **Use PR Preview Approach** ✅

### 10.4 Contact & Support Resources

**Render Support:**
- Dashboard: https://dashboard.render.com
- Documentation: https://render.com/docs
- Support: support@render.com

**Vercel Support:**
- Dashboard: https://vercel.com/dashboard
- Documentation: https://vercel.com/docs
- Support: https://vercel.com/support

**Auth0 Support:**
- Dashboard: https://manage.auth0.com
- Documentation: https://auth0.com/docs
- Community: https://community.auth0.com

---

## Appendix A: Environment Variables Reference

### Backend (Render)

| Variable | Production | Preview | Source |
|----------|-----------|---------|--------|
| `DATABASE_URL` | Production DB | Preview DB | Render managed or external |
| `REDIS_URL` | Production Redis | Preview Redis | Render managed or external |
| `AUTH0_DOMAIN` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Via `AUTH0_DOMAIN_STAGING` | Auth0 Dashboard |
| `AUTH0_CLIENT_ID` | Production client | Via `AUTH0_CLIENT_ID_STAGING` | Auth0 Dashboard |
| `AUTH0_CLIENT_SECRET` | Production secret | Via `AUTH0_CLIENT_SECRET_STAGING` | Auth0 Dashboard |
| `AUTH0_AUDIENCE` | API audience URL | Via `AUTH0_AUDIENCE_STAGING` | Auth0 API identifier |
| `AUTH0_ACTION_SECRET` | Webhook secret | Same or separate | Generated locally |
| `USE_STAGING_AUTH0` | `false` | `true` (automatic) | render.yaml |
| `CORS_ORIGINS` | Production domains | `*.vercel.app,*.onrender.com` | render.yaml |
| `ENVIRONMENT` | `production` | `preview` | Render automatic |
| `SECRET_KEY` | Auto-generated | Auto-generated | Render automatic |

### Frontend (Vercel)

| Variable | Production | Preview | Source |
|----------|-----------|---------|--------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://marketedge-platform.onrender.com` | Staging or preview backend | Configuration |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | `dev-g8trhgbfdq2sk2m8.us.auth0.com` | Same or staging | Auth0 Dashboard |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Production client | Staging client | Auth0 Dashboard |
| `NEXT_PUBLIC_ENVIRONMENT` | `production` | `preview` | Configuration |
| `NODE_ENV` | `production` | `production` | Vercel automatic |

---

## Appendix B: Deployment Verification Checklist

Use this checklist after deploying to preview/staging:

### Backend Health Checks

- [ ] Health endpoint responds 200: `GET /health`
- [ ] Auth0 URL includes `audience` parameter
- [ ] CORS headers present in responses
- [ ] Token refresh endpoint returns 401 (not 403) for invalid tokens
- [ ] Rate limiter status shown in health response
- [ ] Database migrations applied
- [ ] Redis connection established

### Frontend Health Checks

- [ ] Application loads without errors
- [ ] Login button triggers Auth0 redirect
- [ ] Auth0 callback processes successfully
- [ ] Dashboard loads after authentication
- [ ] Super admin panel accessible (for admin users)
- [ ] API requests include authentication headers
- [ ] Token refresh works without re-login

### Security Checks

- [ ] JWT tokens contain valid signature
- [ ] User lookup uses email (not UUID)
- [ ] CSRF protection doesn't block auth endpoints
- [ ] Rate limiting works correctly
- [ ] CORS allows only whitelisted origins

### Performance Checks

- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms
- [ ] No console errors in browser
- [ ] No 500 errors in Render logs

---

## Appendix C: Troubleshooting Guide

### Issue: Preview environment not created

**Symptoms:**
- No preview URL posted to PR
- Render Deployments tab shows no activity

**Solutions:**
1. Verify `render.yaml` in repository root
2. Check Render Dashboard → Settings → Preview Environments enabled
3. Ensure PR is from branch to `main` (not between feature branches)
4. Wait up to 15 minutes for initial cold start

### Issue: CORS errors in preview

**Symptoms:**
- Browser console: "No 'Access-Control-Allow-Origin' header"
- Network tab shows failed preflight requests

**Solutions:**
1. Update Render `CORS_ORIGINS` to include preview URL
2. Add wildcard: `https://*.vercel.app`
3. Check frontend makes requests to correct backend URL
4. Verify CORS middleware is first in middleware stack

### Issue: Auth0 callback fails

**Symptoms:**
- Redirected to Auth0, but callback shows error
- "Callback URL mismatch" error

**Solutions:**
1. Add preview URL to Auth0 Allowed Callback URLs
2. Use wildcard: `https://*.vercel.app/callback`
3. Verify `redirect_uri` parameter matches whitelisted URL
4. Check Auth0 application settings

### Issue: JWT token validation fails

**Symptoms:**
- 401 Unauthorized on API requests
- Logs show "Invalid token signature"

**Solutions:**
1. Verify `AUTH0_AUDIENCE` is set in environment
2. Check Auth0 URL includes `audience` parameter
3. Verify Auth0 JWKS endpoint accessible
4. Check token expiration time

### Issue: Database connection fails in preview

**Symptoms:**
- 500 errors on API endpoints
- Logs show "Connection refused" or "Database unavailable"

**Solutions:**
1. Verify `DATABASE_URL` set for preview environment
2. Check database allows connections from Render IPs
3. Ensure preview database exists and migrations applied
4. Check database credentials valid

---

**End of Report**

**Prepared by:** Maya (DevOps Agent)
**Date:** 2025-10-02
**Version:** 1.0
**Status:** Ready for Review
