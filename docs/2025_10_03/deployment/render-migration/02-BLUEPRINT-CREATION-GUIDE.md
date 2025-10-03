# Render Blueprint Creation Guide

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Status:** Implementation Ready

## Overview

This guide provides step-by-step instructions for creating new Render services from the `render.yaml` blueprint to enable Infrastructure-as-Code (IaC) management.

## Prerequisites

Before beginning blueprint deployment:

- [ ] Repository access with render.yaml file
- [ ] Render account with appropriate permissions
- [ ] Updated render.yaml with new service names (see 04-UPDATED-RENDER-YAML.md)
- [ ] Environment variables documented (see 05-ENVIRONMENT-VARIABLE-MIGRATION.md)
- [ ] Stakeholder approval for migration

## Blueprint Deployment Process

### Step 1: Prepare Git Branch

Create a dedicated branch for blueprint migration:

```bash
# From repository root
cd /Users/matt/Sites/MarketEdge

# Create migration branch
git checkout -b blueprint-migration

# Verify render.yaml exists
ls -la render.yaml

# Optional: Commit any pending changes to render.yaml
git add render.yaml
git commit -m "config: prepare render.yaml for blueprint migration"
git push origin blueprint-migration
```

**Verification:**
- Branch `blueprint-migration` created
- render.yaml present and up-to-date
- Changes pushed to remote repository

### Step 2: Access Render Dashboard

1. Navigate to: https://dashboard.render.com
2. Log in with account credentials
3. Verify you have permission to create new services

**Critical:** Ensure you're logged into the correct Render account that owns the existing `marketedge-platform` service.

### Step 3: Initiate Blueprint Creation

**Option A: Via Dashboard (RECOMMENDED)**

1. Click **"New +"** button in top-right corner
2. Select **"Blueprint"** from dropdown menu
3. You'll be directed to "Create a New Blueprint" screen

**Option B: Via Direct URL**

Navigate directly to: https://dashboard.render.com/select-repo?type=blueprint

### Step 4: Connect Repository

**First-Time Repository Connection:**

1. On "Create a New Blueprint" screen, click **"Connect GitHub"**
2. Authorize Render to access GitHub repositories
3. Select the MarketEdge repository
4. Render will scan for render.yaml automatically

**Existing Repository Connection:**

1. Repository should appear in dropdown: "MarketEdge" or "username/MarketEdge"
2. Select the repository
3. Render will automatically detect render.yaml

**Verification:**
- Repository connected successfully
- Render displays: "Blueprint file found: render.yaml"

### Step 5: Select Branch

**Critical Step:** Select the correct branch for deployment

1. Branch dropdown appears after repository selection
2. **For Migration:** Select `blueprint-migration` branch
3. **Alternative:** Select `main` if render.yaml already updated there

**Verification:**
- Correct branch selected
- Blueprint preview shows expected services

### Step 6: Review Blueprint Configuration

Render will parse render.yaml and display a preview:

**Expected Services Display:**

```
Services to be created:
✓ marketedge-platform-iac (Web Service)
✓ marketedge-platform-staging-iac (Web Service)

Databases to be created:
✓ marketedge-preview-db (PostgreSQL - Free)
✓ marketedge-staging-db-iac (PostgreSQL - Free)

Environment Groups:
✓ production-env
✓ staging-env
```

**Review Checklist:**
- [ ] Service names correct (include -iac suffix)
- [ ] Databases listed as expected
- [ ] No unexpected services or resources
- [ ] Region set correctly (Oregon)
- [ ] Plan types correct (Free tier)

### Step 7: Configure Service-Specific Settings

**Before clicking "Apply"**, review auto-detected settings:

**For Each Service:**
- **Build Command:** Should match render.yaml specification
- **Start Command:** Should be `./render-startup.sh`
- **Environment Variables:** Mark as "will configure manually" (secrets)
- **Auto-Deploy:** Confirm branch deployment triggers

**Common Issues:**

| Issue | Resolution |
|-------|------------|
| Build command empty | Render sometimes doesn't detect from yaml - add manually |
| Start command incorrect | Manually set to `./render-startup.sh` |
| Python version not detected | Will be set via PYTHON_VERSION env var |

### Step 8: Apply Blueprint

1. Review final configuration summary
2. Click **"Apply"** button at bottom of screen
3. Render begins creating all services defined in blueprint

**What Happens Next:**

- Render creates services in parallel
- Databases provisioned first (longest step)
- Web services created and linked to databases
- Initial deployment triggered automatically
- Services appear in dashboard as they're created

**Duration Estimate:**
- Database creation: 2-5 minutes
- Service creation: 1-2 minutes per service
- Initial deployment: 5-10 minutes (includes build time)
- **Total: 10-20 minutes**

### Step 9: Monitor Blueprint Creation

**During Creation:**

1. Render displays real-time progress
2. Each service shows status: Creating → Building → Deploying → Live
3. Monitor for any errors or warnings

**Access Service Logs:**

1. Click on newly created service in dashboard
2. Navigate to "Logs" tab
3. Monitor build and deployment output

