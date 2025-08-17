#!/bin/bash

echo "🚀 CONTINUING RENDER DEPLOYMENT"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== STEP 1: VERIFY SERVICES ===${NC}"
echo "Checking for existing services..."
render services list 2>/dev/null || echo "Note: Services may exist even if CLI can't list them"

echo ""
echo -e "${BLUE}=== STEP 2: SET ENVIRONMENT VARIABLES ===${NC}"
echo "Setting critical environment variables..."
echo ""

# Try to set AUTH0_CLIENT_SECRET
echo "Setting AUTH0_CLIENT_SECRET..."
render env set AUTH0_CLIENT_SECRET "9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2" --service marketedge-platform 2>/dev/null || echo "⚠️  May need manual setting"

echo "Setting AUTH0_DOMAIN..."
render env set AUTH0_DOMAIN "dev-g8trhgbfdq2sk2m8.us.auth0.com" --service marketedge-platform 2>/dev/null || echo "⚠️  May need manual setting"

echo "Setting AUTH0_CLIENT_ID..."
render env set AUTH0_CLIENT_ID "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr" --service marketedge-platform 2>/dev/null || echo "⚠️  May need manual setting"

echo "Setting PORT..."
render env set PORT "8000" --service marketedge-platform 2>/dev/null || echo "⚠️  May need manual setting"

echo "Setting CORS_ORIGINS..."
render env set CORS_ORIGINS '["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]' --service marketedge-platform 2>/dev/null || echo "⚠️  May need manual setting"

echo ""
echo -e "${BLUE}=== STEP 3: MANUAL DATABASE CONFIGURATION ===${NC}"
echo ""
echo -e "${YELLOW}⚠️  MANUAL ACTION REQUIRED:${NC}"
echo ""
echo "1. Go to: https://dashboard.render.com"
echo "2. Click on 'marketedge-platform' service"
echo "3. Go to 'Environment' tab"
echo "4. Add these CRITICAL variables:"
echo ""
echo "   DATABASE_URL = [Copy from marketedge-postgres → Internal Database URL]"
echo "   REDIS_URL = [Copy from marketedge-redis → Internal Database URL]"
echo ""
echo "   If not already set, also add:"
echo "   AUTH0_CLIENT_SECRET = 9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"
echo ""
echo "5. Click 'Save Changes'"
echo "6. Click 'Manual Deploy' → 'Deploy latest commit'"
echo ""

echo -e "${BLUE}=== STEP 4: VALIDATE DEPLOYMENT ===${NC}"
echo "After deployment completes (5-10 minutes), test with:"
echo ""
echo "curl https://marketedge-platform.onrender.com/health"
echo ""
echo "Expected response: {\"status\":\"healthy\"}"
echo ""

echo -e "${GREEN}✅ Once health check passes, Epic 2 is COMPLETE!${NC}"
echo ""
echo "Platform URLs:"
echo "  Backend:  https://marketedge-platform.onrender.com"
echo "  Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
echo ""