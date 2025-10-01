# Rollback Procedure: Enum Migration (US-6A)

## Overview

This document describes the complete rollback procedure for the ApplicationType enum migration (US-6 to US-6A). The migration changes enum values from lowercase (`market_edge`, `causal_edge`, `value_edge`) to uppercase (`MARKET_EDGE`, `CAUSAL_EDGE`, `VALUE_EDGE`).

**Critical**: This procedure must be reviewed and tested before executing the US-6 migration in production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backup Procedure](#backup-procedure)
3. [Rollback Scenarios](#rollback-scenarios)
4. [Rollback Execution](#rollback-execution)
5. [Verification Steps](#verification-steps)
6. [Recovery Time Objectives](#recovery-time-objectives)
7. [Emergency Contacts](#emergency-contacts)

## Prerequisites

### Required Tools

- PostgreSQL client tools (`psql`, `pg_dump`)
- AWS CLI (for S3 backup/restore)
- Access to production database
- Access to S3 backup bucket: `s3://backups/marketedge/`

### Required Access

- Database superuser or owner of affected tables
- S3 bucket read/write permissions
- Alembic migration access

### Environment Variables

```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
export S3_BACKUP_BUCKET="s3://backups/marketedge"
```

## Backup Procedure

### 1. Execute Backup Script

Before any migration, create a complete backup:

```bash
cd /Users/matt/Sites/MarketEdge
./scripts/backup/backup_enum_migration.sh
```

**Expected Output:**
```
[INFO] Starting enum migration backup (US-6A)
[INFO] Checking prerequisites...
[INFO] Creating backup directory: ./backups/enum_migration_YYYYMMDD_HHMMSS
[INFO] Backing up user_application_access table...
[INFO] Backed up N rows from user_application_access
[INFO] Backup completed successfully!
```

### 2. Verify Backup Integrity

Check that all required files are present:

```bash
BACKUP_DIR=./backups/enum_migration_YYYYMMDD_HHMMSS
ls -lh ${BACKUP_DIR}/

# Expected files:
# - user_application_access.sql
# - user_invitations.sql
# - enum_types.sql
# - indexes_and_constraints.sql
# - statistics.txt
# - MANIFEST.txt
# - validation.log
```

### 3. Test Backup Restore (Staging)

**CRITICAL**: Always test restore on staging before production deployment:

```bash
# Use staging database
export DATABASE_URL="postgresql://staging-url"

# Test restore
./scripts/backup/restore_enum_migration.sh ${BACKUP_DIR}

# Verify row counts match
cat ${BACKUP_DIR}/restore_verification.txt
```

### 4. Store Backup in S3

Backup is automatically uploaded to S3 by the backup script:

```bash
# Verify S3 upload
aws s3 ls s3://backups/marketedge/$(date +%Y-%m-%d)/

# Manual upload (if needed)
aws s3 cp ${BACKUP_DIR} \
  s3://backups/marketedge/$(date +%Y-%m-%d)/enum_migration_YYYYMMDD_HHMMSS/ \
  --recursive
```

## Rollback Scenarios

### Scenario A: Migration Not Yet Applied

**Situation**: Migration files created but not executed

**Action**: No rollback needed, simply don't execute the migration

**Steps**:
1. Review migration file
2. Decide to delay or cancel
3. Delete migration file if cancelling permanently

### Scenario B: Migration Applied, Issues Detected Immediately

**Situation**: Migration executed, issues found within minutes

**RTO**: < 5 minutes

**Steps**:
1. Execute Alembic downgrade
2. Verify enum values reverted
3. Test application access

**Commands**:
```bash
# Downgrade migration
alembic downgrade -1

# Verify enum values
psql ${DATABASE_URL} -c "SELECT DISTINCT application FROM user_application_access;"

# Expected output: market_edge, causal_edge, value_edge (lowercase)
```

### Scenario C: Migration Applied, Data Corruption Detected

**Situation**: Migration completed but data integrity compromised

**RTO**: < 10 minutes

**Steps**:
1. Execute Alembic downgrade
2. Restore from backup
3. Verify data integrity

**Commands**:
```bash
# 1. Downgrade migration
alembic downgrade -1

# 2. Restore from backup
export DATABASE_URL="postgresql://production-url"
./scripts/backup/restore_enum_migration.sh ${BACKUP_DIR}

# 3. Verify restoration
psql ${DATABASE_URL} -c "SELECT COUNT(*) FROM user_application_access;"
```

### Scenario D: Migration Applied Hours Ago, Issues Found

**Situation**: Migration successful but breaking changes discovered later

**RTO**: < 15 minutes

**Considerations**:
- New data may have been inserted
- Need to preserve post-migration changes

**Steps**:
1. Create current state backup
2. Identify changes since migration
3. Execute restore with data merge
4. Reapply post-migration changes

**Commands**:
```bash
# 1. Backup current state
./scripts/backup/backup_enum_migration.sh

# 2. Restore original backup
./scripts/backup/restore_enum_migration.sh ${ORIGINAL_BACKUP_DIR}

# 3. Manual merge of new records (if any)
# This requires custom SQL based on specific situation
```

## Rollback Execution

### Step-by-Step Rollback (Scenario B - Standard)

#### 1. Announce Maintenance Window

```bash
# Post to status page
curl -X POST https://status.marketedge.com/api/incidents \
  -d "status=investigating" \
  -d "message=Database rollback in progress"
```

#### 2. Stop Application Traffic (Optional)

```bash
# If using load balancer, drain connections
# Or set application to maintenance mode
```

#### 3. Execute Alembic Downgrade

```bash
cd /Users/matt/Sites/MarketEdge

# Check current migration
alembic current

# Downgrade one version
alembic downgrade -1

# Expected output:
# INFO  [alembic.runtime.migration] Running downgrade ... -> ...
# INFO  [alembic.runtime.migration] Downgrade complete
```

**Timing**: ~30-60 seconds (depending on data volume)

#### 4. Verify Enum Values Reverted

```bash
psql ${DATABASE_URL} <<EOF
-- Check enum values
SELECT DISTINCT application FROM user_application_access;

-- Expected: market_edge, causal_edge, value_edge (lowercase)

-- Check row counts
SELECT COUNT(*) FROM user_application_access;
EOF
```

#### 5. Test Application Access

```bash
# Test Zebra Associates login
curl -X POST https://api.marketedge.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "matt.lindop@zebra.associates", "password": "***"}'

# Verify applications in response
# Expected: ["market_edge", "causal_edge", "value_edge"] (lowercase)
```

#### 6. Restore Application Traffic

```bash
# Remove maintenance mode
# Or restore load balancer traffic
```

#### 7. Monitor for Issues

```bash
# Check error logs
tail -f /var/log/marketedge/app.log

# Check Auth0 dashboard
# Verify no "Invalid Token" errors

# Check Sentry
# Verify no new errors related to application access
```

### Step-by-Step Rollback (Scenario C - Data Corruption)

#### 1. Execute Alembic Downgrade

```bash
alembic downgrade -1
```

#### 2. Restore from Backup

```bash
# Set backup directory
BACKUP_DIR=./backups/enum_migration_YYYYMMDD_HHMMSS

# Execute restore script
./scripts/backup/restore_enum_migration.sh ${BACKUP_DIR}

# Wait for completion (estimated time: 1-2 minutes)
```

#### 3. Verify Data Integrity

```bash
# Compare row counts
BACKUP_COUNT=$(grep "total_rows" ${BACKUP_DIR}/statistics.txt | tail -1)
CURRENT_COUNT=$(psql ${DATABASE_URL} -t -c "SELECT COUNT(*) FROM user_application_access;")

echo "Backup count: ${BACKUP_COUNT}"
echo "Current count: ${CURRENT_COUNT}"

# Check foreign key integrity
psql ${DATABASE_URL} -c "
    SELECT COUNT(*)
    FROM user_application_access uaa
    LEFT JOIN users u ON uaa.user_id = u.id
    WHERE u.id IS NULL;
"

# Expected: 0 (no orphaned records)
```

#### 4. Test Application Functionality

```bash
# Run smoke test
pytest tests/test_auth_smoke.py -v

# Expected: All tests pass

# Test Zebra Associates access
pytest tests/test_zebra_associates.py -v
```

## Verification Steps

### 1. Database Verification

```sql
-- Check enum type definition
SELECT
    t.typname,
    string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder)
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
WHERE t.typname = 'applicationtype'
GROUP BY t.typname;

-- Expected: market_edge, causal_edge, value_edge

-- Check data distribution
SELECT application, COUNT(*) as count
FROM user_application_access
GROUP BY application
ORDER BY count DESC;

-- Verify foreign keys
SELECT
    conname,
    conrelid::regclass,
    confrelid::regclass
FROM pg_constraint
WHERE conrelid = 'user_application_access'::regclass
AND contype = 'f';

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_application_access';
```

### 2. Application Verification

```bash
# Test login flow
curl -X POST https://api.marketedge.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "matt.lindop@zebra.associates",
    "password": "***"
  }'

# Verify token payload
# Should contain: applications: ["market_edge", "causal_edge", "value_edge"]

# Test /auth/me endpoint
curl -X GET https://api.marketedge.com/api/v1/auth/me \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Verify has_access: true for all applications
```

### 3. Auth0 Verification

```bash
# Check Auth0 logs
# Go to: https://manage.auth0.com/dashboard/.../logs

# Verify no errors:
# - "Invalid Token"
# - "Invalid Signature"
# - "Unauthorized"

# Check token payload size
# Go to: Auth0 Dashboard > APIs > MarketEdge API > Settings
# Verify: Token payload < 3.5 KB
```

### 4. End-to-End Verification

```bash
# Run full test suite
pytest tests/ -v

# Run Cypress tests
cd platform-wrapper/frontend
npm run test:e2e

# Verify Zebra Associates smoke test
pytest tests/test_zebra_smoke.py -v
```

## Recovery Time Objectives

### RTO (Recovery Time Objective)

| Scenario | RTO | Steps |
|----------|-----|-------|
| A: Migration not applied | 0 minutes | No action needed |
| B: Immediate issues | < 5 minutes | Alembic downgrade only |
| C: Data corruption | < 10 minutes | Downgrade + restore |
| D: Delayed detection | < 15 minutes | Backup + restore + merge |

### RPO (Recovery Point Objective)

| Scenario | RPO | Data Loss |
|----------|-----|-----------|
| A: Migration not applied | 0 | None |
| B: Immediate issues | < 1 minute | Minimal (during migration) |
| C: Data corruption | 0 | None (full restore) |
| D: Delayed detection | Variable | Depends on merge strategy |

### Measured Timings (Based on Testing)

**Staging Environment** (1000 rows):
- Backup creation: ~5 seconds
- Migration execution: ~30 seconds
- Downgrade execution: ~30 seconds
- Full restore: ~45 seconds
- Verification: ~15 seconds

**Production Estimate** (10,000 rows):
- Backup creation: ~30 seconds
- Migration execution: ~90 seconds
- Downgrade execution: ~90 seconds
- Full restore: ~2 minutes
- Verification: ~30 seconds

## Emergency Contacts

### Primary Contacts

**Database Administrator**
- Name: [DBA Name]
- Email: dba@marketedge.com
- Phone: +44 XXX XXX XXXX
- Available: 24/7

**Backend Lead**
- Name: [Backend Lead]
- Email: backend@marketedge.com
- Phone: +44 XXX XXX XXXX
- Available: Business hours + on-call

**DevOps Engineer**
- Name: [DevOps Name]
- Email: devops@marketedge.com
- Phone: +44 XXX XXX XXXX
- Available: 24/7

### Escalation Path

1. **Level 1** (0-5 minutes): Backend engineer attempts rollback
2. **Level 2** (5-10 minutes): DBA consulted for data integrity
3. **Level 3** (10-15 minutes): CTO notified, full team engaged
4. **Level 4** (15+ minutes): Customer notification, status page update

### Communication Channels

- **Slack**: #incidents channel
- **PagerDuty**: marketedge-database alerts
- **Status Page**: https://status.marketedge.com
- **Email**: incidents@marketedge.com

## Post-Rollback Actions

### Immediate Actions (Within 1 Hour)

1. **Document the incident**
   - What went wrong?
   - When was it detected?
   - What was the impact?
   - How was it resolved?

2. **Update stakeholders**
   - Internal team notification
   - Customer communication (if impacted)
   - Status page update

3. **Preserve evidence**
   - Save error logs
   - Capture screenshots
   - Export metrics/monitoring data

### Short-term Actions (Within 24 Hours)

1. **Root cause analysis**
   - Why did the migration fail?
   - What was missed in testing?
   - Could it have been prevented?

2. **Update procedures**
   - Improve rollback documentation
   - Add additional safety checks
   - Update testing procedures

3. **Plan remediation**
   - Fix underlying issues
   - Retest migration on staging
   - Schedule new deployment

### Long-term Actions (Within 1 Week)

1. **Post-mortem meeting**
   - Full team review
   - Lessons learned
   - Action items assigned

2. **Process improvements**
   - Update deployment checklist
   - Enhance monitoring/alerts
   - Improve testing coverage

3. **Knowledge sharing**
   - Document findings
   - Share with team
   - Update runbooks

## Related Documentation

- [US-6: Uppercase Enum Migration](https://github.com/zebra-devops/MarketEdge-Platform/issues/43)
- [US-6A: Enum Migration Safety](https://github.com/zebra-devops/MarketEdge-Platform/issues/42)
- [Database Migration Guide](../database/migration-guide.md)
- [Backup and Restore Procedures](../operations/backup-restore.md)
- [Incident Response Playbook](../operations/incident-response.md)

## Appendix

### A. Manual Downgrade SQL (If Alembic Fails)

If Alembic downgrade fails, execute this SQL manually:

```sql
-- Start transaction
BEGIN;

-- Create backup of current state
CREATE TABLE user_application_access_backup AS
SELECT * FROM user_application_access;

-- Drop and recreate enum with lowercase values
ALTER TABLE user_application_access
  ALTER COLUMN application TYPE VARCHAR(50);

DROP TYPE applicationtype;

CREATE TYPE applicationtype AS ENUM (
    'market_edge',
    'causal_edge',
    'value_edge'
);

-- Update values to lowercase
UPDATE user_application_access
SET application = LOWER(application);

-- Convert back to enum
ALTER TABLE user_application_access
  ALTER COLUMN application TYPE applicationtype
  USING application::applicationtype;

-- Verify conversion
SELECT DISTINCT application FROM user_application_access;

-- If everything looks good, commit
COMMIT;

-- Otherwise, rollback
-- ROLLBACK;
```

### B. Quick Reference Commands

```bash
# Check current migration
alembic current

# Downgrade one version
alembic downgrade -1

# Restore from backup
./scripts/backup/restore_enum_migration.sh <backup_dir>

# Verify enum values
psql $DATABASE_URL -c "SELECT DISTINCT application FROM user_application_access;"

# Check row count
psql $DATABASE_URL -c "SELECT COUNT(*) FROM user_application_access;"

# Test Zebra login
pytest tests/test_zebra_smoke.py -v

# Check Auth0 logs
open https://manage.auth0.com/dashboard/
```

### C. Backup Location Reference

**Local Backups**:
- Location: `./backups/enum_migration_YYYYMMDD_HHMMSS/`
- Format: Uncompressed SQL files
- Retention: 7 days

**S3 Backups**:
- Location: `s3://backups/marketedge/YYYY-MM-DD/enum_migration_YYYYMMDD_HHMMSS/`
- Format: Compressed tar.gz archives
- Retention: 30 days

**Backup Files**:
1. `user_application_access.sql` - Table data and schema
2. `user_invitations.sql` - Related table data
3. `enum_types.sql` - Enum type definitions
4. `indexes_and_constraints.sql` - Index and FK definitions
5. `statistics.txt` - Pre-migration statistics
6. `MANIFEST.txt` - Backup metadata and instructions

---

**Document Version**: 1.0
**Last Updated**: 2025-10-01
**Owner**: Database Team
**Review Schedule**: Before each migration deployment
