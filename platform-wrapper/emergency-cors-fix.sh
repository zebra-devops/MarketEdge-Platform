#!/bin/bash

# EMERGENCY CORS FIX FOR ODEON DEMO
# Immediate resolution for custom domain CORS issues

set -e

echo "🚨 EMERGENCY CORS FIX FOR ODEON DEMO"
echo "===================================="
echo ""
echo "Issue: Custom domain https://app.zebra.associates blocked by CORS"
echo "Solution: Force Railway redeploy with updated ASGI CORS handler"
echo ""

# Step 1: Commit current changes
echo "📦 Step 1: Committing CORS fixes..."
git add backend/app/main.py
git commit -m "EMERGENCY: Force redeploy with custom domain CORS fix v3

- Updated ASGI CORS handler with deployment timestamp
- Prioritized custom domain in allowed origins
- Added deployment verification logs

🚨 Critical fix for £925K Odeon demo
" || echo "No changes to commit"

# Step 2: Force Railway deployment
echo ""
echo "🚀 Step 2: Force Railway deployment..."
echo "--------------------------------------"

if command -v railway &> /dev/null; then
    echo "🔧 Navigating to backend directory..."
    cd backend
    
    echo "⚡ Setting Railway environment variables..."
    # Force update CORS_ORIGINS with custom domain
    railway variables set CORS_ORIGINS='["http://localhost:3000","http://localhost:3001","https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","https://app.zebra.associates"]'
    
    # Set production environment
    railway variables set ENVIRONMENT="production"
    railway variables set DEBUG="false"
    
    echo "✅ Environment variables updated!"
    echo ""
    
    echo "🚀 Triggering Railway deployment..."
    railway up --detach
    
    echo "✅ Railway deployment started!"
    cd ..
else
    echo "❌ Railway CLI not found!"
    echo "   Install with: npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

# Step 3: Wait and test
echo ""
echo "⏳ Step 3: Waiting for deployment..."
echo "-----------------------------------"
echo "Deployment will take 2-3 minutes."
echo ""

# Function to test CORS
test_cors() {
    echo "🧪 Testing CORS with custom domain..."
    
    # Test OPTIONS request
    echo "Testing OPTIONS preflight request..."
    curl -s -X OPTIONS \
         -H "Origin: https://app.zebra.associates" \
         -H "Access-Control-Request-Method: GET" \
         https://marketedge-backend-production.up.railway.app/health \
         -w "\nStatus: %{http_code}\nResponse time: %{time_total}s\n" || true
    
    echo ""
    
    # Test GET request with Origin header
    echo "Testing GET request with Origin header..."
    curl -s -X GET \
         -H "Origin: https://app.zebra.associates" \
         https://marketedge-backend-production.up.railway.app/health \
         -w "\nStatus: %{http_code}\nResponse time: %{time_total}s\n" || true
}

echo "⏰ Waiting 90 seconds for deployment to complete..."
sleep 90

echo ""
echo "🧪 Step 4: Testing deployment..."
echo "--------------------------------"
test_cors

echo ""
echo "🎯 Step 5: Manual verification steps..."
echo "---------------------------------------"
echo ""
echo "1. Check deployment logs:"
echo "   railway logs --tail"
echo ""
echo "2. Test custom domain authentication:"
echo "   - Go to: https://app.zebra.associates"
echo "   - Open browser dev tools (F12)"
echo "   - Try to login"
echo "   - Check for CORS errors in console"
echo ""
echo "3. If still failing, check Railway deployment status:"
echo "   - https://railway.app (check deployment logs)"
echo "   - Look for 'EMERGENCY CORS FIX v3' messages"
echo "   - Verify custom domain in allowed origins"
echo ""
echo "4. Emergency fallback (if needed):"
echo "   ./emergency-cors-fallback.sh"
echo ""

echo "🚨 EMERGENCY DEPLOYMENT COMPLETE"
echo "================================="
echo ""
echo "📊 Status Summary:"
echo "  ✅ Code updated with CORS fix v3"
echo "  ✅ Railway deployment triggered"
echo "  ✅ Environment variables updated"
echo "  ⏳ Deployment in progress (check Railway dashboard)"
echo ""
echo "🎯 Next: Test authentication at https://app.zebra.associates"
echo ""
echo "🔍 If issues persist:"
echo "   - Check Railway logs: railway logs --tail"
echo "   - Verify deployment status in Railway dashboard"
echo "   - Run: ./verify-cors-fix.sh"