#!/bin/bash

# Production Schema Fix Deployment Script
# =====================================
#
# This script applies comprehensive schema fixes to the production database
# to resolve the critical schema drift blocking Zebra Associates functionality.
#
# CRITICAL REQUIREMENTS:
# 1. Run during scheduled maintenance window
# 2. Have production DATABASE_URL available
# 3. Backup database before execution
# 4. Monitor application after deployment
#
# Usage:
#   # Test with dry run first
#   ./deploy_production_schema_fix.sh --dry-run
#
#   # Apply fixes to production
#   ./deploy_production_schema_fix.sh --apply
#
# Exit Codes:
#   0 = Success
#   1 = Schema validation failed
#   2 = Missing environment variables
#   3 = Database connection failed
#   4 = Backup failed
#   5 = Schema repair failed

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="production_schema_fix_${TIMESTAMP}.log"
BACKUP_FILE="production_backup_${TIMESTAMP}.sql"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit "$2"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if DATABASE_URL is set
    if [ -z "${DATABASE_URL:-}" ]; then
        error_exit "DATABASE_URL environment variable not set" 2
    fi

    # Check if schema repair script exists
    if [ ! -f "$SCRIPT_DIR/database/production_schema_repair.py" ]; then
        error_exit "Schema repair script not found" 2
    fi

    # Check Python dependencies
    if ! python3 -c "import sqlalchemy, psycopg2" 2>/dev/null; then
        error_exit "Required Python packages not installed (sqlalchemy, psycopg2)" 2
    fi

    # Test database connection
    log "Testing database connection..."
    if ! python3 -c "
import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful')
engine.dispose()
" 2>/dev/null; then
        error_exit "Cannot connect to production database" 3
    fi

    log "✅ Prerequisites check passed"
}

# Create database backup
create_backup() {
    log "Creating database backup..."

    # Extract connection details for pg_dump
    if command -v pg_dump >/dev/null 2>&1; then
        if pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null; then
            log "✅ Database backup created: $BACKUP_FILE"
        else
            error_exit "Database backup failed" 4
        fi
    else
        log "⚠️  pg_dump not available - proceeding without backup (NOT RECOMMENDED)"
        read -p "Continue without backup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error_exit "Deployment cancelled by user" 4
        fi
    fi
}

# Validate current schema
validate_schema() {
    log "Validating current production schema..."

    if python3 "$SCRIPT_DIR/database/production_schema_repair.py" --dry-run 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Schema validation completed"
    else
        error_exit "Schema validation failed" 1
    fi
}

# Apply schema fixes
apply_schema_fixes() {
    local dry_run="${1:-false}"

    if [ "$dry_run" = "true" ]; then
        log "Running schema repair in DRY RUN mode..."
        python3 "$SCRIPT_DIR/database/production_schema_repair.py" --dry-run 2>&1 | tee -a "$LOG_FILE"
    else
        log "Applying schema repairs to production database..."

        if python3 "$SCRIPT_DIR/database/production_schema_repair.py" --apply 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ Schema repairs applied successfully"
        else
            error_exit "Schema repair failed" 5
        fi
    fi
}

# Post-deployment verification
verify_deployment() {
    log "Verifying post-deployment state..."

    # Check API health
    log "Testing API health endpoint..."
    if curl -sf "https://marketedge-platform.onrender.com/health" > /dev/null 2>&1; then
        log "✅ API health check passed"
    else
        log "⚠️  API health check failed - may need application restart"
    fi

    # Verify schema is now valid
    log "Re-validating schema after repairs..."
    if python3 "$SCRIPT_DIR/database/production_schema_repair.py" --dry-run 2>&1 | grep -q "no repairs needed"; then
        log "✅ Schema validation passed - all issues resolved"
    else
        log "⚠️  Schema validation shows remaining issues"
    fi

    # Test critical endpoints
    log "Testing critical API endpoints..."

    # These should return 401/403 (auth required) not 404 (missing endpoint)
    for endpoint in "/api/v1/admin/feature-flags" "/api/v1/admin/modules" "/api/v1/features/enabled"; do
        status=$(curl -s -o /dev/null -w "%{http_code}" "https://marketedge-platform.onrender.com$endpoint" || echo "000")
        if [ "$status" = "401" ] || [ "$status" = "403" ]; then
            log "✅ Endpoint $endpoint exists (HTTP $status)"
        elif [ "$status" = "404" ]; then
            log "❌ Endpoint $endpoint missing (HTTP 404)"
        else
            log "⚠️  Endpoint $endpoint returned HTTP $status"
        fi
    done
}

# Main deployment logic
main() {
    local mode="${1:-dry-run}"

    log "=== Production Schema Fix Deployment ==="
    log "Mode: $mode"
    log "Timestamp: $TIMESTAMP"
    log "Database: ${DATABASE_URL:0:30}..."
    log "Log file: $LOG_FILE"
    log "======================================="

    # Phase 1: Prerequisites and validation
    check_prerequisites
    validate_schema

    if [ "$mode" = "--apply" ]; then
        # Phase 2: Create backup (production only)
        create_backup

        # Phase 3: Apply fixes
        apply_schema_fixes false

        # Phase 4: Verify deployment
        verify_deployment

        log "=== DEPLOYMENT COMPLETE ==="
        log "✅ Production schema fixes applied successfully"
        log "📋 Next steps:"
        log "   1. Monitor application logs for errors"
        log "   2. Test Zebra Associates admin functionality"
        log "   3. Verify multi-tenant isolation"
        log "   4. Check feature flag management interface"
        log "========================="

    else
        # Dry run mode
        apply_schema_fixes true

        log "=== DRY RUN COMPLETE ==="
        log "✅ Schema fixes validated and ready for production"
        log "📋 To apply fixes to production:"
        log "   ./deploy_production_schema_fix.sh --apply"
        log "========================="
    fi
}

# Script entry point
if [ $# -eq 0 ]; then
    echo "Usage: $0 [--dry-run|--apply]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Validate and show fixes without applying (default)"
    echo "  --apply      Apply fixes to production database"
    echo ""
    echo "Environment variables required:"
    echo "  DATABASE_URL    PostgreSQL connection string"
    echo ""
    exit 1
fi

main "$@"