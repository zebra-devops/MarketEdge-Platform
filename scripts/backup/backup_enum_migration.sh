#!/bin/bash
# Backup script for enum migration safety (US-6A)
# Creates comprehensive backup before executing uppercase enum migration

set -euo pipefail  # Exit on error, undefined variable, and pipe failures

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/enum_migration_${TIMESTAMP}"
S3_BUCKET="${S3_BACKUP_BUCKET:-s3://backups/marketedge}"
DATABASE_URL="${DATABASE_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Security: Sanitize database error output to prevent credential exposure
sanitize_db_error() {
    sed -E 's/(password|pwd)=([^ ]+)/\1=***/g; s/postgresql:\/\/[^:]+:[^@]+@/postgresql:\/\/***:***@/g'
}

# Security: Sanitize AWS CLI output to prevent key exposure
sanitize_aws_error() {
    grep -vE '(AccessKeyId|SecretAccessKey|SessionToken)' | \
    sed -E 's/AKIA[A-Z0-9]{16}/***ACCESS_KEY***/g'
}

# Security: Redact database URL credentials completely
redact_database_url() {
    echo "${1}" | sed -E 's/postgresql:\/\/[^:]+:[^@]+@/postgresql:\/\/***:***@/g'
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable not set"
        exit 1
    fi

    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi

    if ! command -v aws &> /dev/null; then
        log_warn "AWS CLI not found. S3 upload will be skipped."
    fi

    log_info "Prerequisites check passed"
}

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"
}

# Backup user_application_access table
backup_user_application_access() {
    log_info "Backing up user_application_access table..."

    local backup_file="${BACKUP_DIR}/user_application_access.sql"

    pg_dump "${DATABASE_URL}" \
        --table=user_application_access \
        --clean \
        --if-exists \
        --create \
        --verbose \
        > "${backup_file}" 2> >(sanitize_db_error >&2)

    if [ $? -eq 0 ]; then
        log_info "Table backup completed: ${backup_file}"

        # Get row count
        local row_count=$(grep -c "INSERT INTO" "${backup_file}" || echo "0")
        log_info "Backed up ${row_count} rows from user_application_access"
    else
        log_error "Table backup failed"
        exit 1
    fi
}

# Backup user_invitations table
backup_user_invitations() {
    log_info "Backing up user_invitations table..."

    local backup_file="${BACKUP_DIR}/user_invitations.sql"

    pg_dump "${DATABASE_URL}" \
        --table=user_invitations \
        --clean \
        --if-exists \
        --create \
        --verbose \
        > "${backup_file}" 2> >(sanitize_db_error >&2)

    if [ $? -eq 0 ]; then
        log_info "Table backup completed: ${backup_file}"
    else
        log_error "Table backup failed"
        exit 1
    fi
}

# Backup enum types
backup_enum_types() {
    log_info "Backing up enum types..."

    local backup_file="${BACKUP_DIR}/enum_types.sql"

    # Extract enum type definitions
    psql "${DATABASE_URL}" -t -c "
        SELECT
            'CREATE TYPE ' || t.typname || ' AS ENUM (' ||
            string_agg(quote_literal(e.enumlabel), ', ' ORDER BY e.enumsortorder) || ');'
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname IN ('applicationtype', 'invitationstatus')
        GROUP BY t.typname;
    " > "${backup_file}" 2> >(sanitize_db_error >&2)

    log_info "Enum types backed up: ${backup_file}"
}

# Backup indexes and constraints
backup_indexes_and_constraints() {
    log_info "Backing up indexes and constraints..."

    local backup_file="${BACKUP_DIR}/indexes_and_constraints.sql"

    pg_dump "${DATABASE_URL}" \
        --table=user_application_access \
        --table=user_invitations \
        --schema-only \
        --verbose \
        > "${backup_file}" 2> >(sanitize_db_error >&2)

    log_info "Indexes and constraints backed up: ${backup_file}"
}

# Get table statistics
get_table_statistics() {
    log_info "Gathering table statistics..."

    local stats_file="${BACKUP_DIR}/statistics.txt"
    local database_url_redacted=$(redact_database_url "${DATABASE_URL}")

    cat > "${stats_file}" <<EOF
Backup Statistics
==================
Timestamp: ${TIMESTAMP}
Database: ${database_url_redacted}

Table: user_application_access
-------------------------------
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT application) as unique_applications
        FROM user_application_access;
    " >> "${stats_file}" 2> >(sanitize_db_error >&2)

    cat >> "${stats_file}" <<EOF

Application Value Distribution:
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT application, COUNT(*) as count
        FROM user_application_access
        GROUP BY application
        ORDER BY count DESC;
    " >> "${stats_file}" 2> >(sanitize_db_error >&2)

    cat >> "${stats_file}" <<EOF

Table: user_invitations
-----------------------
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT
            COUNT(*) as total_invitations,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT status) as unique_statuses
        FROM user_invitations;
    " >> "${stats_file}" 2> >(sanitize_db_error >&2)

    log_info "Statistics saved: ${stats_file}"
    cat "${stats_file}"
}

