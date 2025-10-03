# Render Dashboard - Staging Environment Variables Import Instructions

## Prerequisites
- Access to Render Dashboard
- Staging service already created
- Database and Redis instances provisioned for staging

## Step 1: Create Staging Environment Group

1. Navigate to Render Dashboard: https://dashboard.render.com
2. Go to **Environment Groups** section
3. Click **New Environment Group**
4. Name it: `staging-env`
5. Description: "Staging environment variables for MarketEdge Platform"

## Step 2: Import Environment Variables

### Option A: Bulk Import (Recommended)
1. In the staging-env group, click **Bulk Edit**
2. Copy the contents from `STAGING_ENV_VARS.env`
3. Paste into the editor
4. **IMPORTANT**: Replace placeholder values:
   - `[STAGING_DB_USER]` → Your staging database username
   - `[STAGING_DB_PASSWORD]` → Your staging database password
   - `[STAGING_DB_HOST]` → Your staging database host
   - `[STAGING_DB_NAME]` → Your staging database name (e.g., `marketedge_staging`)
   - `[STAGING_REDIS_HOST]` → Your staging Redis host

### Option B: Manual Entry
Add each variable individually:

#### Critical Auth0 Variables (CORRECTED)
- `AUTH0_CLIENT_ID` = `9FRjf82esKN4fx3iY337CT1jpvNVFbAP` ✅ CORRECTED
- `AUTH0_CLIENT_SECRET` = `xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7`
- `AUTH0_CALLBACK_URL` = `https://staging.zebra.associates/callback`

#### Environment Identifier
- `ENVIRONMENT` = `staging`

#### CORS Configuration
- `CORS_ORIGINS` = `["https://staging.zebra.associates","https://frontend-staging-*.vercel.app","http://localhost:3000","http://localhost:3001","https://marketedge-staging.onrender.com"]`

## Step 3: Set Secret Values

After import, manually update these sensitive values:

1. **DATABASE_URL**:
   - Format: `postgresql://[user]:[password]@[host]/[database]`
   - Example: `postgresql://staging_user:SecurePass123@dpg-staging-host/marketedge_staging`

2. **REDIS_URL**:
   - Format: `redis://[host]:[port]`
   - Example: `redis://red-staging-host:6379`

3. **JWT_SECRET_KEY** (Optional - for extra security):
   - Generate new key: `openssl rand -hex 64`
   - Or keep same as production for easier testing

## Step 4: Link Environment Group to Service

1. Navigate to your staging service in Render
2. Go to **Environment** tab
3. Under **Linked Environment Groups**, click **Link**
4. Select `staging-env`
5. Click **Link Environment Group**

## Step 5: Deploy and Verify

1. Trigger a manual deploy or push to staging branch
2. Monitor deployment logs for errors
3. Check health endpoint: `https://marketedge-staging.onrender.com/health`

## Step 6: Verification Checklist

After deployment, verify:

- [ ] Auth0 login works with staging.zebra.associates
- [ ] Correct Auth0 Client ID in logs (9FRjf82esKN4fx3iY337CT1jpvNVFbAP)
- [ ] Database connection successful to staging database
- [ ] Redis connection successful to staging instance
- [ ] CORS allows requests from staging.zebra.associates
- [ ] Environment shows as "staging" in health check

## Common Issues and Solutions

### Issue 1: Auth0 Callback Mismatch
**Error**: "Callback URL mismatch"
**Solution**: Ensure Auth0 app (PlatformWrapper-Staging) has `https://staging.zebra.associates/callback` in allowed callbacks

### Issue 2: CORS Errors
**Error**: "CORS policy blocked request"
**Solution**: Verify CORS_ORIGINS includes your frontend URL

### Issue 3: Database Connection Failed
**Error**: "Could not connect to database"
**Solution**: Check DATABASE_URL format and credentials

### Issue 4: Wrong Auth0 Client
**Error**: "Invalid client" or authentication fails
**Solution**: Verify AUTH0_CLIENT_ID is `9FRjf82esKN4fx3iY337CT1jpvNVFbAP` (NOT the production ID)

## Environment Variable Priority

Render applies environment variables in this order:
1. Service-specific environment variables (highest priority)
2. Linked environment groups
3. Default values in code (lowest priority)

## Rollback Procedure

If issues occur:
1. Unlink staging-env group
2. Link production-env group temporarily
3. Debug and fix staging-env values
4. Re-link staging-env when fixed

## Security Notes

- Never commit `.env` files to Git
- Use Render's secret management for sensitive values
- Rotate secrets regularly
- Keep staging and production secrets separate
- Monitor access logs for unauthorized attempts