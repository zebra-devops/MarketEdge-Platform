# Production Auth0 500 Error Fix Guide

## Problem Analysis

Real Auth0 authorization codes are causing 500 "Internal Server Error" responses in production, while test codes correctly return 400 errors. Our diagnostic testing confirms the backend logic is correct, indicating a production environment configuration issue.

## Root Cause: Missing AUTH0_CLIENT_SECRET

**Evidence:**
- Test codes return 400 errors (correct behavior) 
- Real Auth0 codes return 500 errors (unexpected exceptions)
- render.yaml shows `AUTH0_CLIENT_SECRET: sync: false` (manual configuration required)
- Enhanced error logging deployed but not capturing specific Auth0 API errors

## Immediate Fix Steps

### 1. Verify Auth0 Environment Variables in Render Dashboard

**Required Variables:**
```
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
AUTH0_CLIENT_SECRET=[MUST BE SET MANUALLY IN RENDER DASHBOARD]
AUTH0_CALLBACK_URL=https://marketedge-platform.onrender.com/callback
```

**Action:** 
1. Log into Render dashboard
2. Go to MarketEdge Platform service
3. Navigate to Environment tab
4. Verify `AUTH0_CLIENT_SECRET` is set to the correct value
5. If missing, add it with the production Auth0 application secret

### 2. Force Service Restart

After setting environment variables:
```bash
# In Render dashboard, trigger manual deployment or restart
```

### 3. Test Fix Immediately

```bash
# Run this test to verify the fix
python3 test_auth0_config.py
```

## Why This Causes 500 vs 400 Errors

**Test Authorization Codes:**
1. Code validation → PASS
2. Auth0 token exchange → Auth0 rejects invalid code → Returns None
3. Backend handles None gracefully → Returns 400 "Failed to exchange authorization code"

**Real Authorization Codes with Missing CLIENT_SECRET:**
1. Code validation → PASS  
2. Auth0 token exchange → HTTP request to Auth0 API
3. Auth0 API returns 401/403 due to missing/invalid client_secret
4. httpx library raises HTTPStatusError exception
5. Exception not caught in auth0.py → Bubbles up to error middleware
6. Error middleware catches Exception → Returns 500 "Internal Server Error"

## Secondary Fixes

### Enhanced Error Handling for Auth0 API

Add specific error handling for Auth0 API authentication failures:

```python
# In app/auth/auth0.py exchange_code_for_token method
except httpx.HTTPStatusError as e:
    if e.response.status_code in [401, 403]:
        logger.error(
            "Auth0 authentication failed - check client credentials",
            extra={
                "event": "auth0_auth_failed",
                "status_code": e.response.status_code,
                "response": e.response.text
            }
        )
        return None  # This will cause 400 error instead of 500
    # Re-raise other HTTP errors to maintain existing behavior
    raise
```

### Environment Validation on Startup

Add startup validation to catch missing Auth0 configuration:

```python
# In app/main.py or app/core/config.py
def validate_auth0_config():
    required_vars = ["AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET"]
    missing = [var for var in required_vars if not getattr(settings, var, None)]
    if missing:
        raise ValueError(f"Missing required Auth0 environment variables: {missing}")
```

## Verification Steps

1. **Check Render Environment Variables**
   - Confirm AUTH0_CLIENT_SECRET is set
   - Verify all Auth0 variables are correct

2. **Test with Real Auth0 Code**
   - Authenticate through frontend
   - Should return 400 "Failed to exchange authorization code" instead of 500

3. **Monitor Render Logs**
   - Check for Auth0-related errors
   - Confirm error logging is working

## Expected Behavior After Fix

- **Test codes:** 400 "Failed to exchange authorization code" 
- **Real codes (expired/invalid):** 400 "Failed to exchange authorization code"
- **Real codes (valid):** 200 with authentication success
- **No more 500 errors** for authentication requests

## Prevention

1. Add AUTH0_CLIENT_SECRET to required environment variable validation
2. Implement startup health checks for Auth0 connectivity  
3. Add monitoring alerts for 500 errors on auth endpoints
4. Document manual environment variable requirements in deployment process