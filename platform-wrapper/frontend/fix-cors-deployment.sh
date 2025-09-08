#!/bin/bash

echo "=== CORS DEPLOYMENT FIX ==="
echo "Date: $(date)"
echo "Fixing CORS configuration for multiple Vercel deployments"
echo ""

# Update Railway CORS environment variables to include both URLs
echo "1. Updating Railway CORS configuration..."

CORS_ORIGINS="http://localhost:3000,https://frontend-f93c92lw8-zebraassociates-projects.vercel.app,https://frontend-eey1raa7n-zebraassociates-projects.vercel.app"
CORS_ALLOWED_ORIGINS="https://frontend-f93c92lw8-zebraassociates-projects.vercel.app,https://frontend-eey1raa7n-zebraassociates-projects.vercel.app,http://localhost:3000"

echo "Setting CORS_ORIGINS: $CORS_ORIGINS"
railway variables --set "CORS_ORIGINS=$CORS_ORIGINS" --service marketedge-backend

echo "Setting CORS_ALLOWED_ORIGINS: $CORS_ALLOWED_ORIGINS"  
railway variables --set "CORS_ALLOWED_ORIGINS=$CORS_ALLOWED_ORIGINS" --service marketedge-backend

echo "Setting FRONTEND_URL to new deployment"
railway variables --set "FRONTEND_URL=https://frontend-eey1raa7n-zebraassociates-projects.vercel.app" --service marketedge-backend

echo ""
echo "2. Waiting for Railway to redeploy..."
sleep 30

echo ""
echo "3. Testing CORS configuration..."

echo "Testing old frontend URL CORS:"
curl -s "https://marketedge-backend-production.up.railway.app/health" \
  -H "Origin: https://frontend-f93c92lw8-zebraassociates-projects.vercel.app" \
  -I | grep -E "(access-control|cors)"

echo ""
echo "Testing new frontend URL CORS:"
curl -s "https://marketedge-backend-production.up.railway.app/health" \
  -H "Origin: https://frontend-eey1raa7n-zebraassociates-projects.vercel.app" \
  -I | grep -E "(access-control|cors)"

echo ""
echo "4. Testing auth endpoint CORS:"
curl -s "https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=https%3A%2F%2Ffrontend-f93c92lw8-zebraassociates-projects.vercel.app%2Fcallback" \
  -H "Origin: https://frontend-f93c92lw8-zebraassociates-projects.vercel.app" \
  -I | grep -E "(access-control|cors)"

echo ""
echo "=== FIX COMPLETE ==="
echo "Both Vercel deployments should now be supported:"
echo "- Old: https://frontend-f93c92lw8-zebraassociates-projects.vercel.app"  
echo "- New: https://frontend-eey1raa7n-zebraassociates-projects.vercel.app"
echo ""
echo "Auth0 callback URLs that need to be configured:"
echo "- https://frontend-f93c92lw8-zebraassociates-projects.vercel.app/callback"
echo "- https://frontend-eey1raa7n-zebraassociates-projects.vercel.app/callback"