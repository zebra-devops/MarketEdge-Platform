# Staging Deployment: Authentication Fixes

**Date:** 2025-10-02
**Branch:** `test/trigger-zebra-smoke`
**Environment:** Staging (Render Preview)
**Status:** Ready for Deployment

## 📋 Executive Summary

This document provides step-by-step instructions for deploying critical authentication fixes to the staging environment. The fixes address 5 major authentication issues discovered during testing:

1. **Rate Limiter Storage Access** - Fixed incorrect storage path
2. **CSRF Token Exemptions** - Added `/api/v1/auth/refresh` to exempt paths
3. **JWT Algorithm Validation** - Fixed RSA key construction for Auth0 JWT verification
4. **Auth0 Audience Configuration** - Added `AUTH0_AUDIENCE` for JWT tokens (not opaque tokens)
5. **Auth0 User Lookup** - Changed from UUID lookup to email lookup (CRITICAL FIX)

## 🔍 Pre-Deployment Checklist

### 1. Code Verification

**Branch Status:**
```bash
# Verify branch is up to date
git checkout test/trigger-zebra-smoke
git pull origin test/trigger-zebra-smoke

# Check latest commits
git log --oneline -5
```

**Expected Latest Commits:**
- `50ee1c0` - fix: add AUTH0_AUDIENCE configuration for JWT token generation
- `bba8c4c` - docs: add comprehensive documentation for Auth0 user lookup bug fix
- `9981e5c` - fix: use email for user lookup instead of Auth0 sub to prevent UUID errors
- `6c1e4c7` - docs: add comprehensive summary of Auth0 authentication fixes
- `2c1f918` - fix: resolve Auth0 JWT algorithm validation and CSRF blocking issues

### 2. Environment Variables Required

**CRITICAL:** The following environment variables MUST be configured in Render before deployment:

#### Required for ALL Environments:
```bash
# Auth0 Configuration (Production/Main)
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET=<from 1Password/secrets vault>
AUTH0_ACTION_SECRET=<from 1Password/secrets vault>

# NEW: Auth0 API Audience (CRITICAL FIX)
# Without this, Auth0 returns opaque tokens which cannot be verified cryptographically
# With this, Auth0 returns JWT tokens that can be verified using JWKS
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# JWT Configuration
JWT_SECRET_KEY=<from 1Password/secrets vault>

# Database
DATABASE_URL=<postgres connection string>

# Redis (Optional - for rate limiting)
REDIS_URL=<redis connection string>

# CORS Configuration
CORS_ORIGINS=https://app.zebra.associates,https://*.onrender.com,http://localhost:3000
```

#### Staging/Preview Specific:
```bash
# Enable staging mode
USE_STAGING_AUTH0=true
ENVIRONMENT=staging

# Staging Auth0 Configuration (if different from production)
AUTH0_DOMAIN_STAGING=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID_STAGING=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_CLIENT_SECRET_STAGING=<staging secret>
AUTH0_AUDIENCE_STAGING=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# Enable debug logging for staging
ENABLE_DEBUG_LOGGING=true
```

## 🚀 Deployment Steps

### Option A: Deploy via Render Dashboard (Recommended)

1. **Login to Render Dashboard**
   - Navigate to: https://dashboard.render.com
   - Login with your Render credentials

2. **Select Service**
   - Find service: `marketedge-platform`
   - Click to open service details

3. **Change Deployment Branch**
   - Navigate to: **Settings** → **Build & Deploy**
   - Find: **Branch** setting
   - Change from `main` to `test/trigger-zebra-smoke`
   - Click **Save Changes**

4. **Verify Environment Variables**
   - Navigate to: **Environment** tab
   - Verify all required variables are set (see checklist above)
   - **CRITICAL:** Ensure `AUTH0_AUDIENCE` is set
   - **CRITICAL:** Ensure `USE_STAGING_AUTH0=true` for preview environments

5. **Trigger Manual Deployment**
   - Navigate to: **Manual Deploy** section
   - Select branch: `test/trigger-zebra-smoke`
   - Click: **Deploy latest commit**
   - Monitor deployment logs in real-time

### Option B: Deploy via Render API

If you have a Render API key configured:

