# Schema Validation Quick Start Guide

**TL;DR:** Stop migration whack-a-mole with schema validation before deploying.

## Immediate Actions

### Fix Current Production Issue
```bash
# 1. Check what's missing in production
DATABASE_URL="your_production_url" python database/validate_schema.py --check

# 2. Generate fix SQL
DATABASE_URL="your_production_url" python database/validate_schema.py --fix > production_fixes.sql

# 3. Review and apply fixes
cat production_fixes.sql  # Review before applying
psql $DATABASE_URL < production_fixes.sql

# 4. Verify fixes
DATABASE_URL="your_production_url" python database/validate_schema.py --check
# Should now show: ✅ Schema validation PASSED
```

### Local Development Setup
```bash
# 1. Validate your local database
python database/validate_schema.py --check

# 2. If issues found, apply baseline schema
python database/generate_baseline.py --apply

# 3. Run migrations as normal
alembic upgrade head
```

## Commands Reference

### Schema Validation
```bash
# Check schema status
python database/validate_schema.py --check

# Generate fix SQL (review before applying)
python database/validate_schema.py --fix

# Apply baseline schema (for fresh databases)
python database/generate_baseline.py --apply
```

### Error Scenarios

#### ❌ Missing Tables Error
```
ERROR: Required tables missing: {organisation_modules, module_usage_logs}
```
**Solution:**
```bash
python database/validate_schema.py --fix | psql $DATABASE_URL
```

#### ❌ Missing Columns Error
```
ERROR: Column 'organisation_id' required in table 'organisation_modules'
```
**Solution:**
```bash
python database/validate_schema.py --fix | psql $DATABASE_URL
```

#### ✅ Schema Valid
```
✅ Schema validation PASSED - all required tables and columns exist
```
**Action:** Proceed with migrations

## Deployment Integration

### Staging (Automatic)
- Schema validation runs automatically in `render-startup.sh`
- Issues are fixed automatically with baseline schema
- Migrations run after schema is validated

### Production Emergency
- Set `RUN_MIGRATIONS=true` environment variable
- Schema validation runs first (fail-fast)
- Migration proceeds only if validation passes

### Production Regular
- Schema validation runs as health check
- Warnings logged but deployment continues
- Monitor logs for validation warnings

## Troubleshooting

### Import Errors
```bash
# If you see: ImportError: cannot import name 'X'
# Check that all model imports are correct in:
# - database/validate_schema.py
# - database/generate_baseline.py
```

### Database Connection
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Or pass directly to command
DATABASE_URL="your_url" python database/validate_schema.py --check
```

### Permission Issues
```bash
# Ensure database user has required permissions:
# - SELECT on information_schema.tables
# - SELECT on information_schema.columns
# - CREATE/ALTER permissions for fixes
```

## Success Indicators

- ✅ `python database/validate_schema.py --check` returns exit code 0
- ✅ Migration 004 runs without "column does not exist" errors
- ✅ Deployment startup shows "✅ Schema validation passed"
- ✅ No more whack-a-mole migration debugging

## Next Steps After Setup

1. **Test locally:** Run validation on your development database
2. **Fix staging:** Ensure staging environment has clean schema
3. **Validate production:** Check production schema status
4. **Monitor deployments:** Watch for validation warnings in logs

---

**Emergency Contact:** If schema validation fails in production, use baseline schema application to restore expected schema state.