# Preview Environment Verification Guide

## Date: 2025-09-22
## PR: #18 - Validate: Automatic Preview Environment Generation

### Current Status: TRIGGERED
- **Commit**: 9f6f16e - Added preview environment indicators to health endpoint
- **Push Time**: 2025-09-22 (just now)
- **Expected Preview Ready**: Within 5-10 minutes

## Verification Dashboard

### 1. Render Dashboard Monitoring
**URL**: https://dashboard.render.com

**What to Look For**:
- New service appearing with name pattern: `marketedge-platform-pr-18`
- Status progression: Building → Deploying → Live
- Environment type: Preview
- Connected to PR #18

### 2. Expected Preview URLs
Once deployed, access these endpoints:

**Health Check** (Primary Validation):
```
https://marketedge-platform-pr-18.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "preview_environment": true,
  "pr_number": "18",
  "architecture": "production_lazy_initialization",
  "cors_configured": true,
  "critical_business_ready": true
}
```

**API Documentation**:
```
https://marketedge-platform-pr-18.onrender.com/api/v1/docs
```

**Ready Check**:
```
https://marketedge-platform-pr-18.onrender.com/ready
```

### 3. Validation Commands

Test the preview environment once it's live:

```bash
# Test health endpoint
curl https://marketedge-platform-pr-18.onrender.com/health | jq .

# Check preview indicators
curl https://marketedge-platform-pr-18.onrender.com/health | jq '.preview_environment, .pr_number'

# Test API documentation accessibility
curl -I https://marketedge-platform-pr-18.onrender.com/api/v1/docs

# Test CORS configuration
curl -H "Origin: https://test.example.com" \
     -I https://marketedge-platform-pr-18.onrender.com/health
```

### 4. Blueprint Configuration Validated

The corrected `render.yaml` on main branch includes:
- ✅ Proper `envGroups` schema (was `envGroup`)
- ✅ Correct indentation for all sections
- ✅ Preview environment configuration
- ✅ Health check path set to `/health`
- ✅ Auto-deploy disabled for previews

### 5. Monitoring Checklist

#### Immediate (0-2 minutes):
- [ ] Check Render dashboard for new preview service
- [ ] Verify webhook received in GitHub settings
- [ ] Monitor build logs starting

#### Short-term (2-5 minutes):
- [ ] Build phase completing
- [ ] Docker image created
- [ ] Dependencies installed

#### Deployment (5-10 minutes):
- [ ] Service starting
- [ ] Health checks beginning
- [ ] Service marked as "Live"
- [ ] Preview URL accessible

#### Validation (10+ minutes):
- [ ] Health endpoint returns correct response
- [ ] Preview indicators show `true` and PR number
- [ ] API documentation loads
- [ ] No 502/503 errors

### 6. Troubleshooting Guide

#### Preview Not Appearing:
1. Check Render dashboard → Blueprints → Sync status
2. Verify GitHub webhook: Settings → Webhooks → Recent Deliveries
3. Check render.yaml syntax on main branch
4. Ensure Render has access to the repository

#### Preview Build Failing:
1. Check build logs in Render dashboard
2. Verify Python version matches (3.11)
3. Check for missing environment variables
4. Ensure requirements.txt is accessible

#### Preview Not Accessible:
1. Verify service is marked "Live" in Render
2. Check health check is passing
3. Review service logs for startup errors
4. Confirm port 8000 is being used

### 7. Success Criteria

✅ **Preview Environment Created**: Service appears in Render dashboard
✅ **Deployment Successful**: Service status is "Live"
✅ **Health Check Passing**: /health returns 200 with preview indicators
✅ **PR Integration**: Environment linked to PR #18
✅ **Auto-cleanup Ready**: Will delete when PR is closed/merged

### 8. Business Value Confirmation

This successful preview environment validates:
- **Development Velocity**: Every PR gets isolated testing environment
- **Quality Assurance**: Changes tested before production merge
- **Client Demonstrations**: Safe environment for £925K Zebra Associates demos
- **Risk Mitigation**: Issues caught in preview, not production
- **Team Collaboration**: Reviewers can test live changes

### 9. Next Steps After Validation

Once preview environment is confirmed working:
1. Document the preview URL in PR comments
2. Run integration tests against preview environment
3. Perform security validation on preview
4. Test Auth0 integration if configured
5. Validate database connections if applicable

### 10. Cleanup

The preview environment will automatically be deleted when:
- PR #18 is merged
- PR #18 is closed
- Manual deletion via Render dashboard

No manual cleanup required - Render Blueprint handles lifecycle automatically.

---

## Status Updates

### Update 1: 2025-09-22 - Initial Trigger
- Pushed commit 9f6f16e to PR #18
- Waiting for Render webhook processing
- Monitoring dashboard for preview creation

### Update 2: [Pending]
- Check back in 5-10 minutes for deployment status

### Update 3: [Pending]
- Validation of preview environment functionality

---

**Contact**: For issues, check Render status page or GitHub webhook deliveries
**Documentation**: See render.yaml in repository root for Blueprint configuration