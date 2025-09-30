# Database Snapshot Scripts - Usage Examples

Quick reference with real-world examples for using the database snapshot and restore scripts.

## Quick Start

```bash
# 1. Create a snapshot
export DATABASE_URL="postgresql://user:password@host:5432/database"
bash scripts/production/pre_deploy_snapshot.sh

# 2. Restore from snapshot (CAREFUL!)
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

## Example 1: Manual Pre-Migration Snapshot (Local)

**Scenario:** Testing a new migration locally before deploying.

```bash
# Set local database connection
export DATABASE_URL="postgresql://platform_user@localhost:5432/platform_wrapper"

# Create snapshot
bash scripts/production/pre_deploy_snapshot.sh

# Expected output:
# ========================================
# Pre-Deployment Database Snapshot
# ========================================
#
# 📁 Backup directory: /tmp/db_snapshots
# 🗄️  Database: platform_wrapper
#
# 📸 Creating pre-deployment snapshot...
#    Timestamp: 20250930_212511
# ✅ pg_dump completed successfully
#
# 🔍 Verifying snapshot integrity...
# ✅ Snapshot file size: 24K
# ✅ Gzip compression integrity verified
# ✅ Snapshot path stored for emergency restore
#
# ========================================
# Snapshot Created Successfully
# ========================================

# Now run your migration
alembic upgrade head

# If migration fails, restore from snapshot
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

## Example 2: Production Migration with Automatic Snapshot

**Scenario:** Running emergency migration in production with automatic snapshot.

```bash
# In Render.com Dashboard:
# 1. Go to Services > marketedge-platform
# 2. Environment tab
# 3. Set environment variable:
RUN_MIGRATIONS=true

# 4. Trigger manual deployment or wait for auto-deploy

# What happens:
# - render-startup.sh runs
# - pre_deploy_snapshot.sh executes automatically
# - If snapshot succeeds: migrations run
# - If snapshot fails: deployment blocked (SAFE!)

# Check Render.com logs to verify:
# 📸 Creating pre-deployment database snapshot...
# ✅ Pre-deployment snapshot created successfully
# 🗃️  Running production migrations...
```

## Example 3: Emergency Rollback After Failed Migration

**Scenario:** Production migration failed, need to rollback immediately.

```bash
# 1. Access Render.com shell
# Services > marketedge-platform > Shell

# 2. Check snapshot exists
cat /tmp/last_snapshot.txt
# Output: /tmp/db_snapshots/pre_migration_20250930_143022.sql.gz

ls -lh /tmp/db_snapshots/
# Output: -rw-r--r--  1 user  staff   142K 30 Sep 14:30 pre_migration_20250930_143022.sql.gz

# 3. Execute emergency restore
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh

# Expected output:
# ========================================
# ⚠️  EMERGENCY DATABASE RESTORE
# ========================================
#
# 📄 Found last snapshot reference: /tmp/db_snapshots/pre_migration_20250930_143022.sql.gz
#
# 📸 Snapshot to restore:
#    File: pre_migration_20250930_143022.sql.gz
#    Size: 142K
#    Path: /tmp/db_snapshots/pre_migration_20250930_143022.sql.gz
#
# 🗄️  Target database: marketedge_prod
#
# 🔄 Starting database restore...
#    This will DROP and recreate all tables
#
# ✅ Database restore completed successfully
#
# 🔍 Verifying restore...
# ✅ Verified: 36 tables restored
#
# ========================================
# Restore Completed Successfully
# ========================================

# 4. Verify application health
curl https://marketedge-platform.onrender.com/health

# 5. Test critical functionality
curl -H "Authorization: Bearer $TOKEN" \
  https://marketedge-platform.onrender.com/api/v1/users/me
```

## Example 4: Testing Migration Locally with Rollback

**Scenario:** Test a risky migration locally with easy rollback.

