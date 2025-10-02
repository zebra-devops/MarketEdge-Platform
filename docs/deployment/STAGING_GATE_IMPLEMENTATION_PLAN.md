# Staging Gate Implementation Plan - MarketEdge Platform

**Document Version:** 1.0
**Date:** 2025-10-02
**Prepared By:** Maya (DevOps Engineer)
**Repository:** zebra-devops/MarketEdge-Platform
**Implementation Timeline:** 4-5 weeks (phased approach)

---

## Executive Summary

This document provides a comprehensive, phased implementation plan for introducing a staging gate between PR preview environments and production deployments for the MarketEdge Platform. The plan respects existing infrastructure while adding deliberate UAT capabilities and tag-based production releases.

**Key Objectives:**
1. Add staging environment for UAT testing
2. Implement tag-based production deployments
3. Maintain existing PR preview functionality
4. Zero production downtime during implementation
5. Minimize cost impact (~$14/month increase)

**Implementation Approach:** Phased rollout over 4-5 weeks with backward compatibility maintained throughout.

---

## IMPORTANT: render.yaml Blueprint Approach

**NEW (2025-10-02):** Infrastructure is now managed via render.yaml blueprint for version-controlled, repeatable deployments.

**Key Documents:**
- **render.yaml Blueprint:** `/render.yaml` - Complete infrastructure configuration
- **Migration Guide:** `/docs/deployment/RENDER_YAML_MIGRATION.md` - Safe migration from dashboard config
- **Verification Script:** `/scripts/verify-render-config.sh` - Validate configuration before deployment
- **Reference:** `/docs/deployment/RENDER_YAML_REFERENCE.md` - Complete render.yaml documentation

**Phase 2 Simplified:** Staging service is now defined in render.yaml. Instead of manual dashboard setup, simply:
1. Update render.yaml (already complete)
2. Configure secrets in Render Dashboard
3. Create staging branch
4. Render automatically provisions staging infrastructure

