#!/bin/bash
set -e

# Emergency Database Restore Script
# Restores from last pre-deployment snapshot
# USE WITH EXTREME CAUTION IN PRODUCTION

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/tmp/db_snapshots}"
DATABASE_URL="${DATABASE_URL}"
LAST_SNAPSHOT_FILE="/tmp/last_snapshot.txt"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}⚠️  EMERGENCY DATABASE RESTORE${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Validate DATABASE_URL exists
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable not set${NC}"
    echo -e "${YELLOW}   Set DATABASE_URL to your PostgreSQL connection string${NC}"
    exit 1
fi

# Check for explicit confirmation in non-interactive mode
if [ -z "$CONFIRM_RESTORE" ]; then
    echo -e "${YELLOW}🛑 This will OVERWRITE your current database${NC}"
    echo -e "${YELLOW}   All data since the snapshot will be LOST${NC}"
    echo ""
    echo -e "${BLUE}To proceed, set environment variable:${NC}"
    echo -e "${BLUE}   export CONFIRM_RESTORE=yes${NC}"
    echo ""
    exit 1
fi

if [ "$CONFIRM_RESTORE" != "yes" ]; then
    echo -e "${RED}❌ Restore not confirmed (CONFIRM_RESTORE must be 'yes')${NC}"
    exit 1
fi

# Find snapshot to restore
SNAPSHOT_PATH=""

# First, try to read last snapshot path
if [ -f "$LAST_SNAPSHOT_FILE" ]; then
    SNAPSHOT_PATH=$(cat "$LAST_SNAPSHOT_FILE")
    echo -e "${BLUE}📄 Found last snapshot reference: ${SNAPSHOT_PATH}${NC}"
fi

# If no snapshot path or file doesn't exist, try to find most recent
if [ -z "$SNAPSHOT_PATH" ] || [ ! -f "$SNAPSHOT_PATH" ]; then
    echo -e "${YELLOW}⚠️  Last snapshot reference not valid, searching for most recent...${NC}"

    # Find most recent snapshot in backup directory
    if [ -d "$BACKUP_DIR" ]; then
        SNAPSHOT_PATH=$(ls -t "${BACKUP_DIR}"/pre_migration_*.sql.gz 2>/dev/null | head -1)
    fi
fi

# Validate snapshot exists
if [ -z "$SNAPSHOT_PATH" ] || [ ! -f "$SNAPSHOT_PATH" ]; then
    echo -e "${RED}❌ ERROR: No valid snapshot found${NC}"
    echo -e "${YELLOW}   Checked locations:${NC}"
    echo -e "${YELLOW}   - Last snapshot file: ${LAST_SNAPSHOT_FILE}${NC}"
    echo -e "${YELLOW}   - Backup directory: ${BACKUP_DIR}${NC}"
    echo ""
    echo -e "${BLUE}Available snapshots:${NC}"
    ls -lh "${BACKUP_DIR}"/pre_migration_*.sql.gz 2>/dev/null || echo "   (none found)"
    exit 1
fi

# Display snapshot information
SNAPSHOT_SIZE=$(du -h "$SNAPSHOT_PATH" | cut -f1)
SNAPSHOT_NAME=$(basename "$SNAPSHOT_PATH")
echo ""
echo -e "${BLUE}📸 Snapshot to restore:${NC}"
echo -e "${BLUE}   File: ${SNAPSHOT_NAME}${NC}"
echo -e "${BLUE}   Size: ${SNAPSHOT_SIZE}${NC}"
echo -e "${BLUE}   Path: ${SNAPSHOT_PATH}${NC}"
echo ""

# Extract database name
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
echo -e "${BLUE}🗄️  Target database: ${DB_NAME}${NC}"
echo ""

# Perform restore
echo -e "${YELLOW}🔄 Starting database restore...${NC}"
echo -e "${RED}   This will DROP and recreate all tables${NC}"
echo ""

# Decompress and restore with psql
# The snapshot includes --clean and --if-exists flags, so it will drop existing objects
if gunzip -c "$SNAPSHOT_PATH" | psql "$DATABASE_URL" > /tmp/restore_output.log 2>&1; then
    echo -e "${GREEN}✅ Database restore completed successfully${NC}"
else
    echo -e "${RED}❌ ERROR: Database restore failed${NC}"
    echo -e "${YELLOW}Last 20 lines of restore output:${NC}"
    tail -n 20 /tmp/restore_output.log
    echo ""
    echo -e "${YELLOW}Full output saved to: /tmp/restore_output.log${NC}"
    exit 1
fi

# Verify restore
echo ""
echo -e "${YELLOW}🔍 Verifying restore...${NC}"

# Count tables to verify restore worked
TABLE_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Verified: ${TABLE_COUNT} tables restored${NC}"
else
    echo -e "${RED}❌ WARNING: No tables found after restore${NC}"
    exit 1
fi

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restore Completed Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}📸 Snapshot: ${SNAPSHOT_NAME}${NC}"
echo -e "${BLUE}🗄️  Database: ${DB_NAME}${NC}"
echo -e "${BLUE}📊 Tables restored: ${TABLE_COUNT}${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
echo -e "${YELLOW}1. Verify application functionality${NC}"
echo -e "${YELLOW}2. Check for data integrity${NC}"
echo -e "${YELLOW}3. Review restore logs: /tmp/restore_output.log${NC}"
echo -e "${YELLOW}4. Consider re-running seeds if needed${NC}"
echo ""

exit 0