```bash
curl -X POST "https://api.render.com/v1/services/marketedge-platform/deploys" \
  -H "Authorization: Bearer YOUR_RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "branch": "test/trigger-zebra-smoke",
    "clearCache": "do_not_clear"
  }'
```

### Option C: Create Pull Request to Staging Branch

If you have a dedicated `staging` branch that auto-deploys:

```bash
# Create PR from test branch to staging
gh pr create \
  --base staging \
  --head test/trigger-zebra-smoke \
  --title "Deploy Auth Fixes to Staging" \
  --body "Deploys 5 critical authentication fixes for staging verification"
```

## 📊 Deployment Monitoring

### 1. Monitor Deployment Logs

In Render dashboard:
- Navigate to: **Logs** tab
- Watch for these key events:

**Expected Success Indicators:**
```
✅ Application startup complete
✅ auth_url_audience_added (NEW - confirms AUTH0_AUDIENCE is configured)
✅ STAGING/PREVIEW ENVIRONMENT DETECTED (if USE_STAGING_AUTH0=true)
✅ Using staging Auth0 credentials
✅ Starting FastAPI application...
✅ Application startup complete
```

**Watch For These Events (Should NOT Appear):**
```
❌ No AUTH0_AUDIENCE configured - Auth0 will return opaque tokens
❌ Rate limiter storage access error
❌ JWT verification failed: Algorithm not allowed
❌ CSRF token validation failed for /api/v1/auth/refresh
❌ Invalid UUID format for user lookup
```

### 2. Verify Health Endpoints

Once deployment completes, verify these endpoints:

```bash
# Health check
curl https://marketedge-platform.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "staging",
  "timestamp": "2025-10-02T..."
}

# Check Auth0 URL generation (should include audience parameter)
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback"

# Expected response should include:
{
  "auth_url": "https://dev-g8trhgbfdq2sk2m8.us.auth0.com/authorize?...&audience=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/...",
  "state": "...",
  "nonce": "..."
}
```

### 3. Verify Environment Configuration

Check logs for environment confirmation:

```
📋 Environment Configuration:
   ENVIRONMENT: staging
   USE_STAGING_AUTH0: true
   AUTH0_DOMAIN: dev-g8trhgbfdq2sk2m8.us.auth0.com
   CORS_ORIGINS: https://*.onrender.com,http://localhost:3000
```

## 🧪 Post-Deployment Testing

### 1. Authentication Flow Test

**Test User:** matt.lindop@zebra.associates

1. **Navigate to staging frontend:**
   - URL: https://app.zebra.associates (or Vercel preview URL)

2. **Click "Login" button**
   - Should redirect to Auth0 login page
   - URL should include `audience` parameter (verify in browser address bar)

3. **Authenticate with Auth0:**
   - Email: matt.lindop@zebra.associates
   - Password: <from secrets>

4. **Verify callback redirect:**
   - Should redirect back to application
   - Should NOT see any errors in browser console
   - Should NOT see 401 or 500 errors

5. **Check dashboard access:**
   - Verify user is logged in
   - Check super_admin role is applied
   - Verify admin panel is accessible

### 2. API Endpoint Verification

Test these critical endpoints:

```bash
# Get access token from browser localStorage/cookies
export ACCESS_TOKEN="<token from browser>"

# Test protected endpoint
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://marketedge-platform.onrender.com/api/v1/users/me

# Expected: 200 OK with user data (not 401)

# Test token refresh (should NOT be blocked by CSRF)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}' \
  https://marketedge-platform.onrender.com/api/v1/auth/refresh

# Expected: 200 OK with new access token (not 401/403)
```

### 3. Verify Log Events

Check Render logs for these specific fixes:

**✅ Rate Limiter Fix:**
```
Storage accessed via: self.limiter.limiter.storage
(Should NOT see: AttributeError: 'Limiter' object has no attribute 'storage')
```

**✅ CSRF Exemption Fix:**
```
/api/v1/auth/refresh request processed successfully
(Should NOT see: CSRF token validation failed)
```

**✅ JWT Algorithm Fix:**
```
JWT verification successful using Auth0 JWKS
(Should NOT see: Algorithm not allowed)
```

**✅ Auth0 Audience Fix:**
```
API audience added to auth request for JWT tokens
audience: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
(Should NOT see: No AUTH0_AUDIENCE configured)
```

