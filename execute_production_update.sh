#!/bin/bash

# Production Super Admin Promotion Execution Script
# Critical for £925K Zebra Associates Opportunity

echo "=================================================="
echo "🚀 PRODUCTION SUPER ADMIN PROMOTION"
echo "=================================================="
echo "Purpose: Update Matt Lindop to super_admin role"
echo "Impact: Unblocks £925K Zebra Associates opportunity"
echo "=================================================="
echo ""

# Check if Python script exists
if [ ! -f "production_super_admin_promotion.py" ]; then
    echo "❌ Error: production_super_admin_promotion.py not found"
    echo "Please ensure you're in the correct directory"
    exit 1
fi

# Check for production database URL
if [ -z "$PRODUCTION_DATABASE_URL" ]; then
    echo "⚠️  PRODUCTION DATABASE URL NOT SET"
    echo ""
    echo "Please obtain the database URL from Render:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Select 'marketedge-platform' service"
    echo "3. Go to Environment tab"
    echo "4. Copy the DATABASE_URL value"
    echo ""
    read -p "Enter PRODUCTION_DATABASE_URL: " db_url
    export PRODUCTION_DATABASE_URL="$db_url"
fi

# Execute the promotion script
echo ""
echo "🔄 Executing production database update..."
python production_super_admin_promotion.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ PRODUCTION UPDATE COMPLETED SUCCESSFULLY!"
    echo "=================================================="
    echo ""
    echo "Next Steps:"
    echo "1. Have Matt Lindop log out and log back in"
    echo "2. Test Feature Flags access at /admin/feature-flags"
    echo "3. Run verification: python verify_production_super_admin_access.py"
    echo ""
else
    echo ""
    echo "❌ Update failed. Please check the error messages above."
    exit 1
fi