# Create manifest file
create_manifest() {
    log_info "Creating backup manifest..."

    local manifest_file="${BACKUP_DIR}/MANIFEST.txt"

    cat > "${manifest_file}" <<EOF
MarketEdge Enum Migration Backup Manifest
==========================================

Backup ID: enum_migration_${TIMESTAMP}
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Purpose: Safety backup before US-6 uppercase enum migration

Files Included:
---------------
1. user_application_access.sql - Full table backup with data
2. user_invitations.sql - Full table backup with data
3. enum_types.sql - Enum type definitions (applicationtype, invitationstatus)
4. indexes_and_constraints.sql - Index and constraint definitions
5. statistics.txt - Pre-migration table statistics
6. MANIFEST.txt - This file

Restore Procedure:
------------------
See docs/auth/rollback-enum-migration.md for detailed restore instructions.

Quick Restore:
1. cd ${BACKUP_DIR}
2. psql \$DATABASE_URL < user_application_access.sql
3. psql \$DATABASE_URL < user_invitations.sql
4. Verify row counts match statistics.txt

Migration Rollback:
-------------------
If migration has been applied, run downgrade first:
1. alembic downgrade -1
2. Follow restore procedure above
3. Verify application values are lowercase

Verification Commands:
----------------------
# Check row counts
psql \$DATABASE_URL -c "SELECT COUNT(*) FROM user_application_access;"

# Check enum values
psql \$DATABASE_URL -c "SELECT DISTINCT application FROM user_application_access;"

# Check foreign key integrity
psql \$DATABASE_URL -c "
    SELECT
        conname,
        conrelid::regclass,
        confrelid::regclass
    FROM pg_constraint
    WHERE conrelid IN ('user_application_access'::regclass, 'user_invitations'::regclass);
"

Backup Validation:
------------------
EOF

    # Add file sizes
    ls -lh "${BACKUP_DIR}" | tail -n +2 >> "${manifest_file}"

    log_info "Manifest created: ${manifest_file}"
}

# Validate backup integrity
validate_backup() {
    log_info "Validating backup integrity..."

    local validation_file="${BACKUP_DIR}/validation.log"

    # Check all expected files exist
    local required_files=(
        "user_application_access.sql"
        "user_invitations.sql"
        "enum_types.sql"
        "indexes_and_constraints.sql"
        "statistics.txt"
        "MANIFEST.txt"
    )

    local all_files_exist=true
    for file in "${required_files[@]}"; do
        if [ ! -f "${BACKUP_DIR}/${file}" ]; then
            log_error "Missing required backup file: ${file}"
            all_files_exist=false
        fi
    done

    if [ "$all_files_exist" = false ]; then
        log_error "Backup validation failed: missing files"
        exit 1
    fi

    # Check file sizes
    local min_size=100  # minimum 100 bytes
    for file in "${required_files[@]}"; do
        local size=$(wc -c < "${BACKUP_DIR}/${file}")
        if [ "$size" -lt "$min_size" ]; then
            log_error "File ${file} is suspiciously small (${size} bytes)"
            all_files_exist=false
        fi
    done

    if [ "$all_files_exist" = false ]; then
        log_error "Backup validation failed: files too small"
        exit 1
    fi

    log_info "Backup validation passed"
    echo "Validation completed at $(date)" > "${validation_file}"
}

# Upload to S3 (if AWS CLI available)
upload_to_s3() {
    if command -v aws &> /dev/null; then
        log_info "Uploading backup to S3..."

        local s3_path="${S3_BUCKET}/$(date +%Y-%m-%d)/enum_migration_${TIMESTAMP}/"

        # Security: Sanitize AWS CLI output to prevent credential exposure
        if aws s3 cp "${BACKUP_DIR}" "${s3_path}" --recursive 2>&1 | sanitize_aws_error; then
            log_info "Backup uploaded to: ${s3_path}"
            echo "S3 Location: ${s3_path}" >> "${BACKUP_DIR}/MANIFEST.txt"
        else
            log_warn "S3 upload failed, but local backup is available"
        fi
    else
        log_warn "Skipping S3 upload (AWS CLI not available)"
    fi
}

# Create compressed archive
create_archive() {
    log_info "Creating compressed archive..."

    local archive_file="enum_migration_${TIMESTAMP}.tar.gz"

    tar -czf "${archive_file}" -C "$(dirname "${BACKUP_DIR}")" "$(basename "${BACKUP_DIR}")"

    if [ $? -eq 0 ]; then
        log_info "Archive created: ${archive_file}"
        log_info "Archive size: $(du -h "${archive_file}" | cut -f1)"
    else
        log_error "Archive creation failed"
        exit 1
    fi
}

# Main execution
main() {
    log_info "Starting enum migration backup (US-6A)"
    log_info "================================================"

    check_prerequisites
    create_backup_dir
    backup_user_application_access
    backup_user_invitations
    backup_enum_types
    backup_indexes_and_constraints
    get_table_statistics
    create_manifest
    validate_backup
    upload_to_s3
    create_archive

    log_info "================================================"
    log_info "Backup completed successfully!"
    log_info "Backup location: ${BACKUP_DIR}"
    log_info "Archive: enum_migration_${TIMESTAMP}.tar.gz"
    log_info ""
    log_info "Next steps:"
    log_info "1. Review docs/auth/rollback-enum-migration.md"
    log_info "2. Test migration on staging with this backup"
    log_info "3. Verify rollback procedure works"
    log_info "4. Proceed with US-6 migration"
}

# Run main function
main
