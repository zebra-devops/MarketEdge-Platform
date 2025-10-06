# US-AUTH-3: Atomic Auth State - QA Testing Guide

## Overview

This feature implements atomic authentication state transactions to eliminate race conditions that cause intermittent logout issues. The implementation adds a new storage mechanism that persists tokens and user data in a single transaction, preventing "ghost auth states."

## What Changed

### Technical Changes
- New `AuthStateV2` schema with version 2.0
- Atomic write/read operations for auth state
- Rollback mechanism on storage failures
- Runtime feature flag for gradual rollout
- Legacy storage cleanup migration

### Files Modified
- `/src/services/auth.ts` - Core implementation
- `/src/services/__tests__/auth.atomic.test.ts` - Unit tests (17 tests, all passing)
- `/e2e/auth-navigation.spec.ts` - E2E tests (6 scenarios)

## Testing Instructions

### Prerequisites
1. Access to staging environment
2. Chrome, Safari, and Firefox browsers for testing
3. Ability to open browser DevTools (Console + Application tabs)

### Test 1: Enable Atomic Auth via URL Parameter

**Purpose**: Verify feature flag works via URL parameter

**Steps**:
1. Navigate to login page: `https://[staging-url]/login?atomicAuth=1`
2. Open DevTools Console
3. Complete login flow
4. Look for console message: `"✅ Atomic auth state persisted successfully"`
5. Open DevTools > Application > Session Storage
6. Verify key `za:auth:v2` exists with complete JSON structure

**Expected Result**:
```json
{
  "version": "2.0",
  "access_token": "[token]",
  "refresh_token": "[token]",
  "user": {...},
  "tenant": {...},
  "permissions": [...],
  "expires_at": "[ISO timestamp]",
  "persisted_at": [unix timestamp]
}
```

**Pass/Fail**: ⬜

---

### Test 2: Enable Atomic Auth via localStorage

**Purpose**: Verify feature flag works via localStorage setting (for QA/UAT)

**Steps**:
1. Navigate to login page: `https://[staging-url]/login`
2. Open DevTools Console
3. Run: `localStorage.setItem('za:feature:atomic_auth', 'true')`
4. Refresh page
5. Complete login flow
6. Verify console shows: `"🔐 US-AUTH-3: Using atomic auth state transaction"`
7. Check Session Storage for `za:auth:v2` key

**Expected Result**:
- Atomic auth state persisted
- Login successful
- No logout issues after navigation

**Pass/Fail**: ⬜

---

### Test 3: Navigation Interruption (Critical Test)

**Purpose**: Verify atomic auth prevents "ghost auth state" during navigation

**Steps**:
1. Enable atomic auth: `?atomicAuth=1`
2. Start login flow
3. **Immediately after clicking login**, navigate to dashboard: `/dashboard`
4. Observe console logs
5. Verify user remains authenticated
6. Check API calls succeed (no 401 errors)

**Expected Result**:
- User stays authenticated
- No "Please log in" messages
- Dashboard data loads successfully
- Session Storage has complete auth state

**Pass/Fail**: ⬜

---

### Test 4: Browser Storage Quota Handling

**Purpose**: Verify graceful error handling when storage is full

**Steps**:
1. Open DevTools Console
2. Fill localStorage with data:
   ```javascript
   for (let i = 0; i < 1000; i++) {
     try {
       localStorage.setItem('filler_' + i, 'x'.repeat(100000))
     } catch (e) {
       break
     }
   }
   ```
3. Try to log in with atomic auth enabled
4. Observe error message

**Expected Result**:
- Clear error message: "Browser storage quota exceeded - please clear browser data"
- No partial auth state left behind
- User prompted to clear browser data

**Pass/Fail**: ⬜

---

### Test 5: Token Expiry Handling

**Purpose**: Verify expired tokens are rejected and cleared

**Steps**:
1. Enable atomic auth
2. Log in successfully
3. Open DevTools > Application > Session Storage
4. Edit `za:auth:v2` key, change `expires_at` to past date
5. Refresh page
6. Try to access protected route

**Expected Result**:
- Expired state detected and cleared
- Console shows: `"Auth state expired, clearing"`
- User redirected to login
- Session Storage `za:auth:v2` key removed

**Pass/Fail**: ⬜

---

### Test 6: Schema Version Validation

**Purpose**: Verify forward compatibility with version checking

**Steps**:
1. Enable atomic auth
2. Log in successfully
3. Open DevTools > Application > Session Storage
4. Edit `za:auth:v2` key, change `version` to `"1.0"`
5. Refresh page

