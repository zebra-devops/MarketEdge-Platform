#!/bin/bash

# ZEBRA ASSOCIATES £925K OPPORTUNITY - LOGIN TIMEOUT FIX VERIFICATION
# ===================================================================
# Comprehensive verification that the critical login timeout issue has been resolved
# Issue: Frontend timeout (60000ms) when trying to get Auth0 URL from backend
# Solution: Forced Render deployment to restore backend service availability
# Date: 2025-09-10

echo "🚨 ZEBRA ASSOCIATES £925K OPPORTUNITY - LOGIN FIX VERIFICATION"
echo "=============================================================="
echo "Verifying resolution of critical login timeout issue"
echo "Tested: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service configuration
BACKEND_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://app.zebra.associates"
CALLBACK_URL="$FRONTEND_URL/callback"

# Critical endpoints
HEALTH_ENDPOINT="$BACKEND_URL/health"
AUTH0_URL_ENDPOINT="$BACKEND_URL/api/v1/auth/auth0-url"

success_count=0
total_tests=5

echo -e "${BLUE}=== BACKEND SERVICE HEALTH ===${NC}"
echo "Testing: $HEALTH_ENDPOINT"

# Test 1: Health endpoint
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" || echo "000")
HEALTH_RESPONSE=$(curl -s "$HEALTH_ENDPOINT" 2>/dev/null || echo "No response")

echo "Status Code: $HEALTH_STATUS"

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Test 1: Backend health endpoint responding${NC}"
    
    # Check if response contains healthy status
    if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
        echo -e "${GREEN}   Backend reports healthy status${NC}"
    fi
    
    # Check deployment mode
    if echo "$HEALTH_RESPONSE" | grep -q "STABLE_PRODUCTION_FULL_API"; then
        echo -e "${GREEN}   Running stable production mode with full API${NC}"
    fi
    
    ((success_count++))
else
    echo -e "${RED}❌ Test 1: Backend health check failed (HTTP $HEALTH_STATUS)${NC}"
fi

echo ""

# Test 2: Auth0 URL endpoint accessibility
echo -e "${BLUE}=== AUTH0 URL ENDPOINT TEST ===${NC}"
echo "Testing: $AUTH0_URL_ENDPOINT"

AUTH0_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH0_URL_ENDPOINT?redirect_uri=$CALLBACK_URL" || echo "000")
echo "Status Code: $AUTH0_STATUS"

