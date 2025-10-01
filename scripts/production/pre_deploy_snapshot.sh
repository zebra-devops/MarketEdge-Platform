#!/bin/bash
set -e

# Pre-Deployment Database Snapshot Script
# Creates compressed pg_dump snapshot before migrations
# Designed for Render.com and Railway.app PostgreSQL environments

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pre_migration_${TIMESTAMP}.sql"
BACKUP_DIR="${BACKUP_DIR:-/tmp/db_snapshots}"
DATABASE_URL="${DATABASE_URL}"

# Minimum backup size threshold (1KB - ensures backup isn't empty)
MIN_BACKUP_SIZE=1024

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Deployment Database Snapshot${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate DATABASE_URL exists
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable not set${NC}"
    echo -e "${YELLOW}   Set DATABASE_URL to your PostgreSQL connection string${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
echo -e "${BLUE}📁 Backup directory: ${BACKUP_DIR}${NC}"

# Extract database name for verification
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
echo -e "${BLUE}🗄️  Database: ${DB_NAME}${NC}"
echo ""

# Create snapshot
echo -e "${YELLOW}📸 Creating pre-deployment snapshot...${NC}"
echo -e "${BLUE}   Timestamp: ${TIMESTAMP}${NC}"

# Use pg_dump with error handling
# --no-owner: Skip ownership commands (works across different PostgreSQL users)
# --no-acl: Skip access privileges (works across different environments)
# --clean: Include DROP commands for clean restores
# --if-exists: Use IF EXISTS for DROP commands
if pg_dump "$DATABASE_URL" --no-owner --no-acl --clean --if-exists 2>/tmp/pg_dump_error.log | gzip > "${BACKUP_DIR}/${BACKUP_FILE}.gz"; then
    echo -e "${GREEN}✅ pg_dump completed successfully${NC}"
else
    echo -e "${RED}❌ ERROR: pg_dump failed${NC}"
    echo -e "${YELLOW}Error output:${NC}"
    cat /tmp/pg_dump_error.log
    exit 1
fi

# Verify snapshot integrity
echo ""
echo -e "${YELLOW}🔍 Verifying snapshot integrity...${NC}"

# Check if file exists
if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}.gz" ]; then
    echo -e "${RED}❌ ERROR: Snapshot file not created${NC}"
    exit 1
fi

# Check file size
BACKUP_SIZE_BYTES=$(stat -f%z "${BACKUP_DIR}/${BACKUP_FILE}.gz" 2>/dev/null || stat -c%s "${BACKUP_DIR}/${BACKUP_FILE}.gz" 2>/dev/null)
if [ "$BACKUP_SIZE_BYTES" -lt "$MIN_BACKUP_SIZE" ]; then
    echo -e "${RED}❌ ERROR: Snapshot file too small (${BACKUP_SIZE_BYTES} bytes)${NC}"
    echo -e "${YELLOW}   Minimum expected: ${MIN_BACKUP_SIZE} bytes${NC}"
    exit 1
fi

# Convert to human-readable size
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)
echo -e "${GREEN}✅ Snapshot file size: ${BACKUP_SIZE}${NC}"

# Test gzip integrity
if gzip -t "${BACKUP_DIR}/${BACKUP_FILE}.gz" 2>/dev/null; then
    echo -e "${GREEN}✅ Gzip compression integrity verified${NC}"
else
    echo -e "${RED}❌ ERROR: Gzip file corrupted${NC}"
    exit 1
fi

# Store snapshot path for rollback script
echo "${BACKUP_DIR}/${BACKUP_FILE}.gz" > /tmp/last_snapshot.txt
echo -e "${GREEN}✅ Snapshot path stored for emergency restore${NC}"

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Snapshot Created Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}📄 File: ${BACKUP_FILE}.gz${NC}"
echo -e "${BLUE}📁 Location: ${BACKUP_DIR}/${NC}"
echo -e "${BLUE}💾 Size: ${BACKUP_SIZE}${NC}"
echo -e "${BLUE}🕒 Timestamp: ${TIMESTAMP}${NC}"
echo ""
echo -e "${GREEN}✅ Safe to proceed with migrations${NC}"
echo ""

exit 0
