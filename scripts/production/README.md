# Production Database Snapshot Scripts

Production-ready database backup and restore scripts for protecting against migration failures.

## Overview

These scripts provide automated database snapshots before migrations and emergency restoration capabilities for the MarketEdge Platform.

**Files:**
- `pre_deploy_snapshot.sh` - Creates compressed pg_dump snapshot before migrations
- `emergency_restore.sh` - Restores database from snapshot
- Integrated with `render-startup.sh` for automatic pre-migration snapshots

## Pre-Deployment Snapshot Script

### Purpose
Creates a compressed PostgreSQL dump before running migrations, blocking deployment if snapshot fails to prevent data loss.

### Usage

```bash
# Basic usage
export DATABASE_URL="postgresql://user:password@host:port/database"
bash scripts/production/pre_deploy_snapshot.sh
```

### Features
- Compressed snapshots with gzip (saves disk space)
- Integrity verification (file size, gzip validity)
- Timestamped filenames: `pre_migration_YYYYMMDD_HHMMSS.sql.gz`
- Stores snapshot path for emergency restore
- Exits with error if snapshot fails (blocks deployment)
- Color-coded output for monitoring logs

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `BACKUP_DIR` | No | `/tmp/db_snapshots` | Directory for snapshot storage |

### Output
```
========================================
Pre-Deployment Database Snapshot
========================================

📁 Backup directory: /tmp/db_snapshots
🗄️  Database: marketedge_prod

📸 Creating pre-deployment snapshot...
   Timestamp: 20250930_212207
✅ pg_dump completed successfully

🔍 Verifying snapshot integrity...
✅ Snapshot file size: 24K
✅ Gzip compression integrity verified
✅ Snapshot path stored for emergency restore

========================================
Snapshot Created Successfully
========================================
📄 File: pre_migration_20250930_212207.sql.gz
📁 Location: /tmp/db_snapshots/
💾 Size: 24K
🕒 Timestamp: 20250930_212207

✅ Safe to proceed with migrations
```

### Exit Codes
- `0` - Success (snapshot created and verified)
- `1` - Failure (blocks deployment)

## Emergency Restore Script

### Purpose
Restores database from the last pre-deployment snapshot. **USE WITH EXTREME CAUTION IN PRODUCTION.**

### Usage

```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@host:port/database"
export CONFIRM_RESTORE="yes"  # Required confirmation

# Run restore
bash scripts/production/emergency_restore.sh
```

### Safety Features
- Requires explicit confirmation via `CONFIRM_RESTORE=yes`
- Prevents accidental execution
- Verifies snapshot exists before restore
- Validates restore completed successfully
- Counts restored tables for verification

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `CONFIRM_RESTORE` | Yes | - | Must be "yes" to proceed |
| `BACKUP_DIR` | No | `/tmp/db_snapshots` | Directory where snapshots are stored |

### Output
```
========================================
⚠️  EMERGENCY DATABASE RESTORE
========================================

📄 Found last snapshot reference: /tmp/db_snapshots/pre_migration_20250930_212207.sql.gz

📸 Snapshot to restore:
   File: pre_migration_20250930_212207.sql.gz
   Size: 24K
   Path: /tmp/db_snapshots/pre_migration_20250930_212207.sql.gz

🗄️  Target database: marketedge_prod

🔄 Starting database restore...
   This will DROP and recreate all tables

✅ Database restore completed successfully

🔍 Verifying restore...
✅ Verified: 36 tables restored

========================================
Restore Completed Successfully
========================================
📸 Snapshot: pre_migration_20250930_212207.sql.gz
🗄️  Database: marketedge_prod
📊 Tables restored: 36

⚠️  IMPORTANT NEXT STEPS:
1. Verify application functionality
2. Check for data integrity
3. Review restore logs: /tmp/restore_output.log
4. Consider re-running seeds if needed
```

### Exit Codes
- `0` - Success (database restored)
- `1` - Failure (confirmation missing, snapshot not found, or restore failed)

## Integration with render-startup.sh

The pre-deployment snapshot is automatically executed when `RUN_MIGRATIONS=true`:

```bash
# In render-startup.sh
if [ "$RUN_MIGRATIONS" = "true" ]; then
    # Take snapshot before any changes
    if bash scripts/production/pre_deploy_snapshot.sh; then
        echo "✅ Pre-deployment snapshot created successfully"
    else
        echo "❌ CRITICAL: Pre-deployment snapshot failed"
        echo "🛑 Blocking migration to prevent data loss"
        exit 1
    fi

    # Proceed with migrations...
fi
```

## Testing Locally

