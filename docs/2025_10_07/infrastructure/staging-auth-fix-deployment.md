# Staging Environment Authentication Fix - Deployment Guide

## Critical Issue Fixed
**Environment**: staging.zebra.associates
**Error**: "All token retrieval strategies failed" in production build
**Root Cause**: Staging environment incorrectly detected as production, causing cookie-based token storage failures

## Solution Summary

### 1. Backend CORS Configuration Update
**File**: `/app/main.py`
**Change**: Added `https://staging.zebra.associates` to allowed CORS origins

```python
critical_origins = [
    "https://app.zebra.associates",
    "https://staging.zebra.associates",  # NEW: Staging domain support
    # ... other origins
]
```

### 2. Frontend Environment Detection Enhancement
**File**: `/platform-wrapper/frontend/src/services/auth.ts`
**Change**: Enhanced `detectProductionEnvironment()` method to properly identify staging

Key improvements:
- Staging domain explicitly detected and uses development storage
- Localhost/127.0.0.1 correctly identified as development
- Domain checks occur BEFORE NODE_ENV check

## Deployment Instructions

### Backend Deployment (Render)

1. **Push changes to main branch**:
   ```bash
   git push origin main
   ```

2. **Verify Render auto-deployment**:
   - Navigate to Render dashboard
   - Check staging service: `marketedge-platform-staging`
   - Monitor deployment logs for successful build

3. **Verify CORS headers**:
   ```bash
   curl -I https://marketedge-platform-staging.onrender.com/health \
     -H "Origin: https://staging.zebra.associates"
   ```

   Expected response should include:
   ```
   Access-Control-Allow-Origin: https://staging.zebra.associates
   Access-Control-Allow-Credentials: true
   ```

### Frontend Deployment (Vercel)

1. **Push changes to staging branch**:
   ```bash
   git checkout staging
   git merge main
   git push origin staging
   ```

2. **Verify Vercel deployment**:
   - Check Vercel dashboard for automatic deployment
   - Monitor build logs for success
   - Deployment URL: https://staging.zebra.associates

3. **Environment Variables Verification**:
   Ensure these are set in Vercel:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform-staging.onrender.com
   NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
   NEXT_PUBLIC_AUTH0_CLIENT_ID=9FRjf82esKN4fx3iY337CT1jpvNVFbAP
   NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://staging.zebra.associates/callback
   ```

## Post-Deployment Verification

### 1. Authentication Flow Test

1. **Clear browser storage**:
   - Open DevTools → Application → Storage
   - Clear all site data

2. **Test login**:
   - Navigate to https://staging.zebra.associates
   - Click login
   - Complete Auth0 authentication
   - Verify successful redirect

3. **Verify token storage**:
   - Open DevTools Console
   - Should see: "🔧 Staging environment detected - using development token storage"
   - Check localStorage for `access_token`
   - No "All token retrieval strategies failed" error

### 2. API Communication Test

1. **Check authenticated API calls**:
   ```javascript
   // In browser console
   fetch('https://marketedge-platform-staging.onrender.com/api/v1/auth/me', {
     headers: {
       'Authorization': 'Bearer ' + localStorage.getItem('access_token')
     }
   }).then(r => r.json()).then(console.log)
   ```

2. **Verify response contains user data**

### 3. Cross-Domain Cookie Verification

1. **Check cookie behavior**:
   - DevTools → Application → Cookies
   - Staging should NOT rely on cross-domain cookies
   - Tokens stored in localStorage instead

## Rollback Plan

If issues occur after deployment:

### Backend Rollback
1. Revert commit in Render dashboard
2. OR manually trigger redeploy of previous version

### Frontend Rollback
1. Revert commit in Vercel dashboard
2. OR use Vercel instant rollback feature

### Emergency Fix
If token storage fails:
1. Users can use localStorage fallback
2. Clear browser storage and re-authenticate

## Key Technical Details

### Why This Fix Works

1. **Staging Detection Priority**:
   - Domain checks occur BEFORE NODE_ENV check
   - Prevents production build from overriding staging behavior

2. **Storage Strategy**:
   - Staging uses localStorage (same-origin, reliable)
   - Avoids cross-domain cookie complexities
   - Production still uses secure httpOnly cookies

3. **CORS Configuration**:
   - Backend explicitly allows staging domain
   - Enables API communication from staging frontend

### Environment Detection Logic

```typescript
// Order of checks (critical for correct behavior):
1. Is it staging.zebra.associates? → Use development storage
2. Is it localhost/127.0.0.1? → Use development storage
3. Is NODE_ENV=production? → Use production storage
4. Is it a production domain? → Use production storage
5. Default → Use development storage
```

## Monitoring

### Key Metrics to Watch

1. **Authentication Success Rate**:
   - Monitor Auth0 logs for staging tenant
   - Check for failed authentication attempts

2. **API Error Rates**:
   - Monitor 401/403 errors from staging backend
   - Check CORS rejection errors

3. **User Reports**:
   - "Cannot login" issues
   - "Session expired" complaints
   - Token retrieval errors in console

### Debug Commands

**Check staging environment detection**:
```javascript
// Run in browser console at staging.zebra.associates
console.log('Environment detected as:',
  window.location.hostname.includes('staging') ? 'STAGING' : 'OTHER')
```

**Verify token storage location**:
```javascript
// Check where tokens are stored
console.log('Cookie token:', document.cookie.includes('access_token'))
console.log('LocalStorage token:', !!localStorage.getItem('access_token'))
console.log('SessionStorage backup:', !!sessionStorage.getItem('auth_session_backup'))
```

## Success Criteria

✅ No "All token retrieval strategies failed" errors
✅ Successful login on staging.zebra.associates
✅ API calls authenticate correctly
✅ Token persistence across page refreshes
✅ Console shows "Staging environment detected" message

## Contact for Issues

**Primary**: DevOps team
**Escalation**: Backend team for API issues, Frontend team for UI issues
**Critical Issues**: Platform architect

---

**Deployment Status**: Ready for deployment
**Risk Level**: Low (staging only, with fallback options)
**Expected Downtime**: None (graceful update)