```bash
# 1. Create test database from production dump
createdb -O platform_user migration_test

# 2. Import production data (if you have a dump)
psql postgresql://platform_user@localhost:5432/migration_test < prod_dump.sql

# 3. Create snapshot
export DATABASE_URL="postgresql://platform_user@localhost:5432/migration_test"
bash scripts/production/pre_deploy_snapshot.sh

# 4. Test migration
alembic upgrade head

# 5. Verify changes
psql $DATABASE_URL -c "\dt"

# 6. If issues found, rollback
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh

# 7. Fix migration and try again
# Edit migration file...
alembic downgrade -1
alembic upgrade head

# 8. Clean up
dropdb migration_test
```

## Example 5: Scheduled Daily Snapshot (Cron Job)

**Scenario:** Create daily snapshots for backup (not relying on /tmp).

```bash
# Create cron script: /home/user/daily_snapshot.sh
#!/bin/bash
set -e

export DATABASE_URL="postgresql://user:pass@host:5432/db"
export BACKUP_DIR="/backups/daily"

# Create backup directory if needed
mkdir -p $BACKUP_DIR

# Run snapshot
bash /path/to/scripts/production/pre_deploy_snapshot.sh

# Keep only last 7 days of snapshots
find $BACKUP_DIR -name "pre_migration_*.sql.gz" -mtime +7 -delete

# Log success
echo "$(date): Daily snapshot completed" >> /var/log/daily_snapshot.log

# Add to crontab:
# crontab -e
# 0 2 * * * /home/user/daily_snapshot.sh
```

## Example 6: Multiple Environment Snapshots

**Scenario:** Manage snapshots for different environments.

```bash
# Local development
export DATABASE_URL="postgresql://user@localhost:5432/marketedge_dev"
export BACKUP_DIR="/tmp/snapshots/dev"
bash scripts/production/pre_deploy_snapshot.sh

# Staging
export DATABASE_URL="postgresql://user:pass@staging-host:5432/marketedge_staging"
export BACKUP_DIR="/tmp/snapshots/staging"
bash scripts/production/pre_deploy_snapshot.sh

# Production
export DATABASE_URL="postgresql://user:pass@prod-host:5432/marketedge_prod"
export BACKUP_DIR="/tmp/snapshots/production"
bash scripts/production/pre_deploy_snapshot.sh

# List all snapshots
ls -lh /tmp/snapshots/*/
```

## Example 7: Restore from Specific Snapshot (Not Last)

**Scenario:** Need to restore from older snapshot, not the most recent.

```bash
# 1. List available snapshots
ls -lht /tmp/db_snapshots/pre_migration_*.sql.gz

# Output:
# -rw-r--r--  1 user  staff   142K 30 Sep 14:30 pre_migration_20250930_143022.sql.gz
# -rw-r--r--  1 user  staff   138K 30 Sep 12:15 pre_migration_20250930_121500.sql.gz
# -rw-r--r--  1 user  staff   135K 29 Sep 18:45 pre_migration_20250929_184532.sql.gz

# 2. Manually update last_snapshot.txt
echo "/tmp/db_snapshots/pre_migration_20250929_184532.sql.gz" > /tmp/last_snapshot.txt

# 3. Restore from selected snapshot
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

## Example 8: Snapshot Before Schema Change

**Scenario:** Making manual schema changes outside of migrations.

```bash
# 1. Snapshot before changes
export DATABASE_URL="postgresql://user:pass@host:5432/db"
bash scripts/production/pre_deploy_snapshot.sh

# 2. Make schema changes
psql $DATABASE_URL << EOF
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
CREATE INDEX idx_users_phone ON users(phone);
COMMIT;
EOF

# 3. Test application
# If issues found:

# 4. Rollback schema changes
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

## Example 9: Integration Testing with Snapshots

**Scenario:** Run integration tests with clean database state.

