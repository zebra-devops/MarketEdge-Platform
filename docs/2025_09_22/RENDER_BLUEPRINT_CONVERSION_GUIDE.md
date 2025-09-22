# Render Blueprint Conversion Guide
**Date**: September 22, 2025
**Status**: Ready for Implementation
**Service**: `marketedge-platform` → Blueprint Control

## ✅ Completed Steps

### 1. Blueprint Configuration Deployed
- **Commit**: `263e5e6` - `devops: configure render.yaml Blueprint for existing service conversion`
- **Service Name**: Correctly set to `marketedge-platform` (matches production)
- **Environment Groups**: Linked to existing `production-env` with 23 variables
- **Preview Configuration**: Automatic generation enabled with 7-day cleanup

### 2. Key Configuration Details
```yaml
services:
  - type: web
    name: marketedge-platform  # ✅ Matches existing service
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "./render-startup.sh"
    envGroups:
      - production-env  # ✅ Links to existing environment group
```

## 🔧 Manual Steps Required

### Step 1: Link Blueprint to Existing Service
**Location**: Render Dashboard → Service Settings → Blueprint

1. **Navigate**: Go to https://render.com/dashboard
2. **Select Service**: Find `marketedge-platform` service
3. **Go to Settings**: Click Settings → Blueprint tab
4. **Link Repository**:
   - Repository: `zebra-devops/MarketEdge-Platform`
   - Branch: `main`
   - Blueprint Path: `render.yaml`
5. **Review Changes**: Render will show "Service already exists - update in place"
6. **Accept Conversion**: Click "Link Blueprint" - Zero downtime conversion
7. **Verify**: Status should show "✓ synced just now"

### Step 2: Validate Blueprint Sync
**Expected**: Service continues running normally with Blueprint control

- **URL**: https://marketedge-platform.onrender.com remains unchanged
- **Environment Variables**: All 23 variables remain from `production-env` group
- **Health Check**: `/health` endpoint should respond normally
- **Deployment**: New commits to main trigger automatic deploys

## 🧪 Testing Preview Environment Generation

### Step 3: Create Test PR
```bash
# Create test branch
git checkout -b test/preview-environment-validation

# Make small change to trigger preview
echo "# Preview Environment Test - $(date)" >> README.md

# Commit and push
git add README.md
git commit -m "test: validate automatic preview environment generation"
git push origin test/preview-environment-validation

# Create PR via GitHub
gh pr create --title "Test: Validate Preview Environment Generation" --body "Testing automatic preview environment creation"
```

### Step 4: Monitor Preview Creation
**Timeline**: Preview environment should appear within 30 seconds

1. **Watch Render Dashboard**: New service appears: `marketedge-platform-pr-[number]`
2. **Verify URL Pattern**: `https://marketedge-platform-pr-[number].onrender.com`
3. **Check Environment Group**: `production-env-pr-[number]` created automatically
4. **Test Preview Functionality**:
   - Health check: `https://marketedge-platform-pr-[number].onrender.com/health`
   - Staging Auth0: Should use staging credentials
   - Environment: Should show `staging` not `production`

### Step 5: Validate Preview Configuration
**Preview Environment Specifics**:
- ✅ **Environment**: `ENVIRONMENT=staging`
- ✅ **Auth0**: `USE_STAGING_AUTH0=true`
- ✅ **CORS**: Allows `*.onrender.com` wildcard
- ✅ **Debug Logging**: `ENABLE_DEBUG_LOGGING=true`
- ✅ **Sentry**: Disabled (`SENTRY_DSN=""`)

```bash
# Test preview environment
PREVIEW_URL="https://marketedge-platform-pr-[NUMBER].onrender.com"

# Health check
curl "$PREVIEW_URL/health"

# Environment validation
curl "$PREVIEW_URL/api/v1/environment"

# Auth0 configuration check
curl "$PREVIEW_URL/api/v1/auth/config"
```

## 🎯 Business Impact: £925K Zebra Associates Opportunity

### Enhanced Development Workflow
- **Automatic Demo URLs**: Every PR gets stable preview URL for client presentations
- **Zero Configuration**: No manual preview environment setup required
- **Professional Presentation**: `marketedge-platform-pr-17.onrender.com` style URLs
- **Safe Testing**: Production-isolated preview environments with staging Auth0

### Preview Environment Features
- **Production-like Configuration**: Same FastAPI + PostgreSQL + Redis stack
- **Staging Auth0 Integration**: Safe authentication testing without production impact
- **Automatic Database Setup**: Migrations and seed data applied automatically
- **Environment Variable Inheritance**: All 23 production variables with preview overrides

## 🔒 Security Considerations

### Production Safety
- **Zero Production Impact**: Preview environments use staging Auth0 configuration
- **Environment Isolation**: Preview variables inherit from `production-env-pr-[number]`
- **Secret Management**: Sensitive variables properly isolated between environments
- **Access Control**: Preview environments accessible via unique URLs

### Environment Variable Security
- **Production Variables**: Remain in `production-env` group
- **Preview Variables**: Created in `production-env-pr-[number]` groups
- **Staging Auth0**: Preview environments use staging credentials only
- **Database Isolation**: Preview environments use staging database configuration

## ✅ Success Verification Checklist

### Blueprint Conversion Success
- [ ] Service name matches exactly: `marketedge-platform`
- [ ] Blueprint linked successfully in Render dashboard
- [ ] Service shows "Blueprint linked: ✓ synced just now"
- [ ] Production URL unchanged: https://marketedge-platform.onrender.com
- [ ] All 23 environment variables preserved

### Preview Environment Validation
- [ ] New PR creates preview service automatically
- [ ] Preview URL accessible: `https://marketedge-platform-pr-[number].onrender.com`
- [ ] Health check returns 200: `/health` endpoint
- [ ] Staging Auth0 configuration active
- [ ] Environment variables properly inherited
- [ ] Preview cleanup when PR closed

### Business Functionality Verification
- [ ] Auth0 staging integration working
- [ ] Multi-tenant functionality operational
- [ ] Database connectivity established
- [ ] API endpoints responding correctly
- [ ] Admin panel accessible for demonstrations

## 🚨 Rollback Plan

If Blueprint conversion causes issues:

1. **Disconnect Blueprint**: Render Settings → Blueprint → "Disconnect Blueprint"
2. **Service Continues**: Returns to original manual configuration
3. **Environment Groups**: Remain intact and functional
4. **Zero Downtime**: No service interruption during rollback

## 📋 Post-Implementation Tasks

1. **Update Documentation**: Add preview environment URLs to team documentation
2. **Team Training**: Demonstrate preview environment workflow to development team
3. **Client Presentations**: Use preview environments for Zebra Associates demonstrations
4. **Monitoring Setup**: Configure alerts for preview environment health
5. **Cost Monitoring**: Track preview environment usage and costs

---

**Next Steps**: Execute manual Blueprint linking in Render dashboard, then create test PR to validate automatic preview environment generation.