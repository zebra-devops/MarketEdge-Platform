#!/bin/bash

# Fix Vercel Frontend Configuration for Railway Backend Integration
# This script updates Vercel environment variables and redeploys

echo "🚀 Fixing Vercel Frontend Configuration..."

# Configuration URLs
RAILWAY_BACKEND_URL="https://marketedge-backend-production.up.railway.app"
VERCEL_FRONTEND_URL="https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"

echo "Backend URL: $RAILWAY_BACKEND_URL"
echo "Frontend URL: $VERCEL_FRONTEND_URL"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it:"
    echo "npm install -g vercel"
    echo "Then run: vercel login"
    exit 1
fi

echo "📋 Current Vercel environment variables:"
vercel env ls

echo ""
echo "🔧 Setting Vercel environment variables..."

# Set API Base URL for production
echo "$RAILWAY_BACKEND_URL" | vercel env add NEXT_PUBLIC_API_BASE_URL production

# Set Auth0 Domain for production
echo "dev-g8trhgbfdq2sk2m8.us.auth0.com" | vercel env add NEXT_PUBLIC_AUTH0_DOMAIN production

# Set Auth0 Client ID for production  
echo "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr" | vercel env add NEXT_PUBLIC_AUTH0_CLIENT_ID production

echo "📋 Updated Vercel environment variables:"
vercel env ls

echo ""
echo "✅ Vercel environment variables updated!"
echo "⚡ Triggering new Vercel deployment..."

# Trigger a new deployment to apply the environment variable changes
vercel --prod

echo "🎉 Vercel frontend deployment started with updated configuration!"
echo ""
echo "📝 Summary of changes:"
echo "   - NEXT_PUBLIC_API_BASE_URL: $RAILWAY_BACKEND_URL"
echo "   - NEXT_PUBLIC_AUTH0_DOMAIN: dev-g8trhgbfdq2sk2m8.us.auth0.com"
echo "   - NEXT_PUBLIC_AUTH0_CLIENT_ID: mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
echo ""
echo "🔍 You can monitor the deployment at: https://vercel.com"