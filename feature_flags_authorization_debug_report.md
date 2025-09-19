# Feature Flags Authorization Debug Report

**Date:** 2025-09-18
**Issue:** Matt.Lindop getting "Super admin role required" error when accessing Feature Flags

## 🔍 Key Findings

### 1. Authorization Logic Analysis

**Feature Flags Endpoint Configuration:**
- **File:** `/app/api/api_v1/endpoints/admin.py`
- **Route:** `GET /api/v1/admin/feature-flags`
- **Authorization Dependency:** `require_admin` (line 92)
- **Expected Behavior:** Should accept both `admin` and `super_admin` roles

**require_admin Function Logic:**
```python
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.admin, UserRole.super_admin]:
        # This logs "Admin role required" NOT "Super admin role required"
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return current_user
```

### 2. Database User Analysis

**Matt.Lindop User Accounts Found:**

1. **Account #1:**
   - Email: `matt.lindop@marketedge.com`
   - Role: `admin`
   - ID: `6d662e21-d29b-4edd-ac75-5096c8e54c1f`
   - Organization: Zebra
   - Status: Active
   - **Authorization:** ✅ Should PASS `require_admin`

2. **Account #2:**
   - Email: `matt.lindop@zebra.associates`
   - Role: `super_admin`
   - ID: `f96ed2fb-0c58-445a-855a-e0d66f56fbcf`
   - Organization: Zebra
   - Status: Active
   - **Authorization:** ✅ Should PASS `require_admin`

### 3. Error Source Analysis

**"Super admin role required" Log Origin:**
- **File:** `/app/auth/dependencies.py` line 280
- **Function:** `require_super_admin()` (NOT `require_admin`)
- **Usage:** Only used in organization management and cross-tenant operations
- **NOT USED in Feature Flags endpoint**

### 4. Root Cause Hypothesis

The "Super admin role required" error suggests one of these scenarios:

#### A. Wrong Endpoint Being Called
Matt.Lindop might be hitting a different admin endpoint that uses `require_super_admin`:
- `/api/v1/organisations/*` endpoints
- `/api/v1/user-management/*` endpoints
- `/api/v1/database/*` endpoints

#### B. Auth0 Token Validation Issue
The request might be:
1. Using wrong Matt.Lindop email (`matt.lindop@marketedge.com` vs `matt.lindop@zebra.associates`)
2. Failing token validation and hitting fallback authorization logic
3. Auth0 organization mapping causing role confusion

#### C. Route Confusion
Frontend might be calling wrong endpoint path or method.

## 🔧 Debugging Steps Performed

1. ✅ **Verified Feature Flags endpoint uses `require_admin`**
2. ✅ **Confirmed both Matt.Lindop users should pass authorization**
3. ✅ **Identified "Super admin role required" comes from different function**
4. ✅ **Found UserRole enum includes `super_admin` as valid role**

## 🎯 Resolution Strategy

### Immediate Actions

1. **Check Server Logs for Complete Stack Trace:**
   - Look for which exact endpoint is being called
   - Identify which user account (email) is being used
   - Find the complete error stack trace

2. **Verify Frontend Request:**
   - Confirm frontend is calling `/api/v1/admin/feature-flags`
   - Check which Auth0 email is being used in token
   - Verify HTTP method is GET

3. **Test Direct API Calls:**
   - Test with both Matt.Lindop accounts
   - Use proper Auth0 tokens for each account
   - Verify different admin endpoints behavior

### Code Fixes

**If issue is wrong endpoint being called:**
- Update frontend to use correct Feature Flags endpoint
- Add proper route logging for debugging

**If issue is token validation:**
- Verify Auth0 organization mapping for both accounts
- Check tenant context validation logic
- Update Auth0 fallback token verification

**If issue is authorization confusion:**
- Add detailed logging to `require_admin` function
- Log which user account and role is being used
- Add request path to authorization logs

## 📋 Test Matrix

| User Account | Role | require_admin | require_super_admin | Feature Flags Access |
|-------------|------|---------------|-------------------|-------------------|
| matt.lindop@marketedge.com | admin | ✅ PASS | ❌ FAIL | ✅ Should Work |
| matt.lindop@zebra.associates | super_admin | ✅ PASS | ✅ PASS | ✅ Should Work |

## 🚨 Critical Questions

1. **Which Matt.Lindop email is being used in the failing request?**
2. **What is the exact endpoint path being called?**
3. **What does the complete server error stack trace show?**
4. **Is the error happening during token validation or endpoint authorization?**

## 💡 Quick Fix Recommendations

### Option 1: Ensure Correct User Account
If using `matt.lindop@marketedge.com` (admin role), verify Auth0 token is properly validated.

### Option 2: Promote to Super Admin
If needed for cross-tenant operations, promote `matt.lindop@marketedge.com` to `super_admin` role.

### Option 3: Fix Frontend Route
Ensure frontend calls correct Feature Flags endpoint with proper HTTP method.

---

**Next Steps:** Execute server log analysis and direct API testing to identify exact failure point.