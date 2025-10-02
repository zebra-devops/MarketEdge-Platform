# Staging Gate Implementation Checklist

**Document Version:** 1.0
**Date:** 2025-10-02
**Status:** Implementation Ready

---

## Pre-Implementation Checklist

### Prerequisites (Must Complete First)

**NEW (2025-10-02): render.yaml Blueprint Migration**

- [ ] **Review render.yaml blueprint**
  - File: `/render.yaml` (updated with staging service and fixes)
  - Review: All environment variables, database definitions, services
  - Verify: Configuration matches requirements

- [ ] **Review migration guide**
  - File: `/docs/deployment/RENDER_YAML_MIGRATION.md`
  - Understand: Migration steps and rollback procedures
  - Plan: Schedule migration execution

- [ ] **Run verification script**
  - Command: `./scripts/verify-render-config.sh`
  - Check: render.yaml syntax and configuration
  - Fix: Any errors or warnings

- [ ] **CRITICAL:** Configure AUTH0_AUDIENCE in Render production
  - Value: `https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/`
  - Location: Render Dashboard → marketedge-platform → Environment
  - **NOTE:** Also defined in render.yaml but must be set in Dashboard
  - Test: Verify Auth0 URL includes audience parameter

- [ ] **CRITICAL:** Update CORS_ORIGINS in Render production
  - Value: `https://platform.marketedge.co.uk,...,https://*.vercel.app`
  - Location: Render Dashboard → marketedge-platform → Environment
  - **NOTE:** render.yaml includes this fix, verify in Dashboard
  - Test: Verify CORS headers in API responses

- [ ] **CRITICAL:** Update Auth0 callback URLs
  - Add wildcard patterns for preview/staging environments
  - Location: Auth0 Dashboard → Applications → Settings
  - Test: Login from preview environment works

- [ ] Review current state analysis document
- [ ] Review implementation plan document
- [ ] Get stakeholder approval for staging gate approach
- [ ] Schedule implementation timeline (4-5 weeks)
- [ ] Identify team members for implementation

---

## Phase 1: Foundation (Week 1)

### Git Repository Setup

- [ ] Create `staging` branch from `main`
  ```bash
  git checkout main
  git pull origin main
  git checkout -b staging
  git push origin staging
  ```

- [ ] Configure branch protection for `main`
  - Required reviewers: 1
  - Required status checks: zebra-protection-gate, Database Migration Test
  - No force push
  - No deletion

- [ ] Configure branch protection for `staging`
  - Required reviewers: 1
  - Required status checks: zebra-protection-gate, Database Migration Test
  - No force push
  - No deletion

- [ ] Verify both branches exist and are protected
  ```bash
  git branch -a | grep -E "main|staging"
  ```

### Documentation

- [ ] Document current production deployment process (baseline)
- [ ] Create PRODUCTION_DEPLOYMENT_LEGACY.md
- [ ] Commit all documentation changes
- [ ] Team review of Phase 1 documentation

### Phase 1 Sign-Off

- [ ] All critical configuration issues resolved
- [ ] Staging branch created and protected
- [ ] Documentation complete
- [ ] Team notified of Phase 1 completion

---

## Phase 2: Infrastructure Setup (Week 2)

**NOTE:** Infrastructure now automated via render.yaml blueprint!

### Backend Infrastructure (Render) - Simplified with render.yaml

- [ ] **Apply render.yaml configuration**
  - File: `/render.yaml` already includes staging service definition
  - Action: Render automatically creates service on next deploy
  - Verify: Run `./scripts/verify-render-config.sh` before applying
  - Documentation: `/docs/deployment/RENDER_YAML_MIGRATION.md`

- [ ] **Configure staging secrets (Dashboard)**
  - **REQUIRED SECRETS (manual configuration):**
    - AUTH0_CLIENT_SECRET (same as production or staging-specific)
    - AUTH0_ACTION_SECRET (same as production)
    - JWT_SECRET_KEY (MUST BE DIFFERENT from production)
    - REDIS_URL (can share with production or separate)
  - Location: Render Dashboard → marketedge-platform-staging → Environment
  - **NOTE:** All other env vars auto-injected from render.yaml

- [ ] **Verify staging database auto-provisioned**
  - Database: marketedge-staging-db (auto-created from render.yaml)
  - Verify: Check Render Dashboard → Databases
  - Migrations: Auto-run on deploy (RUN_MIGRATIONS=true in render.yaml)
  - Seed data: May need manual execution after first deploy

- [ ] **Configure staging custom domain (optional)**
  - DNS: CNAME staging-api.zebra.associates → marketedge-platform-staging.onrender.com
  - Render: Add custom domain in service settings
  - Verify: SSL certificate provisioned

- [ ] **Verify staging backend health**
  ```bash
  curl https://marketedge-platform-staging.onrender.com/health
  # Expected: {"status": "healthy", "environment": "staging"}
  ```

