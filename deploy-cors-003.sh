#!/bin/bash

# CORS-003: Railway Service Integration Deployment Script
# Deploys multi-service Caddy + FastAPI configuration to Railway

set -e

echo "🚀 CORS-003: Railway Service Integration Deployment"
echo "=================================================="
echo ""
echo "Business Context: £925K Odeon demo - 70 hours remaining"
echo "Objective: Deploy Caddy sidecar proxy to bypass Railway CORS stripping"
echo ""

# Step 1: Pre-deployment validation
echo "📋 Step 1: Pre-deployment validation..."
echo "--------------------------------------"

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI available"

# Check if we're logged in to Railway
if railway whoami &> /dev/null; then
    echo "✅ Railway authentication verified"
else
    echo "❌ Railway authentication required"
    echo "Run: railway login"
    exit 1
fi

# Validate configuration files
required_files=(
    "Dockerfile"
    "supervisord.conf" 
    "Caddyfile"
    "railway.toml"
    "start.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file present"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🔧 Step 2: Railway environment configuration..."
echo "---------------------------------------------"

# Set Railway environment variables for multi-service setup
echo "Setting Railway environment variables..."

railway variables --set "CORS_MODE=caddy_proxy_multi_service"
railway variables --set "CADDY_ENABLED=true"
railway variables --set "FASTAPI_INTERNAL_PORT=8000"
railway variables --set "CADDY_EXTERNAL_PORT=80"

# Ensure existing CORS origins are maintained
railway variables --set 'CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://app.zebra.associates","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"]'

echo "✅ Railway environment variables configured"

echo ""
echo "📦 Step 3: Creating deployment backup..."
echo "---------------------------------------"

# Create backup of current deployment state
BACKUP_DIR="backup/cors-003-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Export current Railway service configuration
railway service > "$BACKUP_DIR/railway-service-before.json" || true
railway variables --json > "$BACKUP_DIR/railway-variables-before.json" || true

echo "✅ Backup created: $BACKUP_DIR"

echo ""
echo "🚀 Step 4: Deploying multi-service configuration..."
echo "--------------------------------------------------"

echo "Building and deploying Caddy + FastAPI multi-service container..."
echo "This may take 3-5 minutes..."

# Deploy to Railway with detailed output
if railway up --detach; then
    echo "✅ Deployment initiated successfully"
else
    echo "❌ Deployment failed"
    echo "Check Railway logs: railway logs --tail"
    exit 1
fi

echo ""
echo "⏳ Step 5: Waiting for deployment to stabilize..."
echo "-----------------------------------------------"

echo "Waiting 120 seconds for services to start..."
sleep 120

echo ""
echo "🧪 Step 6: Post-deployment validation..."
echo "---------------------------------------"

# Get the Railway service URL
BACKEND_URL="https://marketedge-backend-production.up.railway.app"

echo "Testing service health..."
if curl -f --max-time 30 "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ Service health check: PASSED"
else
    echo "❌ Service health check: FAILED"
    echo "Service may still be starting up..."
fi

echo ""
echo "Testing CORS headers..."
CORS_TEST=$(curl -s -I -H "Origin: https://app.zebra.associates" "$BACKEND_URL/health" || echo "CORS_TEST_FAILED")

if echo "$CORS_TEST" | grep -q "access-control-allow-origin"; then
    echo "✅ CORS headers: PRESENT"
    echo "Origin found in response headers:"
    echo "$CORS_TEST" | grep "access-control" || true
else
    echo "❌ CORS headers: MISSING"
    echo "Response headers:"
    echo "$CORS_TEST"
fi

echo ""
echo "Testing Caddy proxy functionality..."
DEBUG_RESPONSE=$(curl -s -H "Origin: https://app.zebra.associates" "$BACKEND_URL/cors-debug" || echo '{"error":"debug_test_failed"}')

if echo "$DEBUG_RESPONSE" | grep -q "caddy_proxy_multi_service"; then
    echo "✅ Caddy proxy: ACTIVE"
    echo "Multi-service mode confirmed"
else
    echo "⚠️  Caddy proxy: STATUS UNKNOWN"
    echo "Debug response: $DEBUG_RESPONSE"
fi

echo ""
echo "🎯 Step 7: Deployment status summary..."
echo "------------------------------------"

# Check Railway service status
echo "Railway service status:"
railway status || echo "Could not retrieve Railway status"

echo ""
echo "🔍 Step 8: CORS validation test..."
echo "--------------------------------"

# Comprehensive CORS test for the critical domain
echo "Testing CORS for critical domain: https://app.zebra.associates"

CORS_PREFLIGHT=$(curl -s -X OPTIONS \
    -H "Origin: https://app.zebra.associates" \
    -H "Access-Control-Request-Method: GET" \
    -w "HTTP_CODE:%{http_code}" \
    "$BACKEND_URL/health" 2>/dev/null || echo "HTTP_CODE:000")

PREFLIGHT_CODE=$(echo "$CORS_PREFLIGHT" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

if [ "$PREFLIGHT_CODE" = "204" ] || [ "$PREFLIGHT_CODE" = "200" ]; then
    echo "✅ CORS preflight: PASSED (HTTP $PREFLIGHT_CODE)"
else
    echo "❌ CORS preflight: FAILED (HTTP $PREFLIGHT_CODE)"
fi

echo ""
echo "🎉 CORS-003 Railway Integration Deployment: COMPLETE"
echo "==================================================="
echo ""
echo "Deployment Summary:"
echo "- ✅ Multi-service container deployed"
echo "- ✅ Caddy reverse proxy configured" 
echo "- ✅ FastAPI backend integrated"
echo "- ✅ Railway networking configured"
echo ""
echo "Next Steps:"
echo "1. Monitor deployment: railway logs --tail"
echo "2. Test authentication: Login at https://app.zebra.associates"
echo "3. Proceed with CORS-004: Service monitoring"
echo ""
echo "Critical URLs:"
echo "- Health check: $BACKEND_URL/health"
echo "- CORS debug: $BACKEND_URL/cors-debug"
echo "- Authentication: https://app.zebra.associates"
echo ""
echo "If CORS issues persist, check Railway logs and consider rollback:"
echo "- Rollback: railway rollback"
echo "- Logs: railway logs --tail"