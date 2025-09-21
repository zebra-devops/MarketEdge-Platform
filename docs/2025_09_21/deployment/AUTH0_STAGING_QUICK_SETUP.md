# Auth0 Staging Quick Setup Instructions

## IMMEDIATE ACTION REQUIRED

### Step 1: Create Auth0 Staging Application (5 minutes)

**Navigate to Auth0 Dashboard:**
```
https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications
```

**Create Application:**
1. Click "Create Application"
2. **Name**: `MarketEdge-Staging`
3. **Type**: Single Page Application (SPA)
4. Click "Create"

### Step 2: Configure Application URIs (3 minutes)

**In the new staging application Settings tab:**

#### Allowed Callback URLs:
```
https://*.onrender.com/callback,https://localhost:3000/callback,https://marketedge-staging-*.onrender.com/callback,https://pr-*-marketedge-platform.onrender.com/callback
```

#### Allowed Logout URLs:
```
https://*.onrender.com/,https://localhost:3000/,https://marketedge-staging-*.onrender.com/,https://pr-*-marketedge-platform.onrender.com/
```

#### Allowed Web Origins:
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

#### Allowed Origins (CORS):
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

**Click "Save Changes"**

### Step 3: Collect Staging Credentials (1 minute)

**From the staging application Settings tab, copy:**
- **Domain**: `dev-g8trhgbfdq2sk2m8.us.auth0.com` (same as production)
- **Client ID**: `[NEW_STAGING_CLIENT_ID]` (copy from dashboard)
- **Client Secret**: `[NEW_STAGING_CLIENT_SECRET]` (copy from dashboard)

### Step 4: Configure Render Environment Variables (5 minutes)

**Navigate to Render Dashboard:**
```
https://dashboard.render.com/web/srv-[your-service-id]/environment
```

**Add these environment variables:**

1. **AUTH0_DOMAIN_STAGING**
   - Value: `dev-g8trhgbfdq2sk2m8.us.auth0.com`

2. **AUTH0_CLIENT_ID_STAGING**
   - Value: `[PASTE_STAGING_CLIENT_ID]`

3. **AUTH0_CLIENT_SECRET_STAGING**
   - Value: `[PASTE_STAGING_CLIENT_SECRET]`
   - **Mark as secret/encrypted**

4. **AUTH0_AUDIENCE_STAGING**
   - Value: `https://api.marketedge-staging.onrender.com`

**Click "Save" for each variable**

### Step 5: Test Configuration (2 minutes)

1. Create a test PR to trigger preview deployment
2. Access preview URL when ready
3. Test authentication flow
4. Verify no production impact

## Expected Results

✅ **Staging Auth0 Isolated**: Preview environments use separate Auth0 app
✅ **Production Protected**: Production Auth0 unchanged and functional
✅ **Wildcard Support**: All Render preview URLs supported
✅ **Testing Ready**: Safe staging authentication for development

## Verification Commands

**Check staging configuration:**
```bash
# Access preview environment
curl https://pr-[number]-marketedge-platform.onrender.com/health

# Verify staging Auth0 in use
curl https://pr-[number]-marketedge-platform.onrender.com/auth/config
```

**Total setup time: ~15 minutes**
**Impact: Zero production disruption**
**Benefit: Safe staging testing for £925K opportunity**