### Frontend Infrastructure (Vercel)

- [ ] **Configure Vercel staging environment variables**
  - Location: Vercel Dashboard → Project → Settings → Environment Variables
  - Environment: Preview
  - See: ENVIRONMENT_CONFIGURATION.md for complete list

- [ ] **Configure staging custom domain**
  - DNS: CNAME staging.zebra.associates → cname.vercel-dns.com
  - Vercel: Add domain, assign to staging branch
  - Verify: SSL certificate provisioned

- [ ] **Deploy staging frontend**
  ```bash
  cd platform-wrapper/frontend
  git checkout staging
  git push origin staging
  # Vercel auto-deploys
  ```

- [ ] **Verify staging frontend**
  - Open: https://staging.zebra.associates
  - Check: Can reach login page
  - Check: No console errors

### End-to-End Verification

- [ ] **Test complete staging stack**
  - Frontend → Backend connection works
  - Database queries successful
  - Redis connection successful
  - Authentication flow works (if Auth0 configured)

- [ ] **Document staging URLs**
  - Backend: https://marketedge-platform-staging.onrender.com
  - Frontend: https://staging.zebra.associates
  - Health: /health endpoint

### Phase 2 Sign-Off

- [ ] Staging infrastructure fully deployed
- [ ] All services healthy and accessible
- [ ] End-to-end test successful
- [ ] Team has access to staging environment
- [ ] Costs within budget ($0-14/month increase)

---

## Phase 3: CI/CD Workflows (Week 3)

### Workflow Files Creation

- [ ] **Create staging deployment workflow**
  - File: `.github/workflows/staging-deploy.yml`
  - Triggers: Push to staging branch
  - Actions: Wait for deploy, run smoke tests
  - Test: Manual trigger via workflow_dispatch

- [ ] **Create production deployment workflow**
  - File: `.github/workflows/production-deploy.yml`
  - Triggers: GitHub Release tag
  - Actions: Validate tag, deploy, smoke tests
  - Test: Create test release tag

- [ ] **Create rollback workflow (optional but recommended)**
  - File: `.github/workflows/production-rollback.yml`
  - Triggers: Manual or automatic on smoke test failure
  - Actions: Revert to previous tag
  - Test: Manual trigger

### Workflow Testing

- [ ] **Test staging deployment workflow**
  - Push commit to staging branch
  - Verify workflow runs
  - Verify smoke tests execute
  - Verify deployment summary generated

- [ ] **Test production deployment workflow**
  - Create test release tag (v0.0.1-test)
  - Verify workflow runs
  - Verify all validation steps
  - Verify smoke tests execute
  - Delete test release after verification

- [ ] **Test rollback workflow**
  - Trigger manual rollback
  - Verify previous version deployed
  - Verify smoke tests on rolled-back version

### GitHub Configuration

- [ ] **Update required status checks**
  - Add: staging-smoke-tests (if enforcing staging gate)
  - Location: GitHub → Settings → Branches → main protection

- [ ] **Configure GitHub Secrets**
  - All Auth0 credentials
  - Test user credentials
  - JWT secret key
  - Location: GitHub → Settings → Secrets and variables → Actions

### Phase 3 Sign-Off

- [ ] All workflow files created and committed
- [ ] All workflows tested successfully
- [ ] GitHub secrets configured
- [ ] Branch protection updated
- [ ] No workflow errors or failures

---

## Phase 4: Testing & Validation (Week 4)

### End-to-End Flow Testing

- [ ] **Test: Feature → PR Preview**
  - Create test feature branch
  - Push commits
  - Verify PR preview created (Render + Vercel)
  - Verify Zebra smoke tests run
  - Verify preview environment accessible

- [ ] **Test: PR → Staging**
  - Open PR from feature to staging
  - Get approval
  - Merge to staging
  - Verify staging deployment triggered
  - Verify staging smoke tests pass
  - Verify changes visible in staging

- [ ] **Test: Staging → Production**
  - Create PR from staging to main
  - Get approval
  - Merge to main
  - Create GitHub Release (v1.0.0-test)
  - Verify production deployment triggered
  - Verify production smoke tests pass
  - Verify changes visible in production

### Rollback Testing

- [ ] **Test manual rollback**
  - Trigger rollback workflow manually
  - Specify previous version tag
  - Verify rollback completes successfully
  - Verify correct version deployed

- [ ] **Test automated rollback (simulated)**
  - Deploy version with intentional smoke test failure
  - Verify automatic rollback triggers
  - Or manually verify rollback procedure documented

### Documentation Review

- [ ] Review all implementation documentation
- [ ] Update any outdated information
- [ ] Create user guide for team
- [ ] Get documentation approved by tech lead

### Team Training

- [ ] **Conduct training session**
  - New deployment workflow (PR → Staging → Production)
  - How to use staging environment
  - How to create releases
  - How to handle rollbacks

- [ ] **Create training materials**
  - Video walkthrough (optional)
  - Quick reference guide
  - FAQ document

