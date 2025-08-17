#!/bin/bash

echo "🚀 Updating CORS for New Frontend Deployment"
echo "============================================"

# Latest CORS origins including new frontend URL
NEW_CORS_ORIGINS='["https://app.zebra.associates","https://frontend-2q61uheqm-zebraassociates-projects.vercel.app","https://frontend-79pvaaolp-zebraassociates-projects.vercel.app","http://localhost:3000","http://localhost:3001"]'

echo "📝 Updated CORS Origins with new frontend:"
echo "$NEW_CORS_ORIGINS"
echo ""

echo "🔧 Update this in Render Dashboard:"
echo "1. Go to: https://dashboard.render.com"
echo "2. Find your 'marketedge-platform' service"
echo "3. Click Environment tab"
echo "4. Update CORS_ORIGINS variable to:"
echo "   $NEW_CORS_ORIGINS"
echo "5. Deploy the service"
echo ""

echo "📋 Auth0 Callback URLs to add:"
echo "- https://frontend-2q61uheqm-zebraassociates-projects.vercel.app/callback"
echo ""

echo "🧪 After updates, test with:"
echo "curl -H \"Origin: https://frontend-2q61uheqm-zebraassociates-projects.vercel.app\" -I https://marketedge-platform.onrender.com/api/v1/auth/auth0-url"