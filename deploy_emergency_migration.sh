#!/bin/bash

# Emergency Migration Deployment Script
# This script deploys the migration fix to Render production

set -e

echo "🚀 EMERGENCY MIGRATION DEPLOYMENT"
echo "🏢 Business Impact: £925K Zebra Associates opportunity"
echo "🚨 Critical Issue: analytics_modules table missing"
echo ""

# Check if we have the migration script
if [ ! -f "apply_production_migrations_emergency.py" ]; then
    echo "❌ Migration script not found!"
    exit 1
fi

echo "📦 Making migration script executable..."
chmod +x apply_production_migrations_emergency.py

echo "🔧 Creating one-time deployment script..."
cat > render_migration_deployment.py << 'EOF'
#!/usr/bin/env python3
"""
One-time Render deployment for emergency migrations
Executes the migration and then exits
"""

import os
import subprocess
import sys

def main():
    print("🚀 Render Emergency Migration Deployment")
    print("🎯 Target: Create missing analytics_modules table")

    # Verify DATABASE_URL is available
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not available in Render environment!")
        sys.exit(1)

    print("✅ DATABASE_URL found in environment")

    # Run the migration script
    try:
        result = subprocess.run([
            sys.executable,
            'apply_production_migrations_emergency.py'
        ], check=True, capture_output=True, text=True)

        print("✅ Migration script output:")
        print(result.stdout)

        if result.stderr:
            print("⚠️ Migration script warnings:")
            print(result.stderr)

        print("🎉 EMERGENCY MIGRATION COMPLETED!")
        print("✅ analytics_modules table should now exist")
        print("🚀 Matt Lindop can now access admin features")

    except subprocess.CalledProcessError as e:
        print(f"❌ Migration script failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        sys.exit(1)

    print("👋 One-time migration deployment complete - container will exit")

if __name__ == "__main__":
    main()
EOF

echo "✅ One-time migration script created"

echo "🚀 Triggering Render deployment..."

# Update the render-startup.sh to run migrations on startup
echo "📝 Updating render-startup.sh to include migration check..."

cat > render-startup.sh << 'EOF'
#!/bin/bash

# Render Production Startup Script
# Includes emergency migration deployment

echo "🚀 MarketEdge Platform Starting..."
echo "🔧 Checking for emergency migrations..."

# Check if this is a migration deployment
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🚨 EMERGENCY MIGRATION MODE"
    echo "🎯 Creating analytics_modules table"

    python3 apply_production_migrations_emergency.py
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✅ Emergency migrations completed successfully"
        echo "🎉 analytics_modules table created"
    else
        echo "❌ Emergency migrations failed"
        exit 1
    fi
fi

# Normal startup
echo "🟢 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
EOF

chmod +x render-startup.sh

echo "📄 Updating render.yaml for migration deployment..."

cat > render.yaml << 'EOF'
services:
  - type: web
    name: marketedge-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "./render-startup.sh"
    plan: free
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: RUN_MIGRATIONS
        value: true
      - key: PORT
        fromService:
          type: web
          name: marketedge-backend
          property: port
EOF

echo "✅ Render configuration updated for migration deployment"

echo "🔄 Committing changes to trigger Render deployment..."

# Commit the changes
git add apply_production_migrations_emergency.py
git add deploy_emergency_migration.sh
git add render_migration_deployment.py
git add render-startup.sh
git add render.yaml

git commit -m "deploy: EMERGENCY analytics_modules migration deployment

CRITICAL: £925K Zebra Associates opportunity - missing analytics_modules table

Changes:
- Emergency migration deployment script
- One-time migration execution on Render
- Automatic table creation and verification
- Feature flags endpoint 500 error fix

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Changes committed to git"

# Create deployment trigger
echo "📡 Creating deployment trigger..."
date +%s > .render-migration-trigger

git add .render-migration-trigger
git commit -m "trigger: force Render migration deployment

Emergency deployment trigger for analytics_modules table creation

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo ""
echo "🎯 DEPLOYMENT STEPS COMPLETED!"
echo "================================"
echo "✅ Emergency migration script created"
echo "✅ Render configuration updated"
echo "✅ Changes committed to git"
echo "✅ Deployment trigger created"
echo ""
echo "🚀 Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Render will auto-deploy and run migrations"
echo "3. Check Render logs for migration results"
echo "4. Test Feature Flags endpoint: https://marketedge-platform.onrender.com/api/v1/admin/feature-flags"
echo ""
echo "🎉 Expected result: analytics_modules table created, 401 response (not 500)"
EOF

chmod +x deploy_emergency_migration.sh