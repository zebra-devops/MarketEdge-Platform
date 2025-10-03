# Environment Variable Migration Guide

**Document Version:** 1.0
**Created:** 2025-10-03
**Author:** Maya (DevOps Agent)
**Status:** Implementation Ready

## Overview

Comprehensive guide for migrating environment variables from manually-created Render services to Blueprint-managed IaC services.

## Environment Variable Categories

### Category 1: Version-Controlled (in render.yaml)

These are defined in render.yaml and automatically applied:

- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_AUDIENCE`
- `AUTH0_CALLBACK_URL`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS`
- `ENVIRONMENT`
- `DEBUG`
- `LOG_LEVEL`
- `API_V1_STR`
- `PROJECT_NAME`
- `PROJECT_VERSION`
- `CSRF_ENABLED`
- `CADDY_PROXY_MODE`
- `COOKIE_SECURE`
- Feature flags
- `PYTHON_VERSION`

**Action Required:** None - automatically applied from render.yaml

### Category 2: Secrets (Manual Configuration Required)

These MUST be manually configured in Render Dashboard:

- `AUTH0_CLIENT_SECRET`
- `AUTH0_ACTION_SECRET`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `SENTRY_DSN` (optional)

**Action Required:** Manual configuration (see detailed steps below)

## Pre-Migration: Document Current Configuration

### Step 1: Export Current Production Environment Variables

**Access Old Production Service:**

1. Log into Render Dashboard: https://dashboard.render.com
2. Navigate to service: `marketedge-platform`
3. Click "Settings" tab
4. Click "Environment" section

**Document Each Secret:**

Create secure document (password manager or encrypted file):

```plaintext
=== MarketEdge Production Environment Variables ===
Date Exported: 2025-10-03
Service: marketedge-platform

AUTH0_CLIENT_SECRET: [REDACTED - copy actual value]
AUTH0_ACTION_SECRET: [REDACTED - copy actual value]
JWT_SECRET_KEY: [REDACTED - copy actual value]
DATABASE_URL: [REDACTED - copy actual value]
REDIS_URL: [REDACTED - copy actual value]
SENTRY_DSN: [REDACTED - copy actual value if configured]

=== End Production Secrets ===
```

**Security Note:** Store this document securely and delete after migration complete.

### Step 2: Export Current Staging Environment Variables

**Access Old Staging Service:**

1. Navigate to service: `marketedge-platform-staging` (if exists)
2. Click "Settings" tab → "Environment"
3. Document staging-specific secrets

```plaintext
=== MarketEdge Staging Environment Variables ===
Date Exported: 2025-10-03
Service: marketedge-platform-staging

AUTH0_CLIENT_SECRET: [REDACTED - may differ from production]
AUTH0_ACTION_SECRET: [REDACTED - may differ from production]
JWT_SECRET_KEY: [REDACTED - MUST differ from production]
DATABASE_URL: [automatically configured via fromDatabase]
REDIS_URL: [REDACTED - may share with production]

=== End Staging Secrets ===
```

### Step 3: Verify Environment Variable Completeness

**Checklist of Variables to Document:**

- [ ] `AUTH0_CLIENT_SECRET` - Production
- [ ] `AUTH0_CLIENT_SECRET` - Staging
- [ ] `AUTH0_ACTION_SECRET` - Production
- [ ] `AUTH0_ACTION_SECRET` - Staging
- [ ] `JWT_SECRET_KEY` - Production
- [ ] `JWT_SECRET_KEY` - Staging (verify DIFFERENT from production)
- [ ] `DATABASE_URL` - Production
- [ ] `REDIS_URL` - Production
- [ ] `REDIS_URL` - Staging (if separate)
- [ ] `SENTRY_DSN` - Production (if configured)

## Migration: Configure New Services

### Production Service Configuration

**Service:** `marketedge-platform-iac`

#### Step 1: Access New Service Environment Settings

1. Log into Render Dashboard
2. Navigate to newly created service: `marketedge-platform-iac`
3. Click "Settings" tab
4. Scroll to "Environment" section
5. Click "Add Environment Variable"

#### Step 2: Add AUTH0_CLIENT_SECRET

**Variable Configuration:**

```
Key: AUTH0_CLIENT_SECRET
Value: [paste from exported production secrets]
```

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `AUTH0_CLIENT_SECRET`
3. Enter value: [paste actual secret from old service]
4. Click "Save Changes"

**Verification:**
- Variable appears in environment list
- Value is masked (shows as ••••••••)

#### Step 3: Add AUTH0_ACTION_SECRET

**Variable Configuration:**

```
Key: AUTH0_ACTION_SECRET
Value: [paste from exported production secrets]
```

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `AUTH0_ACTION_SECRET`
3. Enter value: [paste actual secret from old service]
4. Click "Save Changes"

