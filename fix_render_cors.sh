#!/bin/bash

echo "🚀 Fixing Render CORS Configuration"
echo "======================================"

# Updated CORS origins to include all frontend URLs
NEW_CORS_ORIGINS='["https://app.zebra.associates","https://frontend-79pvaaolp-zebraassociates-projects.vercel.app","https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app","http://localhost:3000","http://localhost:3001"]'

echo "📝 New CORS Origins:"
echo "$NEW_CORS_ORIGINS"
echo ""

echo "🔧 To fix this issue:"
echo "1. Go to: https://dashboard.render.com"
echo "2. Find your 'marketedge-platform' service"
echo "3. Click Environment tab"
echo "4. Update CORS_ORIGINS variable to:"
echo "   $NEW_CORS_ORIGINS"
echo "5. Deploy the service"
echo ""

echo "🧪 After update, test with:"
echo "curl -H \"Origin: https://frontend-79pvaaolp-zebraassociates-projects.vercel.app\" -I https://marketedge-platform.onrender.com/api/v1/auth/login | grep access-control-allow-origin"
echo ""

echo "✅ Expected result: access-control-allow-origin: https://frontend-79pvaaolp-zebraassociates-projects.vercel.app"