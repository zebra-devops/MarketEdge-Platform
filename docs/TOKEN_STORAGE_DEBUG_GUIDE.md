# Token Storage Debugging Guide

## Problem Summary

**Symptoms:**
- ✅ User successfully authenticates with Auth0 (no errors)
- ✅ User profile data is stored in localStorage
- ❌ Access token is NOT stored in any storage method
- ❌ Refresh token is NOT stored
- ❌ User is not redirected properly after callback

**Console Shows:**
```
✅ User data retrieved from localStorage {source: 'localStorage', email: 'matt.lindop@zebra.associates', role: 'super_admin'}
Token Status: {accessToken: 'MISSING', refreshToken: 'MISSING', storedUser: 'matt.lindop@zebra.associates (super_admin)'}
⚠️ No access token found in any storage method
⚠️ Auth service reports user as not authenticated
```

## Root Cause Hypotheses

### Hypothesis 1: Token Validation Failing
**File:** `/platform-wrapper/frontend/src/services/auth.ts` lines 826-843

The `setTokens()` method has strict validation that throws errors if tokens are empty:

```typescript
if (!tokenResponse.access_token || tokenResponse.access_token.trim() === '') {
  throw new Error('Invalid access token received from backend - token is empty')
}
```

**Test:** Check if backend is returning empty strings instead of valid JWT tokens.

### Hypothesis 2: Race Condition
**File:** `/platform-wrapper/frontend/src/app/callback/page.tsx` lines 114-172

The redirect might happen before cookies are set by the browser:
- Backend returns tokens in response body
- Backend also sets cookies via Set-Cookie headers
- Frontend redirects too fast, before cookies propagate

**Test:** Check if the 500ms delay is sufficient for cookie propagation.

### Hypothesis 3: Cookie Domain/Path Mismatch
**Backend:** Backend sets cookies with specific domain/path settings
**Frontend:** Frontend can't read cookies due to domain/path mismatch

**Test:** Check if cookies are being set but with wrong domain/path attributes.

### Hypothesis 4: Silent Storage Failure
**File:** `/platform-wrapper/frontend/src/services/auth.ts` lines 847-883

LocalStorage or SessionStorage might be failing silently due to:
- Browser privacy settings
- Storage quota exceeded
- Corrupted storage

**Test:** Check for exceptions in storage operations.

## Diagnostic Flow (Now Implemented)

### Enhanced Logging Added

**Commit:** `4f2d79a - fix: add comprehensive token storage diagnostics`

The following diagnostic logging has been added:

#### Callback Page Flow
```
🔐 CALLBACK FLOW STEP 1: Processing auth code
🔐 CALLBACK FLOW STEP 2: Exchanging code for tokens via backend
🔐 CALLBACK FLOW STEP 3: Backend exchange successful
🔐 CALLBACK FLOW STEP 4: Verifying token storage
🔐 CALLBACK FLOW STEP 5: Token storage verification results
🔐 CALLBACK FLOW STEP 6: Waiting for cookie propagation (500ms)
🔐 CALLBACK FLOW STEP 7: Post-delay token verification
🔐 CALLBACK FLOW STEP 8: Redirecting to destination
```

#### Auth Service Token Storage
```
🔐 AUTH SERVICE: setTokens() called with: {full token details}
✅ Token validation passed, proceeding with storage
🔐 AUTH SERVICE: Storing access token
✅ Temporary token stored in memory
✅ Session storage backup created
✅ LocalStorage token stored successfully (dev)
🔐 AUTH SERVICE: Starting cookie availability detection
🔐 Cookie check attempt 1/10: {cookie details}
```

## How to Use the Diagnostics

### Step 1: Reproduce the Issue
1. Clear all browser storage (cookies, localStorage, sessionStorage)
2. Open browser DevTools Console
3. Navigate to `/login`
4. Click "Login with Auth0"
5. Complete Auth0 authentication

### Step 2: Analyze the Console Output

Look for these critical checkpoints:

**✅ Success Indicators:**
```
🔐 CALLBACK FLOW STEP 3: Backend exchange successful {hasAccessToken: true, hasRefreshToken: true}
🔐 AUTH SERVICE: setTokens() called with: {accessTokenLength: 500+}
✅ Token validation passed, proceeding with storage
✅ Temporary token stored in memory
✅ Session storage backup created
✅ LocalStorage token stored successfully
```

**❌ Failure Indicators:**
```
❌ CRITICAL: Cannot store empty access token
❌ CRITICAL: Cannot store empty refresh token
❌ Session storage backup failed
❌ LocalStorage storage failed
⚠️ CRITICAL: Cookies not accessible after 5 seconds
```

### Step 3: Identify the Breaking Point

**If Step 3 shows no tokens:**
- Backend is not returning tokens
- Check backend `/api/v1/auth/login-oauth2` endpoint
- Check Auth0 configuration (refresh token grant type enabled)

**If tokens exist in Step 3 but validation fails:**
- Tokens are empty strings or invalid
- Check backend token exchange logic
- Check Auth0 token response format

**If validation passes but storage fails:**
- Browser storage is blocked or corrupted
- Check browser privacy settings
- Try incognito mode
- Clear all storage and retry

**If storage succeeds but cookies never appear:**
- Cookie domain/path mismatch
- Check backend cookie settings
- Check if SameSite=None requires Secure flag (HTTPS)