```bash
#!/bin/bash
# integration_test.sh

export DATABASE_URL="postgresql://platform_user@localhost:5432/integration_test"

# Create fresh database
dropdb --if-exists integration_test
createdb -O platform_user integration_test

# Take initial snapshot
bash scripts/production/pre_deploy_snapshot.sh

# Run migrations
alembic upgrade head

# Seed test data
python database/seeds/initial_data.py

# Take post-setup snapshot
INITIAL_SNAPSHOT=$(cat /tmp/last_snapshot.txt)

# Run test suite
for test in tests/integration/*.py; do
    echo "Running $test..."
    pytest $test

    # Restore to clean state between tests
    export CONFIRM_RESTORE="yes"
    bash scripts/production/emergency_restore.sh
    alembic upgrade head
    python database/seeds/initial_data.py
done

# Cleanup
dropdb integration_test
```

## Example 10: Monitoring Snapshot Success in CI/CD

**Scenario:** Monitor snapshot creation in deployment pipeline.

```bash
# In deployment script (e.g., .github/workflows/deploy.yml)
#!/bin/bash
set -e

export DATABASE_URL="${PRODUCTION_DATABASE_URL}"

# Create snapshot with error handling
if bash scripts/production/pre_deploy_snapshot.sh; then
    echo "✅ Pre-deployment snapshot created successfully"

    # Send success notification
    curl -X POST https://slack.com/api/chat.postMessage \
        -H "Authorization: Bearer $SLACK_TOKEN" \
        -d "channel=deployments" \
        -d "text=✅ Database snapshot created before deployment"

    # Continue with deployment
    echo "Proceeding with migration..."
    alembic upgrade head
else
    echo "❌ Pre-deployment snapshot failed"

    # Send failure notification
    curl -X POST https://slack.com/api/chat.postMessage \
        -H "Authorization: Bearer $SLACK_TOKEN" \
        -d "channel=deployments" \
        -d "text=❌ Database snapshot FAILED - deployment blocked"

    # Block deployment
    exit 1
fi
```

## Common Patterns

### Pattern 1: Test Migration Locally
```bash
export DATABASE_URL="postgresql://user@localhost:5432/test_db"
bash scripts/production/pre_deploy_snapshot.sh
alembic upgrade head
# Test...
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

### Pattern 2: Production Migration
```bash
# Set in Render.com dashboard:
RUN_MIGRATIONS=true
# Automatic snapshot happens in render-startup.sh
```

### Pattern 3: Emergency Rollback
```bash
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh
```

## Troubleshooting Examples

### Issue: Snapshot too small
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Check for errors
cat /tmp/pg_dump_error.log
```

### Issue: Restore fails
```bash
# Check snapshot integrity
gzip -t /tmp/db_snapshots/pre_migration_*.sql.gz

# Try manual restore
gunzip -c /tmp/db_snapshots/pre_migration_20250930_143022.sql.gz | psql $DATABASE_URL

# Check logs
cat /tmp/restore_output.log
```

## Best Practices

1. **Always test locally first**
   ```bash
   # Test snapshot
   export DATABASE_URL="postgresql://user@localhost:5432/test_db"
   bash scripts/production/pre_deploy_snapshot.sh

   # Test restore
   export CONFIRM_RESTORE="yes"
   bash scripts/production/emergency_restore.sh
   ```

2. **Verify snapshot before proceeding**
   ```bash
   # Check snapshot exists and is valid
   SNAPSHOT=$(cat /tmp/last_snapshot.txt)
   if [ -f "$SNAPSHOT" ] && [ -s "$SNAPSHOT" ]; then
       echo "Snapshot valid, proceeding..."
   else
       echo "Snapshot invalid, aborting!"
       exit 1
   fi
   ```

3. **Keep production rollback plan ready**
   - Document snapshot location
   - Test restore procedure
   - Have emergency contacts ready
   - Monitor deployment logs

---

**For more information:**
- Full documentation: [README.md](README.md)
- Emergency procedures: [EMERGENCY_ROLLBACK.md](EMERGENCY_ROLLBACK.md)
- Implementation details: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
