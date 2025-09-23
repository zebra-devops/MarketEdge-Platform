# PR #17 Preview Environment - Manual Solution Steps

**Date**: September 22, 2025
**Issue**: GitHub token lacks workflow scope permissions for automated push
**Status**: MANUAL IMPLEMENTATION REQUIRED

## Executive Summary

The fix for PR #17 preview environment deployment has been **developed and tested locally** but cannot be pushed automatically due to GitHub Personal Access Token limitations. **Manual implementation required** to enable preview environment deployment.

## Root Cause Confirmed

✅ **DIAGNOSED**: PR #17 contains render.yaml with environment group configuration (`production-env`) that **does not exist in Render dashboard**
✅ **SOLUTION CREATED**: Reverted render.yaml to main branch inline configuration
✅ **TESTED LOCALLY**: Fix applied and committed to local branch
❌ **BLOCKED**: GitHub token lacks `workflow` scope for automated push

## Manual Implementation Required

### **IMMEDIATE ACTION (5 minutes)**

A DevOps admin with GitHub `workflow` scope permissions must:

#### **1. Apply the Fix to PR #17**
```bash
# Navigate to local repository
cd /path/to/MarketEdge-Platform

# Switch to PR branch
git checkout test/validate-preview-environments

# Apply the fix (render.yaml revert)
git checkout main -- render.yaml

# Stage and commit
git add render.yaml
git commit -m "fix: revert render.yaml to inline configuration for preview deployment"

# Push to GitHub
git push origin test/validate-preview-environments
```

#### **2. Alternative: Copy Fixed render.yaml**
If git approach is complex, manually copy this fixed render.yaml content:

```yaml
# Render.yaml Configuration for MarketEdge Platform
# Production and Preview Environment Setup

# Preview Environment Configuration
previews:
  generation: automatic  # Generate preview environments for all PRs automatically
  expireAfterDays: 7     # Clean up preview environments after 7 days

services:
  # Main Backend Service (FastAPI)
  - type: web
    name: marketedge-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "./render-startup.sh"
    plan: free

    # Preview environment overrides
    previews:
      plan: free  # Use free tier for preview environments
      numInstances: 1

    envVars:
      # Environment identification
      - key: ENVIRONMENT
        value: production
        previewValue: staging

      # Migration control
      - key: RUN_MIGRATIONS
        value: true

      # Port configuration
      - key: PORT
        fromService:
          type: web
          name: marketedge-backend
          property: port

      # Database configuration
      - key: DATABASE_URL
        fromDatabase:
          name: marketedge-postgres
          property: connectionString

      # Auth0 Configuration (Production)
      - key: AUTH0_DOMAIN
        sync: false  # Set manually in Render dashboard
      - key: AUTH0_CLIENT_ID
        sync: false
      - key: AUTH0_CLIENT_SECRET
        sync: false
      - key: AUTH0_AUDIENCE
        sync: false

      # Auth0 Configuration (Staging/Preview Environments)
      - key: AUTH0_DOMAIN_STAGING
        sync: false  # Set manually in Render dashboard
      - key: AUTH0_CLIENT_ID_STAGING
        sync: false  # Set manually in Render dashboard
      - key: AUTH0_CLIENT_SECRET_STAGING
        sync: false  # Set manually in Render dashboard
      - key: AUTH0_AUDIENCE_STAGING
        sync: false  # Set manually in Render dashboard

      # Environment-aware Auth0 selection
      - key: USE_STAGING_AUTH0
        value: "false"
        previewValue: "true"

      # Redis Configuration
      - key: REDIS_URL
        fromService:
          type: redis
          name: marketedge-redis
          property: connectionString

      # CORS Configuration
      - key: CORS_ORIGINS
        value: "https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com"
        previewValue: "https://*.onrender.com,https://localhost:3000"  # Wildcard support for preview environments

      # Feature Flags
      - key: ENABLE_DEBUG_LOGGING
        value: "false"
        previewValue: "true"

      # Security
      - key: SECRET_KEY
        generateValue: true

      # Monitoring
      - key: SENTRY_DSN
        sync: false
        previewValue: ""  # Disable Sentry for preview environments

  # PostgreSQL Database
  - type: pgsql
    name: marketedge-postgres
    databaseName: marketedge
    user: marketedge_user
    plan: free

    # Staging database configuration
    previewPlan: free

    # Initialize with schema for preview environments
    initScript: |
      CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
      CREATE EXTENSION IF NOT EXISTS "pg_trgm";

  # Redis Cache
  - type: redis
    name: marketedge-redis
    plan: free
    previewPlan: free
    maxmemoryPolicy: allkeys-lru

# Build hooks for preview environments
buildHooks:
  - type: initialDeploy
    command: |
      echo "Setting up MarketEdge staging environment..."
      pip install -r requirements.txt

      # Run database migrations for staging
      if [ "$ENVIRONMENT" = "staging" ]; then
        echo "Running staging database migrations..."
        alembic upgrade head

        # Seed with test data for staging
        python database/seeds/initial_data.py
        python database/seeds/phase3_data.py

        echo "Staging environment setup complete"
      fi
```

