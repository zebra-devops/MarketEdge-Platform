#!/bin/bash

echo "🚀 RENDER DEPLOYMENT - FIXED VERSION"
echo "==================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_section "CONFIGURING ENVIRONMENT VARIABLES"

# Fixed: Use quotes to prevent bash arithmetic interpretation
AUTH0_SECRET="9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"

echo "Setting AUTH0_CLIENT_SECRET..."
if render env set AUTH0_CLIENT_SECRET "$AUTH0_SECRET" --service marketedge-platform 2>/dev/null; then
    print_success "AUTH0_CLIENT_SECRET set"
else
    print_warning "Failed to set AUTH0_CLIENT_SECRET via CLI"
fi

echo "Setting AUTH0_DOMAIN..."
if render env set AUTH0_DOMAIN "dev-g8trhgbfdq2sk2m8.us.auth0.com" --service marketedge-platform 2>/dev/null; then
    print_success "AUTH0_DOMAIN set"
else
    print_warning "Failed to set AUTH0_DOMAIN via CLI"
fi

echo "Setting AUTH0_CLIENT_ID..."
if render env set AUTH0_CLIENT_ID "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr" --service marketedge-platform 2>/dev/null; then
    print_success "AUTH0_CLIENT_ID set"
else
    print_warning "Failed to set AUTH0_CLIENT_ID via CLI"
fi

echo "Setting PORT..."
if render env set PORT "8000" --service marketedge-platform 2>/dev/null; then
    print_success "PORT set"
else
    print_warning "Failed to set PORT via CLI"
fi

echo "Setting ENVIRONMENT..."
if render env set ENVIRONMENT "production" --service marketedge-platform 2>/dev/null; then
    print_success "ENVIRONMENT set"
else
    print_warning "Failed to set ENVIRONMENT via CLI"
fi

echo "Setting CORS_ORIGINS..."
CORS_VALUE='["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]'
if render env set CORS_ORIGINS "$CORS_VALUE" --service marketedge-platform 2>/dev/null; then
    print_success "CORS_ORIGINS set"
else
    print_warning "Failed to set CORS_ORIGINS via CLI"
fi

print_section "CRITICAL MANUAL STEPS REQUIRED"
echo ""
print_warning "Database URLs must be set manually in Render Dashboard:"
echo ""
echo "1. Go to: https://dashboard.render.com"
echo "2. Click: marketedge-platform service"
echo "3. Environment tab → Add these variables:"
echo ""
echo "   DATABASE_URL = [Copy from marketedge-postgres Internal Database URL]"
echo "   REDIS_URL = [Copy from marketedge-redis Internal Database URL]"
echo ""
echo "4. Click 'Save Changes'"
echo "5. Click 'Manual Deploy' → 'Deploy latest commit'"

print_section "TRIGGER DEPLOYMENT"
echo "Attempting to trigger deployment..."
if render deploy --service marketedge-platform 2>/dev/null; then
    print_success "Deployment triggered"
else
    print_warning "Use manual deployment in dashboard"
fi

print_section "VALIDATION"
echo "After deployment completes, test with:"
echo ""
echo "curl https://marketedge-platform.onrender.com/health"
echo ""
print_success "Epic 2 will be COMPLETE once health check passes!"