**✅ Email Lookup Fix:**
```
User lookup by email: matt.lindop@zebra.associates
(Should NOT see: Invalid UUID format)
```

## 🔄 Rollback Procedures

If deployment fails or causes critical issues:

### Immediate Rollback

**Via Render Dashboard:**

1. Navigate to: **Deployments** tab
2. Find previous successful deployment
3. Click: **Redeploy** on last known good deployment
4. Monitor rollback logs

**Via Render API:**

```bash
# Get previous deployment ID
curl "https://api.render.com/v1/services/marketedge-platform/deploys" \
  -H "Authorization: Bearer YOUR_RENDER_API_KEY"

# Rollback to specific deployment
curl -X POST "https://api.render.com/v1/services/marketedge-platform/deploys/PREVIOUS_DEPLOY_ID/rollback" \
  -H "Authorization: Bearer YOUR_RENDER_API_KEY"
```

**Via Git Branch Revert:**

1. Navigate to: **Settings** → **Build & Deploy**
2. Change **Branch** back to `main`
3. Click: **Save Changes**
4. Service will auto-deploy from `main` branch

### Rollback Verification

After rollback, verify:

```bash
# Check health endpoint
curl https://marketedge-platform.onrender.com/health

# Verify previous version is deployed
curl https://marketedge-platform.onrender.com/api/v1/version
```

## ⚠️ Known Issues & Mitigations

### Issue 1: Cold Start Delays (52+ seconds)

**Symptom:** First request after deployment takes 52+ seconds
**Mitigation:**
- Warm up application after deployment
- Use health check endpoint: `/health`
- Consider upgrading to paid Render plan for persistent instances

### Issue 2: Missing AUTH0_AUDIENCE Environment Variable

**Symptom:** Logs show "No AUTH0_AUDIENCE configured"
**Impact:** Auth0 returns opaque tokens instead of JWT tokens
**Fix:**
1. Add `AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/` to Render environment variables
2. Redeploy service

### Issue 3: Database Migration Failures

**Symptom:** Deployment fails during migration phase
**Mitigation:**
1. Check `RUN_MIGRATIONS` environment variable (should be `true` for production, auto-handled for staging)
2. Review migration logs in Render dashboard
3. If needed, set `RUN_MIGRATIONS=false` and run migrations manually

## 📈 Success Criteria

Deployment is considered successful when ALL of the following are verified:

- [ ] Service deploys without errors
- [ ] Health check endpoint returns `200 OK`
- [ ] Auth0 URL generation includes `audience` parameter
- [ ] User can login with matt.lindop@zebra.associates
- [ ] Protected endpoints return `200 OK` (not 401/500)
- [ ] Token refresh works without CSRF errors
- [ ] No rate limiter errors in logs
- [ ] No JWT verification errors in logs
- [ ] No "invalid UUID" errors in logs
- [ ] Super admin panel is accessible

## 🎯 Next Steps After Successful Staging Deployment

1. **Monitor Staging for 24-48 hours**
   - Check logs for any unexpected errors
   - Verify user authentication flows work consistently
   - Monitor performance metrics

2. **Run Full Test Suite**
   - Execute Zebra smoke tests: `npm run test:e2e`
   - Run integration tests: `pytest tests/`
   - Verify multi-tenant isolation

3. **Create Production Deployment Plan**
   - Document staging results
   - Schedule production deployment window
   - Prepare production rollback procedures
   - Notify stakeholders of deployment timeline

4. **Merge to Main Branch** (after staging validation)
   ```bash
   git checkout main
   git merge test/trigger-zebra-smoke
   git push origin main
   ```

## 📞 Emergency Contacts

**If deployment fails and requires immediate attention:**

- **DevOps Lead:** [Contact information]
- **Backend Lead:** [Contact information]
- **On-Call Engineer:** [Contact information]
- **Render Support:** support@render.com (paid plans only)

## 📚 Related Documentation

- [Auth0 Security Fixes Summary](../AUTH0_SECURITY_FIXES.md)
- [Auth0 User Lookup Bug Fix](../AUTH0_USER_LOOKUP_BUG_FIX.md)
- [Render Deployment Configuration](../../render.yaml)
- [Environment Variables Guide](../../.env.example)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Author:** Maya (DevOps Agent)
