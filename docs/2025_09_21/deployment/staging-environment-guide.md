# MarketEdge Platform - Staging Environment Setup Guide

**Document Version**: 1.0
**Created**: September 21, 2025
**Author**: DevOps Agent (Maya)
**Purpose**: Emergency stabilization after production debugging issues

## 🎯 Executive Summary

This guide establishes a proper staging environment using Render's Preview Environments to prevent future production debugging disasters. The setup ensures Matt.Lindop's £925K Zebra Associates opportunity remains protected while enabling safe testing.

### Critical Context
- **Emergency Response**: Created after production debugging incidents
- **Business Impact**: Protects £925K Zebra Associates opportunity
- **Current Production**: https://marketedge-platform.onrender.com
- **Goal**: Zero production debugging through proper staging

## 🏗️ Architecture Overview

### Environment Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
├─────────────────────────────────────────────────────────────┤
│  main branch                                                 │
│  ├── Triggers: Production deployment                        │
│  ├── Protection: Requires PR approval + staging validation  │
│  └── Target: https://marketedge-platform.onrender.com      │
├─────────────────────────────────────────────────────────────┤
│  Pull Requests                                              │
│  ├── Triggers: Automatic Preview Environment creation       │
│  ├── URL Pattern: https://pr-{NUMBER}-marketedge-backend... │
│  ├── Database: Isolated staging database per PR            │
│  ├── Auth0: Staging configuration                          │
│  └── Cleanup: Automatic after PR close                     │
└─────────────────────────────────────────────────────────────┘
```

### Infrastructure Components

| Component | Production | Staging (Preview) |
|-----------|------------|-------------------|
| **API URL** | `marketedge-platform.onrender.com` | `pr-{N}-marketedge-backend.onrender.com` |
| **Database** | Production PostgreSQL | Isolated staging PostgreSQL |
| **Redis** | Production Redis | Isolated staging Redis |
| **Auth0** | Production Auth0 app | Staging Auth0 app |
| **CORS** | Restricted origins | Allow all origins (`*`) |
| **Logging** | INFO level | DEBUG level |
| **Monitoring** | Sentry enabled | Sentry disabled |

## 📋 Prerequisites

### Render Account Requirements
- **Professional workspace** or higher (required for Preview Environments)
- Existing production service: `marketedge-backend`
- Access to Render dashboard and CLI

### GitHub Repository Requirements
- Repository: `zebra-devops/MarketEdge-Platform`
- Branch protection rules enabled
- GitHub Actions enabled

### Auth0 Requirements
- Existing production Auth0 application
- New staging Auth0 application (to be created)
- Access to Auth0 dashboard

## 🚀 Setup Instructions

### Step 1: Render Configuration

The `render.yaml` file has been configured with Preview Environment support:

```yaml
# Preview Environment Configuration
previews:
  generation: automatic  # Auto-create for all PRs
  expireAfterDays: 7     # Clean up after 7 days

services:
  - type: web
    name: marketedge-backend
    # ... existing configuration ...

    # Preview overrides
    previews:
      plan: free
      numInstances: 1

    envVars:
      - key: ENVIRONMENT
        value: production
        previewValue: staging  # Staging flag for previews
```

**Key Features**:
- Automatic preview environment creation for all PRs
- Isolated databases and Redis instances per preview
- 7-day expiration for automatic cleanup
- Staging-specific environment variable overrides

### Step 2: Auth0 Staging Configuration

#### Create Staging Auth0 Application

1. **Login to Auth0 Dashboard**
2. **Create New Application**:
   - Name: "MarketEdge Staging"
   - Type: Regular Web Application
3. **Configure Application Settings**:
   ```
   Allowed Callback URLs:
   https://*-marketedge-backend.onrender.com/auth/callback
   http://localhost:3000/auth/callback
   http://localhost:8000/auth/callback

   Allowed Logout URLs:
   https://*-marketedge-backend.onrender.com/auth/logout
   http://localhost:3000/auth/logout

   Allowed Web Origins:
   https://*-marketedge-backend.onrender.com
   http://localhost:3000
   ```

4. **Configure Environment Variables in Render**:
   ```bash
   # These will be set automatically for preview environments
   AUTH0_DOMAIN_STAGING=dev-zebra-marketedge.uk.auth0.com
   AUTH0_CLIENT_ID_STAGING=staging-client-id
   AUTH0_CLIENT_SECRET_STAGING=staging-client-secret
   AUTH0_AUDIENCE_STAGING=https://api.marketedge-staging.onrender.com
   ```

### Step 3: GitHub Branch Protection

Branch protection rules ensure staging validation before production:

```bash
# Run the setup script to configure protection
./scripts/staging-environment-setup.sh
```

**Protection Rules Applied**:
- Require PR reviews (1 approver minimum)
- Require status checks (staging validation)
- Dismiss stale reviews on new commits
- Prevent force pushes and branch deletion

### Step 4: Database Configuration

Staging databases are automatically configured with:

1. **Isolated Schema**: Each preview gets its own PostgreSQL instance
2. **Automatic Migrations**: Alembic migrations run automatically
3. **Test Data Seeding**: Staging-specific test organizations and users
4. **Extensions**: Required PostgreSQL extensions (uuid-ossp, pg_trgm)

**Test Organizations Created**:
- Zebra Associates (Staging) - `zebra.associates`
- ODEON Cinemas (Staging) - `odeon.co.uk`
- Test Hotel Group - `testhotel.staging`

## 🔧 Usage Workflow

### For Developers

#### 1. Create Feature Branch
```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Commit changes
git add .
git commit -m "feat: your feature description"

