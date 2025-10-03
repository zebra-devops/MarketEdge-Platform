# Updated render.yaml for Blueprint Migration

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Status:** Ready for Deployment

## Overview

This document contains the updated `render.yaml` configuration with new service names to enable Blueprint/IaC management without conflicting with existing manually-created services.

## Key Changes

### Service Naming Convention

All services use `-iac` suffix to differentiate from existing manual services:

| Old Service Name | New Service Name | Reason |
|-----------------|------------------|---------|
| `marketedge-platform` | `marketedge-platform-iac` | Avoid naming conflict, enable IaC |
| `marketedge-platform-staging` | `marketedge-platform-staging-iac` | Consistency with production naming |
| `marketedge-staging-db` | `marketedge-staging-db-iac` | Match service naming convention |
| `marketedge-preview-db` | `marketedge-preview-db` | Unchanged (shared resource) |

### Why `-iac` Suffix?

1. **Clear Differentiation:** Immediately identify Blueprint-managed services
2. **No Conflicts:** Allows parallel running during migration
3. **Future-Proof:** When old services deprecated, can remove suffix via blueprint update
4. **Team Communication:** Clear which infrastructure is IaC-managed

## Updated render.yaml Configuration

Save this as `/Users/matt/Sites/MarketEdge/render.yaml` in the `blueprint-migration` branch:

