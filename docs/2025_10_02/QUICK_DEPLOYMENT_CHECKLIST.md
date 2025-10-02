# Quick Deployment Checklist - test/trigger-zebra-smoke

**Target:** Deploy authentication fixes to preview environment
**Estimated Time:** 70 minutes
**Risk Level:** LOW (using PR preview approach)

---

## Pre-Deployment Setup (30 minutes)

### 1. Render Dashboard Configuration

**URL:** https://dashboard.render.com → Services → marketedge-platform → Environment

**Add These Variables:**

```bash
# CRITICAL - Without this, Auth0 returns opaque tokens
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

# For preview environments
AUTH0_AUDIENCE_STAGING=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
AUTH0_DOMAIN_STAGING=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID_STAGING=<your-staging-client-id>
AUTH0_CLIENT_SECRET_STAGING=<your-staging-client-secret>
```

**Update This Variable:**

```bash
# OLD VALUE:
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com

# NEW VALUE:
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app
```

**Verify These Settings:**
- [ ] Preview Environments: ENABLED
- [ ] Preview Expiration: 7 days
- [ ] `USE_STAGING_AUTH0`: Already configured in render.yaml (no action needed)

---

### 2. Auth0 Dashboard Configuration

**URL:** https://manage.auth0.com → Applications → [Your App]

**Update Application URIs:**

**Allowed Callback URLs:**
```
http://localhost:3000/callback,
https://app.zebra.associates/callback,
https://staging.zebra.associates/callback,
https://*.vercel.app/callback,
https://*.onrender.com/callback
```

**Allowed Logout URLs:**
```
http://localhost:3000,
https://app.zebra.associates,
https://staging.zebra.associates,
https://*.vercel.app,
https://*.onrender.com
```

**Allowed Web Origins:**
```
http://localhost:3000,
https://app.zebra.associates,
https://staging.zebra.associates,
https://*.vercel.app
```

**Verify API Configuration:**
- [ ] Navigate: APIs → [Your API]
- [ ] Verify Identifier: `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/`
- [ ] Verify Signing Algorithm: `RS256`
- [ ] Enable RBAC: YES
- [ ] Add Permissions in Access Token: YES

---

### 3. Vercel Dashboard Configuration

**URL:** https://vercel.com/dashboard → [Your Project]

**Settings → Environment Variables → Preview:**

```bash
NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform.onrender.com  # Or staging backend
NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=<your-staging-or-production-client-id>
NEXT_PUBLIC_ENVIRONMENT=preview
```

**Settings → Git:**
- [ ] Verify: GitHub integration active
- [ ] Verify: Repository `zebra-devops/MarketEdge-Platform`
- [ ] Verify: Automatic deployments enabled

---

## Deployment (40 minutes)

### 4. Create Pull Request

```bash
# Ensure you're on the correct branch
git checkout test/trigger-zebra-smoke
git pull origin test/trigger-zebra-smoke

# Push to ensure remote is up to date
git push origin test/trigger-zebra-smoke

# Create PR using GitHub CLI
gh pr create \
  --title "🔒 Authentication Fixes - Critical Security Updates" \
  --body "Deploys authentication fixes including:\n- Auth0 JWT signature verification\n- AUTH0_AUDIENCE configuration\n- Token refresh flow consistency\n- Rate limiter storage access fix\n- User lookup by email" \
  --base main \
  --head test/trigger-zebra-smoke \
  --label "security,authentication,critical"

# Or create via GitHub UI: https://github.com/zebra-devops/MarketEdge-Platform/compare
```

### 5. Monitor Preview Creation

**Render:**
- [ ] Go to: https://dashboard.render.com → marketedge-platform → Deployments
- [ ] Wait for preview environment (5-10 minutes)
- [ ] Note preview URL: `https://marketedge-platform-pr-<number>.onrender.com`
- [ ] Check for deployment errors in logs

**Vercel:**
- [ ] Check GitHub PR for Vercel deployment comment
- [ ] Note preview URL: `https://test-trigger-zebra-smoke-<project>.vercel.app`
- [ ] Wait for build completion (~3-5 minutes)

### 6. Run Automated Verification

```bash
# Replace <render-preview-url> with actual URL from step 5
STAGING_URL=https://marketedge-platform-pr-<number>.onrender.com \
FRONTEND_URL=https://test-trigger-zebra-smoke-<project>.vercel.app \
./scripts/deployment/verify_staging_deployment.sh
```

