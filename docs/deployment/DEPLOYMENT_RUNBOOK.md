# Deployment Runbook - Staging Gate Operations

**Document Version:** 1.0
**Date:** 2025-10-02
**Prepared By:** Maya (DevOps Engineer)

---

## Quick Start

### Daily Developer Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes, commit, and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 3. Open PR to staging branch (NOT main)
# GitHub UI: New Pull Request → base: staging

# 4. After approval, merge to staging
# Staging auto-deploys within 5-10 minutes

# 5. Test in staging: https://staging.zebra.associates

# 6. When ready for production:
#    - Open PR from staging to main
#    - After merge, create GitHub Release tag
#    - Production auto-deploys from tag
```

---

## Deployment Procedures

### Procedure 1: Deploy Feature to Staging

**When:** Feature development complete, ready for UAT

**Steps:**
1. **Create PR to staging branch**
   ```bash
   # Ensure feature branch is up to date
   git checkout feature/my-feature
   git pull origin staging
   git push origin feature/my-feature

   # Create PR via GitHub UI
   # Base: staging, Compare: feature/my-feature
   ```

2. **Wait for CI checks**
   - Zebra smoke tests must pass
   - Database migration tests must pass
   - Code review must be approved

3. **Merge PR**
   - Click "Squash and merge" or "Merge pull request"
   - Delete feature branch after merge

4. **Monitor staging deployment**
   ```bash
   # Watch GitHub Actions
   # Workflow: "Staging Environment Deployment"

   # Check deployment status
   curl https://marketedge-platform-staging.onrender.com/health
   ```

5. **Verify in staging**
   - Open: https://staging.zebra.associates
   - Test feature manually
   - Get stakeholder approval

**Expected Duration:** 15-30 minutes from merge to verified deployment

---

### Procedure 2: Deploy Staging to Production

**When:** Staging validated, ready for production release

**Prerequisites:**
- [ ] All features tested in staging
- [ ] Stakeholder approval received
- [ ] No critical bugs in staging
- [ ] Database migrations tested

**Steps:**

1. **Create PR from staging to main**
   ```bash
   # Via GitHub UI
   # Base: main, Compare: staging
   # Title: "Release v1.x.x - [Description]"
   ```

2. **Review changes**
   - Review all commits since last production release
   - Verify database migrations
   - Check for breaking changes
   - Get final approval

3. **Merge PR to main**
   - Click "Merge pull request" (do NOT squash for releases)
   - This does NOT trigger production deployment yet

4. **Create GitHub Release**
   ```bash
   # Via GitHub UI: Releases → Draft a new release

   Tag: v1.0.0
   Target: main
   Title: Release v1.0.0 - [Brief Description]
   Description:
   ## Features
   - Feature 1
   - Feature 2

   ## Bug Fixes
   - Fix 1
   - Fix 2

   ## Breaking Changes
   - None

   # Click: "Publish release"
   ```

5. **Monitor production deployment**
   ```bash
   # Watch GitHub Actions
   # Workflow: "Production Deployment (Tag-Based)"

   # Wait for deployment to complete (~10-15 minutes)
   # Includes:
   # - Tag validation
   # - Pre-deployment checks
   # - Render deployment
   # - Smoke tests
   ```

6. **Verify production deployment**
   ```bash
   # Check health endpoint
   curl https://marketedge-platform.onrender.com/health

   # Test critical functionality
   # - Login flow
   # - Dashboard access
   # - Super admin panel
   ```

7. **Monitor for 24 hours**
   - Watch error rates
   - Monitor response times
   - Check user feedback
   - Review logs for issues

**Expected Duration:** 30-45 minutes from release tag to verified production deployment

---

### Procedure 3: Emergency Hotfix

**When:** Critical bug in production requiring immediate fix

**Steps:**

1. **Create hotfix branch from main**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-bug-fix
   ```

2. **Make minimal fix**
   - Keep changes as small as possible
   - Focus only on the critical issue
   - Add tests if possible

3. **Fast-track through staging**
   ```bash
   # Create PR to staging
   # Label: "hotfix" and "urgent"
   # Request immediate review

   # After merge and staging verification
   # Create PR to main
   # Create release tag immediately
   ```

4. **Option: Bypass staging (extreme emergencies only)**
   ```bash
   # Create PR directly to main
   # Requires approval from tech lead
   # Must include justification for bypass
   ```