**Common Creation Issues:**

| Error | Cause | Resolution |
|-------|-------|------------|
| "Database not ready" | Database still provisioning | Wait for DB creation to complete |
| "Build failed: requirements.txt" | Dependency issue | Check requirements.txt compatibility |
| "Start command failed" | Missing startup script | Verify render-startup.sh in repository |
| "Environment variable missing" | Required secret not set | Add via dashboard (expected - see Step 10) |

### Step 10: Verify IaC Toggle Enabled

**CRITICAL VERIFICATION:**

After services are created, verify IaC management is enabled:

1. Click on newly created service: `marketedge-platform-iac`
2. Navigate to **"Settings"** tab
3. Scroll to **"Blueprint"** section
4. **Verify:** Toggle shows "Blueprint file: render.yaml" with edit option

**Expected Display:**

```
Blueprint
This service is managed by a Blueprint file.
Blueprint file: render.yaml
[Edit Blueprint] button available
```

**If IaC Toggle Not Present:**
- Service was NOT created from blueprint
- Restart process from Step 3
- Verify branch selection in Step 5 was correct

### Step 11: Configure Environment Variables

**Critical Secrets (MUST be set manually):**

For **marketedge-platform-iac** (Production):

1. Navigate to service → Settings → Environment
2. Add the following secrets:

```bash
# Auth0 Secrets
AUTH0_CLIENT_SECRET=<copy from old service>
AUTH0_ACTION_SECRET=<copy from old service>

# JWT Secret
JWT_SECRET_KEY=<copy from old service>

# Database (Production)
DATABASE_URL=<copy from old service>

# Redis
REDIS_URL=<copy from old service>

# Optional: Sentry
SENTRY_DSN=<copy from old service if configured>
```

For **marketedge-platform-staging-iac** (Staging):

```bash
# Auth0 Secrets (staging)
AUTH0_CLIENT_SECRET=<copy from old staging or use dev>
AUTH0_ACTION_SECRET=<copy from old staging or use dev>

# JWT Secret (DIFFERENT from production)
JWT_SECRET_KEY=<generate new staging secret>

# Database (automatically configured via fromDatabase)
# No manual DATABASE_URL needed

# Redis (can share with production or separate)
REDIS_URL=<staging redis URL>
```

**How to Copy from Old Service:**

```bash
# Via Render Dashboard (RECOMMENDED)
1. Open old service: marketedge-platform
2. Settings → Environment tab
3. Copy each secret value
4. Paste into new service environment variables

# Note: Render masks secret values - you may need access to original values
```

**Security Note:** Do NOT commit secrets to render.yaml. All secrets marked with `sync: false` must be configured via dashboard.

### Step 12: Trigger Initial Deployment

After environment variables configured:

1. Navigate to service dashboard
2. Click **"Manual Deploy"** dropdown
3. Select **"Deploy latest commit"**
4. Deployment begins with all environment variables available

**Monitor Deployment:**

- **Logs Tab:** Real-time build and startup logs
- **Events Tab:** Deployment status and triggers
- **Expected Duration:** 5-10 minutes for first deployment

### Step 13: Verify Service Health

**Health Check Endpoints:**

```bash
# Production Service
curl https://marketedge-platform-iac.onrender.com/health

# Expected Response
{
  "status": "healthy",
  "timestamp": "2025-10-03T...",
  "version": "1.0.0"
}

# Staging Service
curl https://marketedge-platform-staging-iac.onrender.com/health
```

**Comprehensive Verification:**

```bash
# Test API endpoints
curl https://marketedge-platform-iac.onrender.com/api/v1/

# Test authentication
curl https://marketedge-platform-iac.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"test"}'

# Verify database connection
curl https://marketedge-platform-iac.onrender.com/api/v1/health/db
```

**Success Criteria:**
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible at /docs
- [ ] Authentication endpoints respond correctly
- [ ] Database connection verified
- [ ] No critical errors in logs

## Post-Deployment Verification

### Verify Blueprint Management

**Test IaC Workflow:**

1. Make a minor change to render.yaml (e.g., update comment)
2. Commit and push to blueprint-migration branch
3. Verify Render detects change and offers to redeploy
4. Confirm automatic deployment triggered

**Expected Behavior:**
- Render dashboard shows: "Blueprint file updated"
- Option to "Apply Changes" appears
- Clicking "Apply Changes" triggers redeployment with new configuration

### Compare Old vs New Services

Create comparison checklist:

| Aspect | Old Service | New Service | Match? |
|--------|------------|-------------|--------|
| Service URL | marketedge-platform.onrender.com | marketedge-platform-iac.onrender.com | ✓ |
| Environment Variables | 25+ configured | 25+ configured | ☐ Verify |
| Database Connection | Production DB | Production DB (same) | ☐ Verify |
| Health Status | Healthy | Healthy | ☐ Verify |
| Build Time | ~8 minutes | ~8 minutes | ☐ Verify |
| Start Time | ~30 seconds | ~30 seconds | ☐ Verify |

