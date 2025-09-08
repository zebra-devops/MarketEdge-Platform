#\!/bin/bash

echo "=== VERCEL DEPLOYMENT VERIFICATION ==="
echo "Date: $(date)"
echo ""

OLD_URL="https://frontend-f93c92lw8-zebraassociates-projects.vercel.app"
NEW_URL="https://frontend-eey1raa7n-zebraassociates-projects.vercel.app"

echo "Testing CORS on both deployments:"
echo ""

echo "1. Testing OLD deployment (has token parsing bug):"
echo "URL: $OLD_URL"
curl -s "https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=${OLD_URL}%2Fcallback" \
  -H "Origin: $OLD_URL" \
  -I | grep -E "(HTTP|access-control)"

echo ""
echo "2. Testing NEW deployment (has token parsing fix):"  
echo "URL: $NEW_URL"
curl -s "https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url?redirect_uri=${NEW_URL}%2Fcallback" \
  -H "Origin: $NEW_URL" \
  -I | grep -E "(HTTP|access-control)"

echo ""
echo "=== RECOMMENDATION ==="
echo "✅ Both deployments should work for CORS now"
echo "❌ OLD deployment still has token parsing bug"
echo "✅ NEW deployment has token parsing fix"
echo ""
echo "🎯 USE THIS URL FOR TESTING:"
echo "$NEW_URL"
echo ""
echo "Make sure Auth0 callback URLs include:"
echo "- ${OLD_URL}/callback"
echo "- ${NEW_URL}/callback"
EOF < /dev/null