See: `/docs/deployment/RENDER_YAML_MIGRATION.md` for detailed migration steps.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Implementation Phases](#2-implementation-phases)
3. [Phase 1: Foundation (Week 1)](#3-phase-1-foundation-week-1)
4. [Phase 2: Infrastructure Setup (Week 2)](#4-phase-2-infrastructure-setup-week-2)
5. [Phase 3: CI/CD Workflows (Week 3)](#5-phase-3-cicd-workflows-week-3)
6. [Phase 4: Testing & Validation (Week 4)](#6-phase-4-testing--validation-week-4)
7. [Phase 5: Production Cutover (Week 5)](#7-phase-5-production-cutover-week-5)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Success Criteria](#9-success-criteria)
10. [Resource Requirements](#10-resource-requirements)

---

## 1. Architecture Overview

### 1.1 Current Architecture

```
┌─────────────────┐
│  Feature Branch │
└────────┬────────┘
         │
         ├─────────────► PR Preview Environment
         │               (Render + Vercel)
         │
         ▼
  ┌─────────────┐
  │ Pull Request│
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  main branch│
  └──────┬──────┘
         │
         ▼ (auto-deploy)
  ┌─────────────┐
  │ PRODUCTION  │
  └─────────────┘
```

**Issues:**
- No UAT environment
- Direct production deployment
- No release control
- High risk of production incidents

### 1.2 Target Architecture

```
┌─────────────────┐
│  Feature Branch │
└────────┬────────┘
         │
         ├─────────────► PR Preview Environment
         │               (Render + Vercel)
         │               7-day lifecycle
         ▼
  ┌─────────────┐
  │ Pull Request│
  └──────┬──────┘
         │
         ▼ (merge)
  ┌──────────────┐
  │staging branch│
  └──────┬───────┘
         │
         ▼ (auto-deploy)
  ┌─────────────┐
  │  STAGING    │◄──── UAT Testing
  │ Environment │      Stakeholder Validation
  └──────┬──────┘      Integration Tests
         │
         ▼ (after approval)
  ┌─────────────┐
  │  main branch│
  └──────┬──────┘
         │
         ▼ (create release tag)
  ┌─────────────┐
  │ GitHub      │
  │ Release v1.x│
  └──────┬──────┘
         │
         ▼ (tag-based deploy)
  ┌─────────────┐
  │ PRODUCTION  │◄──── Post-Deploy Smoke Tests
  │ Environment │      Monitoring
  └─────────────┘      Automated Rollback
```

**Benefits:**
- ✅ UAT environment for stakeholder validation
- ✅ Controlled production releases
- ✅ Tag-based versioning
- ✅ Automated smoke tests at each stage
- ✅ Rollback capability
- ✅ Maintains PR preview functionality

### 1.3 Environment Matrix

| Environment | Branch | Deploy Trigger | Database | Auth0 Tenant | Purpose | Lifecycle |
|-------------|--------|----------------|----------|--------------|---------|-----------|
| **Development** | feature/* | Manual | Local | dev-g8trhgbfdq2sk2m8 | Local dev | Manual |
| **PR Preview** | feature/* | Auto (PR open) | Preview DB | dev-g8trhgbfdq2sk2m8 | PR review | 7 days |
| **Staging** | staging | Auto (merge) | Staging DB | dev-g8trhgbfdq2sk2m8 | UAT | Permanent |
| **Production** | main | Tag-based | Production DB | dev-g8trhgbfdq2sk2m8 | Live | Permanent |

---

## 2. Implementation Phases

### 2.1 Phase Overview

| Phase | Duration | Focus | Risk Level | Dependencies |
|-------|----------|-------|------------|--------------|
| Phase 1 | Week 1 | Foundation & Critical Fixes | LOW | None |
| Phase 2 | Week 2 | Infrastructure Setup | MEDIUM | Phase 1 complete |
| Phase 3 | Week 3 | CI/CD Workflows | MEDIUM | Phase 2 complete |
| Phase 4 | Week 4 | Testing & Validation | LOW | Phase 3 complete |
| Phase 5 | Week 5 | Production Cutover | HIGH | Phase 4 validated |

### 2.2 Implementation Timeline

```
Week 1: Foundation
├── Critical config fixes (AUTH0_AUDIENCE, CORS)
├── Create staging branch
├── Set up branch protection
└── Document current state

Week 2: Infrastructure
├── Provision staging Render service
├── Create staging database
├── Configure staging Vercel environment
└── Set up staging environment variables

Week 3: CI/CD Workflows
├── Create staging deployment workflow
├── Create staging smoke test workflow
├── Create production deployment workflow (tag-based)
└── Create production smoke test workflow

Week 4: Testing & Validation
├── Test staging deployment end-to-end
├── Validate smoke tests
├── Test tag-based production deployment
└── Validate rollback procedures

Week 5: Production Cutover
├── Enable staging gate for all PRs
├── Switch production to tag-based deploys
├── Monitor and iterate
└── Team training complete
```

### 2.3 Backward Compatibility Strategy

**Critical Requirement:** Maintain existing PR preview functionality throughout implementation.

**Strategy:**
1. Phase 1-4: Production continues to deploy from `main` branch (no changes)
2. PR previews continue to work as-is (no changes)
3. Staging gate runs in parallel (optional use)
4. Phase 5: Cutover to mandatory staging gate

**Rollback Plan:** If issues arise, disable staging gate and revert to branch-based production deploys.

---

## 3. Phase 1: Foundation (Week 1)

### 3.1 Critical Configuration Fixes

**Priority:** 🔴 CRITICAL - Must complete before any other work

#### Task 1.1: Configure AUTH0_AUDIENCE

**Problem:** Auth0 returns opaque tokens instead of JWT tokens
**Impact:** Authentication will fail after token exchange
**Time Estimate:** 5 minutes

**Steps:**
1. Login to Render Dashboard: https://dashboard.render.com
2. Navigate to: `marketedge-platform` → Environment
3. Click: Add Environment Variable
4. Add variable:
   ```
   Key: AUTH0_AUDIENCE
   Value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
   ```
5. Click: Save Changes
6. Trigger manual redeploy to apply changes

**Verification:**
```bash
# Test Auth0 URL includes audience parameter
curl "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback"

# Should return URL with: &audience=https%3A%2F%2Fdev-g8trhgbfdq2sk2m8.us.auth0.com%2Fapi%2Fv2%2F
```

**Success Criteria:**
- ✅ AUTH0_AUDIENCE environment variable visible in Render
- ✅ Auth0 URL includes audience parameter
- ✅ Login flow works end-to-end
- ✅ JWT tokens returned (not opaque tokens)

---

#### Task 1.2: Update CORS Configuration

**Problem:** CORS_ORIGINS missing Vercel domains
**Impact:** Frontend requests blocked by browser CORS policy
**Time Estimate:** 5 minutes

**Steps:**
1. Login to Render Dashboard
2. Navigate to: `marketedge-platform` → Environment
3. Find: `CORS_ORIGINS` variable
4. Update value to:
   ```
   https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app
   ```
5. Click: Save Changes
6. Trigger manual redeploy

**Verification:**
```bash
# Test CORS headers
curl -H "Origin: https://test-branch.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS \
     https://marketedge-platform.onrender.com/api/v1/auth/login

# Should return Access-Control-Allow-Origin header
```

**Success Criteria:**
- ✅ CORS_ORIGINS includes Vercel wildcard
- ✅ OPTIONS requests return proper CORS headers
- ✅ Frontend can make API requests from Vercel domains

---

#### Task 1.3: Verify Auth0 Callback URLs

**Problem:** Auth0 may not accept wildcard callback URLs
**Impact:** Authentication fails in preview/staging environments
**Time Estimate:** 10 minutes

**Steps:**
1. Login to Auth0 Dashboard: https://manage.auth0.com
2. Navigate to: Applications → MarketEdge Platform → Settings
3. Verify/Update **Allowed Callback URLs:**
   ```
   http://localhost:3000/callback,
   https://app.zebra.associates/callback,
   https://platform.marketedge.co.uk/callback,
   https://staging.zebra.associates/callback,
   https://*.vercel.app/callback,
   https://*.onrender.com/callback
   ```
4. Verify/Update **Allowed Logout URLs:**
   ```
   http://localhost:3000,
   https://app.zebra.associates,
   https://platform.marketedge.co.uk,
   https://staging.zebra.associates,
   https://*.vercel.app,
   https://*.onrender.com
   ```
5. Verify/Update **Allowed Web Origins:**
   ```
   http://localhost:3000,
   https://app.zebra.associates,
   https://platform.marketedge.co.uk,
   https://staging.zebra.associates,
   https://*.vercel.app,
   https://*.onrender.com
   ```
6. Click: Save Changes

**Note:** Auth0 may not support wildcards in all plans. If wildcards not supported:
- Create separate Auth0 application for staging
- Configure staging-specific client ID and secret

**Verification:**
```bash
# Test authentication from preview URL
# Manual test: Open preview URL, click login, verify redirect works
```

**Success Criteria:**
- ✅ Auth0 callback URLs configured
- ✅ Test login from preview environment works
- ✅ Test login from staging environment works (after staging setup)

---

### 3.2 Git Repository Setup

#### Task 1.4: Create Staging Branch

**Time Estimate:** 5 minutes

**Steps:**
```bash
# Ensure local main is up to date
git checkout main
git pull origin main

# Create staging branch from main
git checkout -b staging
git push origin staging

# Return to current working branch
git checkout test/trigger-zebra-smoke
```

**Verification:**
```bash
# Verify staging branch exists
git branch -a | grep staging

# Should show:
# staging
# remotes/origin/staging
```

**Success Criteria:**
- ✅ `staging` branch exists locally
- ✅ `staging` branch pushed to origin
- ✅ `staging` branch identical to `main` (initially)

---

#### Task 1.5: Set Up Branch Protection Rules

**Time Estimate:** 15 minutes

**Steps:**
1. Navigate to: GitHub Repository → Settings → Branches
2. Click: Add branch protection rule

**For `main` branch:**
```yaml
Branch name pattern: main

Protection rules:
  ✅ Require a pull request before merging
     - Required approvals: 1
     - Dismiss stale approvals: true
  ✅ Require status checks to pass before merging
     - Required checks:
       - zebra-protection-gate
       - Database Migration Test
  ✅ Require conversation resolution before merging
  ✅ Do not allow bypassing the above settings
  ❌ Allow force pushes (keep disabled)
  ❌ Allow deletions (keep disabled)
```

**For `staging` branch:**
```yaml
Branch name pattern: staging

Protection rules:
  ✅ Require a pull request before merging
     - Required approvals: 1
     - Dismiss stale approvals: true
  ✅ Require status checks to pass before merging
     - Required checks:
       - zebra-protection-gate
       - Database Migration Test
  ✅ Require conversation resolution before merging
  ✅ Do not allow bypassing the above settings
  ❌ Allow force pushes (keep disabled)
  ❌ Allow deletions (keep disabled)
```

**Success Criteria:**
- ✅ `main` branch protected
- ✅ `staging` branch protected
- ✅ Required status checks configured
- ✅ Force push disabled
- ✅ Deletion disabled

---

### 3.3 Documentation

#### Task 1.6: Document Current Production Deployment

**Time Estimate:** 1 hour

**Create document:** `/docs/deployment/PRODUCTION_DEPLOYMENT_LEGACY.md`

**Content:**
- Current deployment process (branch-based)
- Manual deployment steps
- Rollback procedures
- Known issues and workarounds
- Emergency contact information

**Purpose:** Capture current state before changes for:
- Team reference
- Rollback procedures
- Comparison to new process

**Success Criteria:**
- ✅ Document created and committed
- ✅ Current process fully documented
- ✅ Rollback procedures documented
- ✅ Team reviewed and approved

---

### 3.4 Phase 1 Checklist

**Before proceeding to Phase 2, verify:**
- [ ] AUTH0_AUDIENCE configured in Render production
- [ ] CORS_ORIGINS updated with Vercel domains
- [ ] Auth0 callback URLs verified and updated
- [ ] `staging` branch created and pushed
- [ ] Branch protection rules configured for `main` and `staging`
- [ ] Current production deployment process documented
- [ ] All changes tested and verified
- [ ] Team notified of Phase 1 completion

**Phase 1 Success:** All critical configuration issues resolved, foundation in place for infrastructure setup.

---

## 4. Phase 2: Infrastructure Setup (Week 2)

### 4.1 Staging Backend (Render)

#### Task 2.1: Create Staging Render Service

**Time Estimate:** 45 minutes

**Option A: Via Render Dashboard (Recommended)**

1. Login to Render Dashboard: https://dashboard.render.com
2. Click: New → Web Service
3. Configure service:
   ```yaml
   Name: marketedge-platform-staging
   Environment: Python 3.11
   Region: Oregon (us-west)
   Branch: staging
   Build Command: python --version && pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements.txt
   Start Command: ./render-startup.sh
   Plan: Free (or Starter $7/month for better performance)
   ```
4. Click: Create Web Service

**Option B: Via render.yaml (Preferred for IaC)**

Add to `/render.yaml`:
```yaml
services:
  # ... existing production service ...

  - type: web
    name: marketedge-platform-staging
    env: python-3.11
    plan: free
    branch: staging
    buildCommand: "python --version && pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements.txt"
    startCommand: ./render-startup.sh
    envVarGroups:
      - staging-env
    envVars:
      - key: ENVIRONMENT
        value: staging
      - key: RUN_MIGRATIONS
        value: true
      - key: PORT
        fromService:
          type: web
          name: marketedge-platform-staging
          property: port
      # ... other env vars (copy from production, modify as needed)

envVarGroups:
  # ... existing production-env ...

  - name: staging-env
```

**Environment Variables to Configure:**
See [Task 2.4](#task-24-configure-staging-environment-variables) for complete list.

**Success Criteria:**
- ✅ Staging Render service created
- ✅ Service deploys from `staging` branch
- ✅ Health endpoint returns 200 OK
- ✅ Service URL accessible: `https://marketedge-platform-staging.onrender.com`

---

#### Task 2.2: Create Staging Database

**Time Estimate:** 30 minutes

**Option A: Via Render Dashboard**

1. Navigate to: Dashboard → New → PostgreSQL
2. Configure database:
   ```yaml
   Name: marketedge-staging-db
   Database: marketedge_staging
   User: marketedge_staging_user
   Region: Oregon (us-west)
   Plan: Free (or Starter $7/month for 1GB)
   ```
3. Click: Create Database
4. Copy connection string (Internal Database URL)

**Option B: Render Internal Database (Recommended for Free Plan)**

Render automatically provides a free PostgreSQL instance with each web service on Free plan.

**Database Initialization:**

```bash
# Set DATABASE_URL in staging service to point to staging database

# Migrations will run automatically on deploy via RUN_MIGRATIONS=true

# Seed initial data via startup script or manual execution:
python database/seeds/initial_data.py
python database/seeds/phase3_data.py
```

**Database Strategy:**
- **Schema:** Same as production (via migrations)
- **Data:** Test data only (no production data)
- **Sync:** Manual schema sync via migrations (not data sync)

**Success Criteria:**
- ✅ Staging database provisioned
- ✅ DATABASE_URL configured in staging service
- ✅ Migrations run successfully
- ✅ Initial data seeded
- ✅ Database accessible from staging service

---

#### Task 2.3: Configure Staging Custom Domain (Optional)

**Time Estimate:** 20 minutes

**Requirement:** Custom domain `staging-api.zebra.associates` for staging backend

**Steps:**
1. **DNS Configuration:**
   - Create CNAME record: `staging-api.zebra.associates` → `marketedge-platform-staging.onrender.com`
   - TTL: 300 seconds (5 minutes)

2. **Render Custom Domain:**
   - Navigate to: Staging service → Settings → Custom Domain
   - Add domain: `staging-api.zebra.associates`
   - Wait for DNS propagation (5-30 minutes)
   - Render automatically provisions SSL certificate

**Alternative:** Use default Render URL for staging backend
- URL: `https://marketedge-platform-staging.onrender.com`
- Update frontend configuration to use default URL

**Success Criteria:**
- ✅ DNS CNAME record created
- ✅ Custom domain added in Render
- ✅ SSL certificate provisioned
- ✅ HTTPS endpoint accessible

---

#### Task 2.4: Configure Staging Environment Variables

**Time Estimate:** 30 minutes

**Required Environment Variables for Staging:**

**Database & Redis:**
```bash
DATABASE_URL=<staging-database-internal-url>
REDIS_URL=<staging-redis-url-or-same-as-production>
```

**Auth0:**
```bash
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=<staging-client-id-or-same-as-production>
AUTH0_CLIENT_SECRET=<staging-client-secret>
AUTH0_ACTION_SECRET=<same-as-production>
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
```

**JWT:**
```bash
JWT_SECRET_KEY=<different-from-production-for-security>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Environment:**
```bash
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG
```

**CORS:**
```bash
CORS_ORIGINS=https://staging.zebra.associates,https://*.vercel.app,http://localhost:3000
```

**Security:**
```bash
CSRF_ENABLED=false
CADDY_PROXY_MODE=false
```

**Feature Flags:**
```bash
ENABLE_DEBUG_LOGGING=true
```

**Monitoring:**
```bash
SENTRY_DSN=<staging-sentry-dsn-or-empty>
```

**Configuration Method:**
1. Via Render Dashboard: Environment tab
2. Or via `envVarGroups` in render.yaml (preferred)

**Success Criteria:**
- ✅ All required environment variables configured
- ✅ Staging service restarts successfully
- ✅ Health endpoint returns environment: staging
- ✅ No missing environment variable errors in logs

---

### 4.2 Staging Frontend (Vercel)

#### Task 2.5: Configure Vercel Staging Environment

**Time Estimate:** 30 minutes

**Steps:**

1. **Verify Vercel Project:**
   ```bash
   cd platform-wrapper/frontend
   vercel link
   # Should show: Linked to zebra-devops/marketedge-frontend (or similar)
   ```

2. **Configure Staging Environment Variables (via Vercel Dashboard):**
   - Navigate to: Vercel Dashboard → Project → Settings → Environment Variables
   - Set variables for **Preview** and **Production** (staging will use Preview):

   **Preview Environment:**
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://marketedge-platform-staging.onrender.com
   NEXT_PUBLIC_ENVIRONMENT=staging
   NEXT_PUBLIC_AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
   NEXT_PUBLIC_AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
   NEXT_PUBLIC_EPIC_1_ENABLED=true
   NEXT_PUBLIC_EPIC_2_ENABLED=true
   NEXT_PUBLIC_DEBUG_MODE=true
   ```

   **Note:** Vercel "Preview" environment is used for non-production deployments. We'll configure it to point to staging backend.

3. **Configure Git Integration:**
   - Navigate to: Project → Settings → Git
   - Production Branch: `main`
   - Automatic deployments for: All branches

**Success Criteria:**
- ✅ Vercel project linked
- ✅ Environment variables configured for Preview
- ✅ Git integration configured
- ✅ Test deployment from `staging` branch works

---

#### Task 2.6: Configure Staging Custom Domain (Vercel)

**Time Estimate:** 20 minutes

**Requirement:** Custom domain `staging.zebra.associates` for staging frontend

**Steps:**

1. **DNS Configuration:**
   - Create CNAME record: `staging.zebra.associates` → `cname.vercel-dns.com`
   - TTL: 300 seconds (5 minutes)

2. **Vercel Custom Domain:**
   - Navigate to: Vercel Dashboard → Project → Settings → Domains
   - Add domain: `staging.zebra.associates`
   - Assign to branch: `staging`
   - Wait for DNS propagation (5-30 minutes)
   - Vercel automatically provisions SSL certificate

**Verification:**
```bash
# Test DNS resolution
dig staging.zebra.associates

# Test HTTPS access
curl -I https://staging.zebra.associates
```

**Success Criteria:**
- ✅ DNS CNAME record created
- ✅ Custom domain added in Vercel
- ✅ SSL certificate provisioned
- ✅ Domain assigned to `staging` branch
- ✅ HTTPS endpoint accessible

---

### 4.3 Phase 2 Checklist

**Before proceeding to Phase 3, verify:**
- [ ] Staging Render service created and deployed
- [ ] Staging database provisioned and migrated
- [ ] Staging custom domain configured (backend)
- [ ] Staging environment variables configured (backend)
- [ ] Staging health endpoint returns 200 OK
- [ ] Vercel staging environment configured
- [ ] Vercel custom domain configured (frontend)
- [ ] Staging frontend deploys successfully
- [ ] End-to-end test: Frontend → Backend → Database works
- [ ] All infrastructure documented

**Phase 2 Success:** Complete staging infrastructure deployed and accessible.

---

## 5. Phase 3: CI/CD Workflows (Week 3)

### 5.1 Staging Deployment Workflow

#### Task 3.1: Create Staging Deployment Workflow

**Time Estimate:** 2 hours

**Create file:** `.github/workflows/staging-deploy.yml`

**See:** [STAGING_DEPLOY_WORKFLOW.yml](#staging-deployment-workflow-file) in deliverables section.

**Workflow Features:**
- Triggers on merge to `staging` branch
- Runs database migrations
- Deploys to staging environment
- Runs staging smoke tests
- Comments on PR with deployment status

**Success Criteria:**
- ✅ Workflow file created and committed
- ✅ Workflow triggers on merge to `staging`
- ✅ Deployment completes successfully
- ✅ Smoke tests pass
- ✅ PR comment shows deployment status

---

#### Task 3.2: Create Staging Smoke Test Workflow

**Time Estimate:** 2 hours

**Create file:** `.github/workflows/staging-smoke-tests.yml`

**Workflow Features:**
- Triggers after staging deployment
- Runs E2E tests against staging environment
- Tests critical user journeys
- Tests Zebra Associates specific functionality
- Uploads test results and artifacts

**Test Coverage:**
- ✅ Health endpoint check
- ✅ Authentication flow (matt.lindop@zebra.associates)
- ✅ Super admin panel access
- ✅ Dashboard loading
- ✅ API endpoint availability
- ✅ Database connectivity
- ✅ Redis connectivity

**Success Criteria:**
- ✅ Workflow file created and committed
- ✅ Workflow triggers after staging deploy
- ✅ All smoke tests pass
- ✅ Test artifacts uploaded
- ✅ Failures reported clearly

---

### 5.2 Production Deployment Workflow

#### Task 3.3: Create Production Deployment Workflow (Tag-Based)

**Time Estimate:** 2 hours

**Create file:** `.github/workflows/production-deploy.yml`

**See:** [PRODUCTION_DEPLOY_WORKFLOW.yml](#production-deployment-workflow-file) in deliverables section.

**Workflow Features:**
- Triggers on GitHub Release tag creation
- Validates tag format (v1.0.0)
- Creates production deployment
- Runs production smoke tests
- Notifies team of deployment status
- Automated rollback on smoke test failure

**Success Criteria:**
- ✅ Workflow file created and committed
- ✅ Workflow triggers on release tag
- ✅ Tag format validated
- ✅ Deployment completes successfully
- ✅ Smoke tests pass
- ✅ Team notified

---

#### Task 3.4: Create Production Smoke Test Workflow

**Time Estimate:** 1 hour

**Create file:** `.github/workflows/production-smoke-tests.yml`

**Workflow Features:**
- Triggers after production deployment
- Runs critical smoke tests against production
- Minimal test suite (fast execution)
- Alerts on failure
- Triggers rollback workflow on failure

**Test Coverage:**
- ✅ Production health endpoint
- ✅ Authentication flow (production user)
- ✅ Critical API endpoints
- ✅ Database connectivity
- ✅ Redis connectivity

**Success Criteria:**
- ✅ Workflow file created and committed
- ✅ Workflow triggers after production deploy
- ✅ Tests complete in < 5 minutes
- ✅ Failures trigger alerts
- ✅ Rollback triggered on failure

---

### 5.3 Rollback Workflow

#### Task 3.5: Create Automated Rollback Workflow

**Time Estimate:** 1 hour

**Create file:** `.github/workflows/production-rollback.yml`

**Workflow Features:**
- Triggers on production smoke test failure
- Or manual trigger (workflow_dispatch)
- Reverts to previous release tag
- Redeploys previous version
- Runs smoke tests on rolled-back version
- Notifies team of rollback

**Success Criteria:**
- ✅ Workflow file created and committed
- ✅ Manual rollback works
- ✅ Automated rollback on smoke test failure works
- ✅ Rollback completes in < 10 minutes
- ✅ Team notified

---

### 5.4 Phase 3 Checklist

**Before proceeding to Phase 4, verify:**
- [ ] Staging deployment workflow created
- [ ] Staging smoke test workflow created
- [ ] Production deployment workflow created (tag-based)
- [ ] Production smoke test workflow created
- [ ] Rollback workflow created
- [ ] All workflows linted and validated
- [ ] Test runs of each workflow successful
- [ ] Workflow documentation created

**Phase 3 Success:** All CI/CD workflows implemented and tested.

---

## 6. Phase 4: Testing & Validation (Week 4)

### 6.1 End-to-End Testing

#### Task 4.1: Test PR Preview → Staging Flow

**Time Estimate:** 1 hour

**Test Scenario:**
1. Create test feature branch
2. Make sample code change
3. Open PR to `staging` branch
4. Verify PR preview created automatically
5. Verify Zebra smoke tests run
6. Merge PR to `staging`
7. Verify staging deployment triggered
8. Verify staging smoke tests run
9. Verify staging environment updated

**Success Criteria:**
- ✅ PR preview created automatically
- ✅ Zebra smoke tests pass
- ✅ Merge triggers staging deployment
- ✅ Staging deployment completes successfully
- ✅ Staging smoke tests pass
- ✅ Changes visible in staging environment

---

#### Task 4.2: Test Staging → Production Flow

**Time Estimate:** 1 hour

**Test Scenario:**
1. Verify staging environment stable
2. Create PR from `staging` to `main`
3. Review changes
4. Merge PR to `main` (does NOT trigger production deploy)
5. Create GitHub Release (tag: v1.0.0-test)
6. Verify production deployment triggered by tag
7. Verify production smoke tests run
8. Verify production environment updated

**Success Criteria:**
- ✅ PR from staging to main created
- ✅ Merge to main does NOT trigger deploy
- ✅ Release tag triggers production deploy
- ✅ Production deployment completes successfully
- ✅ Production smoke tests pass
- ✅ Changes visible in production environment

---

#### Task 4.3: Test Rollback Procedures

**Time Estimate:** 1 hour

**Test Scenario A: Manual Rollback**
1. Note current production version
2. Trigger manual rollback workflow
3. Verify rollback to previous version
4. Verify smoke tests run on rolled-back version
5. Verify production environment restored

**Test Scenario B: Automated Rollback (Simulated)**
1. Deploy version with intentional failure
2. Verify smoke tests fail
3. Verify rollback automatically triggered
4. Verify rollback completes successfully
5. Verify production environment restored

**Success Criteria:**
- ✅ Manual rollback completes in < 10 minutes
- ✅ Automated rollback triggers on smoke test failure
- ✅ Rollback restores previous version correctly
- ✅ Smoke tests pass on rolled-back version
- ✅ Team notified of rollback

---

### 6.2 Workflow Validation

#### Task 4.4: Validate All Workflows

**Time Estimate:** 2 hours

**Workflows to Validate:**
1. ✅ PR preview creation (Render + Vercel)
2. ✅ Zebra smoke tests on PR
3. ✅ Staging deployment on merge
4. ✅ Staging smoke tests post-deploy
5. ✅ Production deployment on release tag
6. ✅ Production smoke tests post-deploy
7. ✅ Manual rollback
8. ✅ Automated rollback

**For each workflow:**
- Test successful execution
- Test failure handling
- Test notification delivery
- Test artifact upload
- Verify execution time

**Success Criteria:**
- ✅ All workflows execute successfully
- ✅ Failure scenarios handled gracefully
- ✅ Notifications delivered correctly
- ✅ Artifacts uploaded and accessible
- ✅ Execution times within targets

---

### 6.3 Documentation Updates

#### Task 4.5: Update Deployment Documentation

**Time Estimate:** 2 hours

**Documents to Update:**
1. Update DEPLOYMENT_RUNBOOK.md with new process
2. Create STAGING_GATE_USER_GUIDE.md for team
3. Update ROLLBACK_PROCEDURES.md
4. Create RELEASE_MANAGEMENT_GUIDE.md
5. Update README.md with new workflow

**Success Criteria:**
- ✅ All documentation updated
- ✅ New deployment process documented
- ✅ User guide created
- ✅ Team reviewed documentation
- ✅ Documentation approved

---

### 6.4 Phase 4 Checklist

**Before proceeding to Phase 5, verify:**
- [ ] PR preview → Staging flow tested successfully
- [ ] Staging → Production flow tested successfully
- [ ] Manual rollback tested successfully
- [ ] Automated rollback tested successfully
- [ ] All workflows validated
- [ ] Documentation updated and approved
- [ ] Team trained on new process
- [ ] Stakeholders informed

**Phase 4 Success:** All workflows tested, validated, and documented.

---

## 7. Phase 5: Production Cutover (Week 5)

### 7.1 Final Preparation

#### Task 5.1: Pre-Cutover Checklist

**Time Estimate:** 1 hour

**Verify:**
- [ ] All Phase 1-4 tasks completed
- [ ] All workflows tested and validated
- [ ] Documentation complete and approved
- [ ] Team trained on new process
- [ ] Stakeholders informed of cutover
- [ ] Rollback plan ready
- [ ] Communication plan ready
- [ ] Monitoring in place

---

#### Task 5.2: Update Production Branch Protection

**Time Estimate:** 15 minutes

**Steps:**
1. Navigate to: GitHub → Settings → Branches → `main` protection
2. Update required status checks:
   ```yaml
   Required checks:
     - zebra-protection-gate
     - Database Migration Test
     - staging-smoke-tests (NEW)
   ```
3. Add rule: "Require branches to be up to date before merging"

**Success Criteria:**
- ✅ Production branch protection updated
- ✅ Staging smoke tests required before production merge
- ✅ Team aware of new requirements

---

### 7.2 Cutover Execution

#### Task 5.3: Enable Staging Gate

**Time Estimate:** 30 minutes

**Steps:**
1. Announce cutover to team (Slack/Email)
2. Update PR template to include staging gate instructions
3. Update CONTRIBUTING.md with new workflow
4. Monitor first PRs through new workflow
5. Provide support as needed

**Communication Template:**
```
Subject: New Staging Gate Deployment Process - Effective Immediately

Team,

We are now live with the new staging gate deployment process. Here's what changes:

NEW WORKFLOW:
1. Create feature branch → PR to `staging` (not `main`)
2. After PR approval → Merge to `staging`
3. Staging auto-deploys → Test in staging environment
4. Create PR from `staging` to `main`
5. After approval → Merge to `main`
6. Create GitHub Release tag (v1.x.x)
7. Production auto-deploys from tag

BENEFITS:
- UAT environment for stakeholder validation
- Controlled production releases
- Automated smoke tests at each stage
- Easy rollback capability

DOCUMENTATION:
- Deployment Runbook: /docs/deployment/DEPLOYMENT_RUNBOOK.md
- User Guide: /docs/deployment/STAGING_GATE_USER_GUIDE.md

Questions? Reach out in #engineering

Thanks!
```

**Success Criteria:**
- ✅ Team notified
- ✅ Documentation updated
- ✅ First PRs successful through new workflow
- ✅ No confusion or blockers
- ✅ Team adoption complete

---

#### Task 5.4: Disable Direct Production Deployment

**Time Estimate:** 15 minutes

**Steps:**
1. Update Render production service:
   - Settings → Build & Deploy
   - Change Auto-Deploy from `main` branch to **Manual Only**
2. Production now only deploys via GitHub Action (tag-based)

**Verification:**
```bash
# Push to main should NOT trigger production deploy
git checkout main
git commit --allow-empty -m "test: verify no auto-deploy"
git push origin main

# Check Render dashboard - should show no new deployment
```

**Success Criteria:**
- ✅ Direct branch-based production deploy disabled
- ✅ Tag-based production deploy tested and working
- ✅ Team aware of change

---

### 7.3 Post-Cutover Monitoring

#### Task 5.5: Monitor and Iterate (Week 5+)

**Time Estimate:** Ongoing

**Monitoring Plan:**
- **Week 5-6:** Daily monitoring of deployment metrics
- **Week 7-8:** Weekly review of deployment metrics
- **Month 2+:** Monthly review and iteration

**Metrics to Track:**
| Metric | Target | Actual |
|--------|--------|--------|
| Staging deployments per week | 2-3 | - |
| Production deployments per week | 1 | - |
| Deployment failure rate | <5% | - |
| Rollback rate | <2% | - |
| Staging bugs found | >90% | - |
| Production incidents | <1/month | - |
| Time from PR to staging | <1 hour | - |
| Time from staging to production | <24 hours | - |

**Success Criteria:**
- ✅ Deployment metrics tracked
- ✅ No critical incidents
- ✅ Team comfortable with new process
- ✅ Stakeholders satisfied with UAT gate
- ✅ Rollback procedures tested (if needed)

---

### 7.4 Phase 5 Checklist

**Cutover complete when:**
- [ ] Team notified and trained
- [ ] Production branch protection updated
- [ ] Staging gate enabled
- [ ] Direct production deployment disabled
- [ ] First production release via tag successful
- [ ] Monitoring in place
- [ ] No critical issues
- [ ] Team feedback collected
- [ ] Documentation finalized

**Phase 5 Success:** Staging gate fully operational and adopted by team.

---

## 8. Rollback Procedures

### 8.1 Rollback Triggers

**Automatic Rollback:**
- Production smoke tests fail after deployment
- Health endpoint returns errors for >5 minutes
- Critical error rate >10%

**Manual Rollback:**
- Critical production issue discovered
- Stakeholder-requested rollback
- Emergency situation

### 8.2 Rollback to Previous Staging Gate

**Scenario:** Staging gate causing issues, need to revert to branch-based deploys

**Steps:**
1. Disable staging gate requirement:
   ```bash
   # GitHub → Settings → Branches → main
   # Remove "staging-smoke-tests" from required checks
   ```

2. Re-enable direct production deployment:
   ```bash
   # Render Dashboard → Production Service → Settings
   # Change Auto-Deploy to: main branch
   ```

3. Notify team of rollback

4. Continue using branch-based deploys while investigating

**Time:** ~15 minutes

---

### 8.3 Rollback to Previous Production Version

**Scenario:** Production deployment failed, need to restore previous version

**Option A: Automated Rollback (Preferred)**
```bash
# GitHub Actions will automatically rollback on smoke test failure
# Or trigger manually via workflow_dispatch
```

**Option B: Manual Rollback via Render**
1. Render Dashboard → Production Service → Deployments
2. Find previous successful deployment
3. Click "Redeploy"

**Option C: Manual Rollback via Git**
```bash
# Create rollback release tag
git tag -a v1.0.0-rollback -m "Rollback to v1.0.0"
git push origin v1.0.0-rollback

# Production deploy workflow will trigger
```

**Time:** ~10 minutes

---

## 9. Success Criteria

### 9.1 Implementation Success Criteria

**Phase 1 Complete:**
- ✅ All critical configuration issues resolved
- ✅ Foundation in place

**Phase 2 Complete:**
- ✅ Complete staging infrastructure deployed
- ✅ All environments accessible

**Phase 3 Complete:**
- ✅ All CI/CD workflows implemented
- ✅ Workflows tested and validated

**Phase 4 Complete:**
- ✅ End-to-end testing successful
- ✅ Documentation complete

**Phase 5 Complete:**
- ✅ Staging gate operational
- ✅ Team adoption complete

**Overall Success:**
- ✅ Zero production downtime during implementation
- ✅ No critical production incidents post-cutover
- ✅ Team confident with new process
- ✅ Stakeholders satisfied with UAT gate
- ✅ Deployment metrics within targets

### 9.2 Key Performance Indicators (Post-Implementation)

**Deployment Metrics:**
- Staging deployments: 2-3 per week (Target met)
- Production deployments: 1 per week (Target met)
- Deployment failure rate: <5% (Target met)
- Rollback rate: <2% (Target met)

**Quality Metrics:**
- Staging bugs found: >90% (Target met)
- Production incidents: <1 per month (Target met)
- Time to detect issues: <5 minutes (Target met)
- Time to rollback: <10 minutes (Target met)

**Process Metrics:**
- Time from PR to staging: <1 hour (Target met)
- Time from staging to production: <24 hours for hotfixes (Target met)
- Average release cycle: 1-2 weeks (Target met)

---

## 10. Resource Requirements

### 10.1 Infrastructure Costs

**Additional Monthly Costs:**

| Resource | Plan | Monthly Cost |
|----------|------|--------------|
| Render Staging Service | Free or Starter | $0 - $7 |
| Render Staging Database | Free or Starter | $0 - $7 |
| Vercel Staging Deployment | Included | $0 |
| Auth0 Staging Tenant | Free (separate) | $0 |
| **Total Additional Cost** | | **$0 - $14/month** |

**Current Infrastructure:** $0-260/month
**Projected Infrastructure:** $0-274/month
**Increase:** $0-14/month (0-5% increase)

**Cost-Benefit Analysis:**
- Staging cost: ~$14/month
- Cost of single production incident: Hours of engineering time + customer impact
- ROI: Highly positive (incident prevention >> staging costs)

---

### 10.2 Time Investment

**Implementation Time:**

| Phase | Duration | Engineer Hours |
|-------|----------|----------------|
| Phase 1 | Week 1 | 8 hours |
| Phase 2 | Week 2 | 16 hours |
| Phase 3 | Week 3 | 20 hours |
| Phase 4 | Week 4 | 16 hours |
| Phase 5 | Week 5 | 8 hours |
| **Total** | **5 weeks** | **68 hours** |

**Breakdown:**
- DevOps Engineer: 40 hours
- Backend Developer: 16 hours
- Frontend Developer: 8 hours
- QA Engineer: 4 hours

**Ongoing Maintenance:**
- Monitoring: 2 hours/week
- Iteration: 4 hours/month

---

### 10.3 Team Training

**Training Requirements:**

| Topic | Audience | Duration |
|-------|----------|----------|
| New Deployment Workflow | All Engineers | 1 hour |
| Staging Environment Usage | All Engineers | 30 minutes |
| Release Management Process | Tech Leads | 1 hour |
| Rollback Procedures | On-Call Engineers | 1 hour |
| Troubleshooting Guide | All Engineers | 30 minutes |

**Total Training Time:** ~4 hours per engineer

**Training Materials:**
- Deployment Runbook
- Staging Gate User Guide
- Video walkthrough
- FAQ document

---

## 11. Risk Mitigation

### 11.1 Implementation Risks

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Breaking PR previews | HIGH | LOW | Phased rollout, maintain backward compat |
| Database sync issues | MEDIUM | MEDIUM | Separate staging database, schema-only sync |
| Cost overrun | LOW | LOW | Use free tiers, monitor usage |
| Team workflow disruption | MEDIUM | MEDIUM | Training, documentation, gradual adoption |
| Production downtime | HIGH | LOW | Zero-downtime deployment, rollback ready |

### 11.2 Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Staging environment down | MEDIUM | Bypass staging gate for hotfixes |
| Production deployment failure | HIGH | Automated rollback, smoke tests |
| Rollback failure | HIGH | Manual rollback procedures documented |
| Database migration failure | HIGH | Migration testing in staging first |

---

## 12. Appendices

### Appendix A: Quick Reference

**New Developer Workflow:**
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and commit
git add .
git commit -m "feat: my feature"
git push origin feature/my-feature

# 3. Open PR to staging (not main)
# GitHub → New Pull Request → base: staging

# 4. After approval, merge to staging
# Staging auto-deploys

# 5. Test in staging environment
# https://staging.zebra.associates

# 6. Open PR from staging to main
# GitHub → New Pull Request → base: main, compare: staging

# 7. After approval, merge to main

# 8. Create GitHub Release
# GitHub → Releases → Create new release → v1.0.0

# 9. Production auto-deploys from tag
```

---

### Appendix B: Command Reference

**Staging Deployment:**
```bash
# Manual staging deployment (if needed)
git checkout staging
git pull origin staging
# Deployment happens automatically via Render

# Check staging health
curl https://marketedge-platform-staging.onrender.com/health
```

**Production Deployment:**
```bash
# Create production release
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0: Description"
git push origin v1.0.0

# Production deployment happens automatically via GitHub Actions
```

**Rollback:**
```bash
# Option 1: Via GitHub Actions (preferred)
# Go to Actions → Production Rollback → Run workflow

# Option 2: Via new release tag
git tag -a v1.0.0-rollback -m "Rollback to v1.0.0"
git push origin v1.0.0-rollback
```

---

### Appendix C: Troubleshooting

**Issue: Staging deployment failed**
```bash
# Check Render logs
# Render Dashboard → Staging Service → Logs

# Common causes:
# - Migration failure → Check database connection
# - Environment variable missing → Check environment tab
# - Build failure → Check build logs
```

**Issue: Production smoke tests failing**
```bash
# Check GitHub Actions logs
# GitHub → Actions → Production Smoke Tests → View logs

# Common causes:
# - Production health endpoint down → Check Render service
# - Authentication failure → Check Auth0 configuration
# - Database connection issue → Check DATABASE_URL
```

**Issue: Rollback not working**
```bash
# Manual rollback via Render
# Dashboard → Production Service → Deployments → Redeploy previous

# Verify rollback
curl https://marketedge-platform.onrender.com/health
```

---

### Appendix D: Contact Information

**Emergency Contacts:**
- DevOps Lead: [Contact]
- Backend Lead: [Contact]
- Frontend Lead: [Contact]
- On-Call Engineer: [Contact]

**External Services:**
- Render Support: support@render.com
- Vercel Support: support@vercel.com
- Auth0 Support: support@auth0.com

---

## Conclusion

This implementation plan provides a comprehensive, phased approach to introducing a staging gate between PR previews and production deployments. The plan respects existing infrastructure, maintains backward compatibility, and minimizes risk through gradual rollout and comprehensive testing.

**Key Takeaways:**
- ✅ 5-week phased implementation
- ✅ Zero production downtime
- ✅ Minimal cost increase ($0-14/month)
- ✅ Comprehensive testing and validation
- ✅ Rollback procedures in place
- ✅ Team training and documentation

**Next Steps:**
1. Review this plan with engineering team
2. Approve implementation timeline
3. Begin Phase 1 (critical fixes)
4. Execute phases sequentially
5. Monitor and iterate post-cutover

---

**Document Version:** 1.0
**Date:** 2025-10-02
**Author:** Maya (DevOps Engineer)
**Status:** ✅ Ready for Review
**Next Document:** STAGING_DEPLOY_WORKFLOW.yml, PRODUCTION_DEPLOY_WORKFLOW.yml
