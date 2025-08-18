#!/bin/bash

# Force Railway Redeploy Script
# Ensures multi-service Caddy + FastAPI deployment

echo "🚀 CRITICAL: Force Railway redeploy for multi-service architecture"
echo "Business Impact: £925K Odeon demo authentication fix"
echo ""

# Verify current configuration
echo "📋 Current Configuration:"
echo "- railway.toml: Multi-service with supervisord"
echo "- Dockerfile: supervisord managing Caddy + FastAPI"
echo "- CADDY_PROXY_MODE: true"
echo "- External Port: 80 (Caddy proxy)"
echo "- Internal Port: 8000 (FastAPI)"
echo ""

# Force rebuild by making an empty commit and pushing
echo "🔄 Forcing Railway deployment rebuild..."
echo "Deployment trigger: $(date)" >> .railway-deploy-trigger
git add .railway-deploy-trigger

git commit -m "FORCE REBUILD: Multi-service Caddy proxy deployment

CRITICAL: Trigger Railway rebuild for multi-service architecture
- Caddy proxy on port 80 with CORS headers  
- FastAPI backend on port 8000
- Supervisord process management
- Fixes Odeon demo authentication CORS issues

$(date)"

echo "⬆️ Pushing to trigger Railway rebuild..."
git push origin main

echo ""
echo "✅ Railway redeploy triggered successfully"
echo "⏰ Wait 3-5 minutes for deployment completion"
echo "🔍 Monitor: https://railway.app/project/your-project/service/backend"
echo ""
echo "📝 Next Steps:"
echo "1. Wait for deployment completion"
echo "2. Test CORS headers: curl -H 'Origin: https://app.zebra.associates' https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url"
echo "3. Validate Caddy proxy: Check for 'server: caddy' in response headers"
echo "4. Confirm multi-service health: Both Caddy and FastAPI running"