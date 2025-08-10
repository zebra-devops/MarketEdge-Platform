#!/bin/bash

# Railway deployment script with health check fixes
set -e

echo "=== Railway Deployment with Health Check Fixes ==="
echo ""

# Step 1: Show what we've fixed
echo "🔧 Applied Health Check Fixes:"
echo "   ✅ Removed database migration from startup (start.sh)"
echo "   ✅ Simplified health endpoint to not depend on external services"
echo "   ✅ Increased Railway health check timeout to 300s"
echo "   ✅ Updated Docker health check timing"
echo "   ✅ Created separate migration script (migrate.sh)"
echo ""

# Step 2: Validate files exist and are executable
echo "📋 Validating deployment files..."
files_to_check=(
    "start.sh"
    "migrate.sh" 
    "Dockerfile"
    "railway.toml"
    "requirements.txt"
    "app/main.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file missing"
        exit 1
    fi
done

# Make scripts executable
chmod +x start.sh migrate.sh test_health_endpoint.py

echo ""
echo "🚀 Deploying to Railway..."
echo "   This deployment includes health check fixes"
echo "   The application should start faster and respond to health checks"
echo ""

# Deploy to Railway
railway up

echo ""
echo "⏳ Waiting for deployment to complete..."
echo "   Railway will now test the /health endpoint"
echo "   Expected: HTTP 200 with status: healthy"
echo ""
echo "🔍 Monitor deployment status:"
echo "   railway logs --deployment"
echo ""
echo "🩺 Test health endpoint after deployment:"
echo "   railway run python3 test_health_endpoint.py"
echo ""
echo "📊 If deployment still fails, check:"
echo "   1. Railway environment variables are set correctly"
echo "   2. PORT variable is available to the application" 
echo "   3. Application logs for startup errors"
echo ""
echo "✨ Deployment initiated with health check fixes!"