```yaml
# Render Blueprint Configuration for MarketEdge Platform
# Infrastructure-as-Code for Backend Deployment
# Migration Version: Blue-Green Deployment with IaC Management
# Documentation: /docs/2025_10_03/deployment/render-migration/

# Preview Environment Configuration
# Applies to all PR preview deployments
previews:
  generation: automatic  # Generate preview for every PR
  expireAfterDays: 7    # Auto-cleanup after 7 days

# Environment Variable Groups
envVarGroups:
  - name: production-env-iac
    # Production environment variables managed via Render Dashboard
    # Secrets (sync: false) must be configured manually:
    # - DATABASE_URL
    # - REDIS_URL
    # - AUTH0_CLIENT_SECRET
    # - AUTH0_ACTION_SECRET
    # - JWT_SECRET_KEY

  - name: staging-env-iac
    # Staging environment variables
    # Managed via Render Dashboard for long-lived staging service

# Database Configuration
databases:
  # Preview Database (shared by all PR previews)
  - name: marketedge-preview-db
    databaseName: marketedge_preview
    plan: free
    # Each preview gets isolated data via application-level tenant separation
    # Note: This database is shared with old preview environments

  # Staging Database (dedicated, long-lived) - IaC Managed
  - name: marketedge-staging-db-iac
    databaseName: marketedge_staging_iac
    plan: free  # Upgrade to starter ($7/month) for better performance
    # Note: Production database managed separately (not in render.yaml)

# Services Configuration
services:
  # ============================================================================
  # PRODUCTION SERVICE (IaC Managed)
  # ============================================================================
  - type: web
    name: marketedge-platform-iac
    runtime: python
    plan: free
    region: oregon
    buildCommand: "python --version && pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements.txt"
    startCommand: ./render-startup.sh

    # Preview Configuration (inherited by PR previews)
    previews:
      generation: automatic

    # Production and Preview Environment Variables
    envVars:
      # From Environment Group
      - fromGroup: production-env-iac

      # ========================================================================
      # CRITICAL FIXES (Applied 2025-10-02)
      # ========================================================================

      # CRITICAL FIX #1: AUTH0_AUDIENCE (MUST BE SET)
      # Without this, Auth0 returns opaque tokens instead of JWT tokens
      - key: AUTH0_AUDIENCE
        value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

      # ========================================================================
      # AUTH0 CONFIGURATION (Production)
      # ========================================================================

      - key: AUTH0_DOMAIN
        value: dev-g8trhgbfdq2sk2m8.us.auth0.com

      - key: AUTH0_CLIENT_ID
        value: wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6

      - key: AUTH0_CLIENT_SECRET
        sync: false  # MUST be set in Render Dashboard

      - key: AUTH0_ACTION_SECRET
        sync: false  # MUST be set in Render Dashboard

      # Auth0 Callback URL (production)
      # NOTE: Update to new service URL after custom domain migration
      - key: AUTH0_CALLBACK_URL
        value: https://app.zebra.associates/callback
        previewValue: https://${RENDER_SERVICE_NAME}.onrender.com/callback

      # ========================================================================
      # AUTH0 CONFIGURATION (Staging/Preview Environments)
      # ========================================================================

      - key: AUTH0_DOMAIN_STAGING
        value: dev-g8trhgbfdq2sk2m8.us.auth0.com

      - key: AUTH0_CLIENT_ID_STAGING
        value: wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6

      - key: AUTH0_CLIENT_SECRET_STAGING
        sync: false  # MUST be set in Render Dashboard

      - key: AUTH0_AUDIENCE_STAGING
        value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

      # Environment-aware Auth0 selection
      - key: USE_STAGING_AUTH0
        value: "false"
        previewValue: "true"

      # ========================================================================
      # JWT CONFIGURATION
      # ========================================================================

      - key: JWT_SECRET_KEY
        sync: false  # MUST be set in Render Dashboard (different per environment)

      - key: JWT_ALGORITHM
        value: HS256

      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: "30"

      - key: REFRESH_TOKEN_EXPIRE_DAYS
        value: "7"

      # ========================================================================
      # DATABASE CONFIGURATION
      # ========================================================================

      - key: DATABASE_URL
        sync: false  # MUST be set in Render Dashboard (production DB)
        # NOTE: Use SAME production database as old service for seamless migration

      - key: RUN_MIGRATIONS
        value: "true"  # Auto-run migrations on deploy

      # ========================================================================
      # REDIS CONFIGURATION
      # ========================================================================

      - key: REDIS_URL
        sync: false  # MUST be set in Render Dashboard
        # NOTE: Can share Redis with old service (no conflicts)

      # ========================================================================
      # CORS CONFIGURATION
      # ========================================================================

      # Production CORS (includes Vercel domains for frontend)
      - key: CORS_ORIGINS
        value: "https://platform.marketedge.co.uk,https://marketedge-platform.onrender.com,https://marketedge-platform-iac.onrender.com,https://app.zebra.associates,https://staging.zebra.associates,https://*.vercel.app"
        previewValue: "https://*.onrender.com,https://*.vercel.app,http://localhost:3000"

      # ========================================================================
      # ENVIRONMENT CONFIGURATION
      # ========================================================================

      - key: ENVIRONMENT
        value: production
        previewValue: preview

      - key: DEBUG
        value: "false"
        previewValue: "true"

      - key: LOG_LEVEL
        value: INFO
        previewValue: DEBUG

      # ========================================================================
      # API CONFIGURATION
      # ========================================================================

      - key: API_V1_STR
        value: /api/v1

      - key: PROJECT_NAME
        value: MarketEdge Platform

      - key: PROJECT_VERSION
        value: 1.0.0

      # ========================================================================
      # SECURITY CONFIGURATION
      # ========================================================================

      - key: CSRF_ENABLED
        value: "false"  # Enable after smoke test (5 minutes post-deploy)

      - key: CADDY_PROXY_MODE
        value: "true"
        previewValue: "false"

      - key: COOKIE_SECURE
        value: "true"
        previewValue: "false"

      # ========================================================================
      # FEATURE FLAGS
      # ========================================================================

      - key: ENABLE_DEBUG_LOGGING
        value: "false"
        previewValue: "true"

      - key: RATE_LIMIT_ENABLED
        value: "true"

      - key: RATE_LIMIT_REQUESTS_PER_MINUTE
        value: "60"

      # ========================================================================
      # MONITORING
      # ========================================================================

      - key: SENTRY_DSN
        sync: false  # Set in Dashboard for production
        previewValue: ""  # Disable Sentry for previews

      # ========================================================================
      # PYTHON VERSION
      # ========================================================================

      - key: PYTHON_VERSION
        value: "3.11.10"

      # ========================================================================
      # PORT CONFIGURATION
      # ========================================================================

      - key: PORT
        fromService:
          type: web
          name: marketedge-platform-iac
          property: port

  # ============================================================================
  # STAGING SERVICE (Long-Lived) - IaC Managed
  # ============================================================================
  - type: web
    name: marketedge-platform-staging-iac
    runtime: python
    plan: free  # Upgrade to starter ($7/month) for better performance
    region: oregon
    branch: staging  # CRITICAL: Deploy only from staging branch
    buildCommand: "python --version && pip install --upgrade pip && pip install --no-cache-dir --only-binary=:all: -r requirements.txt"
    startCommand: ./render-startup.sh

    # Staging Environment Variables
    envVars:
      # From Staging Environment Group
      - fromGroup: staging-env-iac

      # ========================================================================
      # AUTH0 CONFIGURATION (Staging)
      # ========================================================================

      - key: AUTH0_DOMAIN
        value: dev-g8trhgbfdq2sk2m8.us.auth0.com

      - key: AUTH0_CLIENT_ID
        value: wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6

      - key: AUTH0_CLIENT_SECRET
        sync: false  # MUST be set in Render Dashboard

      - key: AUTH0_ACTION_SECRET
        sync: false  # MUST be set in Render Dashboard

      - key: AUTH0_AUDIENCE
        value: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/

      - key: AUTH0_CALLBACK_URL
        value: https://staging.zebra.associates/callback

      # ========================================================================
      # JWT CONFIGURATION (Staging)
      # ========================================================================

      - key: JWT_SECRET_KEY
        sync: false  # MUST be set in Dashboard (DIFFERENT from production)

      - key: JWT_ALGORITHM
        value: HS256

      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: "30"

      - key: REFRESH_TOKEN_EXPIRE_DAYS
        value: "7"

      # ========================================================================
      # DATABASE CONFIGURATION (Staging)
      # ========================================================================

      - key: DATABASE_URL
        fromDatabase:
          name: marketedge-staging-db-iac
          property: connectionString

      - key: RUN_MIGRATIONS
        value: "true"

      # ========================================================================
      # REDIS CONFIGURATION (Staging)
      # ========================================================================

      - key: REDIS_URL
        sync: false  # MUST be set in Dashboard (can share with production or separate)

      # ========================================================================
      # CORS CONFIGURATION (Staging)
      # ========================================================================

      - key: CORS_ORIGINS
        value: "https://staging.zebra.associates,https://marketedge-platform-staging-iac.onrender.com,https://*.vercel.app,http://localhost:3000"

      # ========================================================================
      # ENVIRONMENT CONFIGURATION (Staging)
      # ========================================================================

      - key: ENVIRONMENT
        value: staging

      - key: DEBUG
        value: "true"

      - key: LOG_LEVEL
        value: DEBUG

      # ========================================================================
      # SECURITY CONFIGURATION (Staging)
      # ========================================================================

      - key: CSRF_ENABLED
        value: "false"

      - key: CADDY_PROXY_MODE
        value: "false"

      - key: COOKIE_SECURE
        value: "true"

      # ========================================================================
      # FEATURE FLAGS (Staging)
      # ========================================================================

      - key: ENABLE_DEBUG_LOGGING
        value: "true"

      - key: RATE_LIMIT_ENABLED
        value: "true"

      - key: RATE_LIMIT_REQUESTS_PER_MINUTE
        value: "60"

      # ========================================================================
      # MONITORING (Staging)
      # ========================================================================

      - key: SENTRY_DSN
        value: ""  # Optional: separate staging Sentry project

      # ========================================================================
      # PYTHON VERSION (Staging)
      # ========================================================================

      - key: PYTHON_VERSION
        value: "3.11.10"

      # ========================================================================
      # PORT CONFIGURATION (Staging)
      # ========================================================================

      - key: PORT
        fromService:
          type: web
          name: marketedge-platform-staging-iac
          property: port

# ============================================================================
# IMPORTANT NOTES - BLUEPRINT MIGRATION
# ============================================================================
#
# 1. NEW SERVICE NAMING:
#    - All services use -iac suffix for IaC management
#    - Enables parallel running during migration (no conflicts)
#    - Old services: marketedge-platform, marketedge-platform-staging
#    - New services: marketedge-platform-iac, marketedge-platform-staging-iac
#
# 2. DATABASE STRATEGY:
#    - Production: Uses SAME database as old service (seamless data continuity)
#    - Staging: New dedicated database (marketedge-staging-db-iac)
#    - Preview: Shares existing preview database (no changes needed)
#
# 3. SECRETS CONFIGURATION:
#    These MUST be manually configured in Render Dashboard:
#    - AUTH0_CLIENT_SECRET (production and staging)
#    - AUTH0_ACTION_SECRET (production and staging)
#    - JWT_SECRET_KEY (DIFFERENT for production and staging)
#    - DATABASE_URL (production only - staging uses fromDatabase)
#    - REDIS_URL (production and staging - can share or separate)
#    - SENTRY_DSN (optional, production only)
#
# 4. CORS CONFIGURATION:
#    - Includes both old and new service URLs during migration
#    - Remove old URLs after successful migration completion
#
# 5. CUSTOM DOMAIN MIGRATION:
#    - Keep Auth0 callback URL as app.zebra.associates
#    - Custom domain will be migrated from old to new service
#    - Update CORS_ORIGINS after domain migration complete
#
# 6. VERIFICATION:
#    - After blueprint deployment, verify IaC toggle enabled
#    - Test all endpoints with new service URLs
#    - Compare performance with old service baseline
#
# 7. ROLLBACK PLAN:
#    - Old services remain running during migration
#    - Can switch DNS back to old service within 10 minutes
#    - Shared database ensures no data loss during rollback
#
# 8. POST-MIGRATION CLEANUP:
#    - After 72 hours stable operation, deprecate old services
#    - Remove old service URLs from CORS configuration
#    - Update documentation with new service details
#
# ============================================================================
```

