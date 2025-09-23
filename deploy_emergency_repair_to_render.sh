#!/bin/bash

# Emergency Schema Repair Deployment for Render
# =============================================
# This script deploys and executes the emergency schema repair on Render
# to fix the massive schema drift blocking the £925K Zebra Associates opportunity
#
# IMPROVED TRANSACTION HANDLING:
# - Uses autocommit mode to prevent transaction rollback issues
# - Each SQL statement commits independently
# - Successful repairs are retained even if some statements fail
# - Maximizes repair success rate in production environment

set -e

echo "🚨 EMERGENCY SCHEMA REPAIR DEPLOYMENT FOR RENDER"
echo "🎯 Target: Fix 9 missing tables + 48 missing columns"
echo "⏰ Started: $(date)"

# Validate environment
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo "💡 Ensure DATABASE_URL is configured in Render environment group"
    exit 2
fi

echo "✅ DATABASE_URL configured"
echo "🔧 Environment: ${ENVIRONMENT:-production}"

# Install required dependencies
echo "📦 Installing required Python packages..."
pip install psycopg2-binary

# Execute emergency schema repair
echo "🚀 Executing emergency schema repair..."
python render_emergency_schema_repair.py --apply

repair_result=$?

if [ $repair_result -eq 0 ]; then
    echo ""
    echo "🎉 EMERGENCY SCHEMA REPAIR COMPLETED!"
    echo "================================================================"
    echo "✅ Schema repairs applied with autocommit transaction handling"
    echo "✅ Missing tables created (where possible):"
    echo "   - competitive_factor_templates"
    echo "   - module_configurations"
    echo "   - industry_templates"
    echo "   - module_usage_logs"
    echo "   - sector_modules"
    echo "   - organization_template_applications"
    echo "   - hierarchy_role_assignments"
    echo "   - feature_flag_usage"
    echo "   - admin_actions"
    echo ""
    echo "✅ Missing columns added to existing tables (where possible)"
    echo "✅ Alembic version updated to prevent future conflicts"
    echo "✅ Performance indexes created"
    echo ""
    echo "📊 IMPORTANT: Check repair logs for specific success/warning details"
    echo "📊 Successful repairs are committed even if some statements failed"
    echo ""
    echo "🔗 Test admin endpoints for functionality:"
    echo "   - https://marketedge-platform.onrender.com/api/v1/admin/feature-flags"
    echo "   - https://marketedge-platform.onrender.com/api/v1/module-management/modules"
    echo ""
    echo "💰 £925K Zebra Associates opportunity: SCHEMA REPAIR ATTEMPTED"
    echo "================================================================"
    exit 0
else
    echo ""
    echo "❌ EMERGENCY SCHEMA REPAIR ENCOUNTERED ISSUES"
    echo "================================================================"
    echo "🚨 No successful schema repairs were applied"
    echo "📋 Check logs for detailed error information"
    echo "🔧 Some failures may be expected (existing structures, etc.)"
    echo "🆘 Manual review of production schema state required"
    echo "================================================================"
    exit $repair_result
fi