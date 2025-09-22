# Render Blueprint Deployment Guide
**Date**: 2025-09-22
**Service**: MarketEdge Platform Backend
**Environment**: Production + Automatic Preview Environments

## Current Status
✅ **render.yaml Configuration**: Fixed and code review approved
✅ **Environment Groups**: production-env group confirmed with 23 variables
🔄 **Blueprint Linking**: Ready for deployment
⏳ **Preview Environments**: Waiting for Blueprint activation

## Blueprint Configuration Summary

### Key Features Implemented
- **Automatic Preview Generation**: All PRs get isolated preview environments
- **Environment Group Integration**: Links to existing production-env configuration
- **Auth0 Dual Configuration**: Separate Auth0 apps for production vs staging/preview
- **Resource Optimization**: Free tier for preview environments with 7-day cleanup
- **CORS Wildcard Support**: `*.onrender.com` for dynamic preview URLs

### Critical Configuration Details
```yaml
previews:
  generation: automatic  # Generate for all PRs
  expireAfterDays: 7     # Auto-cleanup

envGroups:
  - production-env      # Links to existing 23 environment variables

previews:
  plan: free           # Cost-optimized preview environments
  numInstances: 1
```

## Deployment Steps

### Step 1: Access Render Dashboard
1. Navigate to [Render Dashboard](https://dashboard.render.com)
2. Locate existing service: `marketedge-platform`
3. Current status: Manual deployment mode

### Step 2: Convert to Blueprint Management
1. **Service Settings**: Click on `marketedge-platform` service
2. **Blueprint Tab**: Navigate to "Blueprint" section
3. **Link Repository**:
   - Repository: `matt/MarketEdge` (or your GitHub username)
   - Branch: `main`
   - Blueprint Path: `render.yaml`
4. **Confirm Environment Groups**: Verify `production-env` is linked

### Step 3: Blueprint Activation Process
1. **Initial Sync**: Render will analyze render.yaml configuration
2. **Environment Validation**: Verify all 23 production-env variables are accessible
3. **Service Migration**: Existing service will be converted to Blueprint management
4. **First Blueprint Deploy**: Trigger initial deployment from render.yaml

### Step 4: Verify Preview Environment Setup
1. **Check PR #17**: Navigate to existing pull request
2. **Preview Generation**: Should automatically create preview environment
3. **Environment Variables**: Verify staging Auth0 configuration is active
4. **Database Isolation**: Confirm preview uses separate database instance

## Environment Variable Configuration

### Production Environment (production-env group)
```
AUTH0_DOMAIN=marketedge.eu.auth0.com
AUTH0_CLIENT_ID=[production_client_id]
AUTH0_CLIENT_SECRET=[production_secret]
AUTH0_AUDIENCE=https://api.marketedge.co.uk
DATABASE_URL=[production_postgres_url]
REDIS_URL=[production_redis_url]
...21 additional variables
```

### Preview Environment Overrides
```
ENVIRONMENT=staging
USE_STAGING_AUTH0=true
ENABLE_DEBUG_LOGGING=true
CORS_ORIGINS=https://*.onrender.com,https://localhost:3000
RUN_MIGRATIONS=true
```

## Auth0 Staging Configuration Required

### Create Staging Auth0 Application
1. **Auth0 Dashboard**: Create new application for staging/preview
2. **Application Type**: Single Page Application
3. **Allowed Callback URLs**: `https://*.onrender.com/api/auth/callback`
4. **Allowed Logout URLs**: `https://*.onrender.com`
5. **Allowed Web Origins**: `https://*.onrender.com`

### Environment Variables to Set in Render
```
AUTH0_DOMAIN_STAGING=marketedge-staging.eu.auth0.com
AUTH0_CLIENT_ID_STAGING=[staging_client_id]
AUTH0_CLIENT_SECRET_STAGING=[staging_secret]
AUTH0_AUDIENCE_STAGING=https://api-staging.marketedge.co.uk
```

## Post-Deployment Verification

### Step 1: Production Service Health
- **URL**: https://marketedge-platform.onrender.com/health
- **Expected**: `{"status": "healthy", "environment": "production"}`
- **Database**: Verify production data integrity

### Step 2: Preview Environment Validation
- **PR #17 Preview URL**: Check automatically generated URL
- **Health Check**: `https://[preview-url]/health`
- **Expected**: `{"status": "healthy", "environment": "staging"}`
- **Auth0 Integration**: Test login with staging Auth0 configuration

### Step 3: Blueprint Workflow Testing
1. **Create Test PR**: Make minor change and create new PR
2. **Automatic Generation**: Verify preview environment creates automatically
3. **Environment Isolation**: Confirm separate database and Redis instances
4. **Cleanup Testing**: Verify preview environments expire after 7 days

## Troubleshooting

### Common Issues

#### Blueprint Sync Failures
- **Symptom**: "Blueprint sync failed" error
- **Solution**: Verify render.yaml syntax with YAML validator
- **Check**: Ensure production-env group exists and is accessible

#### Preview Environment Auth Failures
- **Symptom**: 401 errors in preview environments
- **Solution**: Verify AUTH0_*_STAGING variables are set
- **Check**: Confirm staging Auth0 application callback URLs include wildcard

#### Database Connection Issues
- **Symptom**: Preview environments can't connect to database
- **Solution**: Verify preview environments get separate database instances
- **Check**: Ensure DATABASE_URL is properly configured for preview tier

#### CORS Errors in Preview
- **Symptom**: Frontend can't connect to preview API
- **Solution**: Verify CORS_ORIGINS includes `https://*.onrender.com`
- **Check**: Confirm previewValue overrides are working

## Success Metrics

### Deployment Success Indicators
- ✅ Production service remains healthy during Blueprint migration
- ✅ Preview environment automatically created for PR #17
- ✅ Staging Auth0 authentication working in preview
- ✅ Database isolation confirmed between environments
- ✅ 7-day cleanup policy active for preview environments

### Business Impact
- **Zebra Associates Opportunity**: £925K deal validation enabled
- **Preview Environments**: Stakeholder demo capability for matt.lindop@zebra.associates
- **Development Velocity**: Automatic preview environments for all PRs
- **Cost Optimization**: Free tier preview environments with automatic cleanup

## Next Steps After Deployment

1. **Test PR #17 Preview**: Validate automatic preview environment generation
2. **Stakeholder Demo**: Share preview URL with Zebra Associates contact
3. **Monitor Costs**: Track preview environment usage and cleanup
4. **Document Process**: Update team documentation with new Blueprint workflow

## Emergency Rollback Plan

If Blueprint deployment fails:
1. **Immediate**: Revert to manual deployment mode in Render dashboard
2. **Service Recovery**: Redeploy from last known good commit
3. **Environment Groups**: Verify production-env variables remain intact
4. **Investigation**: Analyze Blueprint sync logs for specific failure points

---

**Deployment Contact**: DevOps Engineer (Maya)
**Business Stakeholder**: matt.lindop@zebra.associates
**Critical Success Factor**: Automatic preview environments for £925K opportunity validation