## Implementation Steps

### 1. Create Migration Branch

```bash
cd /Users/matt/Sites/MarketEdge

# Create and checkout migration branch
git checkout -b blueprint-migration

# Backup current render.yaml
cp render.yaml render.yaml.backup

# Update render.yaml with new configuration (use content above)
# Replace contents of render.yaml with the configuration above
```

### 2. Update render.yaml File

Replace the current `/Users/matt/Sites/MarketEdge/render.yaml` with the configuration above.

**Key Changes to Make:**

1. **Service Names:**
   - `marketedge-platform` → `marketedge-platform-iac`
   - `marketedge-platform-staging` → `marketedge-platform-staging-iac`

2. **Database Names:**
   - `marketedge-staging-db` → `marketedge-staging-db-iac`

3. **Environment Groups:**
   - `production-env` → `production-env-iac`
   - `staging-env` → `staging-env-iac`

4. **CORS Origins:**
   - Add new service URLs to CORS_ORIGINS
   - Keep old URLs during migration period

5. **PORT Configuration:**
   - Update `fromService.name` to match new service names

### 3. Validate YAML Syntax

```bash
# Install yamllint if not already installed
pip install yamllint

# Validate render.yaml syntax
yamllint render.yaml

# Expected output: No errors
```

**Alternative Online Validation:**
- https://www.yamllint.com/
- Paste render.yaml contents and verify syntax