**Verification:**
- Variable appears in environment list
- Value is masked

#### Step 4: Add JWT_SECRET_KEY

**Variable Configuration:**

```
Key: JWT_SECRET_KEY
Value: [paste from exported production secrets]
```

**CRITICAL:** Use the SAME JWT_SECRET_KEY as old production service to ensure existing tokens remain valid during migration.

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `JWT_SECRET_KEY`
3. Enter value: [paste actual secret from old service]
4. Click "Save Changes"

**Verification:**
- Variable appears in environment list
- Value is masked

#### Step 5: Add DATABASE_URL

**Variable Configuration:**

```
Key: DATABASE_URL
Value: [paste from exported production secrets]
```

**CRITICAL:** Use the SAME DATABASE_URL as old production service. Both services will connect to the same database during migration.

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `DATABASE_URL`
3. Enter value: [paste actual connection string from old service]
4. Click "Save Changes"

**Verification:**
- Variable appears in environment list
- Value is masked
- Format: `postgresql://user:password@host:port/database`

#### Step 6: Add REDIS_URL

**Variable Configuration:**

```
Key: REDIS_URL
Value: [paste from exported production secrets]
```

**Note:** Both old and new services can safely share the same Redis instance.

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `REDIS_URL`
3. Enter value: [paste actual connection string from old service]
4. Click "Save Changes"

**Verification:**
- Variable appears in environment list
- Value is masked
- Format: `redis://user:password@host:port`

#### Step 7: Add SENTRY_DSN (Optional)

**Variable Configuration:**

```
Key: SENTRY_DSN
Value: [paste from exported production secrets if configured]
```

**Steps:**
1. Click "Add Environment Variable"
2. Enter key: `SENTRY_DSN`
3. Enter value: [paste actual DSN from old service]
4. Click "Save Changes"

**Skip if:** Sentry not configured in old service

#### Step 8: Verify All Production Secrets Configured

**Production Service Environment Variables Checklist:**

- [ ] `AUTH0_CLIENT_SECRET` - Added and masked
- [ ] `AUTH0_ACTION_SECRET` - Added and masked
- [ ] `JWT_SECRET_KEY` - Added and masked (SAME as old service)
- [ ] `DATABASE_URL` - Added and masked (SAME as old service)
- [ ] `REDIS_URL` - Added and masked (SAME as old service)
- [ ] `SENTRY_DSN` - Added if applicable
- [ ] All other variables inherited from render.yaml (verify in environment list)

### Staging Service Configuration

**Service:** `marketedge-platform-staging-iac`

#### Step 1: Access Staging Service Environment Settings

1. Navigate to service: `marketedge-platform-staging-iac`
2. Click "Settings" tab
3. Scroll to "Environment" section

#### Step 2: Add Staging Secrets

**AUTH0_CLIENT_SECRET (Staging):**

```
Key: AUTH0_CLIENT_SECRET
Value: [paste from exported staging secrets OR use production value]
```

**Note:** Staging can use the same Auth0 application as production (currently configured this way).

**AUTH0_ACTION_SECRET (Staging):**

```
Key: AUTH0_ACTION_SECRET
Value: [paste from exported staging secrets OR use production value]
```

**JWT_SECRET_KEY (Staging):**

```
Key: JWT_SECRET_KEY
Value: [MUST be DIFFERENT from production]
```

**CRITICAL:** Generate a NEW JWT_SECRET_KEY for staging if not already documented.

**Generate New JWT Secret (if needed):**

```bash
# Option 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Use the generated value as JWT_SECRET_KEY for staging
```

**DATABASE_URL (Staging):**

**Note:** Staging database automatically configured via `fromDatabase` in render.yaml. No manual configuration needed.

**Verification:**
- Check environment list for `DATABASE_URL`
- Should be automatically populated by Render
- Format: `postgresql://...marketedge_staging_iac...`

**REDIS_URL (Staging):**

```
Key: REDIS_URL
Value: [staging Redis URL or share production Redis]
```

**Options:**
- **Option A (Shared):** Use same REDIS_URL as production (acceptable for staging)
- **Option B (Separate):** Use dedicated staging Redis instance

#### Step 3: Verify All Staging Secrets Configured

**Staging Service Environment Variables Checklist:**

- [ ] `AUTH0_CLIENT_SECRET` - Added
- [ ] `AUTH0_ACTION_SECRET` - Added
- [ ] `JWT_SECRET_KEY` - Added (DIFFERENT from production)
- [ ] `DATABASE_URL` - Auto-configured (verify present)
- [ ] `REDIS_URL` - Added
- [ ] All other variables inherited from render.yaml

## Post-Configuration: Trigger Deployment

### Step 1: Trigger Production Deployment

After all environment variables configured:

