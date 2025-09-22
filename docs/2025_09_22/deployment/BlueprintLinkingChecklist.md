# Render Blueprint Linking Checklist
**Date**: 2025-09-22
**Service**: marketedge-platform
**Repository**: MarketEdge

## Pre-Deployment Verification

### ✅ Configuration Ready
- [x] render.yaml validated and committed
- [x] Code review approved (commit: 370c8f5)
- [x] production-env group exists with 23 variables
- [x] Current service running in manual mode

### ⏳ Auth0 Staging Setup Required
- [ ] Create staging Auth0 application
- [ ] Configure callback URLs with wildcard support
- [ ] Set AUTH0_*_STAGING environment variables in Render

## Blueprint Linking Steps

### Step 1: Access Service Settings
**Action**: Navigate to Render Dashboard
```
1. Go to: https://dashboard.render.com
2. Click on: marketedge-platform service
3. Current URL: https://marketedge-platform.onrender.com
4. Current Status: Manual deployment mode
```

### Step 2: Enable Blueprint Management
**Action**: Link repository to Blueprint
```
1. Click: "Settings" tab
2. Find: "Blueprint" section
3. Click: "Link Repository" or "Enable Blueprint"
4. Configure:
   - Repository: matt/MarketEdge (or your GitHub username)
   - Branch: main
   - Blueprint Path: render.yaml
   - Environment Groups: production-env
```

### Step 3: Validate Configuration
**Action**: Review Blueprint sync preview
```
1. Render will analyze render.yaml
2. Preview changes before applying
3. Verify:
   - Service name: marketedge-platform
   - Environment group: production-env linked
   - Preview configuration: automatic generation enabled
   - Plan: free tier for previews
```

### Step 4: Confirm Blueprint Activation
**Action**: Apply Blueprint configuration
```
1. Review all changes carefully
2. Click: "Apply Blueprint" or "Sync"
3. Monitor deployment progress
4. Verify: Service remains healthy during migration
```

## Post-Deployment Verification

### Step 5: Verify Production Service
**Commands to run**:
```bash
# Test production health
curl https://marketedge-platform.onrender.com/health

# Expected response:
# {"status": "healthy", "environment": "production"}

# Test production API
curl -H "Authorization: Bearer [token]" https://marketedge-platform.onrender.com/api/v1/health
```

### Step 6: Check PR #17 Preview Environment
**Action**: Verify automatic preview generation
```
1. Navigate to: GitHub PR #17
2. Look for: Render deployment status check
3. Find: Automatically generated preview URL
4. Format: https://marketedge-platform-pr-17-[hash].onrender.com
```

### Step 7: Test Preview Environment
**Commands to run**:
```bash
# Get preview URL from PR #17 status check
PREVIEW_URL="https://marketedge-platform-pr-17-[hash].onrender.com"

# Test preview health
curl $PREVIEW_URL/health

# Expected response:
# {"status": "healthy", "environment": "staging"}

# Verify staging Auth0 configuration
curl $PREVIEW_URL/api/auth/config
```

## Auth0 Staging Configuration

### Required Auth0 Setup
**Before Blueprint activation**:
```
1. Auth0 Dashboard → Applications → Create Application
2. Name: MarketEdge Platform (Staging)
3. Type: Single Page Application
4. Settings:
   - Allowed Callback URLs: https://*.onrender.com/api/auth/callback
   - Allowed Logout URLs: https://*.onrender.com
   - Allowed Web Origins: https://*.onrender.com
   - Web Origins: https://*.onrender.com
```

### Environment Variables to Set
**In Render Dashboard → Environment**:
```
AUTH0_DOMAIN_STAGING=marketedge-staging.eu.auth0.com
AUTH0_CLIENT_ID_STAGING=[staging_client_id]
AUTH0_CLIENT_SECRET_STAGING=[staging_secret]
AUTH0_AUDIENCE_STAGING=https://api-staging.marketedge.co.uk
```

## Success Criteria

### ✅ Blueprint Deployment Success
- [ ] Production service health check passes
- [ ] Service converted to Blueprint management mode
- [ ] Environment group (production-env) remains linked
- [ ] No downtime during migration

### ✅ Preview Environment Success
- [ ] PR #17 automatically generated preview environment
- [ ] Preview health check returns "staging" environment
- [ ] Preview environment uses staging Auth0 configuration
- [ ] Preview URL accessible and functional

### ✅ Workflow Integration Success
- [ ] GitHub status checks show Render deployment
- [ ] Preview environments auto-expire after 7 days
- [ ] New PRs automatically trigger preview generation
- [ ] Cost optimization: previews use free tier

## Troubleshooting Quick Reference

### Common Issues and Solutions

#### "Blueprint sync failed"
```bash
# Check render.yaml syntax
yamllint render.yaml

# Verify environment group exists
# Go to Render Dashboard → Environment Groups → production-env
```

#### "Preview environment auth failures"
```bash
# Check staging Auth0 variables are set
curl $PREVIEW_URL/api/auth/config

# Verify callback URLs include wildcard
# Auth0 Dashboard → Applications → Settings → Allowed Callback URLs
```

#### "Service health check fails"
```bash
# Check service logs in Render dashboard
# Verify DATABASE_URL and REDIS_URL are accessible
# Confirm migrations ran successfully
```

## Emergency Contacts

**Immediate Support**:
- DevOps Engineer: Maya (Blueprint specialist)
- Repository Owner: User (GitHub access)
- Business Stakeholder: matt.lindop@zebra.associates

**Rollback Plan**:
1. Render Dashboard → Service Settings → Disable Blueprint
2. Revert to manual deployment mode
3. Redeploy from last known good commit: 370c8f5

## Post-Deployment Actions

### Immediate (Within 1 hour)
- [ ] Test PR #17 preview environment functionality
- [ ] Share preview URL with Zebra Associates contact
- [ ] Monitor production service stability

### Short-term (Within 24 hours)
- [ ] Create test PR to validate automatic preview generation
- [ ] Document any Auth0 staging setup requirements
- [ ] Update team on new Blueprint workflow

### Long-term (Within 1 week)
- [ ] Monitor preview environment costs and usage
- [ ] Validate 7-day cleanup policy is working
- [ ] Gather feedback from Zebra Associates demo usage

---

**Ready for Blueprint Deployment**: All prerequisites met, render.yaml approved
**Next Step**: Begin Step 1 - Access Service Settings in Render Dashboard