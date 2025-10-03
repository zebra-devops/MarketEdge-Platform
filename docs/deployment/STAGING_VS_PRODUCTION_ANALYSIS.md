# Staging vs Production Environment Variables Analysis

## Production Configuration Analysis

### Current Production Auth0 Settings (INCORRECT)
- **AUTH0_CLIENT_ID**: `mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr` (Production App)
- **AUTH0_CLIENT_ID_STAGING**: `9FRjf82esKN4fx3iY337CT1jpvNVFbAP` (Staging App - stored but not used)
- **Issue**: Production is using the production Auth0 app, staging values stored but not actively used

### Environment-Specific Variables (MUST BE DIFFERENT)

| Variable | Production | Staging | Notes |
|----------|------------|---------|-------|
| **AUTH0_CLIENT_ID** | mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr | 9FRjf82esKN4fx3iY337CT1jpvNVFbAP | **CRITICAL: Must use staging client** |
| **AUTH0_CLIENT_SECRET** | 9CnJeRKicS44doQi48R12v... | xrdILihwwXxXNqDjxEa65J1a... | Different secret per app |
| **AUTH0_CALLBACK_URL** | https://app.zebra.associates/callback | https://staging.zebra.associates/callback | Different domain |
| **ENVIRONMENT** | production | staging | Environment identifier |
| **DATABASE_URL** | postgresql://...marketedge_production | postgresql://...marketedge_staging | Different database |
| **REDIS_URL** | redis://red-d2gfer3uibrs73eai6og:6379 | redis://[STAGING_REDIS]:6379 | Different Redis instance |
| **CORS_ORIGINS** | app.zebra.associates, etc. | staging.zebra.associates, etc. | Different allowed origins |

### Environment-Agnostic Variables (CAN BE SAME)

| Variable | Value | Notes |
|----------|-------|-------|
| **AUTH0_DOMAIN** | dev-g8trhgbfdq2sk2m8.us.auth0.com | Same Auth0 tenant |
| **AUTH0_AUDIENCE** | https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/ | Same API audience |
| **AUTH0_ACTION_SECRET** | 0mSkHhYYz8PcB_MylserTVm9DXuZJSCrM77KCKxlY5U | Webhook validation |
| **JWT_SECRET_KEY** | pu1PUYs3-1DtNcMTaECe9K... | Can share for now |
| **JWT_ALGORITHM** | HS256 | Standard algorithm |
| **JWT_ISSUER** | market-edge-platform | Same issuer |
| **JWT_AUDIENCE** | market-edge-api | Same audience |
| **ACCESS_TOKEN_EXPIRE_MINUTES** | 30 | Same timeout |
| **COOKIE_DOMAIN** | .zebra.associates | Same root domain |
| **DEBUG** | false | Both non-debug |
| **LOG_LEVEL** | INFO | Same logging |
| **PORT/FASTAPI_PORT** | 8000 | Same port |
| **RATE_LIMIT_*** | false/60 | Same limits |

## Critical Corrections Required

### 1. Auth0 Client ID Mismatch
**Problem**: Production env vars show staging client ID stored but not used
**Solution**: Staging must use `AUTH0_CLIENT_ID=9FRjf82esKN4fx3iY337CT1jpvNVFbAP`

### 2. Callback URL Configuration
**Problem**: Production uses app.zebra.associates
**Solution**: Staging must use staging.zebra.associates

### 3. CORS Origins
**Problem**: Production allows app.zebra.associates
**Solution**: Staging must allow staging.zebra.associates

## Secrets That Need Regeneration for Staging

1. **DATABASE_URL**: Must point to staging database
2. **REDIS_URL**: Must point to staging Redis instance
3. **JWT_SECRET_KEY**: Consider using different key for staging (optional but recommended)

## Environment Variable Groups Structure

### Production Environment Group (production-env)
- Uses production Auth0 app
- Points to production database
- Allows app.zebra.associates origins

### Staging Environment Group (staging-env) - TO BE CREATED
- Uses staging Auth0 app (9FRjf82esKN4fx3iY337CT1jpvNVFbAP)
- Points to staging database
- Allows staging.zebra.associates origins

## Migration Path

1. Create new staging-env group in Render
2. Import STAGING_ENV_VARS.env
3. Update DATABASE_URL with staging database
4. Update REDIS_URL with staging Redis
5. Apply to staging service
6. Test Auth0 flow with correct client ID