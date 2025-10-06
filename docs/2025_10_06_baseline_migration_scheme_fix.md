# Baseline Migration postgres:// Scheme Fix

**Date**: 2025-10-06  
**Status**: DEPLOYED TO STAGING  
**Commit**: 3528118  
**Severity**: CRITICAL - 500 error blocker

## Executive Summary

Fixed critical missing postgres:// → postgresql+asyncpg:// transformation in baseline migration script causing 500 errors in Render staging environment.

## The Problem

### Root Cause Discovery Process

1. **Initial Investigation** (commits 27d2344, 8711d24):
   - Added extensive diagnostic logging to `app/core/database.py`
   - Logged [SCHEME-FIX-3396375] transformation successful in app initialization
   - BUT: 500 error still occurred BEFORE app startup

2. **Critical Insight**:
   - Logs showed: "✅ Baseline schema applied successfully"
   - But diagnostic log `[SCHEME-FIX-3396375]` NEVER appeared
   - This proved: baseline migration runs BEFORE async engine initialization

3. **Root Cause Identified**:
   ```python
   # database/generate_baseline.py (line 244 - BEFORE FIX)
   engine = create_async_engine(database_url, echo=False)  # ❌ NO TRANSFORMATION
   ```
   
   - Baseline migration imports `create_async_engine` directly
   - Never goes through `app/core/database.py` transformation
   - Render provides `postgres://` URL (not `postgresql://`)
   - asyncpg requires `postgresql+asyncpg://` scheme

### Why This Was Missed

```bash
# render-startup.sh execution order (staging):
1. Schema validation          # ✅ sync operations (psycopg2)
2. Baseline migration         # ❌ async operations WITHOUT transformation
3. Alembic migrations         # ✅ sync operations (psycopg2)  
4. Seed data                  # ✅ sync operations (psycopg2)
5. App startup               # ✅ async WITH transformation
```

The baseline migration is the ONLY step using async operations before app initialization.

## The Fix

### Code Changes

**File**: `database/generate_baseline.py`  
**Lines**: 240-257

```python
async def apply_baseline_schema(database_url: str):
    """Apply baseline schema directly to database"""
    import logging
    logger = logging.getLogger(__name__)

    schema_sql = generate_baseline_schema()

    # CRITICAL: Transform postgres:// to postgresql+asyncpg:// for async engine
    # This handles Render's DATABASE_URL which uses postgres:// scheme
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    if async_database_url == database_url:  # No replacement happened
        async_database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    original_scheme = database_url.split('://')[0] if '://' in database_url else 'unknown'
    async_scheme = async_database_url.split('://')[0] if '://' in async_database_url else 'unknown'
    logger.info(f"[BASELINE-SCHEME-TRANSFORM] original={original_scheme} async={async_scheme}")

    engine = create_async_engine(async_database_url, echo=False)
```

### Diagnostic Logging

New log marker to verify fix:
```
[BASELINE-SCHEME-TRANSFORM] original=postgres async=postgresql+asyncpg
```

This will appear in render-startup.sh logs when baseline migration runs.

## Verification Steps

### 1. Watch Render Staging Deployment Logs

```bash
# Expected successful log sequence:
🔍 Validating database schema...
⚠️  Schema validation issues detected
🔧 Generating schema fixes...
📄 Schema fixes generated, applying baseline schema...
[BASELINE-SCHEME-TRANSFORM] original=postgres async=postgresql+asyncpg  # ← NEW
✅ Baseline schema applied successfully
🗃️  Running staging database migrations...
```

### 2. Success Indicators

✅ **Success**:
- Log shows `[BASELINE-SCHEME-TRANSFORM] original=postgres async=postgresql+asyncpg`
- No `asyncpg.exceptions.InvalidCatalogNameError`
- Baseline schema applied successfully
- Migrations proceed normally
- App starts without 500 errors

❌ **Failure** (if transformation still missing):
- No `[BASELINE-SCHEME-TRANSFORM]` log
- Error: `asyncpg.exceptions.InvalidCatalogNameError: database "user" does not exist`
- Baseline application fails

### 3. Testing Checklist

- [ ] Trigger Render staging redeployment
- [ ] Monitor startup logs for `[BASELINE-SCHEME-TRANSFORM]` diagnostic
- [ ] Verify baseline schema applies without errors
- [ ] Confirm app starts and serves requests
- [ ] Test /health endpoint returns 200 OK
- [ ] Check /api/v1/admin/feature-flags (requires authentication)

## Related Issues

### Other Scripts with Similar Pattern

Found 18 scripts using `create_async_engine` directly:
- Most already handle transformation (e.g., `fix_auth0_tenant_context_mismatch.py`)
- Some only handle `postgresql://`, not `postgres://`
- Recommendation: Audit all for Render compatibility

### Previous Related Fixes

1. **Commit 27d2344**: Added [SCHEME-FIX-3396375] to app/core/database.py
   - Fixed async engine initialization in FastAPI app
   - Did NOT fix baseline migration (separate code path)

2. **Commit 8711d24**: Enhanced diagnostic logging
   - Proved app-level transformation working
   - Revealed baseline migration bypasses app initialization

## Lessons Learned

1. **Migration execution context matters**:
   - Baseline migrations run BEFORE app initialization
   - Cannot rely on app-level transformations
   - Must handle scheme transformation in migration scripts

2. **Diagnostic logging strategy**:
   - Module-level fatal checks can be misleading
   - Transformation happens in function calls, not module imports
   - Need distinct log markers for each code path

3. **Database URL scheme handling**:
   - Render uses `postgres://` (legacy Heroku format)
   - asyncpg requires `postgresql+asyncpg://`
   - psycopg2 accepts both `postgres://` and `postgresql://`
   - Always transform for async operations

## Next Steps

1. **Monitor Staging Deployment** (IMMEDIATE):
   - Watch for `[BASELINE-SCHEME-TRANSFORM]` in logs
   - Confirm no asyncpg errors
   - Verify app functionality

2. **Production Deployment** (AFTER STAGING VERIFICATION):
   - Same fix applies if production uses Render
   - Monitor identical diagnostic logs
   - Have rollback plan ready

3. **Code Audit** (FOLLOW-UP):
   - Review all 18 scripts using `create_async_engine`
   - Ensure postgres:// scheme handled in all async paths
   - Consider centralizing transformation utility

4. **Documentation Update** (FOLLOW-UP):
   - Update deployment troubleshooting guide
   - Add section on database URL scheme requirements
   - Document diagnostic log markers

## Files Changed

- `database/generate_baseline.py` - Added postgres:// transformation (14 lines)

## Deployment Timeline

- **2025-10-06 11:51**: Fix committed to staging
- **2025-10-06 11:52**: Pushed to origin/staging (triggers Render deployment)
- **Next**: Monitor Render staging deployment logs

---

**Deployment Command**:
```bash
git push origin staging  # Triggers automatic Render deployment
```

**Verification URL**:
```
https://marketedge-platform-staging.onrender.com/health
```