1. Navigate to `marketedge-platform-iac` service
2. Click "Manual Deploy" dropdown (top-right)
3. Select "Deploy latest commit"
4. Click "Deploy"

**Monitor Deployment:**
- Click "Logs" tab
- Watch for successful startup
- Verify no environment variable errors
- Expected duration: 5-10 minutes

### Step 2: Trigger Staging Deployment

1. Navigate to `marketedge-platform-staging-iac` service
2. Click "Manual Deploy" → "Deploy latest commit"
3. Monitor logs for successful startup

### Step 3: Verify Environment Variables Active

**Production Service:**

```bash
# Test that service starts successfully
curl https://marketedge-platform-iac.onrender.com/health

# Expected: {"status":"healthy",...}
```

**Staging Service:**

```bash
# Test staging service
curl https://marketedge-platform-staging-iac.onrender.com/health

# Expected: {"status":"healthy",...}
```

## Verification Tests

### Test 1: Auth0 Configuration

**Purpose:** Verify Auth0 secrets working correctly

```bash
# Test authentication endpoint (requires valid credentials)
curl -X POST https://marketedge-platform-iac.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_password"
  }'

# Expected: 200 OK with access_token (if credentials valid)
# OR: 401 Unauthorized (if credentials invalid - but no 500 errors)
```

**Success Criteria:**
- No "Missing AUTH0_CLIENT_SECRET" errors
- No "Missing AUTH0_ACTION_SECRET" errors
- Authentication flow completes (success or failure based on credentials)

### Test 2: Database Connection

**Purpose:** Verify DATABASE_URL configured correctly

```bash
# Test database health endpoint
curl https://marketedge-platform-iac.onrender.com/api/v1/health/db

# Expected: {"status":"healthy","database":"connected"}
```

**Success Criteria:**
- No "Could not connect to database" errors
- Database queries execute successfully
- Migrations applied correctly

**Check Logs:**
```
Look for: "Database connection established"
No errors: "psycopg2.OperationalError"
```

### Test 3: Redis Connection

**Purpose:** Verify REDIS_URL configured correctly

```bash
# Test Redis-dependent functionality (e.g., caching)
curl https://marketedge-platform-iac.onrender.com/api/v1/health/cache

# Expected: {"status":"healthy","cache":"connected"}
```

**Success Criteria:**
- No "Could not connect to Redis" errors
- Session management working
- Caching functional

### Test 4: JWT Token Generation

**Purpose:** Verify JWT_SECRET_KEY configured correctly

**Scenario 1: New Service Generates Tokens**

```bash
# Login and receive token from new service
curl -X POST https://marketedge-platform-iac.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"valid@example.com","password":"valid_password"}' \
  -c cookies.txt

# Use token to access protected endpoint
curl https://marketedge-platform-iac.onrender.com/api/v1/protected \
  -b cookies.txt
```

**Scenario 2: Existing Tokens Valid (CRITICAL for Migration)**

Since new service uses SAME JWT_SECRET_KEY as old service:

```bash
# Get token from OLD service
OLD_TOKEN=$(curl -X POST https://marketedge-platform.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"valid@example.com","password":"valid_password"}' | jq -r '.access_token')

# Use OLD token with NEW service
curl https://marketedge-platform-iac.onrender.com/api/v1/protected \
  -H "Authorization: Bearer $OLD_TOKEN"

# Expected: 200 OK (token valid across both services)
```

**Success Criteria:**
- New service generates valid tokens
- Tokens from old service work with new service
- No "Invalid token" errors for valid tokens

### Test 5: Sentry Integration (If Configured)

**Purpose:** Verify SENTRY_DSN configured correctly

```bash
# Trigger a test error
curl https://marketedge-platform-iac.onrender.com/api/v1/test/error

# Check Sentry dashboard for error logged
```

**Success Criteria:**
- Errors appear in Sentry dashboard
- Error tracking functional
- No "Sentry configuration error" messages

## Environment Variable Comparison Report

After migration, generate comparison report:

### Production Service Comparison

| Variable | Old Service | New Service | Match? |
|----------|------------|-------------|--------|
| `AUTH0_CLIENT_SECRET` | Set (masked) | Set (masked) | ✓ Same value |
| `AUTH0_ACTION_SECRET` | Set (masked) | Set (masked) | ✓ Same value |
| `JWT_SECRET_KEY` | Set (masked) | Set (masked) | ✓ Same value (CRITICAL) |
| `DATABASE_URL` | Set (masked) | Set (masked) | ✓ Same value (shared DB) |
| `REDIS_URL` | Set (masked) | Set (masked) | ✓ Same value (shared) |
| `SENTRY_DSN` | Set (masked) | Set (masked) | ✓ Same value |
| `AUTH0_AUDIENCE` | Not set | Set | ⚠️ CRITICAL FIX applied |
| `CORS_ORIGINS` | Old URLs only | Old + New URLs | ✓ Updated for migration |