## Storage Locations Checked

The system checks tokens in this order:

1. **Cookies** (primary in production)
   - `Cookies.get('access_token')`
   - Set by backend via `Set-Cookie` headers

2. **Temporary Memory** (immediate fallback)
   - `authService.temporaryAccessToken`
   - Set immediately on login response

3. **Session Storage** (navigation persistence)
   - `sessionStorage.getItem('auth_session_backup')`
   - Survives page navigation, cleared on tab close

4. **Local Storage** (development fallback)
   - `localStorage.getItem('access_token')`
   - Only used in development (NODE_ENV !== 'production')

## Expected Token Flow

```
1. User clicks "Login with Auth0"
   ↓
2. Redirect to Auth0 login page
   ↓
3. Auth0 authenticates user
   ↓
4. Redirect to /callback?code=AUTH_CODE
   ↓
5. Frontend exchanges code for tokens via POST /api/v1/auth/login-oauth2
   ↓
6. Backend calls Auth0 token endpoint
   ↓
7. Backend receives {access_token, refresh_token} from Auth0
   ↓
8. Backend sets cookies: Set-Cookie: access_token=...; Set-Cookie: refresh_token=...
   ↓
9. Backend returns JSON: {access_token, refresh_token, user, tenant, permissions}
   ↓
10. Frontend calls authService.login(loginData)
    ↓
11. authService.setTokens(response) is called
    ↓
12. Token validation: check tokens are not empty
    ↓
13. Store in temporary memory (immediate)
    ↓
14. Store in sessionStorage (navigation persistence)
    ↓
15. Store in localStorage (development only)
    ↓
16. Wait 500ms for browser to process Set-Cookie headers
    ↓
17. Verify cookies are accessible via document.cookie
    ↓
18. Redirect to /dashboard (or intended destination)
```

## Common Issues and Solutions

### Issue 1: Tokens Are Empty Strings
**Symptom:** `❌ CRITICAL: Cannot store empty access token`

**Cause:** Auth0 configuration issue or backend not handling token exchange properly

**Solution:**
1. Check Auth0 Application Settings → Advanced → Grant Types → Ensure "Authorization Code" and "Refresh Token" are enabled
2. Check backend logs for Auth0 API errors
3. Verify Auth0 credentials in `.env` file

### Issue 2: Cookies Not Setting
**Symptom:** `⚠️ CRITICAL: Cookies not accessible after 5 seconds`

**Cause:** Cookie domain/path/SameSite issues

**Solution:**
1. Check backend cookie settings in `app/core/config.py`
2. Ensure SameSite=None has Secure=True (requires HTTPS)
3. Check cookie domain matches frontend domain
4. Check cookie path is "/" (accessible everywhere)

### Issue 3: LocalStorage Quota Exceeded
**Symptom:** `❌ LocalStorage storage failed: QuotaExceededError`

**Cause:** Browser storage full

**Solution:**
1. Clear browser storage: DevTools → Application → Storage → Clear Site Data
2. Check for other apps using same domain storing large data
3. Reduce data stored in localStorage

### Issue 4: Session Storage Corrupted
**Symptom:** `❌ Session storage backup failed: JSON parse error`

**Cause:** Invalid JSON in sessionStorage

**Solution:**
1. Clear sessionStorage: `sessionStorage.clear()`
2. Refresh page
3. Retry authentication

## Testing Checklist

Before marking the issue as resolved, verify:

- [ ] Console shows Step 3 with `hasAccessToken: true, hasRefreshToken: true`
- [ ] Console shows `✅ Token validation passed`
- [ ] Console shows `✅ Temporary token stored in memory`
- [ ] Console shows `✅ Session storage backup created`
- [ ] Console shows `✅ LocalStorage token stored successfully` (dev mode)
- [ ] Console shows `✅ Cookie-based token access confirmed` within 5 seconds
- [ ] After redirect, `localStorage.getItem('access_token')` returns JWT token (dev)
- [ ] After redirect, `document.cookie` contains `access_token=` (production)
- [ ] After redirect, user is shown dashboard/intended page
- [ ] After refresh, user remains authenticated

## Next Steps

1. **Reproduce issue with enhanced logging** - Follow "How to Use the Diagnostics" above
2. **Identify exact failure point** - Note which step shows the first error
3. **Apply targeted fix** - Based on the failure point identified
4. **Verify fix** - Run through Testing Checklist
5. **Report findings** - Share console output showing success/failure

## Files Modified

- `/Users/matt/Sites/MarketEdge/platform-wrapper/frontend/src/app/callback/page.tsx`
  - Added 8-step diagnostic flow
  - Added token storage verification
  - Added 500ms cookie propagation delay

- `/Users/matt/Sites/MarketEdge/platform-wrapper/frontend/src/services/auth.ts`
  - Enhanced setTokens() logging
  - Added per-attempt cookie detection logging
  - Added storage operation error handling

## Support

If issue persists after following this guide:

1. Capture full console output from login to redirect
2. Check Network tab for `/api/v1/auth/login-oauth2` response
3. Check Application tab for cookies, localStorage, sessionStorage
4. Share findings for further investigation

---

**Status:** LOCAL ONLY
**Branch:** test/trigger-zebra-smoke
**Commit:** 4f2d79a
**Next:** Test authentication flow with enhanced logging
