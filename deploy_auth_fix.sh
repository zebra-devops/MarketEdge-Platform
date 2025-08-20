#!/bin/bash

echo "🚀 DEPLOYING AUTH FIX TO PRODUCTION"
echo "===================================="
echo ""
echo "This script will deploy the authentication fix for cross-domain cookie issues."
echo ""

# Navigate to the frontend directory
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend

echo "📦 Building frontend with auth fixes..."
npm run build

echo ""
echo "🎯 DEPLOYMENT INSTRUCTIONS:"
echo "============================"
echo ""
echo "The authentication fix has been implemented. The frontend now:"
echo "1. Stores tokens from the response body in cookies"
echo "2. Automatically includes tokens in API requests"
echo "3. Handles cross-domain authentication correctly"
echo ""
echo "To deploy to production:"
echo ""
echo "Option 1: Vercel (if frontend is on Vercel)"
echo "  vercel --prod"
echo ""
echo "Option 2: Git push (if auto-deploy is configured)"
echo "  git add -A"
echo "  git commit -m 'Fix: Store Auth0 tokens in cookies for cross-domain authentication'"
echo "  git push origin main"
echo ""
echo "Option 3: Manual deployment"
echo "  Upload the built files from ./out or ./.next to your hosting provider"
echo ""
echo "After deployment, test the authentication flow:"
echo "1. Go to https://app.zebra.associates"
echo "2. Click login to authenticate with Auth0"
echo "3. Check browser DevTools > Application > Cookies"
echo "4. Verify 'access_token' and 'refresh_token' cookies exist"
echo "5. Check that API requests include Authorization headers"
echo ""
echo "✅ AUTH FIX READY FOR DEPLOYMENT!"