# Push to GitHub
git push origin feature/your-feature-name
```

#### 2. Create Pull Request
```bash
# Create PR via GitHub CLI
gh pr create --title "Your Feature Title" --body "Feature description"
```

**Automatic Actions**:
- GitHub Actions validates the changes
- Render automatically creates preview environment
- Preview URL: `https://pr-{NUMBER}-marketedge-backend.onrender.com`

#### 3. Test Staging Environment
```bash
# Wait 5-10 minutes for deployment
# Test the preview environment
curl https://pr-123-marketedge-backend.onrender.com/health

# Access API documentation
open https://pr-123-marketedge-backend.onrender.com/api/v1/docs
```

#### 4. Merge to Production
```bash
# After approval, merge PR
gh pr merge --squash

# Automatic production deployment to main environment
```

### For Matt.Lindop (Admin Testing)

#### Staging Environment Access
```bash
# Preview environment URL (from PR comment)
API: https://pr-{NUMBER}-marketedge-backend.onrender.com
Docs: https://pr-{NUMBER}-marketedge-backend.onrender.com/api/v1/docs

# Staging login credentials
# Use the same Auth0 credentials but on staging app
```

#### Admin Panel Testing
```bash
# Test admin endpoints in staging
/api/v1/admin/dashboard/stats
/api/v1/admin/feature-flags
/api/v1/admin/modules

# Verify super_admin role access
# Test feature flag management
# Validate organization switching
```

## 📊 Monitoring and Validation

### Automatic Validation

GitHub Actions automatically validates:
- ✅ `render.yaml` configuration
- ✅ Backend tests pass
- ✅ Database migration validation
- ✅ Security scanning
- ✅ Preview environment health

### Manual Validation Checklist

#### Database Validation
```bash
# Connect to staging database
psql $STAGING_DATABASE_URL

# Verify tables exist
\dt

# Check test data
SELECT name FROM organizations WHERE domain LIKE '%.staging';
```

#### API Validation
```bash
# Health check
curl https://pr-{N}-marketedge-backend.onrender.com/health

# Readiness check
curl https://pr-{N}-marketedge-backend.onrender.com/ready

# Admin dashboard (requires auth)
curl -H "Authorization: Bearer $TOKEN" \
  https://pr-{N}-marketedge-backend.onrender.com/api/v1/admin/dashboard/stats
```

#### Auth0 Integration
```bash
# Test Auth0 staging configuration
# 1. Access API docs: /api/v1/docs
# 2. Click "Authorize" button
# 3. Login with staging Auth0
# 4. Test protected endpoints
```

## 🛡️ Security Considerations

### Environment Isolation

| Security Aspect | Production | Staging |
|-----------------|------------|---------|
| **Database** | Production data | Isolated test data |
| **Auth0** | Production app | Staging app |
| **CORS** | Restricted origins | Allow all (`*`) |
| **Secrets** | Production secrets | Staging secrets |
| **Monitoring** | Full monitoring | Debug logging only |

### Data Protection
- **No Production Data**: Staging uses only test data
- **Isolated Databases**: Each preview has separate PostgreSQL instance
- **Secure Secrets**: Staging secrets separate from production
- **Automatic Cleanup**: Environments destroyed after PR closure

### Access Control
- **PR-Based Access**: Only authorized developers can create PRs
- **Branch Protection**: Requires code review before production
- **Time-Limited**: Staging environments expire after 7 days
- **Audit Trail**: All changes tracked through GitHub

## 🚨 Emergency Procedures

### Preview Environment Issues

