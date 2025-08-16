#!/bin/bash

# Epic 2: Railway to Render Migration - Critical Deployment Validation
# DevOps validation script for platform restoration

set -e
set -o pipefail

echo "🚀 Epic 2: Railway to Render Migration - Critical Deployment Validation"
echo "========================================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Critical environment variables validation
RENDER_URL="${RENDER_URL:-https://marketedge-platform.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://frontend-5r7ft62po-zebraassociates-projects.vercel.app}"

echo -e "${BLUE}Configuration:${NC}"
echo "Backend URL: $RENDER_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "URL: $url"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 30 "$url" || echo "HTTPSTATUS:000")
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*$//')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ SUCCESS: $description (HTTP $http_code)${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED: $description (HTTP $http_code)${NC}"
        if [ "$http_code" != "000" ] && [ -n "$body" ]; then
            echo "Response body: $body"
        fi
        return 1
    fi
}

# Function to test CORS
test_cors() {
    local backend_url=$1
    local origin=$2
    local description=$3
    
    echo -e "${YELLOW}Testing CORS: $description${NC}"
    echo "Backend: $backend_url"
    echo "Origin: $origin"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -H "Origin: $origin" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Authorization" \
        -X OPTIONS \
        --max-time 10 \
        "$backend_url/health" 2>/dev/null || echo "HTTPSTATUS:000")
    
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$http_code" -eq 204 ] || [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ CORS SUCCESS: $description (HTTP $http_code)${NC}"
        return 0
    else
        echo -e "${RED}❌ CORS FAILED: $description (HTTP $http_code)${NC}"
        return 1
    fi
}

echo -e "${BLUE}Phase 1: Basic Backend Health Checks${NC}"
echo "============================================"

# Critical health endpoint
if test_endpoint "$RENDER_URL/health" "Backend Health Endpoint"; then
    HEALTH_PASSED=true
else
    HEALTH_PASSED=false
fi

# API docs endpoint
if test_endpoint "$RENDER_URL/docs" "API Documentation" 200; then
    DOCS_PASSED=true
else
    DOCS_PASSED=false
fi

echo ""
echo -e "${BLUE}Phase 2: CORS Validation${NC}"
echo "=========================="

# Test CORS for Vercel frontend
if test_cors "$RENDER_URL" "$FRONTEND_URL" "Vercel Frontend CORS"; then
    CORS_VERCEL_PASSED=true
else
    CORS_VERCEL_PASSED=false
fi

# Test CORS for localhost development
if test_cors "$RENDER_URL" "http://localhost:3000" "Localhost Development CORS"; then
    CORS_LOCALHOST_PASSED=true
else
    CORS_LOCALHOST_PASSED=false
fi

echo ""
echo -e "${BLUE}Phase 3: API Endpoint Validation${NC}"
echo "=================================="

# Test organization endpoints (basic functionality)
if test_endpoint "$RENDER_URL/api/v1/admin/organizations" "Organizations API" 401; then
    ORG_API_PASSED=true
else
    ORG_API_PASSED=false
fi

# Test rate limiting endpoint
if test_endpoint "$RENDER_URL/api/v1/admin/rate-limits" "Rate Limits API" 401; then
    RATE_LIMIT_API_PASSED=true
else
    RATE_LIMIT_API_PASSED=false
fi

echo ""
echo -e "${BLUE}Phase 4: Critical Business Validation${NC}"
echo "======================================"

# Test that CORS is working with actual frontend request simulation
echo -e "${YELLOW}Testing: Simulated Frontend Request${NC}"
frontend_response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -H "Origin: $FRONTEND_URL" \
    -H "Content-Type: application/json" \
    "$RENDER_URL/health" || echo "HTTPSTATUS:000")

frontend_http_code=$(echo "$frontend_response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
if [ "$frontend_http_code" -eq 200 ]; then
    echo -e "${GREEN}✅ Frontend Integration Test PASSED${NC}"
    FRONTEND_INTEGRATION_PASSED=true
else
    echo -e "${RED}❌ Frontend Integration Test FAILED (HTTP $frontend_http_code)${NC}"
    FRONTEND_INTEGRATION_PASSED=false
fi

echo ""
echo -e "${BLUE}FINAL VALIDATION REPORT${NC}"
echo "========================"

# Summary table
echo "Component                 | Status"
echo "--------------------------|--------"
echo -n "Backend Health            | "
[ "$HEALTH_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "API Documentation         | "
[ "$DOCS_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "CORS Vercel Frontend      | "
[ "$CORS_VERCEL_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "CORS Localhost Dev        | "
[ "$CORS_LOCALHOST_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "Organizations API         | "
[ "$ORG_API_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "Rate Limits API           | "
[ "$RATE_LIMIT_API_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo -n "Frontend Integration      | "
[ "$FRONTEND_INTEGRATION_PASSED" = true ] && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo ""

# Critical success criteria
CRITICAL_PASSED=0
CRITICAL_TOTAL=4

[ "$HEALTH_PASSED" = true ] && ((CRITICAL_PASSED++))
[ "$CORS_VERCEL_PASSED" = true ] && ((CRITICAL_PASSED++))
[ "$ORG_API_PASSED" = true ] && ((CRITICAL_PASSED++))
[ "$FRONTEND_INTEGRATION_PASSED" = true ] && ((CRITICAL_PASSED++))

echo -e "${BLUE}CRITICAL SUCCESS CRITERIA: $CRITICAL_PASSED/$CRITICAL_TOTAL${NC}"

if [ $CRITICAL_PASSED -eq $CRITICAL_TOTAL ]; then
    echo -e "${GREEN}"
    echo "🎉 EPIC 2 DEPLOYMENT SUCCESSFUL! 🎉"
    echo "===================================="
    echo "✅ Platform is OPERATIONAL"
    echo "✅ CORS issues RESOLVED"
    echo "✅ Frontend connectivity RESTORED"
    echo "✅ Railway to Render migration COMPLETE"
    echo -e "${NC}"
    
    echo "Next Steps:"
    echo "1. Update frontend environment variables to use: $RENDER_URL"
    echo "2. Verify £925K Odeon demo functionality"
    echo "3. Monitor deployment stability"
    
    exit 0
else
    echo -e "${RED}"
    echo "❌ EPIC 2 DEPLOYMENT INCOMPLETE"
    echo "==============================="
    echo "❌ Critical validation failures detected"
    echo "❌ Platform NOT fully operational"
    echo -e "${NC}"
    
    echo "Required Actions:"
    echo "1. Review failed components above"
    echo "2. Check Render deployment logs"
    echo "3. Verify environment variables"
    echo "4. Retry deployment if necessary"
    
    exit 1
fi