### Staging Service Comparison

| Variable | Old Service | New Service | Notes |
|----------|------------|-------------|-------|
| `AUTH0_CLIENT_SECRET` | Set | Set | May differ from production |
| `JWT_SECRET_KEY` | Set | Set | MUST differ from production |
| `DATABASE_URL` | Manual | Auto-configured | New staging DB |

## Troubleshooting

### Issue: "Missing environment variable" Error

**Symptoms:**
- Service fails to start
- Logs show: "Missing required environment variable: [name]"

**Resolution:**

1. Verify variable configured in dashboard
2. Check variable name spelling (case-sensitive)
3. Ensure no trailing spaces in value
4. Redeploy service after adding variable

### Issue: Authentication Fails After Migration

**Symptoms:**
- Login returns 500 error
- Logs show: "Invalid Auth0 credentials"

**Resolution:**

1. Verify `AUTH0_CLIENT_SECRET` matches old service
2. Verify `AUTH0_ACTION_SECRET` matches old service
3. Check Auth0 dashboard for service URLs configured
4. Test Auth0 credentials with curl

### Issue: Database Connection Fails

**Symptoms:**
- Service starts but database errors
- Logs show: "Could not connect to database"

**Resolution:**

1. Verify `DATABASE_URL` format correct
2. Check database service status (should be "Available")
3. Verify both services in same region (connection speed)
4. Test connection string manually with psql

### Issue: Existing Tokens Invalid After Migration

**Symptoms:**
- Users logged out after migration
- Tokens return "Invalid token" error

**Root Cause:** `JWT_SECRET_KEY` differs between old and new service

**Resolution:**

1. Verify `JWT_SECRET_KEY` in new service matches old service EXACTLY
2. Regenerate token from new service
3. If different key used accidentally:
   - Update new service with correct key
   - Redeploy service
   - Users may need to re-authenticate once

### Issue: Redis Connection Fails

**Symptoms:**
- Caching errors
- Session management broken
- Logs show: "Could not connect to Redis"

**Resolution:**

1. Verify `REDIS_URL` format correct
2. Test connection: `redis-cli -u $REDIS_URL ping`
3. Check Redis service status
4. Verify firewall/network connectivity

## Security Best Practices

### Secret Rotation Post-Migration

**After successful migration and old service deprecation:**

Consider rotating secrets for enhanced security:

1. **Generate New Secrets:**
   ```bash
   # New JWT_SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"

   # Update in Render Dashboard
   # This will invalidate all existing tokens (users must re-authenticate)
   ```

2. **Update Auth0 Configuration:**
   - Rotate `AUTH0_CLIENT_SECRET` in Auth0 dashboard
   - Update Render environment variable
   - Redeploy service

3. **Database Credentials:**
   - Consider rotating database password
   - Update `DATABASE_URL` with new credentials

### Access Control

**Limit Dashboard Access:**
- Only DevOps team should access Render Dashboard
- Use separate staging and production access controls
- Enable 2FA on Render accounts

### Audit Trail

**Document All Changes:**
- Record who configured environment variables
- Track when secrets were last rotated
- Maintain changelog of configuration updates

## Post-Migration Cleanup

### After 72 Hours Stable Operation

1. **Remove Old Service Access:**
   - Document old service configuration (final backup)
   - Export logs for archival
   - Suspend old service (don't delete yet)

2. **Update Documentation:**
   - Update deployment guides with new service names
   - Document environment variable configuration
   - Create runbooks for new infrastructure

3. **Security Audit:**
   - Verify no secrets committed to Git
   - Confirm environment variables properly masked
   - Review access control policies

4. **Delete Exported Secrets:**
   - Securely delete exported secret document
   - Remove from password manager if temporary
   - Ensure no plaintext secrets in communication channels

## Checklist: Environment Variable Migration Complete

- [ ] All production secrets documented from old service
- [ ] All staging secrets documented from old service
- [ ] Production secrets configured in new service
- [ ] Staging secrets configured in new service
- [ ] JWT_SECRET_KEY matches old service (production)
- [ ] JWT_SECRET_KEY differs from production (staging)
- [ ] DATABASE_URL matches old service (production)
- [ ] All services deployed successfully
- [ ] Health checks passing
- [ ] Authentication tested and working
- [ ] Database connections verified
- [ ] Redis connections verified
- [ ] Token validation working (old tokens valid with new service)
- [ ] Comparison report generated
- [ ] Troubleshooting guide reviewed
- [ ] Team trained on new configuration management

---

**Document Status:** READY FOR IMPLEMENTATION
**Security Level:** HIGH - Contains procedures for sensitive data
**Review Required:** Yes - Security team review recommended before execution
