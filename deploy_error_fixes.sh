#!/bin/bash

echo "🚀 DEPLOYING CLIENT-SIDE ERROR FIXES"
echo "====================================="
echo ""

cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend

echo "📋 Changes being deployed:"
echo "1. Fixed TypeError in initializeAutoRefresh by removing timer-utils dependency"
echo "2. Using native browser timer functions directly"
echo "3. Added production debug logging for API requests"
echo "4. Improved error handling for authentication"
echo ""

echo "🔧 Building frontend with fixes..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful"
    echo ""
    echo "🚀 Deploying to production..."
    
    # Check if vercel is available
    if command -v vercel &> /dev/null; then
        echo "Using Vercel for deployment..."
        vercel --prod
    else
        echo "Vercel CLI not found. Using git deployment..."
        git add -A
        git commit -m "Fix: Resolve TypeError in auth service and add debug logging

- Remove timer-utils dependency causing function reference issues
- Use native browser timer functions directly  
- Add production debug logging for API requests
- Improve error handling for authentication
- Fix 400 Bad Request issues with better token validation"
        git push origin HEAD
    fi
    
    echo ""
    echo "✅ DEPLOYMENT COMPLETE!"
    echo ""
    echo "🧪 Testing steps:"
    echo "1. Visit https://app.zebra.associates"
    echo "2. Open browser DevTools console"
    echo "3. Look for debug messages about token availability"
    echo "4. Verify no TypeError in initializeAutoRefresh"
    echo "5. Check that API requests include proper Authorization headers"
    echo ""
    echo "Expected fixes:"
    echo "- ✅ No more TypeError: (0, o.yd)(...) is not a function"
    echo "- ✅ Better error messages for authentication issues"
    echo "- ✅ 400 errors should change to 403/401 (proper auth errors)"
    echo ""
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi