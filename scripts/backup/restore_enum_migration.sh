#!/bin/bash
# Restore script for enum migration rollback (US-6A)
# Restores database state from backup created by backup_enum_migration.sh

set -euo pipefail  # Exit on error, undefined variable, and pipe failures

# Configuration
BACKUP_DIR="${1:-}"
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

# Security: Redact database URL credentials completely
redact_database_url() {
    echo "${1}" | sed -E 's/postgresql:\/\/[^:]+:[^@]+@/postgresql:\/\/***:***@/g'
}

# Usage
usage() {
    cat <<EOF
Usage: $0 <backup_directory>

Restore database from enum migration backup.

Arguments:
  backup_directory    Path to backup directory created by backup_enum_migration.sh

Environment Variables:
  DATABASE_URL       PostgreSQL connection string

Example:
  export DATABASE_URL="postgresql://user:pass@localhost/dbname"
  $0 ./backups/enum_migration_20250101_120000

EOF
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ -z "$BACKUP_DIR" ]; then
        log_error "Backup directory not specified"
        usage
    fi

    # Security: Prevent path traversal attacks
    if [[ "$BACKUP_DIR" == *".."* ]]; then
        log_error "Invalid backup directory: path traversal detected"
        exit 1
    fi

    # Security: Ensure backup directory is within expected location
    local normalized_path=$(realpath -m "$BACKUP_DIR" 2>/dev/null || echo "$BACKUP_DIR")
    if [[ ! "$normalized_path" =~ ^/.*backups/enum_migration_.* ]] && [[ ! "$normalized_path" =~ ^\./backups/enum_migration_.* ]]; then
        log_warn "Backup directory outside expected location: ${normalized_path}"
        log_warn "Expected format: ./backups/enum_migration_YYYYMMDD_HHMMSS"
        read -p "Continue anyway? (type 'YES' to confirm): " confirm
        if [ "$confirm" != "YES" ]; then
            log_info "Restore cancelled by user"
            exit 0
        fi
    fi

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory does not exist: ${BACKUP_DIR}"
        exit 1
    fi

    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable not set"
        exit 1
    fi

    if ! command -v psql &> /dev/null; then
        log_error "psql not found. Please install PostgreSQL client tools."
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# Validate backup directory
validate_backup_dir() {
    log_info "Validating backup directory..."

    local required_files=(
        "user_application_access.sql"
        "user_invitations.sql"
        "enum_types.sql"
        "indexes_and_constraints.sql"
        "statistics.txt"
        "MANIFEST.txt"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "${BACKUP_DIR}/${file}" ]; then
            log_error "Missing required backup file: ${file}"
            exit 1
        fi
    done

    log_info "Backup directory validation passed"
}

# Get pre-restore statistics
get_pre_restore_statistics() {
    log_info "Gathering pre-restore statistics..."

    local stats_file="${BACKUP_DIR}/pre_restore_stats.txt"

    cat > "${stats_file}" <<EOF
Pre-Restore Statistics
======================
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Table: user_application_access
-------------------------------
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT application) as unique_applications
        FROM user_application_access;
    " >> "${stats_file}" 2>/dev/null || echo "Table does not exist or is empty" >> "${stats_file}"

    cat >> "${stats_file}" <<EOF

Application Value Distribution:
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT application, COUNT(*) as count
        FROM user_application_access
        GROUP BY application
        ORDER BY count DESC;
    " >> "${stats_file}" 2>/dev/null || echo "No data" >> "${stats_file}"

    log_info "Pre-restore statistics saved: ${stats_file}"
}

