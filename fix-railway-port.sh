#!/bin/bash

echo "🔧 Fixing Railway PORT configuration for multi-service deployment"

# Get current Railway project status
echo "Current Railway status:"
railway status

echo ""
echo "🚀 Re-deploying with corrected configuration..."

# Force redeploy to apply the railway.toml configuration properly
railway up

echo "✅ Deployment completed. The railway.toml file should now take precedence."
echo "📋 Current railway.toml configuration:"
cat railway.toml

echo ""
echo "🩺 Testing health endpoint..."
sleep 30
curl -s https://marketedge-backend-production.up.railway.app/health | jq '.' || echo "Health check endpoint not responding correctly"