**Expected Results:**
- ✅ Health check passes (200 OK)
- ✅ Auth0 URL includes `audience` parameter
- ✅ CORS headers present
- ✅ Token refresh returns 401 (not 403 - CSRF exempt)
- ✅ Rate limiter status available

**If Any Test Fails:**
- Check Render logs for errors
- Verify environment variables set correctly
- Ensure Auth0 callback URLs include preview domains
- Review CORS configuration

---

## Manual Testing (15 minutes)

### 7. Authentication Flow Test

**Visit Vercel Preview URL:**

1. **Home Page Load**
   - [ ] Page loads without errors
   - [ ] No console errors in browser DevTools
   - [ ] Login button visible

2. **Login Flow**
   - [ ] Click "Login" button
   - [ ] Redirected to Auth0 login page
   - [ ] Login with: `matt.lindop@zebra.associates`
   - [ ] Successfully redirected back to application
   - [ ] Dashboard loads without errors

3. **Authentication Verification**
   - [ ] Open browser DevTools → Application → Cookies
   - [ ] Verify `access_token` cookie present
   - [ ] Verify `refresh_token` cookie present (httpOnly)
   - [ ] Check Network tab: API requests include Authorization header

4. **Super Admin Access**
   - [ ] Navigate to admin panel
   - [ ] Verify feature flags visible
   - [ ] Check organization management access
   - [ ] Confirm super admin role permissions work

5. **Token Refresh Test**
   - [ ] Wait for token to approach expiration (30 min default)
   - [ ] Or: Delete access_token cookie and refresh page
   - [ ] Verify: Token refresh happens automatically
   - [ ] Verify: No redirect to login page

### 8. Review Render Logs

**Render Dashboard → Logs:**

Search for these log entries to verify fixes:

```
# Fix #1: Rate limiter storage access
✅ Search: "limiter.storage" or "rate_limiter"
✅ Expected: Successful storage access, no AttributeError

# Fix #2: CSRF exempt paths
✅ Search: "CSRF" and "/api/v1/auth/refresh"
✅ Expected: Refresh endpoint not blocked

# Fix #3: JWT verification
✅ Search: "JWKS" or "JWT verification"
✅ Expected: Successful signature verification

# Fix #4: AUTH0_AUDIENCE
✅ Search: "audience"
✅ Expected: Audience parameter in Auth0 requests

# Fix #5: User lookup by email
✅ Search: "user lookup" or "matt.lindop@zebra.associates"
✅ Expected: User found by email, not UUID
```

**Critical Errors to Watch For:**
- ❌ `AttributeError: 'NoneType' object has no attribute 'limiter'`
- ❌ `CSRF validation failed`
- ❌ `Invalid token signature`
- ❌ `User not found: auth0|<uuid>`

---

## Production Deployment (5 minutes)

### 9. Merge to Production

**If all tests pass:**

```bash
# Merge PR via GitHub CLI
gh pr merge <pr-number> --squash --delete-branch

# Or via GitHub UI with these settings:
# - Merge method: Squash and merge
# - Delete branch after merge: YES
```

### 10. Monitor Production Deployment

**Render Production:**
- [ ] Go to: https://dashboard.render.com → marketedge-platform → Deployments
- [ ] Monitor deployment progress (5-10 minutes)
- [ ] Watch logs for errors
- [ ] Wait for "Live" status

**Vercel Production:**
- [ ] Check: https://vercel.com/dashboard → Deployments
- [ ] Verify: Production deployment triggered
- [ ] Monitor build status
- [ ] Wait for "Ready" status

### 11. Production Health Check

```bash
# Backend health
curl https://marketedge-platform.onrender.com/health | jq

# Expected: 200 OK with health status

# Auth0 URL check
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback" | grep "audience="

# Expected: audience parameter present
```

**Manual Production Test:**
1. Visit: https://app.zebra.associates
2. Login with: matt.lindop@zebra.associates
3. Verify: Dashboard loads successfully
4. Check: Super admin panel accessible
5. Monitor: No errors in console or logs

---

## Rollback Plan (If Issues Occur)

### Emergency Rollback

**If critical issues in production:**

