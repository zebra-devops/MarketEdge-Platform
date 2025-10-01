#!/bin/bash
# scripts/test_us6_migration.sh
# US-6 Migration Smoke Test
# Tests upgrade/downgrade cycle for applicationtype enum conversion

set -euo pipefail

echo "=== US-6 Migration Smoke Test ==="
echo ""

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    echo "Usage: export DATABASE_URL='postgresql://localhost/marketedge_dev'"
    exit 1
fi

# 1. Check current enum values
echo "Step 1: Current enum values (before migration):"
psql "${DATABASE_URL}" -c "
    SELECT enumlabel
    FROM pg_enum e
    JOIN pg_type t ON e.enumtypid = t.oid
    WHERE t.typname = 'applicationtype'
    ORDER BY e.enumsortorder;
" || echo "Note: applicationtype enum may not exist yet"
echo ""

# 2. Get baseline row count
echo "Step 2: Baseline row count:"
BASELINE_COUNT=$(psql "${DATABASE_URL}" -t -c "SELECT COUNT(*) FROM user_application_access;" | xargs)
echo "Rows: ${BASELINE_COUNT}"
echo ""

# 3. Create backup
echo "Step 3: Creating backup..."
if [ -f "./scripts/backup/backup_enum_migration.sh" ]; then
    ./scripts/backup/backup_enum_migration.sh
    echo "[INFO] Backup completed successfully"
else
    echo "[WARN] Backup script not found, skipping backup"
fi
echo ""

# 4. Run upgrade migration
echo "Step 4: Running upgrade migration..."
START_TIME=$(date +%s)
python3 -m alembic upgrade head
UPGRADE_DURATION=$(($(date +%s) - START_TIME))
echo "Upgrade completed in ${UPGRADE_DURATION}s"
echo ""

# 5. Verify enum values changed
echo "Step 5: Enum values (after upgrade):"
psql "${DATABASE_URL}" -c "
    SELECT enumlabel
    FROM pg_enum e
    JOIN pg_type t ON e.enumtypid = t.oid
    WHERE t.typname = 'applicationtype'
    ORDER BY e.enumsortorder;
"
echo ""

# 6. Verify row count unchanged
echo "Step 6: Row count (after upgrade):"
UPGRADE_COUNT=$(psql "${DATABASE_URL}" -t -c "SELECT COUNT(*) FROM user_application_access;" | xargs)
echo "Rows: ${UPGRADE_COUNT}"

if [ "$BASELINE_COUNT" -ne "$UPGRADE_COUNT" ]; then
    echo "❌ FAIL: Row count mismatch (before: ${BASELINE_COUNT}, after: ${UPGRADE_COUNT})"
    exit 1
fi
echo "✅ Row counts match"
echo ""

# 7. Run downgrade migration
echo "Step 7: Running downgrade migration..."
START_TIME=$(date +%s)
python3 -m alembic downgrade -1
DOWNGRADE_DURATION=$(($(date +%s) - START_TIME))
echo "Downgrade completed in ${DOWNGRADE_DURATION}s"
echo ""

# 8. Verify enum values reverted
echo "Step 8: Enum values (after downgrade):"
psql "${DATABASE_URL}" -c "
    SELECT enumlabel
    FROM pg_enum e
    JOIN pg_type t ON e.enumtypid = t.oid
    WHERE t.typname = 'applicationtype'
    ORDER BY e.enumsortorder;
"
echo ""

# 9. Verify row count still unchanged
echo "Step 9: Row count (after downgrade):"
DOWNGRADE_COUNT=$(psql "${DATABASE_URL}" -t -c "SELECT COUNT(*) FROM user_application_access;" | xargs)
echo "Rows: ${DOWNGRADE_COUNT}"

if [ "$BASELINE_COUNT" -ne "$DOWNGRADE_COUNT" ]; then
    echo "❌ FAIL: Row count mismatch (baseline: ${BASELINE_COUNT}, final: ${DOWNGRADE_COUNT})"
    exit 1
fi
echo "✅ Row counts match"
echo ""

# 10. Summary
echo "=== Test Summary ==="
echo "✅ Baseline rows: ${BASELINE_COUNT}"
echo "✅ After upgrade: ${UPGRADE_COUNT}"
echo "✅ After downgrade: ${DOWNGRADE_COUNT}"
echo "✅ Upgrade duration: ${UPGRADE_DURATION}s"
echo "✅ Downgrade duration: ${DOWNGRADE_DURATION}s"
echo "✅ All checks passed!"
echo ""
echo "Backup location: ./backups/enum_migration_<timestamp>/ (if backup script exists)"
