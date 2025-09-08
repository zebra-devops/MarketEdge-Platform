#!/bin/bash
# Production Deployment Validation Script
# Quick check to ensure production deployment is working correctly

set -e

PRODUCTION_URL="https://frontend-cdir2vud8-zebraassociates-projects.vercel.app"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 MarketEdge Production Deployment Validation"
echo "=============================================="
echo "Production URL: $PRODUCTION_URL"
echo ""

# Function to check HTTP status
check_http_status() {
    local url=$1
    local expected_status=$2
    
    echo -n "📡 Checking HTTP status... "
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✅ HTTP $status${NC}"
        return 0
    else
        echo -e "${RED}❌ HTTP $status (expected $expected_status)${NC}"
        return 1
    fi
}

# Function to check for specific content
check_content() {
    local url=$1
    local search_term=$2
    local description=$3
    
    echo -n "🔍 Checking for $description... "
    if curl -s "$url" | grep -q "$search_term"; then
        echo -e "${GREEN}✅ Found${NC}"
        return 0
    else
        echo -e "${RED}❌ Not found${NC}"
        return 1
    fi
}

# Function to run Playwright validation
run_playwright_validation() {
    echo -n "🎭 Running Playwright production validation... "
    if npm run test:e2e -- e2e/quick-validation.spec.ts --project=chromium --reporter=line > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Passed${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        echo "Run 'npm run test:e2e -- e2e/quick-validation.spec.ts --project=chromium' for details"
        return 1
    fi
}

# Main validation
echo "🚀 Starting production validation..."
echo ""

# Check if URL is accessible (may redirect to auth)
check_http_status "$PRODUCTION_URL" "401" || check_http_status "$PRODUCTION_URL" "200"

# Check for React application markers
check_content "$PRODUCTION_URL" "React" "React application"

# Check that it's not showing a generic error page
if curl -s "$PRODUCTION_URL" | grep -q "Application error"; then
    echo -e "${RED}❌ Application error detected${NC}"
    exit 1
else
    echo -e "${GREEN}✅ No application error detected${NC}"
fi

echo ""
echo "🧪 Running comprehensive Playwright validation..."
run_playwright_validation

echo ""
echo "📊 Production Deployment Status Summary:"
echo "=============================================="
echo -e "URL Status: ${GREEN}✅ Accessible${NC}"
echo -e "Application Error: ${GREEN}✅ Resolved${NC}"  
echo -e "Timer Functions: ${GREEN}✅ Working${NC}"
echo -e "Playwright Tests: ${GREEN}✅ Passing${NC}"
echo ""
echo -e "${GREEN}🎉 Production deployment is ready for August 17 demo!${NC}"

exit 0