**Expected Duration:** 15-30 minutes (expedited process)

**Post-Hotfix:**
- Document what happened
- Review why hotfix was needed
- Add tests to prevent recurrence
- Schedule proper fix if hotfix is temporary

---

### Procedure 4: Rollback Production Deployment

**When:** Production deployment failed or critical issue discovered

**Option A: Automated Rollback (Preferred)**

```bash
# GitHub Actions will automatically rollback if smoke tests fail
# Or trigger manually:

# 1. Go to GitHub Actions
# 2. Select "Production Rollback" workflow
# 3. Click "Run workflow"
# 4. Enter previous successful tag (e.g., v1.0.0)
# 5. Click "Run workflow"
```

**Option B: Manual Rollback via Render**

```bash
# 1. Login to Render Dashboard
# 2. Select: marketedge-platform (production service)
# 3. Go to: Deployments tab
# 4. Find: Previous successful deployment
# 5. Click: "Redeploy"
# 6. Verify: Health endpoint returns 200 OK
```

**Option C: Rollback via Git Tag**

```bash
# Create rollback release tag
git tag -a v1.0.0-rollback -m "Rollback to v1.0.0 due to [reason]"
git push origin v1.0.0-rollback

# Production deployment workflow will trigger
# Will deploy code from v1.0.0 tag
```

**Verification:**
```bash
# Check production health
curl https://marketedge-platform.onrender.com/health

# Test critical functionality
# - Login works
# - Dashboard loads
# - No errors in logs
```

**Expected Duration:** 5-10 minutes

**Post-Rollback:**
- Notify team via Slack/email
- Document rollback reason
- Create incident report
- Plan fix for rolled-back issue

---

## Monitoring and Alerting

### Health Checks

**Staging:**
```bash
# Health endpoint
curl https://marketedge-platform-staging.onrender.com/health

# Expected response:
# {"status": "healthy", "environment": "staging"}
```

**Production:**
```bash
# Health endpoint
curl https://marketedge-platform.onrender.com/health

# Expected response:
# {"status": "healthy", "environment": "production"}
```

### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Error Rate | <1% | >5% |
| Response Time (p95) | <500ms | >2000ms |
| Health Endpoint Uptime | 99.9% | <99% |
| Failed Logins | <5% | >20% |
| Database Connection Pool | <80% | >90% |

### Log Monitoring

**Render Logs:**
```bash
# Via Render Dashboard
# Service → Logs tab
# Filter by log level: ERROR, WARN
```

**Key Log Patterns to Watch:**
```bash
# Authentication errors
"JWT verification failed"
"Invalid token"
"Auth0 user lookup failed"

# Database errors
"Connection refused"
"Migration failed"
"Deadlock detected"

# Application errors
"Internal server error"
"Unhandled exception"
"Rate limit exceeded"
```

---

## Troubleshooting Guide

### Issue: Staging Deployment Failed

**Symptoms:**
- GitHub Actions workflow fails
- Render shows deployment error
- Health endpoint not responding

**Diagnosis:**
```bash
# 1. Check GitHub Actions logs
# GitHub → Actions → Failed workflow → View logs

# 2. Check Render deployment logs
# Render Dashboard → Staging Service → Logs

# 3. Common causes:
# - Database migration failure
# - Environment variable missing
# - Build failure (missing dependency)
# - Startup script error
```

**Resolution:**
```bash
# Fix the issue, then:
# 1. Push fix to staging branch
# 2. Render will auto-redeploy
# 3. Monitor for successful deployment
```

---

### Issue: Production Smoke Tests Failing

**Symptoms:**
- Production deployment completes but smoke tests fail
- Automatic rollback triggered

**Diagnosis:**
```bash
# Check smoke test logs in GitHub Actions
# Common failures:
# - Health endpoint timeout
# - Authentication failure
# - Missing environment variable
# - CORS configuration issue
```

**Resolution:**
```bash
# If rollback occurred:
# 1. Fix the issue in staging first
# 2. Test thoroughly in staging
# 3. Create new production release

# If no rollback yet:
# 1. Manually trigger rollback
# 2. Fix in staging
# 3. Redeploy when fixed
```

---

### Issue: Cannot Login After Deployment