## Troubleshooting Guide

### Issue: Blueprint Not Detected

**Symptoms:**
- Render doesn't show "Blueprint file found"
- No services listed for creation

**Resolution:**
1. Verify render.yaml exists in repository root
2. Check render.yaml syntax (use online YAML validator)
3. Ensure branch selection is correct
4. Try refreshing repository connection

### Issue: Service Creation Fails

**Symptoms:**
- Service stuck in "Creating" state
- Error message during creation

**Resolution:**
1. Check Render status page: https://status.render.com
2. Verify account limits not exceeded (free tier: 100 services max)
3. Review render.yaml for syntax errors
4. Check service name conflicts with existing services

### Issue: Build Fails

**Symptoms:**
- Build logs show errors
- Service never reaches "Live" state

**Common Causes & Fixes:**

```bash
# Python version mismatch
Error: Python 3.11.10 not found
Fix: Verify PYTHON_VERSION env var set correctly

# Dependency installation failure
Error: Could not find a version that satisfies the requirement
Fix: Update requirements.txt with compatible versions

# Missing requirements.txt
Error: requirements.txt not found
Fix: Verify file exists in repository root

# Out of memory during build
Error: Killed (OOM)
Fix: Upgrade to Starter plan or optimize dependencies
```

### Issue: Start Command Fails

**Symptoms:**
- Build succeeds but service crashes immediately
- Logs show "Start command exited with error"

**Resolution:**

```bash
# Verify startup script exists
ls -la render-startup.sh

# Check script permissions
chmod +x render-startup.sh

# Test startup script locally
./render-startup.sh

# Common startup script errors:
Error: uvicorn: command not found
Fix: Ensure uvicorn in requirements.txt

Error: app.main:app not found
Fix: Verify PYTHONPATH includes app directory
```

### Issue: Environment Variables Missing

**Symptoms:**
- Service starts but authentication fails
- Database connection errors
- "Missing required configuration" errors

**Resolution:**
1. Verify all sync: false variables configured manually
2. Check variable names match exactly (case-sensitive)
3. Ensure no trailing spaces in values
4. Verify secrets copied correctly from old service

### Issue: Database Connection Fails

**Symptoms:**
- "Could not connect to database" errors
- SQLAlchemy connection timeout

**Resolution:**

```bash
# Verify DATABASE_URL format
postgresql://user:password@host:port/database

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Check database service status
# Dashboard → Database → Status should be "Available"

# Verify network connectivity
# Both service and database should be in same region
```

## Emergency Rollback During Blueprint Creation

**If Blueprint Deployment Goes Wrong:**

### Immediate Actions:

1. **Stop Deployment:**
   - Render dashboard → Service → Settings → Suspend Service
   - This prevents further resource consumption

2. **Preserve Old Service:**
   - Verify old service `marketedge-platform` still running
   - Traffic continues flowing to old service (no impact)

3. **Delete Failed Services:**
   - Dashboard → Service → Settings → Delete Service
   - Remove all services created by failed blueprint
   - Databases can be deleted separately

4. **Review Errors:**
   - Download logs from failed services
   - Identify root cause before retry
   - Update render.yaml to fix issues

5. **Retry Blueprint Creation:**
   - Fix render.yaml configuration
   - Commit and push changes
   - Restart from Step 3

**No User Impact:** Old service remains operational throughout blueprint creation process.

## Success Validation Checklist

After completing all steps, verify:

- [ ] Services created with `-iac` suffix names
- [ ] IaC toggle visible in service settings
- [ ] Blueprint file shows: render.yaml
- [ ] All environment variables configured
- [ ] Health endpoints return 200 OK
- [ ] Authentication endpoints functional
- [ ] Database connections established
- [ ] Logs show no critical errors
- [ ] Services accessible via .onrender.com URLs
- [ ] Old services still running (not affected)

## Next Steps

Upon successful blueprint creation:

1. **Proceed to Testing:** See [07-VERIFICATION-TESTS.md](./07-VERIFICATION-TESTS.md)
2. **Plan Traffic Migration:** See [08-TRAFFIC-MIGRATION-GUIDE.md](./08-TRAFFIC-MIGRATION-GUIDE.md)
3. **Prepare Monitoring:** Configure alerts for new services
4. **Document URLs:** Record new service URLs for team reference

## Related Documents

- [03-MIGRATION-CHECKLIST.md](./03-MIGRATION-CHECKLIST.md) - Full migration task list
- [05-ENVIRONMENT-VARIABLE-MIGRATION.md](./05-ENVIRONMENT-VARIABLE-MIGRATION.md) - Detailed env var guide
- [06-ROLLBACK-PROCEDURES.md](./06-ROLLBACK-PROCEDURES.md) - Emergency procedures
- [07-VERIFICATION-TESTS.md](./07-VERIFICATION-TESTS.md) - Testing procedures

---

**Document Status:** READY FOR IMPLEMENTATION
**Complexity:** Moderate - requires careful attention to environment variables
**Estimated Duration:** 30-45 minutes (excluding initial deployment time)
