# Emergency Database Rollback - Quick Reference

**USE IN PRODUCTION EMERGENCIES ONLY**

## When to Use

- Critical migration failure in production
- Data corruption after deployment
- Need to restore to pre-migration state
- Application broken after database changes

## Prerequisites

- Pre-deployment snapshot exists (automatically created when RUN_MIGRATIONS=true)
- Access to Render.com shell or SSH
- Database credentials (DATABASE_URL)

## Emergency Rollback Procedure

### Step 1: Access Production Environment

**Render.com:**
```bash
# Via Render.com Dashboard
# Services > marketedge-platform > Shell
```

### Step 2: Verify Snapshot Exists

```bash
# Check for snapshots
ls -lh /tmp/db_snapshots/

# Check last snapshot reference
cat /tmp/last_snapshot.txt
```

Expected output:
```
/tmp/db_snapshots/pre_migration_20250930_212207.sql.gz
```

### Step 3: Execute Emergency Restore

```bash
# CRITICAL: This will OVERWRITE your current database
# All data since the snapshot will be LOST

export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

### Step 4: Verify Restoration

```bash
# Check application health
curl https://marketedge-platform.onrender.com/health

# Verify database tables
python -c "
from database.base import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables: {len(tables)}')
"
```

### Step 5: Re-seed Data (If Needed)

```bash
# Only if seeds are required
python database/seeds/initial_data.py
python database/seeds/phase3_data.py
```

### Step 6: Restart Application

```bash
# Render.com will auto-restart after shell exit
# Or manually trigger deployment
```

## Verification Checklist

After rollback:
- [ ] Application responds to /health endpoint
- [ ] User authentication works (test with matt.lindop@zebra.associates)
- [ ] Dashboard loads without errors
- [ ] Admin panel accessible
- [ ] Organization switching works
- [ ] Feature flags functional

## If Rollback Fails

### Scenario 1: Snapshot Not Found

```bash
# List all available snapshots
ls -lh /tmp/db_snapshots/

# Manually specify snapshot
export SNAPSHOT_PATH="/tmp/db_snapshots/pre_migration_YYYYMMDD_HHMMSS.sql.gz"
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

### Scenario 2: Restore Errors

```bash
# Check restore logs
cat /tmp/restore_output.log

# Verify database connection
psql $DATABASE_URL -c "SELECT version();"
```

### Scenario 3: No Snapshot Available

**Option A: Use Render.com Backup**
1. Go to Render.com Dashboard
2. Services > PostgreSQL database
3. Backups tab
4. Restore from most recent backup

**Option B: Use Railway.app Backup**
1. Railway.app dashboard
2. PostgreSQL plugin
3. Backups > Restore

**Option C: Rebuild from Seeds**
```bash
# LAST RESORT - loses production data
alembic downgrade base
alembic upgrade head
python database/seeds/initial_data.py
python database/seeds/phase3_data.py
```

## Post-Incident Actions

1. **Document Incident**
   - What migration failed?
   - What was the error?
   - When did failure occur?
   - How was it resolved?

2. **Review Migration**
   - Identify root cause
   - Test migration locally
   - Create fix or rollback migration

3. **Update Monitoring**
   - Add alerts for similar issues
   - Improve health checks
   - Document lessons learned

## Prevention Checklist

- [ ] Always test migrations locally first
- [ ] Run migrations on staging before production
- [ ] Verify RUN_MIGRATIONS=true triggers snapshot
- [ ] Monitor deployment logs for snapshot success
- [ ] Keep Render.com backup schedule active
- [ ] Document migration dependencies

## Emergency Contacts

**Platform Issues:**
- Check #incidents Slack channel
- Review Render.com status page
- Contact database administrator

**Database Access:**
- Render.com dashboard: https://dashboard.render.com
- Railway.app dashboard: https://railway.app

## Recovery Time Objectives

- Snapshot verification: < 1 minute
- Rollback execution: 2-5 minutes
- Application restart: 1-2 minutes
- Total recovery: < 10 minutes

## Important Notes

1. **Data Loss**: Rollback loses all changes since snapshot
2. **User Impact**: Application downtime during restore (2-5 min)
3. **Confirmation Required**: Must set CONFIRM_RESTORE=yes
4. **Snapshot Retention**: Snapshots in /tmp are ephemeral
5. **Communication**: Notify stakeholders of rollback

## Testing Rollback Locally

**NEVER test on production database**

```bash
# Create test database
createdb -O platform_user rollback_test

# Take snapshot
export DATABASE_URL="postgresql://platform_user@localhost:5432/rollback_test"
bash scripts/production/pre_deploy_snapshot.sh

# Make changes (simulate migration)
psql $DATABASE_URL -c "CREATE TABLE test_migration (id INT);"

# Test rollback
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh

# Verify test_migration table is gone
psql $DATABASE_URL -c "\dt test_migration"

# Clean up
dropdb rollback_test
```

---

**Last Updated:** 2025-09-30
**Script Version:** 1.0
**Tested On:** macOS, Render.com, Railway.app
