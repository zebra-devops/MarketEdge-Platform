#!/bin/bash

# Emergency Schema Repair Deployment for Render
# =============================================
# This script deploys and executes the emergency schema repair on Render
# to fix the massive schema drift blocking the £925K Zebra Associates opportunity

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
    echo "🎉 EMERGENCY SCHEMA REPAIR COMPLETED SUCCESSFULLY!"
    echo "================================================================"
    echo "✅ All 9 missing tables created:"
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
    echo "✅ All 48 missing columns added to existing tables"
    echo "✅ Alembic version updated to prevent future conflicts"
    echo "✅ Performance indexes created"
    echo ""
    echo "🔗 Admin endpoints should now be functional:"
    echo "   - https://marketedge-platform.onrender.com/api/v1/admin/feature-flags"
    echo "   - https://marketedge-platform.onrender.com/api/v1/module-management/modules"
    echo ""
    echo "💰 £925K Zebra Associates opportunity: UNBLOCKED"
    echo "================================================================"
    exit 0
else
    echo ""
    echo "❌ EMERGENCY SCHEMA REPAIR FAILED"
    echo "================================================================"
    echo "🚨 Critical error occurred during schema repair"
    echo "📋 Check logs for detailed error information"
    echo "🆘 Manual intervention required"
    echo "================================================================"
    exit $repair_result
fi