#!/bin/bash

# Comprehensive CORS Fix and Deployment Script
# Fixes CORS issues between Vercel frontend and Railway backend

set -e  # Exit on any error

echo "🚀 Starting CORS Configuration Fix..."
echo "=====================================/"

# Configuration URLs
VERCEL_FRONTEND_URL="https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"
RAILWAY_BACKEND_URL="https://marketedge-backend-production.up.railway.app"

echo "Frontend URL: $VERCEL_FRONTEND_URL"
echo "Backend URL: $RAILWAY_BACKEND_URL"
echo ""

# Check required tools
echo "🔧 Checking required tools..."

if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found. Install with: npm install -g @railway/cli"
    echo "   Then run: railway login"
fi

if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not found. Install with: npm install -g vercel"
    echo "   Then run: vercel login"
fi

echo ""

# Step 1: Fix Railway Backend CORS
echo "📡 Step 1: Fixing Railway Backend CORS Configuration..."
echo "--------------------------------------------------------"

if command -v railway &> /dev/null; then
    echo "🔧 Updating Railway environment variables..."
    
    # Navigate to backend directory
    cd backend
    
    # Set CORS_ORIGINS to include Vercel domain
    railway variables set CORS_ORIGINS="[\"http://localhost:3000\",\"http://localhost:3001\",\"$VERCEL_FRONTEND_URL\"]"
    
    # Update AUTH0_CALLBACK_URL
    railway variables set AUTH0_CALLBACK_URL="$VERCEL_FRONTEND_URL/callback"
    
    # Set production environment
    railway variables set ENVIRONMENT="production"
    railway variables set DEBUG="false"
    
    echo "✅ Railway environment variables updated!"
    
    # Trigger deployment
    echo "⚡ Deploying Railway backend..."
    railway up --detach
    
    echo "🎉 Railway deployment started!"
    
    cd ..
else
    echo "⚠️  Railway CLI not available. Please run backend/fix-railway-cors.sh manually."
fi

echo ""

# Step 2: Fix Vercel Frontend Configuration
echo "🌐 Step 2: Fixing Vercel Frontend Configuration..."
echo "---------------------------------------------------"

if command -v vercel &> /dev/null; then
    echo "🔧 Updating Vercel environment variables..."
    
    # Navigate to frontend directory
    cd frontend
    
    # Update environment variables for production
    echo "$RAILWAY_BACKEND_URL" | vercel env add NEXT_PUBLIC_API_BASE_URL production --force
    echo "dev-g8trhgbfdq2sk2m8.us.auth0.com" | vercel env add NEXT_PUBLIC_AUTH0_DOMAIN production --force
    echo "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr" | vercel env add NEXT_PUBLIC_AUTH0_CLIENT_ID production --force
    
    echo "✅ Vercel environment variables updated!"
    
    # Trigger deployment
    echo "⚡ Deploying Vercel frontend..."
    vercel --prod
    
    echo "🎉 Vercel deployment started!"
    
    cd ..
else
    echo "⚠️  Vercel CLI not available. Please run frontend/fix-vercel-cors.sh manually."
fi

echo ""

# Step 3: Auth0 Configuration Instructions
echo "🔐 Step 3: Auth0 Configuration Required..."
echo "-------------------------------------------"
echo ""
echo "📋 MANUAL STEP: Update Auth0 Application Settings"
echo "   1. Go to https://manage.auth0.com/"
echo "   2. Navigate to Applications → Applications"
echo "   3. Select application: mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
echo "   4. Update the following fields:"
echo ""
echo "   📌 Allowed Callback URLs:"
echo "      http://localhost:3000/callback,$VERCEL_FRONTEND_URL/callback"
echo ""
echo "   📌 Allowed Logout URLs:"
echo "      http://localhost:3000/login,$VERCEL_FRONTEND_URL/login"
echo ""
echo "   📌 Allowed Web Origins:"
echo "      http://localhost:3000,$VERCEL_FRONTEND_URL"
echo ""
echo "   📌 Allowed Origins (CORS):"
echo "      http://localhost:3000,$VERCEL_FRONTEND_URL"
echo ""
echo "   5. Click 'Save Changes'"
echo ""
echo "📖 Detailed instructions: docs/AUTH0_CONFIGURATION_FIX.md"

echo ""

# Step 4: Verification Instructions
echo "✅ Step 4: Verification Steps..."
echo "--------------------------------"
echo ""
echo "After Auth0 configuration is complete:"
echo ""
echo "1. 🧪 Test Backend Health:"
echo "   curl -X GET \"$RAILWAY_BACKEND_URL/health\""
echo ""
echo "2. 🔗 Test Auth0 URL Endpoint:"
echo "   curl -X GET \"$RAILWAY_BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$VERCEL_FRONTEND_URL/callback\""
echo ""
echo "3. 🌐 Test Frontend Login:"
echo "   - Navigate to: $VERCEL_FRONTEND_URL/login"
echo "   - Click 'Login with Auth0'"
echo "   - Complete authentication flow"
echo ""
echo "4. 📊 Access Dashboard:"
echo "   - After login, access: $VERCEL_FRONTEND_URL/dashboard"
echo "   - Test organization switching and user management"

echo ""
echo "🎉 CORS Configuration Fix Complete!"
echo "===================================="
echo ""
echo "📝 Summary of Changes:"
echo "   ✅ Railway CORS origins updated to include Vercel domain"
echo "   ✅ Railway Auth0 callback URL updated"
echo "   ✅ Vercel environment variables updated"
echo "   ⏳ Auth0 configuration requires manual update"
echo ""
echo "🚀 Both platforms are deploying with updated configurations."
echo "   Monitor deployments at:"
echo "   - Railway: https://railway.app"
echo "   - Vercel: https://vercel.com"
echo ""
echo "📖 For detailed Auth0 setup instructions, see:"
echo "   docs/AUTH0_CONFIGURATION_FIX.md"