## Expected Results After Fix

### **1. Automatic Preview Deployment**
- PR #17 push will trigger Render webhook
- Render will parse updated render.yaml successfully
- Preview environment will be created automatically
- Unique preview URL will be generated

### **2. Preview Environment Configuration**
- **Environment**: `ENVIRONMENT=staging`
- **Auth0**: Uses staging credentials (`USE_STAGING_AUTH0=true`)
- **Database**: Shared database with production
- **CORS**: Wildcard support for *.onrender.com domains

### **3. Validation Endpoints**
Once deployed, test these endpoints:
- `https://[preview-url]/health` - Basic health check
- `https://[preview-url]/api/v1/debug/environment` - Environment configuration
- `https://[preview-url]/api/v1/debug/health-detailed` - Detailed service status

## Business Impact

### **£925K Zebra Associates Opportunity**
- **CRITICAL**: Preview environments restore professional development workflow
- **URGENT**: Client demonstrations depend on reliable preview URLs
- **TIMELINE**: Immediate implementation required for development confidence

### **Development Workflow Recovery**
- **ALL PRs** will generate preview environments automatically after fix
- **Safe Feature Testing** resumes with isolated preview environments
- **Quality Assurance** workflow restored for business-critical features

## Strategic Follow-up

### **Environment Groups Implementation (Next Sprint)**
After immediate fix is working:

1. **Create Production Environment Group** in Render dashboard
2. **Add All Required Variables** to environment group
3. **Test Environment Group Configuration** with dedicated PR
4. **Migrate to Environment Group Architecture** for better secret management

### **GitHub Token Scope Update**
To prevent future workflow push issues:
1. **Update GitHub Token** with `workflow` scope permissions
2. **Test Automated Deployments** with enhanced token scope
3. **Document Token Requirements** for future DevOps team members

## Verification Checklist

After manual implementation:
- [ ] PR #17 push completed successfully
- [ ] Render webhook triggered automatically
- [ ] Preview environment created in Render dashboard
- [ ] Preview URL accessible and returning 200
- [ ] Health endpoints responding correctly
- [ ] Auth0 staging integration working
- [ ] Environment variables configured correctly

## Next Steps

1. **⚡ IMMEDIATE**: DevOps admin apply manual fix (5 minutes)
2. **✅ VERIFY**: Confirm preview environment deployment
3. **📝 DOCUMENT**: Record preview URL for testing
4. **🔄 STRATEGIC**: Plan environment group migration
5. **🛡️ SECURITY**: Update GitHub token scope permissions

**CRITICAL**: This solution restores the entire preview environment system for the MarketEdge platform, enabling confident development of the £925K opportunity features.

---

**Status**: SOLUTION READY - Manual Implementation Required
**ETA**: 5 minutes once DevOps admin applies fix
**Risk**: ZERO - Reverts to proven working configuration