1. **Render Rollback:**
   ```
   Render Dashboard → marketedge-platform → Deployments
   → Find previous successful deployment
   → Click "Redeploy"
   ```

2. **Vercel Rollback:**
   ```
   Vercel Dashboard → Deployments
   → Find previous production deployment
   → Click "..." → "Promote to Production"
   ```

3. **GitHub Revert:**
   ```bash
   # If merge caused issues, revert the merge commit
   git revert -m 1 <merge-commit-sha>
   git push origin main
   ```

### Partial Rollback (Environment Variables Only)

**If only configuration issue:**

1. Render Dashboard → Environment Variables
2. Revert changed variables to previous values
3. Click "Save"
4. Deployment auto-restarts

---

## Post-Deployment Verification

### 12. Production Monitoring (24 hours)

**Monitor these metrics:**

- [ ] **Error Rate:** Should remain < 1%
- [ ] **Response Time:** Should remain < 500ms average
- [ ] **Authentication Success Rate:** Should be > 95%
- [ ] **Token Refresh Rate:** Monitor for failures

**Tools:**
- Render Dashboard → Logs (filter by ERROR)
- Sentry (if configured) → Error tracking
- Browser console → Check for JS errors
- Network tab → Monitor API response codes

**Specific Checks:**

```bash
# Every 6 hours for first 24 hours
curl https://marketedge-platform.onrender.com/health

# Check authentication endpoint
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback"

# Manual login test
# Visit app.zebra.associates and login
```

---

## Critical Issues & Solutions

### Issue: AUTH0_AUDIENCE not set

**Symptoms:**
- Login fails after Auth0 redirect
- Logs show "Invalid token" or "Opaque token received"

**Solution:**
```bash
# Render Dashboard → Environment Variables → Add
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
```

### Issue: CORS blocks frontend requests

**Symptoms:**
- Browser console: "No 'Access-Control-Allow-Origin' header"
- API requests fail with 0 status code

**Solution:**
```bash
# Render Dashboard → Environment Variables → Update CORS_ORIGINS
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://*.vercel.app
```

### Issue: Auth0 callback URL not whitelisted

**Symptoms:**
- After Auth0 login, error: "Callback URL mismatch"

**Solution:**
```
Auth0 Dashboard → Applications → [Your App] → Settings
→ Allowed Callback URLs → Add preview URL
```

### Issue: Preview environment not created

**Symptoms:**
- No preview URL in PR comments after 15 minutes

**Solution:**
1. Check render.yaml exists in repo root
2. Verify Render Dashboard → Settings → Preview Environments: ENABLED
3. Ensure PR is from feature branch to `main` branch
4. Check Render Dashboard → Logs for build errors

---

## Success Criteria

**Preview deployment is successful when:**
- ✅ All automated verification tests pass
- ✅ Manual authentication flow works end-to-end
- ✅ Super admin panel accessible
- ✅ Token refresh works without re-login
- ✅ No errors in Render or browser logs
- ✅ All 5 authentication fixes verified in logs

**Production deployment is successful when:**
- ✅ All preview success criteria met
- ✅ Production health endpoint returns 200
- ✅ matt.lindop@zebra.associates can login
- ✅ No increase in error rate (< 1%)
- ✅ No increase in response time (< 500ms avg)
- ✅ 24-hour monitoring shows stability

---

## Contact & Support

**If you encounter issues:**

1. **Check Logs:**
   - Render: https://dashboard.render.com → marketedge-platform → Logs
   - Vercel: https://vercel.com/dashboard → [Project] → Deployments → Logs
   - Browser: DevTools → Console

2. **Review Configuration:**
   - Compare actual values against this checklist
   - Verify all environment variables set correctly
   - Check Auth0 settings match documentation

3. **Run Diagnostics:**
   ```bash
   # Use verification script
   ./scripts/deployment/verify_staging_deployment.sh

   # Check specific endpoints
   curl https://marketedge-platform.onrender.com/health
   ```

4. **Escalate if Needed:**
   - Render Support: support@render.com
   - Vercel Support: https://vercel.com/support
   - Auth0 Support: https://community.auth0.com

---

**Prepared by:** Maya (DevOps Agent)
**Date:** 2025-10-02
**Branch:** test/trigger-zebra-smoke
**Commit:** 8534897

**Ready to Deploy!** ✅