### Test Snapshot Creation

```bash
# Use local database
export DATABASE_URL="postgresql://platform_user@localhost:5432/platform_wrapper"
bash scripts/production/pre_deploy_snapshot.sh

# Verify snapshot created
ls -lh /tmp/db_snapshots/
cat /tmp/last_snapshot.txt
```

### Test Emergency Restore

```bash
# Create test database
createdb -O platform_user snapshot_restore_test

# Restore to test database
export DATABASE_URL="postgresql://platform_user@localhost:5432/snapshot_restore_test"
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh

# Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Clean up
dropdb snapshot_restore_test
```

## Production Deployment Workflow

### Normal Deployment (No Migrations)
```bash
# Render.com automatically runs render-startup.sh
# No snapshot taken if RUN_MIGRATIONS != "true"
```

### Emergency Migration Deployment
```bash
# Set environment variable in Render.com dashboard
RUN_MIGRATIONS=true

# Automatic workflow:
# 1. render-startup.sh executes
# 2. pre_deploy_snapshot.sh creates snapshot
# 3. If snapshot succeeds -> migrations run
# 4. If snapshot fails -> deployment blocked
```

### Emergency Rollback
```bash
# SSH into Render.com instance
# Or use Render.com shell

# Set confirmation and restore
export CONFIRM_RESTORE="yes"
bash scripts/production/emergency_restore.sh

# Verify application health
curl https://marketedge-platform.onrender.com/health

# If needed, re-run seeds
python database/seeds/initial_data.py
python database/seeds/phase3_data.py
```

## Platform Compatibility

### Render.com
- Ubuntu/Debian environment
- PostgreSQL via DATABASE_URL
- Snapshots stored in `/tmp/db_snapshots`
- Persists during deployment (lost on rebuild)

### Railway.app
- Compatible with Railway PostgreSQL
- Same environment variables
- Works with Railway shell access

### Local Development
- macOS/Linux/WSL
- Requires PostgreSQL client tools (pg_dump, psql)
- Tested on macOS with Homebrew PostgreSQL

## Snapshot Retention

**Important:** Snapshots are stored in `/tmp/db_snapshots` which is ephemeral on most cloud platforms.

**Retention Strategy:**
- Snapshots persist during deployment
- Lost on platform rebuild/restart
- For long-term backups, use platform-specific backup solutions:
  - Render.com: PostgreSQL backups dashboard
  - Railway.app: Automated daily backups
  - AWS RDS: Automated snapshot retention

## Troubleshooting

### Snapshot Creation Fails

**Error:** `pg_dump failed`
```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Check disk space
df -h /tmp
```

**Error:** `Snapshot file too small`
```bash
# Database might be empty or connection failed
# Check for errors in /tmp/pg_dump_error.log
cat /tmp/pg_dump_error.log
```

### Restore Fails

**Error:** `No valid snapshot found`
```bash
# List available snapshots
ls -lh /tmp/db_snapshots/

# Check last snapshot reference
cat /tmp/last_snapshot.txt

# Manually specify snapshot
export SNAPSHOT_PATH="/tmp/db_snapshots/pre_migration_20250930_212207.sql.gz"
```

**Error:** `Database restore failed`
```bash
# Check restore logs
cat /tmp/restore_output.log

# Verify database exists and is accessible
psql $DATABASE_URL -c "SELECT 1;"
```

## Security Considerations

1. **Database Credentials**: Never commit DATABASE_URL to git
2. **Snapshot Contents**: Snapshots contain full database data (PII, credentials)
3. **Access Control**: Restrict script execution to authorized personnel
4. **Confirmation Required**: Restore requires explicit CONFIRM_RESTORE=yes
5. **Audit Trail**: All restore operations logged to /tmp/restore_output.log

## Best Practices

1. **Always snapshot before migrations**: Automated in render-startup.sh
2. **Verify snapshot success**: Check exit code before proceeding
3. **Test restore locally**: Validate process before production emergency
4. **Monitor disk space**: Snapshots consume storage
5. **Document rollback decisions**: Create incident reports for auditing

## Related Documentation

- [CLAUDE.md](/Users/matt/Sites/MarketEdge/CLAUDE.md) - Database migration patterns
- [Database Migrations](/Users/matt/Sites/MarketEdge/database/migrations/) - Alembic migrations
- [Emergency Procedures](/Users/matt/Sites/MarketEdge/CLAUDE.md#emergency-procedures) - Production issue protocols

## Support

For issues or questions:
1. Review troubleshooting section above
2. Check Render.com deployment logs
3. Verify PostgreSQL connection and permissions
4. Contact platform administrator
