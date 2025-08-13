#!/bin/bash

# Fix Railway Backend CORS Configuration for Vercel Frontend
# This script updates the Railway environment variables to include Vercel domain in CORS origins

echo "🚀 Fixing Railway Backend CORS Configuration..."

# Vercel Frontend URL
VERCEL_FRONTEND_URL="https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"

# Current Railway Backend URL
RAILWAY_BACKEND_URL="https://marketedge-backend-production.up.railway.app"

echo "Frontend URL: $VERCEL_FRONTEND_URL"
echo "Backend URL: $RAILWAY_BACKEND_URL"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it:"
    echo "npm install -g @railway/cli"
    echo "Then run: railway login"
    exit 1
fi

echo "📋 Current Railway environment variables:"
railway variables

echo ""
echo "🔧 Setting CORS_ORIGINS to include Vercel domain..."

# Set CORS_ORIGINS to include both localhost and Vercel domain
railway variables set CORS_ORIGINS="[\"http://localhost:3000\",\"http://localhost:3001\",\"$VERCEL_FRONTEND_URL\"]"

echo "🔧 Updating AUTH0_CALLBACK_URL to include Vercel domain..."

# Update AUTH0_CALLBACK_URL to support Vercel deployment
railway variables set AUTH0_CALLBACK_URL="$VERCEL_FRONTEND_URL/callback"

echo "🔧 Setting production environment configuration..."

# Set production environment
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"

echo "📋 Updated Railway environment variables:"
railway variables

echo ""
echo "✅ Railway CORS configuration updated!"
echo "⚡ Deploying changes to Railway..."

# Trigger a new deployment to apply the environment variable changes
railway up --detach

echo "🎉 Railway backend deployment started with updated CORS configuration!"
echo ""
echo "📝 Summary of changes:"
echo "   - CORS_ORIGINS: Updated to include $VERCEL_FRONTEND_URL"
echo "   - AUTH0_CALLBACK_URL: Set to $VERCEL_FRONTEND_URL/callback"
echo "   - ENVIRONMENT: Set to production"
echo "   - DEBUG: Set to false"
echo ""
echo "🔍 You can monitor the deployment at: https://railway.app"