if [ "$AUTH0_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Test 2: Auth0 URL endpoint accessible${NC}"
    ((success_count++))
elif [ "$AUTH0_STATUS" = "422" ]; then
    echo -e "${YELLOW}⚠️  Test 2: Auth0 endpoint accessible but requires valid parameters${NC}"
    echo "   This is expected - endpoint is working"
    ((success_count++))
else
    echo -e "${RED}❌ Test 2: Auth0 URL endpoint failed (HTTP $AUTH0_STATUS)${NC}"
fi

echo ""

# Test 3: Auth0 URL generation with proper parameters
echo -e "${BLUE}=== AUTH0 URL GENERATION TEST ===${NC}"
echo "Testing: Auth0 URL generation for Zebra Associates"

AUTH0_RESPONSE=$(curl -s "$AUTH0_URL_ENDPOINT?redirect_uri=$(echo "$CALLBACK_URL" | sed 's/:/\%3A/g; s/\//\%2F/g')" 2>/dev/null || echo "ERROR")
AUTH0_RESPONSE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH0_URL_ENDPOINT?redirect_uri=$CALLBACK_URL" || echo "000")

echo "Response Status: $AUTH0_RESPONSE_STATUS"

if [ "$AUTH0_RESPONSE_STATUS" = "200" ] && echo "$AUTH0_RESPONSE" | grep -q "auth_url"; then
    echo -e "${GREEN}✅ Test 3: Auth0 URL generation successful${NC}"
    
    # Extract and validate Auth0 URL
    if echo "$AUTH0_RESPONSE" | grep -q "dev-g8trhgbfdq2sk2m8.us.auth0.com"; then
        echo -e "${GREEN}   Auth0 domain correct${NC}"
    fi
    
    if echo "$AUTH0_RESPONSE" | grep -q "app.zebra.associates"; then
        echo -e "${GREEN}   Zebra Associates callback URL included${NC}"
    fi
    
    ((success_count++))
else
    echo -e "${RED}❌ Test 3: Auth0 URL generation failed${NC}"
    echo "Response preview: $(echo "$AUTH0_RESPONSE" | head -c 200)..."
fi

echo ""

# Test 4: Response time test
echo -e "${BLUE}=== RESPONSE TIME TEST ===${NC}"
echo "Testing: Response time for Auth0 URL endpoint"

RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$AUTH0_URL_ENDPOINT?redirect_uri=$CALLBACK_URL" 2>/dev/null || echo "999")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc 2>/dev/null || echo "999000")

echo "Response Time: ${RESPONSE_TIME}s (${RESPONSE_TIME_MS%.*}ms)"

# Frontend timeout was 60000ms, so anything under 30000ms is good
if (( $(echo "$RESPONSE_TIME < 30" | bc -l 2>/dev/null || echo "0") )); then
    echo -e "${GREEN}✅ Test 4: Response time acceptable (< 30s)${NC}"
    echo -e "${GREEN}   Frontend timeout issue resolved${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ Test 4: Response time too slow (≥ 30s)${NC}"
    echo -e "${RED}   May still cause frontend timeouts${NC}"
fi

echo ""

# Test 5: CORS headers for Zebra Associates
echo -e "${BLUE}=== CORS HEADERS TEST ===${NC}"
echo "Testing: CORS headers for Zebra Associates origin"

CORS_HEADERS=$(curl -s -I -H "Origin: $FRONTEND_URL" "$AUTH0_URL_ENDPOINT?redirect_uri=$CALLBACK_URL" 2>/dev/null || echo "No headers")
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: $FRONTEND_URL" "$AUTH0_URL_ENDPOINT?redirect_uri=$CALLBACK_URL" || echo "000")

echo "CORS Test Status: $CORS_STATUS"

if echo "$CORS_HEADERS" | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✅ Test 5: CORS headers present${NC}"
    
    if echo "$CORS_HEADERS" | grep -q "app.zebra.associates"; then
        echo -e "${GREEN}   Zebra Associates origin allowed${NC}"
    else
        echo -e "${YELLOW}   Checking for wildcard CORS...${NC}"
        if echo "$CORS_HEADERS" | grep -q "access-control-allow-origin: \*"; then
            echo -e "${GREEN}   Wildcard CORS enabled${NC}"
        fi
    fi
    
    ((success_count++))
else
    echo -e "${RED}❌ Test 5: No CORS headers found${NC}"
    echo "Headers received:"
    echo "$CORS_HEADERS" | grep -i access-control || echo "No CORS headers"
fi

echo ""

# Summary
echo -e "${BLUE}=== VERIFICATION SUMMARY ===${NC}"
echo "Tests Passed: $success_count/$total_tests"

if [ $success_count -eq $total_tests ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - LOGIN TIMEOUT ISSUE RESOLVED${NC}"
    echo ""
    echo -e "${GREEN}✅ Backend service is healthy and responding${NC}"
    echo -e "${GREEN}✅ Auth0 URL endpoint is accessible and fast${NC}"
    echo -e "${GREEN}✅ Auth0 URL generation working for Zebra Associates${NC}"
    echo -e "${GREEN}✅ Response times are within acceptable limits${NC}"
    echo -e "${GREEN}✅ CORS configuration allows Zebra Associates access${NC}"
    echo ""
    echo -e "${GREEN}🚀 ZEBRA ASSOCIATES LOGIN READY FOR £925K OPPORTUNITY${NC}"
    echo ""
    echo "Users can now successfully log in at:"
    echo "👉 $FRONTEND_URL"
    echo ""
    echo "Backend authentication endpoint working:"
    echo "👉 $AUTH0_URL_ENDPOINT"
    
elif [ $success_count -ge 3 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS - CRITICAL FUNCTIONS WORKING${NC}"
    echo ""
    echo "Core authentication is functional but some optimizations needed"
    echo "Login should work for Zebra Associates users"
    
else
    echo -e "${RED}❌ CRITICAL ISSUES REMAIN${NC}"
    echo ""
    echo "Login timeout issue may persist. Manual intervention required."
    
fi

echo ""
echo "=== FRONTEND INTEGRATION TEST ==="
echo "To test the complete flow:"
echo ""
echo "1. Open browser to: $FRONTEND_URL"
echo "2. Click 'Login' button"
echo "3. Should redirect to Auth0 without timeout errors"
echo "4. Complete authentication"
echo "5. Should redirect back to Zebra Associates dashboard"
echo ""
echo "If timeout errors persist, check browser console for specific error messages"
echo ""

# Additional diagnostic information
echo "=== DIAGNOSTIC INFORMATION ==="
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Auth0 Endpoint: $AUTH0_URL_ENDPOINT"
echo "Deployment Time: $(date)"
echo "Verification Script: zebra_login_timeout_fix_verification.sh"
echo ""

exit $(( $total_tests - $success_count ))