# Confirm restore operation
confirm_restore() {
<<<<<<< HEAD
    local database_url_redacted=$(redact_database_url "${DATABASE_URL}")

=======
>>>>>>> origin/main
    log_warn "================================"
    log_warn "WARNING: Database Restore Operation"
    log_warn "================================"
    log_warn "This will REPLACE current data with backup data."
    log_warn "Backup location: ${BACKUP_DIR}"
<<<<<<< HEAD
    log_warn "Target database: ${database_url_redacted}"
=======
    log_warn "Target database: ${DATABASE_URL%%@*}@***"
>>>>>>> origin/main
    log_warn ""

    # Show backup manifest
    if [ -f "${BACKUP_DIR}/MANIFEST.txt" ]; then
        log_info "Backup Manifest:"
        head -n 20 "${BACKUP_DIR}/MANIFEST.txt"
    fi

    echo ""
    read -p "Are you sure you want to proceed? (type 'YES' to confirm): " confirm

    if [ "$confirm" != "YES" ]; then
        log_info "Restore cancelled by user"
        exit 0
    fi

    log_info "Restore confirmed, proceeding..."
}

# Drop existing tables (if needed)
drop_existing_tables() {
    log_info "Dropping existing tables (if they exist)..."

    psql "${DATABASE_URL}" -c "
        DROP TABLE IF EXISTS user_invitations CASCADE;
        DROP TABLE IF EXISTS user_application_access CASCADE;
        DROP TYPE IF EXISTS invitationstatus CASCADE;
        DROP TYPE IF EXISTS applicationtype CASCADE;
<<<<<<< HEAD
    " 2> >(sanitize_db_error >&2)
=======
    " 2>&1
>>>>>>> origin/main

    log_info "Existing tables dropped"
}

# Restore enum types
restore_enum_types() {
    log_info "Restoring enum types..."

<<<<<<< HEAD
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/enum_types.sql" 2> >(sanitize_db_error >&2)
=======
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/enum_types.sql" 2>&1
>>>>>>> origin/main

    log_info "Enum types restored"
}

# Restore user_application_access table
restore_user_application_access() {
    log_info "Restoring user_application_access table..."

    local start_time=$(date +%s)

<<<<<<< HEAD
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/user_application_access.sql" 2> >(sanitize_db_error >&2)
=======
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/user_application_access.sql" 2>&1
>>>>>>> origin/main

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_info "user_application_access table restored in ${duration} seconds"
}

# Restore user_invitations table
restore_user_invitations() {
    log_info "Restoring user_invitations table..."

<<<<<<< HEAD
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/user_invitations.sql" 2> >(sanitize_db_error >&2)
=======
    psql "${DATABASE_URL}" < "${BACKUP_DIR}/user_invitations.sql" 2>&1
>>>>>>> origin/main

    log_info "user_invitations table restored"
}

# Verify restore
verify_restore() {
    log_info "Verifying restore..."

    local verification_file="${BACKUP_DIR}/restore_verification.txt"

    cat > "${verification_file}" <<EOF
Restore Verification
====================
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Table: user_application_access
-------------------------------
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT application) as unique_applications
        FROM user_application_access;
    " >> "${verification_file}"

    cat >> "${verification_file}" <<EOF

Application Value Distribution:
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT application, COUNT(*) as count
        FROM user_application_access
        GROUP BY application
        ORDER BY count DESC;
    " >> "${verification_file}"

    cat >> "${verification_file}" <<EOF

Foreign Key Constraints:
------------------------
EOF

    psql "${DATABASE_URL}" -t -c "
        SELECT
            conname,
            conrelid::regclass,
            confrelid::regclass,
            confdeltype as on_delete
        FROM pg_constraint
        WHERE conrelid IN ('user_application_access'::regclass, 'user_invitations'::regclass)
        AND contype = 'f';
    " >> "${verification_file}"

    log_info "Verification data saved: ${verification_file}"

