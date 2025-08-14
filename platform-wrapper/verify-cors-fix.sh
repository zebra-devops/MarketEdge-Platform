#!/bin/bash

# CORS Fix Verification Script
# Tests all endpoints and configurations after CORS fixes are deployed

set -e  # Exit on any error

echo "🔍 Verifying CORS Configuration Fix..."
echo "======================================"

# Configuration URLs
VERCEL_FRONTEND_URL="https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"
RAILWAY_BACKEND_URL="https://marketedge-backend-production.up.railway.app"

echo "Frontend URL: $VERCEL_FRONTEND_URL"
echo "Backend URL: $RAILWAY_BACKEND_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "🧪 Testing $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $response, expected $expected_status)"
        ((TESTS_FAILED++))
    fi
}

# Function to test CORS headers
test_cors() {
    local url=$1
    local origin=$2
    local description=$3
    
    echo -n "🌐 Testing CORS for $description... "
    
    response=$(curl -s -I -H "Origin: $origin" -H "Access-Control-Request-Method: GET" "$url" | grep -i "access-control-allow-origin" || echo "")
    
    if [[ $response == *"$origin"* ]] || [[ $response == *"*"* ]]; then
        echo -e "${GREEN}✅ PASSED${NC} (CORS headers present)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC} (No CORS headers for origin)"
        ((TESTS_FAILED++))
    fi
}

echo "📋 Starting endpoint tests..."
echo "-----------------------------"

# Test 1: Railway Backend Health
test_endpoint "$RAILWAY_BACKEND_URL/health" "Railway backend health"

# Test 2: Railway Backend API ready
test_endpoint "$RAILWAY_BACKEND_URL/ready" "Railway backend readiness"

# Test 3: Railway Backend Auth0 URL endpoint
test_endpoint "$RAILWAY_BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$VERCEL_FRONTEND_URL/callback" "Auth0 URL generation"

# Test 4: Vercel Frontend
test_endpoint "$VERCEL_FRONTEND_URL" "Vercel frontend"

# Test 5: Vercel Frontend Login Page
test_endpoint "$VERCEL_FRONTEND_URL/login" "Vercel login page"

echo ""
echo "🌐 Starting CORS tests..."
echo "-------------------------"

# Test 6: CORS from Vercel domain to Railway backend
test_cors "$RAILWAY_BACKEND_URL/api/v1/auth/auth0-url" "$VERCEL_FRONTEND_URL" "Vercel to Railway backend"

# Test 7: CORS preflight request
echo -n "🚁 Testing CORS preflight request... "
preflight_response=$(curl -s -I -X OPTIONS \
    -H "Origin: $VERCEL_FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    "$RAILWAY_BACKEND_URL/api/v1/auth/login" | head -1)

if [[ $preflight_response == *"200"* ]] || [[ $preflight_response == *"204"* ]]; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED${NC} (Preflight request failed)"
    ((TESTS_FAILED++))
fi

echo ""
echo "🔐 Auth0 Configuration Tests..."
echo "-------------------------------"

# Test 8: Auth0 Well-known Configuration
test_endpoint "https://dev-g8trhgbfdq2sk2m8.us.auth0.com/.well-known/openid_configuration" "Auth0 well-known config"

# Test 9: Auth0 URL Generation with correct parameters
echo -n "🔗 Testing Auth0 URL generation... "
auth0_response=$(curl -s "$RAILWAY_BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$VERCEL_FRONTEND_URL/callback")

if [[ $auth0_response == *"auth_url"* ]] && [[ $auth0_response == *"frontend-jitpuqzpd-zebraassociates-projects.vercel.app"* ]]; then
    echo -e "${GREEN}✅ PASSED${NC} (Auth0 URL contains Vercel domain)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED${NC} (Auth0 URL malformed or missing Vercel domain)"
    ((TESTS_FAILED++))
    echo "Response: $auth0_response"
fi

echo ""
echo "📊 Test Results Summary"
echo "======================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! CORS configuration is working correctly.${NC}"
    echo ""
    echo "✅ Next Steps:"
    echo "1. Navigate to: $VERCEL_FRONTEND_URL/login"
    echo "2. Click 'Login with Auth0'"
    echo "3. Complete authentication flow"
    echo "4. Verify dashboard access and organization switching"
    echo ""
    echo "🚀 Your application is ready for demo!"
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please review the configuration.${NC}"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Verify Railway environment variables are set correctly"
    echo "2. Ensure Vercel environment variables are deployed"
    echo "3. Check Auth0 application settings include Vercel domain"
    echo "4. Monitor deployment logs for any errors"
    echo ""
    echo "📖 Detailed instructions: docs/AUTH0_CONFIGURATION_FIX.md"
fi

echo ""
echo "🔍 Additional Manual Tests:"
echo "---------------------------"
echo "1. Browser Developer Console:"
echo "   - Open $VERCEL_FRONTEND_URL/login"
echo "   - Check for CORS errors in console"
echo ""
echo "2. Network Tab:"
echo "   - Monitor requests to $RAILWAY_BACKEND_URL"
echo "   - Verify response headers include Access-Control-Allow-Origin"
echo ""
echo "3. Authentication Flow:"
echo "   - Complete login process"
echo "   - Verify token storage and API requests work"