- [ ] **Team feedback collected**
  - Address any questions or concerns
  - Update documentation based on feedback

### Phase 4 Sign-Off

- [ ] All end-to-end flows tested successfully
- [ ] Rollback procedures tested and documented
- [ ] Team trained on new process
- [ ] Documentation complete and approved
- [ ] No critical issues identified

---

## Phase 5: Production Cutover (Week 5)

### Pre-Cutover Validation

- [ ] **Final checklist review**
  - All Phase 1-4 tasks completed
  - All workflows tested
  - Team trained
  - Documentation complete

- [ ] **Stakeholder communication**
  - Notify team of cutover date/time
  - Send communication about new process
  - Answer any last-minute questions

### Cutover Execution

- [ ] **Update PR template**
  - Add staging gate instructions
  - Update base branch guidance
  - Location: `.github/pull_request_template.md`

- [ ] **Update CONTRIBUTING.md**
  - Document new workflow
  - Add staging gate process
  - Update release process

- [ ] **Disable direct production deployment (optional)**
  - Render: Change auto-deploy to Manual
  - Or: Keep auto-deploy but rely on tag-based workflow
  - Document decision

- [ ] **Enable staging gate requirement**
  - Update branch protection: require staging-smoke-tests
  - Or: Enforce via team process (not technical gate)

- [ ] **Send cutover announcement**
  - Team notification
  - New workflow effective immediately
  - Support channel for questions

### Post-Cutover Monitoring (Week 5-6)

- [ ] **Monitor first production release**
  - First release through new process
  - Watch for any issues
  - Provide hands-on support

- [ ] **Daily check-ins (Week 5)**
  - Team standup: any staging gate issues?
  - Quick fixes for any pain points
  - Document lessons learned

- [ ] **Weekly review (Week 6-8)**
  - Deployment metrics tracking
  - Team feedback collection
  - Process iteration and improvement

### Phase 5 Sign-Off

- [ ] Cutover executed successfully
- [ ] First production release successful
- [ ] No critical issues
- [ ] Team comfortable with new process
- [ ] Metrics tracking in place

---

## Post-Implementation

### Week 6-8: Stabilization

- [ ] Track deployment metrics
  - Staging deployments per week
  - Production deployments per week
  - Deployment failure rate
  - Rollback rate
  - Time from PR to staging
  - Time from staging to production

- [ ] Collect team feedback
  - What's working well?
  - What's causing friction?
  - Any process improvements?

- [ ] Iterate on process
  - Update documentation based on feedback
  - Adjust workflows if needed
  - Add automation where helpful

### Month 2+: Optimization

- [ ] Review metrics monthly
- [ ] Update documentation as needed
- [ ] Add advanced features:
  - [ ] Automated performance testing
  - [ ] Enhanced monitoring and alerting
  - [ ] Deployment analytics dashboard

- [ ] Success criteria validation
  - [ ] Staging deployments: 2-3 per week ✓
  - [ ] Production deployments: 1 per week ✓
  - [ ] Deployment failure rate: <5% ✓
  - [ ] Rollback rate: <2% ✓
  - [ ] Staging bugs found: >90% ✓
  - [ ] Production incidents: <1/month ✓

---

## Rollback Plan

### If Staging Gate Causes Major Issues

- [ ] **Immediate actions**
  - Disable staging gate requirement in branch protection
  - Re-enable direct production deployment (if disabled)
  - Notify team of rollback to old process

- [ ] **Investigation**
  - Document what went wrong
  - Identify root cause
  - Plan fixes

- [ ] **Re-implementation**
  - Fix identified issues
  - Test thoroughly
  - Re-enable staging gate when ready

---

## Success Criteria

### Implementation Success

- [ ] Zero production downtime during implementation
- [ ] All 5 phases completed on schedule (or close)
- [ ] Team adopts new process
- [ ] No critical incidents caused by staging gate

### Operational Success (Post-Implementation)

- [ ] Deployment frequency maintained or improved
- [ ] Deployment failure rate reduced
- [ ] Production incidents reduced
- [ ] Team satisfaction with process
- [ ] Stakeholder confidence increased

---

## Sign-Off

### Phase Completion

- [ ] Phase 1: Foundation - Completed by: __________ Date: __________
- [ ] Phase 2: Infrastructure - Completed by: __________ Date: __________
- [ ] Phase 3: CI/CD Workflows - Completed by: __________ Date: __________
- [ ] Phase 4: Testing & Validation - Completed by: __________ Date: __________
- [ ] Phase 5: Production Cutover - Completed by: __________ Date: __________

### Final Approval

- [ ] DevOps Lead: __________ Date: __________
- [ ] Tech Lead: __________ Date: __________
- [ ] Engineering Manager: __________ Date: __________

---

**Document Version:** 1.0
**Last Updated:** 2025-10-02
**Status:** ✅ Ready for Implementation