**Expected Result**:
- Console shows: `"Auth state schema mismatch, clearing"`
- Invalid state cleared
- User redirected to login

**Pass/Fail**: ⬜

---

### Test 7: Legacy Path Fallback (Default Behavior)

**Purpose**: Verify existing auth works when atomic auth is disabled

**Steps**:
1. Navigate to login **without** `?atomicAuth=1` parameter
2. Do NOT set localStorage flag
3. Complete login flow
4. Verify login succeeds
5. Check console - should NOT see atomic auth messages

**Expected Result**:
- Login works normally
- Existing storage keys used (`access_token`, `current_user`, etc.)
- No atomic auth messages in console
- Backward compatibility maintained

**Pass/Fail**: ⬜

---

### Test 8: Cross-Browser Compatibility

**Purpose**: Verify atomic auth works across browsers

**Browsers to Test**:
- [ ] Chrome/Chromium
- [ ] Safari
- [ ] Firefox
- [ ] Edge (optional)

**Steps** (repeat for each browser):
1. Navigate to: `[staging-url]/login?atomicAuth=1`
2. Complete login flow
3. Navigate between pages (dashboard, settings, reports)
4. Log out and log back in
5. Close tab and reopen (should require re-login)

**Expected Result**:
- Login works in all browsers
- Navigation persistence works
- Tab closure properly clears session storage
- No browser-specific errors

**Pass/Fail**:
- Chrome: ⬜
- Safari: ⬜
- Firefox: ⬜
- Edge: ⬜

---

### Test 9: Legacy Migration Cleanup

**Purpose**: Verify old storage keys are cleaned up

**Steps**:
1. Manually set old storage keys:
   ```javascript
   localStorage.setItem('access_token', 'old_token')
   localStorage.setItem('refresh_token', 'old_refresh')
   localStorage.setItem('token_expires_at', new Date().toISOString())
   ```
2. Enable atomic auth: `localStorage.setItem('za:feature:atomic_auth', 'true')`
3. Log in successfully
4. Check localStorage

**Expected Result**:
- Old keys removed: `access_token`, `refresh_token`, `token_expires_at`, `auth_session_backup`
- New key present: `za:auth:v2`
- Migration flag set: `za:auth:migrated = "true"`
- Console shows: `"✅ Legacy auth storage cleaned up"`

**Pass/Fail**: ⬜

---

### Test 10: Admin Panel Access (Zebra Associates Critical)

**Purpose**: Verify atomic auth doesn't break admin workflows

**Prerequisites**: Super admin account (matt.lindop@zebra.associates)

**Steps**:
1. Log in with `?atomicAuth=1`
2. Navigate to admin panel: `/admin/feature-flags`
3. Toggle a feature flag
4. Navigate to dashboard
5. Return to admin panel
6. Verify changes persisted

**Expected Result**:
- Admin panel loads successfully
- Feature flag changes work
- Navigation doesn't logout admin
- Permissions persist across navigation

**Pass/Fail**: ⬜

---

## Rollback Plan

If critical issues are found during QA:

### Immediate Rollback
1. No code deployment needed - feature is behind flag
2. Disable globally by setting default return value in `useAtomicAuth()` to `false`
3. Or instruct affected users to clear: `localStorage.removeItem('za:feature:atomic_auth')`

### Clear User State
If users experience issues:
```javascript
// Run in browser console
sessionStorage.removeItem('za:auth:v2')
localStorage.removeItem('za:auth:v2')
localStorage.removeItem('za:auth:migrated')
localStorage.removeItem('za:feature:atomic_auth')
location.reload()
```

## Success Metrics

After QA sign-off and production rollout, monitor:
- **Auth failure rate**: Should be < 0.1% during navigation
- **Ghost auth states**: Zero reports
- **Support tickets**: Reduced logout-related tickets
- **Performance**: No degradation in login time

## Questions or Issues?

Contact:
- **Tech Lead**: Review GitHub Issue #92
- **QA Lead**: Document findings in issue comments
- **DevOps**: Staging environment setup questions

---

## QA Sign-Off

**Tester Name**: ___________________

**Date**: ___________________

**Overall Assessment**:
- [ ] All tests passed
- [ ] Minor issues found (document below)
- [ ] Major issues found - recommend rollback

**Notes**:
```
[Add any observations, edge cases found, or recommendations]
```

**Recommendation**:
- [ ] Approve for production rollout
- [ ] Request fixes before production
- [ ] Reject - needs significant rework