### 4. Commit and Push

```bash
# Stage changes
git add render.yaml

# Commit with descriptive message
git commit -m "config: update render.yaml for Blueprint IaC migration

- Rename services with -iac suffix to enable IaC management
- Update database names to avoid conflicts
- Maintain shared production database for seamless migration
- Add new service URLs to CORS configuration
- Update environment group names for clarity

Migration Strategy: Blue-Green Deployment
Related: docs/2025_10_03/deployment/render-migration/"

# Push to remote
git push origin blueprint-migration
```

### 5. Verify Branch on GitHub

```bash
# Open GitHub repository in browser
open https://github.com/[your-username]/MarketEdge/tree/blueprint-migration

# Verify:
# - Branch exists
# - render.yaml updated correctly
# - Commit visible
```

## Configuration Differences: Old vs New

### Service Configuration Comparison

| Configuration | Old Service | New Service (IaC) | Notes |
|--------------|-------------|-------------------|-------|
| Service Name | `marketedge-platform` | `marketedge-platform-iac` | -iac suffix for IaC management |
| Management Method | Manual Dashboard | Blueprint (render.yaml) | IaC toggle enabled |
| Service URL | `marketedge-platform.onrender.com` | `marketedge-platform-iac.onrender.com` | Temporary during migration |
| Custom Domain | `platform.marketedge.co.uk` | Will migrate after verification | Same domain, different service |
| Database | Production DB (manual config) | Same production DB | Shared database |
| Redis | Production Redis | Same Redis instance | Shared Redis |
| Environment Variables | Dashboard only | render.yaml + Dashboard secrets | Version-controlled config |
| Auto-Deploy | Enabled | Enabled | Consistent behavior |
| Health Check | `/health` | `/health` | No change |

