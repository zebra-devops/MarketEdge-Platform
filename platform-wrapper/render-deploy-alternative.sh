#!/bin/bash

echo "🚀 MarketEdge Epic 2: Alternative Render Deployment Methods"
echo "=========================================================="
echo
echo "ISSUE: Render CLI token generation failed - Using alternative approaches"
echo
echo "📋 DEPLOYMENT OPTIONS (Choose One):"
echo
echo "1. GITHUB REPOSITORY DEPLOYMENT (Recommended):"
echo "   ➤ Open: https://dashboard.render.com"
echo "   ➤ Click 'New' → 'Web Service'"
echo "   ➤ Connect GitHub: zebraassociates-projects/platform-wrapper"
echo "   ➤ Configure manually:"
echo "     - Name: marketedge-platform"
echo "     - Runtime: Docker"
echo "     - Docker Context: ./backend"
echo "     - Dockerfile Path: ./backend/Dockerfile"
echo "     - Plan: Standard"
echo
echo "2. BLUEPRINT VIA WEB INTERFACE:"
echo "   ➤ Open: https://dashboard.render.com"
echo "   ➤ Click 'New' → 'Blueprint'"
echo "   ➤ Upload file: backend/render.yaml"
echo "   ➤ Follow setup wizard"
echo
echo "3. MANUAL SERVICE CREATION:"
echo "   ➤ Create PostgreSQL database first"
echo "   ➤ Create Redis instance"
echo "   ➤ Create web service with environment variables"
echo
echo "🔧 REQUIRED ENVIRONMENT VARIABLES:"
echo "Set these in Render dashboard after creating service:"
echo
cat << 'EOF'
# === Core Settings ===
PORT=80
FASTAPI_PORT=8000
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# === Auth0 (CRITICAL) ===
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
AUTH0_CLIENT_SECRET=<YOUR_SECRET_HERE>
AUTH0_CALLBACK_URL=https://marketedge-platform.onrender.com/callback

# === CORS (Include Vercel URL) ===
CORS_ORIGINS=["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","https://marketedge-frontend.onrender.com","http://localhost:3000"]

# === Security ===
JWT_SECRET_KEY=<GENERATE_RANDOM_STRING>
JWT_ALGORITHM=HS256

# === Database (Auto-filled by Render) ===
DATABASE_URL=<AUTO_FROM_POSTGRES>
REDIS_URL=<AUTO_FROM_REDIS>
EOF

echo
echo "🔗 DATABASE SETUP:"
echo "1. Create PostgreSQL:"
echo "   - Name: marketedge-postgres"
echo "   - Database: marketedge_production"
echo "   - User: marketedge_user"
echo "   - Plan: Standard"
echo
echo "2. Create Redis:"
echo "   - Name: marketedge-redis"
echo "   - Plan: Standard"
echo
echo "⚡ DEPLOYMENT STATUS:"
echo "✅ Frontend: Updated to Render URL"
echo "❌ Backend: Manual deployment required (token issue)"
echo "❌ CORS: Will resolve after backend deploys"
echo
echo "🚨 CRITICAL: Add Vercel URL to CORS configuration:"
echo "CORS_ORIGINS must include: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
echo
echo "📞 NEXT STEPS:"
echo "1. Deploy backend using one of the methods above"
echo "2. Set all environment variables (especially AUTH0_CLIENT_SECRET)"
echo "3. Test: curl https://marketedge-platform.onrender.com/health"
echo "4. Update Auth0 callback URLs"
echo "5. Test frontend authentication flow"
echo