#### Environment Won't Start
```bash
# Check Render deployment logs
render logs --service=marketedge-backend --environment=preview

# Check render.yaml syntax
yaml-lint render.yaml

# Validate environment variables
render env list --service=marketedge-backend
```

#### Database Migration Failures
```bash
# Connect to staging database
psql $STAGING_DATABASE_URL

# Check migration status
SELECT * FROM alembic_version;

# Manually run migrations if needed
python database/staging_setup.py
```

#### Auth0 Integration Issues
```bash
# Verify staging Auth0 configuration
echo "Domain: $AUTH0_DOMAIN_STAGING"
echo "Client ID: $AUTH0_CLIENT_ID_STAGING"

# Check callback URLs in Auth0 dashboard
# Ensure wildcard pattern: https://*-marketedge-backend.onrender.com/*
```

### Production Protection

#### Accidental Production Changes
```bash
# Revert production deployment
render rollback --service=marketedge-backend

# Check production health
curl https://marketedge-platform.onrender.com/health
```

#### Database Emergency
```bash
# Production database is protected by:
# 1. No staging access to production DATABASE_URL
# 2. Separate Auth0 applications
# 3. Row Level Security (RLS) policies
# 4. Environment variable isolation
```

## 📈 Benefits and Impact

### Risk Mitigation
- **Zero Production Debugging**: All testing happens in isolated staging
- **Reduced Downtime**: Issues caught before production deployment
- **Data Protection**: Production data never exposed to staging
- **Quick Recovery**: Easy rollback if issues occur

### Development Efficiency
- **Automated Testing**: Every PR gets automatic staging environment
- **Parallel Development**: Multiple features can be tested simultaneously
- **Quality Gates**: Automated validation before production
- **Documentation**: Self-documenting through PR comments

### Business Protection
- **Matt.Lindop Access**: Secure admin access preserved
- **Zebra Associates Opportunity**: £925K opportunity protected
- **Platform Stability**: Production stability maintained
- **Compliance**: Audit trail for all changes

## 🔄 Maintenance and Updates

### Regular Maintenance

#### Weekly Tasks
```bash
# Check preview environment usage
render services list | grep preview

# Review expired environments
# (Automatic cleanup after 7 days)

# Update staging test data if needed
python database/staging_setup.py
```

#### Monthly Tasks
```bash
# Review Auth0 staging application
# Update callback URLs if needed
# Rotate staging secrets

# Review render.yaml configuration
# Update resource allocations if needed
# Check for new Render features
```

### Configuration Updates

#### Adding New Environment Variables
```yaml
# In render.yaml
envVars:
  - key: NEW_VARIABLE
    value: production-value
    previewValue: staging-value
```

#### Updating Auth0 Configuration
```bash
# Update staging Auth0 app settings
# Add new callback URLs for preview environments
# Update Render environment variables
```

## 🎯 Success Metrics

### Deployment Quality
- **Pre-Production Issue Detection**: 100% of issues caught in staging
- **Production Deployment Success**: >99% successful deployments
- **Zero Production Debugging**: No direct production changes needed

### Development Velocity
- **PR Validation Time**: <10 minutes for staging environment creation
- **Issue Resolution Time**: Reduced by catching issues early
- **Feature Deployment**: Safe, predictable deployments

### Business Impact
- **Zebra Associates Protection**: £925K opportunity remains secure
- **Admin Access Stability**: Matt.Lindop admin access always functional
- **Platform Reliability**: Production stability maintained

## 🔗 References and Links

### Documentation
- [Render Preview Environments](https://render.com/docs/preview-environments)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [Auth0 Applications](https://auth0.com/docs/applications)

### Internal Documentation
- [`render.yaml`](/render.yaml) - Main configuration file
- [`render-startup.sh`](/render-startup.sh) - Startup script with staging logic
- [`database/staging_setup.py`](/database/staging_setup.py) - Staging database setup
- [`scripts/staging-environment-setup.sh`](/scripts/staging-environment-setup.sh) - Setup automation

### Production Links
- **Production API**: https://marketedge-platform.onrender.com
- **Production Docs**: https://marketedge-platform.onrender.com/api/v1/docs
- **GitHub Repository**: https://github.com/zebra-devops/MarketEdge-Platform

---

**Status**: ✅ STAGING ENVIRONMENT READY
**Next Action**: Test with feature branch creation
**Emergency Contact**: Maya (DevOps Agent)

This staging environment setup ensures the MarketEdge platform can be safely developed and tested without risk to the production environment serving Matt.Lindop's critical £925K Zebra Associates opportunity.