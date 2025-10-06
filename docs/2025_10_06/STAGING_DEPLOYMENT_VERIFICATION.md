# Staging Deployment Verification Checklist
**Date**: 2025-10-06
**Issue**: Empty staging database with postgres:// scheme incompatibility
**Fix Applied**: Async driver scheme transformation

## Problem Summary
- **Database**: marketedge-preview-db (empty schema)
- **Error**: `postgres://` scheme not supported by asyncpg driver
- **Fix**: Added scheme transformation logic to handle both `postgresql://` and `postgres://`

## Fix Details

### Code Changes (app/core/database.py)
```python
# Transform to async driver (handles both postgresql:// and postgres:// schemes)
async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
if async_database_url == database_url:  # No replacement happened
    async_database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

logger.info(f"Async database URL scheme: {async_database_url.split('://')[0]}")
```

### Branch Status
- **Main branch**: Fix committed (8f54374)
- **Staging branch**: Fix merged and pushed (8f54374)
- **Deployment branch**: `staging` (per render.yaml line 259)

## Deployment Trigger Instructions

### Option 1: Manual Trigger via Render Dashboard
1. Go to Render Dashboard: https://dashboard.render.com
2. Navigate to `marketedge-platform-staging` service
3. Click **Manual Deploy** → **Deploy latest commit**
4. Monitor deployment logs

### Option 2: Git Push Trigger (Already Done)
```bash
# Already executed - pushed to staging branch
git checkout staging
git merge main -m "fix: merge async driver postgres:// scheme fix"
git push origin staging
```

## Deployment Monitoring Checklist

### 1. Build Phase Logs
Look for:
```
Installing dependencies...
Successfully installed asyncpg psycopg2-binary alembic...
```

### 2. Startup Script Execution
Expected log sequence:
```
=== MarketEdge Platform Startup Script ===
Starting application initialization...
Database URL scheme: postgres  # or postgresql
```

### 3. Migration Detection
Expected behavior for empty database:
```
Checking database schema...
Database appears empty. Running baseline migration...
Running migrations with alembic...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial database schema
```

### 4. Async Driver Transformation
Critical logs to verify:
```
Initializing database engine with lazy loading...
Database URL scheme: postgres
Async database URL scheme: postgresql+asyncpg
```

### 5. FastAPI Startup
Success indicators:
```
INFO:     Started server process [xxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

## Verification Steps

### Step 1: Check Service Health
```bash
# Wait for deployment to complete, then:
curl https://marketedge-platform-staging.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-06T...",
  "environment": "staging"
}
```

### Step 2: Verify Database Tables Created
Via Render Dashboard SQL console:
```sql
-- List all tables
\dt

-- Expected tables:
-- alembic_version
-- audit_logs
-- billing_details
-- feature_assignments
-- feature_flags
-- industry_benchmark_calculations
-- ...
```

### Step 3: Check Migration Status
```sql
SELECT * FROM alembic_version;

-- Expected: Should show latest migration ID
```

### Step 4: Test API Endpoints
```bash
# Test root endpoint
curl https://marketedge-platform-staging.onrender.com/

# Test API documentation
curl https://marketedge-platform-staging.onrender.com/docs
```

## Potential Issues & Solutions

### Issue 1: Still Getting postgres:// Error
**Symptom**: `NotImplementedError: postgres:// scheme is not supported`
**Solution**:
- Verify the fix is deployed: Check build timestamp in logs
- Check environment variable: Must use Internal Database URL from Render
- Confirm asyncpg is installed: Check build logs

### Issue 2: Migrations Not Running
**Symptom**: Tables not created, empty schema
**Solution**:
- Check RUN_MIGRATIONS=true in environment variables
- Verify render-startup.sh is executable
- Check alembic can connect with sync driver

### Issue 3: Health Check Failing
**Symptom**: 502 Bad Gateway or timeout
**Solution**:
- Check for startup errors in logs
- Verify all environment variables are set
- Check Redis connection if configured

## Environment Variables Verification

Critical variables for staging deployment:
```
DATABASE_URL=postgresql://marketedge_preview_user:***@dpg-d3fvcr2li9vc73ep08a0-a:5432/marketedge_preview
RUN_MIGRATIONS=true
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6
AUTH0_AUDIENCE=https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/
```

## Expected Deployment Timeline
1. **Build phase**: 2-3 minutes (dependency installation)
2. **Startup script**: 30-60 seconds (migrations + app init)
3. **Health check**: Should pass within 90 seconds
4. **Total time**: ~5 minutes for full deployment

## Success Criteria
- ✅ Health endpoint returns 200 OK
- ✅ Database has all expected tables
- ✅ No async driver errors in logs
- ✅ API documentation accessible at /docs
- ✅ Authentication endpoints functional

## Post-Deployment Actions
1. Verify all endpoints respond correctly
2. Test Auth0 integration with staging client
3. Run smoke tests if available
4. Monitor error logs for first 10 minutes
5. Document any issues for future reference

## Rollback Plan
If deployment fails:
1. Check deployment logs for specific error
2. Previous working version available in deployment history
3. Can rollback via Render Dashboard
4. Database backup available (if data exists)

## Contact for Issues
- Check logs in Render Dashboard first
- Review this checklist for common issues
- Database connection details in screenshot provided

## Notes
- This is a fresh staging database with no existing data
- Migrations will create all tables from scratch
- The postgres:// → postgresql+asyncpg:// transformation is critical
- Both sync (Alembic) and async (FastAPI) engines now handle the scheme correctly