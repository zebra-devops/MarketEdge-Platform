# Preview Environment Auth0 Validation Guide

## Overview

This guide documents the process for validating that Render preview environments correctly use staging Auth0 configuration instead of production credentials. This ensures complete isolation between staging and production environments for the £925K Zebra Associates opportunity.

## Test Endpoints Created

### 1. `/api/v1/system/environment-config` (Public)
- **Purpose**: Verify Auth0 configuration without authentication
- **Use Case**: Initial validation of preview environment setup
- **Returns**: Environment details, masked Auth0 config, CORS settings

### 2. `/api/v1/system/staging-health` (Public)
- **Purpose**: Comprehensive health check for staging environments
- **Use Case**: Validate database, Redis, and environment variable configuration
- **Returns**: Health status, connection tests, staging-specific settings

### 3. `/api/v1/system/auth0-validation` (Authenticated)
- **Purpose**: Validate complete Auth0 authentication flow
- **Use Case**: Confirm staging Auth0 is processing authentication correctly
- **Returns**: User details, Auth0 configuration confirmation, environment verification

## Validation Workflow

### Step 1: Create Test Branch
```bash
git checkout -b test/preview-environment-auth0-validation
```

### Step 2: Make Test Changes
- Add validation endpoints to `/app/api/api_v1/endpoints/system.py`
- Update documentation
- Create simple configuration changes to trigger build

### Step 3: Create Pull Request
```bash
git add .
git commit -m "test: add Auth0 staging validation endpoints for preview environment testing"
git push origin test/preview-environment-auth0-validation
```

### Step 4: Monitor Render Dashboard
1. Go to Render dashboard
2. Navigate to MarketEdge Backend service
3. Check for automatic preview environment creation
4. Wait for build and deployment completion

### Step 5: Test Preview Environment
1. **Public Environment Check**:
   ```bash
   curl https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/environment-config
   ```

   Expected Response:
   ```json
   {
     "environment": {
       "ENVIRONMENT": "staging",
       "is_staging": true,
       "USE_STAGING_AUTH0": true
     },
     "auth0_config": {
       "domain": "marketedge-staging.auth0.com"
     }
   }
   ```

2. **Health Check**:
   ```bash
   curl https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/staging-health
   ```

3. **Authenticated Test** (requires staging Auth0 user):
   ```bash
   curl -H "Authorization: Bearer <staging-token>" \
        https://marketedge-backend-pr-XXX.onrender.com/api/v1/system/auth0-validation
   ```

## Critical Validation Points

### Environment Configuration Validation
- ✅ `ENVIRONMENT` should be "staging"
- ✅ `USE_STAGING_AUTH0` should be `true`
- ✅ `is_staging` should be `true`
- ✅ Auth0 domain should be staging tenant

### CORS Configuration Validation
- ✅ `CORS_ORIGINS` should include `"https://*.onrender.com"`
- ✅ Wildcard domains should be supported for preview URLs

### Database Isolation Validation
- ✅ Preview environment uses separate database instance
- ✅ Migrations run automatically on preview deployment
- ✅ Test data seeded correctly

### Security Validation
- ✅ Production Auth0 credentials not exposed
- ✅ Staging Auth0 credentials working correctly
- ✅ No production data accessible from preview environment

## Expected Configuration in Render

### Environment Variables (Preview)
```
ENVIRONMENT=staging
USE_STAGING_AUTH0=true
AUTH0_DOMAIN=<staging-auth0-domain>
AUTH0_CLIENT_ID_STAGING=<staging-client-id>
AUTH0_CLIENT_SECRET_STAGING=<staging-client-secret>
AUTH0_AUDIENCE_STAGING=<staging-audience>
CORS_ORIGINS=https://*.onrender.com,https://localhost:3000
ENABLE_DEBUG_LOGGING=true
```

### Environment Variables (Production)
```
ENVIRONMENT=production
USE_STAGING_AUTH0=false
AUTH0_DOMAIN=<production-auth0-domain>
AUTH0_CLIENT_ID=<production-client-id>
AUTH0_CLIENT_SECRET=<production-client-secret>
AUTH0_AUDIENCE=<production-audience>
CORS_ORIGINS=https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com
ENABLE_DEBUG_LOGGING=false
```

## Troubleshooting

### Preview Environment Not Using Staging Auth0
1. Check Render environment variables for preview
2. Verify `USE_STAGING_AUTH0=true` in preview
3. Confirm staging Auth0 credentials are set in Render
4. Check `render.yaml` configuration for `previewValue` settings

### CORS Issues with Preview URL
1. Verify wildcard CORS origins: `https://*.onrender.com`
2. Check that preview URL follows pattern: `https://marketedge-backend-pr-XXX.onrender.com`
3. Confirm CORS middleware is first in middleware stack

### Authentication Failures
1. Verify staging Auth0 tenant is accessible
2. Check Auth0 callback URLs include preview environment pattern
3. Validate JWT token issuer matches staging domain
4. Confirm user exists in staging Auth0 tenant

## Success Criteria

### ✅ Environment Isolation Confirmed
- Preview environment shows `ENVIRONMENT=staging`
- Auth0 configuration points to staging tenant
- No production credentials exposed

### ✅ Authentication Working
- Staging Auth0 users can authenticate
- JWT tokens validated correctly
- User roles and permissions working

### ✅ Wildcard URL Support
- Preview environment URL accessible
- CORS configured for `*.onrender.com`
- All API endpoints responding correctly

### ✅ Database Isolation
- Preview uses separate database
- Migrations applied automatically
- Test data available for testing

## Business Impact

This validation ensures:
- **Matt.Lindop** can safely test Zebra Associates features in preview environments
- **Production data protection** - zero risk of production data exposure
- **Staging workflow reliability** - preview environments are true staging replicas
- **Development velocity** - faster iteration with isolated preview environments

## Next Steps After Validation

1. Document successful validation results
2. Create standard preview environment testing checklist
3. Add automated tests for environment configuration
4. Update deployment documentation with validation steps
5. Train team on preview environment usage

## Emergency Rollback Plan

If preview environment validation fails:
1. Check Render configuration immediately
2. Verify no production credentials in preview
3. Disable automatic preview generation if needed
4. Fix configuration before re-enabling previews

This validation process protects the £925K Zebra Associates opportunity by ensuring complete staging/production isolation.