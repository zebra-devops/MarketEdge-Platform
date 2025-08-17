#!/bin/bash

# Super Admin Migration Script Wrapper
# =====================================
# 
# This script provides a convenient way to run the super admin migration
# with proper environment setup and error handling.
#
# Usage:
#   ./run_super_admin_migration.sh
#
# Environment:
#   Set DATABASE_URL before running this script

set -e  # Exit on any error

echo "============================================================"
echo "MARKETEDGE SUPER ADMIN MIGRATION"
echo "============================================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable not set"
    echo ""
    echo "Please set your database URL:"
    echo "export DATABASE_URL='postgresql://user:password@host:port/database'"
    echo ""
    echo "For Render PostgreSQL, get the External Database URL from your dashboard"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Migration directory: $SCRIPT_DIR"
echo "Database: $(echo $DATABASE_URL | sed 's/:[^:]*@/:****@/g')"
echo ""

# Check if required files exist
if [ ! -f "$SCRIPT_DIR/add_super_admin_migration.py" ]; then
    echo "❌ Error: Migration script not found"
    echo "Expected: $SCRIPT_DIR/add_super_admin_migration.py"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/test_db_connection.py" ]; then
    echo "❌ Error: Connection test script not found"
    echo "Expected: $SCRIPT_DIR/test_db_connection.py"
    exit 1
fi

# Test database connection first
echo "Step 1: Testing database connection..."
echo "------------------------------------------------------------"
cd "$SCRIPT_DIR"
python3 test_db_connection.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Database connection test failed. Please fix connection issues first."
    exit 1
fi

echo ""
echo "Step 2: Running super admin migration..."
echo "------------------------------------------------------------"

# Ask for confirmation if this looks like production
if echo "$DATABASE_URL" | grep -q -E "(render\.com|railway|postgres\.render|railway\.app)"; then
    echo ""
    echo "⚠️  WARNING: This appears to be a PRODUCTION database!"
    echo "   Database URL contains production indicators"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " confirmation
    
    if [ "$confirmation" != "yes" ] && [ "$confirmation" != "y" ]; then
        echo ""
        echo "Migration cancelled by user."
        exit 0
    fi
    echo ""
fi

# Run the migration
python3 add_super_admin_migration.py

migration_exit_code=$?

echo ""
echo "============================================================"
if [ $migration_exit_code -eq 0 ]; then
    echo "✅ SUPER ADMIN MIGRATION COMPLETED SUCCESSFULLY"
    echo ""
    echo "Matt Lindop has been added as a super admin:"
    echo "  Email: matt.lindop@zebra.associates"
    echo "  Organization: Zebra Associates"
    echo "  Role: super_admin (platform-wide access)"
    echo ""
    echo "Next steps:"
    echo "  1. Test login with the new super admin account"
    echo "  2. Verify access to all platform features"
    echo "  3. Check audit logs for the migration activities"
else
    echo "❌ MIGRATION FAILED"
    echo ""
    echo "Check the migration log file for detailed error information."
    echo "Common issues:"
    echo "  - Database connectivity problems"
    echo "  - Insufficient database permissions"
    echo "  - Missing database tables (run migrations first)"
fi
echo "============================================================"

exit $migration_exit_code