### Environment Variable Changes

**No Changes Required for:**
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_AUDIENCE`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- Database configuration (using same DB)
- All feature flags

**Changes Required:**
- Environment group names (cosmetic only)
- CORS origins (includes new service URLs)
- Service references in PORT configuration

**Manual Configuration Still Required:**
- `AUTH0_CLIENT_SECRET` (copy from old service)
- `AUTH0_ACTION_SECRET` (copy from old service)
- `JWT_SECRET_KEY` (copy from old service)
- `DATABASE_URL` (copy from old service - same DB)
- `REDIS_URL` (copy from old service - same Redis)

## Testing the Configuration

### Pre-Deployment Validation

Before creating blueprint in Render:

```bash
# 1. Validate YAML syntax
yamllint render.yaml

# 2. Check for common issues
grep -n "sync: false" render.yaml  # Should find all secrets
grep -n "fromService" render.yaml  # Verify service name references
grep -n "fromDatabase" render.yaml # Verify database references

# 3. Verify no duplicate keys
python3 << EOF
import yaml
with open('render.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print("✓ YAML valid and parseable")
    print(f"Services defined: {len(config.get('services', []))}")
    print(f"Databases defined: {len(config.get('databases', []))}")
EOF
```

### Post-Deployment Validation

After blueprint creates services:

```bash
# Test health endpoint (production)
curl -i https://marketedge-platform-iac.onrender.com/health

# Test health endpoint (staging)
curl -i https://marketedge-platform-staging-iac.onrender.com/health

# Test API documentation
curl -i https://marketedge-platform-iac.onrender.com/docs

# Test authentication endpoint
curl -i https://marketedge-platform-iac.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

## Troubleshooting

### Issue: YAML Syntax Error

**Error:** `Blueprint file parsing failed`

**Resolution:**
1. Validate YAML syntax with yamllint
2. Check indentation (must use spaces, not tabs)
3. Verify quotes around string values with special characters
4. Ensure no duplicate keys

### Issue: Service Name Conflicts

**Error:** `Service name already exists`

**Resolution:**
1. Verify `-iac` suffix used consistently
2. Check for typos in service names
3. Ensure old service names not reused

### Issue: Database Reference Not Found

**Error:** `fromDatabase: database not found`

**Resolution:**
1. Verify database defined in `databases` section
2. Check database name matches exactly (case-sensitive)
3. Ensure database created before service references it

### Issue: Environment Group Not Found

**Error:** `fromGroup: environment group not found`

**Resolution:**
1. Verify environment group defined in `envVarGroups`
2. Check group name matches exactly
3. Ensure no typos in group references

## Security Considerations

### Secrets Management

**NEVER commit these values to render.yaml:**
- `AUTH0_CLIENT_SECRET`
- `AUTH0_ACTION_SECRET`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `SENTRY_DSN`

**Always mark as `sync: false` in render.yaml**

### Access Control

**Before creating blueprint:**
- Verify only authorized team members have Render dashboard access
- Review GitHub repository access permissions
- Ensure sensitive environment variables protected

### Audit Trail

**After blueprint deployment:**
- Document who created the blueprint
- Record when services were created
- Maintain changelog of render.yaml updates
- Track environment variable changes

## Next Steps

After updating render.yaml:

1. **Review Changes:** Have team review updated configuration
2. **Deploy Blueprint:** Follow [02-BLUEPRINT-CREATION-GUIDE.md](./02-BLUEPRINT-CREATION-GUIDE.md)
3. **Configure Secrets:** Follow [05-ENVIRONMENT-VARIABLE-MIGRATION.md](./05-ENVIRONMENT-VARIABLE-MIGRATION.md)
4. **Run Tests:** Follow [07-VERIFICATION-TESTS.md](./07-VERIFICATION-TESTS.md)
5. **Migrate Traffic:** Follow [08-TRAFFIC-MIGRATION-GUIDE.md](./08-TRAFFIC-MIGRATION-GUIDE.md)

---

**Document Status:** READY FOR IMPLEMENTATION
**Configuration Validated:** ✓ YAML syntax correct
**Security Review:** ✓ No secrets in configuration
**Naming Convention:** ✓ -iac suffix applied consistently