<<<<<<< HEAD
    # Compare with original statistics (CRITICAL: Must match for successful restore)
    if [ -f "${BACKUP_DIR}/statistics.txt" ]; then
        log_info "Comparing with backup statistics..."

        # Security: Extract and validate numeric row counts only
        local backup_count=$(grep -A 1 "total_rows" "${BACKUP_DIR}/statistics.txt" | tail -1 | tr -d ' ' | grep -o '[0-9]*' || echo "0")
        local restore_count=$(grep -A 1 "total_rows" "${verification_file}" | tail -1 | tr -d ' ' | grep -o '[0-9]*' || echo "0")

        # Use numeric comparison (not string comparison)
        if [ "${backup_count}" -eq "${restore_count}" ] 2>/dev/null; then
            log_info "Row count verification PASSED: ${restore_count} rows"
        else
            log_error "Row count mismatch: backup=${backup_count}, restored=${restore_count}"
            log_error "CRITICAL: Restore failed - data integrity check failed"
            exit 1
        fi
    else
        log_warn "No backup statistics found, skipping row count verification"
=======
    # Compare with original statistics
    if [ -f "${BACKUP_DIR}/statistics.txt" ]; then
        log_info "Comparing with backup statistics..."

        local backup_count=$(grep -A 1 "total_rows" "${BACKUP_DIR}/statistics.txt" | tail -1 | tr -d ' ')
        local restore_count=$(grep -A 1 "total_rows" "${verification_file}" | tail -1 | tr -d ' ')

        if [ "$backup_count" = "$restore_count" ]; then
            log_info "Row count verification PASSED: ${restore_count} rows"
        else
            log_warn "Row count mismatch: backup=${backup_count}, restored=${restore_count}"
        fi
>>>>>>> origin/main
    fi
}

# Check foreign key integrity
check_foreign_key_integrity() {
    log_info "Checking foreign key integrity..."

    local fk_check=$(psql "${DATABASE_URL}" -t -c "
        SELECT COUNT(*)
        FROM user_application_access uaa
        LEFT JOIN users u ON uaa.user_id = u.id
        WHERE u.id IS NULL;
    ")

    if [ "$fk_check" -eq 0 ]; then
        log_info "Foreign key integrity check PASSED"
    else
        log_error "Foreign key integrity check FAILED: ${fk_check} orphaned records found"
        exit 1
    fi
}

# Create restore log
create_restore_log() {
    log_info "Creating restore log..."

    local log_file="${BACKUP_DIR}/restore_log.txt"
<<<<<<< HEAD
    local database_url_redacted=$(redact_database_url "${DATABASE_URL}")
=======
>>>>>>> origin/main

    cat > "${log_file}" <<EOF
Restore Log
===========
Backup Directory: ${BACKUP_DIR}
<<<<<<< HEAD
Target Database: ${database_url_redacted}
=======
Target Database: ${DATABASE_URL%%@*}@***
>>>>>>> origin/main
Restore Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

Operations Performed:
---------------------
1. Pre-restore statistics collected
2. Existing tables dropped
3. Enum types restored
4. user_application_access table restored
5. user_invitations table restored
6. Data verification completed
7. Foreign key integrity verified

Result: SUCCESS

Files Generated:
----------------
- pre_restore_stats.txt
- restore_verification.txt
- restore_log.txt

Next Steps:
-----------
1. Review restore_verification.txt
2. Test application functionality
3. Verify user access to applications
4. Check Auth0 integration

EOF

    log_info "Restore log created: ${log_file}"
}

# Main execution
main() {
    log_info "Starting enum migration restore (US-6A)"
    log_info "================================================"

    check_prerequisites
    validate_backup_dir
    get_pre_restore_statistics
    confirm_restore
    drop_existing_tables
    restore_enum_types
    restore_user_application_access
    restore_user_invitations
    verify_restore
    check_foreign_key_integrity
    create_restore_log

    log_info "================================================"
    log_info "Restore completed successfully!"
    log_info "Review restore_verification.txt for details"
    log_info ""
    log_info "Next steps:"
    log_info "1. Test application login"
    log_info "2. Verify user access to MARKET_EDGE, CAUSAL_EDGE, VALUE_EDGE"
    log_info "3. Check Auth0 integration"
    log_info "4. Monitor for any errors"
}

# Run main function
main
