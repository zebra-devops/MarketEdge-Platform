# 🚨 STAGING QUICK FIX CHECKLIST

**Issue:** Database error during authentication on staging
**Root Cause:** Wrong AUTH0_CLIENT_ID in environment variables

## ⚡ IMMEDIATE FIX (Do This First!)

### 1️⃣ Fix Auth0 Client ID in Render Dashboard

**WRONG VALUE (Currently Set):**
```
wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
```

**CORRECT VALUE (Must Change To):**
```
9FRjf82esKN4fx3iY337CT1jpvNVFbAP
```

**Steps:**
1. Go to https://dashboard.render.com/
2. Click on "marketedge-platform-staging"
3. Click "Environment" tab
4. Find `AUTH0_CLIENT_ID`
5. Change to: `9FRjf82esKN4fx3iY337CT1jpvNVFbAP`
6. Click "Save Changes"
7. Wait for auto-redeploy

## ✅ Complete Environment Variable Checklist

Copy these values to Render Dashboard:

### Critical Variables (MUST BE SET):

```bash
# Auth0 Configuration
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=9FRjf82esKN4fx3iY337CT1jpvNVFbAP
AUTH0_CLIENT_SECRET=xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
AUTH0_ACTION_SECRET=0mSkHhYYz8PcB_MylserTVm9DXuZJSCrM77KCKxlY5U
AUTH0_CALLBACK_URL=https://staging.zebra.associates/callback

# JWT Configuration
JWT_SECRET_KEY=pu1PUYs3-1DtNcMTaECe9KBihlzC7FPZa4FHmJ9Ou9r2-IHIKApIoO1mLTtxF1Ge
JWT_ALGORITHM=HS256
JWT_ISSUER=market-edge-platform
JWT_AUDIENCE=market-edge-api
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=staging
RUN_MIGRATIONS=true

# CORS
CORS_ORIGINS=https://staging.zebra.associates,https://*.vercel.app,http://localhost:3000
COOKIE_DOMAIN=.zebra.associates
```

### Database (Should be auto-set from Render):
- DATABASE_URL - Use INTERNAL URL from Render (ends with -a)

### Optional:
- REDIS_URL - If using Redis
- DEBUG=false
- LOG_LEVEL=INFO

## 🔍 Verification Steps

After saving changes:

1. **Check Service Logs:**
   - Look for "Uvicorn running on"
   - No database connection errors
   - No Auth0 errors

2. **Test Health Endpoint:**
   ```bash
   curl https://marketedge-staging.onrender.com/health
   ```

3. **Test Login:**
   - Go to https://staging.zebra.associates
   - Try logging in
   - Should work without "Database error"

## ❌ What NOT to Do

- DON'T use `wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6` (that's dev, not staging)
- DON'T use external database URL (must be internal)
- DON'T leave AUTH0_AUDIENCE empty
- DON'T skip setting JWT_SECRET_KEY

## 📋 Verify in Render Dashboard

| Variable | Current (Wrong) | Should Be (Correct) | ✅ |
|----------|----------------|-------------------|---|
| AUTH0_CLIENT_ID | wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6 | 9FRjf82esKN4fx3iY337CT1jpvNVFbAP | ⬜ |
| AUTH0_CLIENT_SECRET | (empty) | xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7 | ⬜ |
| AUTH0_AUDIENCE | (check) | https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/ | ⬜ |
| JWT_SECRET_KEY | (empty) | pu1PUYs3-1DtNcMTaECe9KBihlzC7FPZa4FHmJ9Ou9r2... | ⬜ |
| DATABASE_URL | (check) | Internal URL (ends with -a) | ⬜ |

## 🆘 If Still Broken After Fix

1. Check Render logs for specific error
2. SSH into service and run diagnostic script
3. Verify Auth0 application exists with correct Client ID
4. Check if database migrations ran (RUN_MIGRATIONS=true)

---

**PRIORITY ACTION:** Change AUTH0_CLIENT_ID to `9FRjf82esKN4fx3iY337CT1jpvNVFbAP` NOW!