**Symptoms:**
- Users cannot authenticate
- "Invalid credentials" or "Auth0 error"

**Diagnosis:**
```bash
# 1. Check Auth0 configuration
curl "https://backend-url/api/v1/auth/auth0-url?redirect_uri=..."

# Should include 'audience' parameter

# 2. Check Auth0 callback URLs
# Verify current domain is in allowed callback URLs

# 3. Check browser console
# Look for CORS errors or 401/403 responses
```

**Resolution:**
```bash
# If AUTH0_AUDIENCE missing:
# 1. Add via Render Dashboard
# 2. Redeploy service
# 3. Verify in Auth0 URL response

# If callback URL not configured:
# 1. Add to Auth0 Dashboard
# 2. Test login again
```

---

### Issue: Database Migration Failed

**Symptoms:**
- Deployment fails with "Migration error"
- Application won't start

**Diagnosis:**
```bash
# Check migration logs in Render
# Common causes:
# - Syntax error in migration
# - Conflicting migrations
# - Database permissions issue
# - Timeout during large migration
```

**Resolution:**
```bash
# 1. Review migration file
# 2. Test migration locally
# 3. Fix migration
# 4. Redeploy

# If migration partially applied:
# 1. Connect to database
# 2. Check alembic_version table
# 3. Manually rollback if needed
# 4. Reapply corrected migration
```

---

## On-Call Procedures

### P0 Incident: Production Down

**Immediate Actions (5 minutes):**
1. Verify production health endpoint
2. Check Render service status
3. Review recent deployments
4. Initiate rollback if recent deploy

**Communication:**
1. Post in #incidents Slack channel
2. Update status page
3. Notify stakeholders

**Resolution:**
1. Rollback to last known good version
2. Verify service restored
3. Investigate root cause
4. Create incident report

---

### P1 Incident: Critical Feature Broken

**Immediate Actions (15 minutes):**
1. Assess impact (how many users affected?)
2. Determine if rollback needed
3. Check if workaround available

**Resolution:**
1. If recent deploy: rollback
2. If existing issue: create hotfix
3. Deploy hotfix through expedited process
4. Verify fix in production

---

## Maintenance Windows

### Scheduled Maintenance

**When:** Major database migrations, infrastructure updates

**Process:**
1. **1 week before:**
   - Announce maintenance window
   - Notify all stakeholders
   - Prepare rollback plan

2. **24 hours before:**
   - Final reminder
   - Verify backup procedures
   - Review execution plan

3. **During maintenance:**
   - Update status page
   - Execute changes
   - Monitor closely
   - Test thoroughly

4. **After maintenance:**
   - Verify all systems operational
   - Update status page
   - Send completion notice
   - Document any issues

**Recommended Windows:**
- Weekdays: Tuesday-Thursday, 10 AM - 2 PM GMT (low traffic)
- Avoid: Mondays, Fridays, weekends, holidays

---

## Release Calendar

### Regular Release Cadence

**Weekly Releases:**
- Target day: Thursday (allows Friday for monitoring)
- Cut-off for staging: Wednesday 5 PM
- Production release: Thursday 10 AM

**Hotfixes:**
- As needed, expedited process
- Any day/time if critical

**Major Releases:**
- Monthly or quarterly
- Requires advance notice
- May need maintenance window

---

## Team Contacts

### Escalation Path

**P0 Incidents:**
1. On-call engineer (immediate)
2. DevOps lead (within 15 minutes)
3. CTO (within 30 minutes)

**P1 Incidents:**
1. On-call engineer (immediate)
2. DevOps lead (within 1 hour)

**Regular Deployments:**
1. Developer (self-service)
2. Tech lead (approval)
3. DevOps (support)

### External Services

**Render Support:**
- Email: support@render.com
- Dashboard: https://dashboard.render.com

**Vercel Support:**
- Email: support@vercel.com
- Dashboard: https://vercel.com/support

**Auth0 Support:**
- Support Portal: https://support.auth0.com
- Dashboard: https://manage.auth0.com

---

## Document Maintenance

**Review Schedule:** Monthly
**Owner:** DevOps Team
**Last Review:** 2025-10-02
**Next Review:** 2025-11-02

**Change Log:**
- 2025-10-02: Initial version created

---

**Document Version:** 1.0
**Status:** ✅ Ready for Use
