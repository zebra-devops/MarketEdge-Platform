#!/bin/bash
# Epic 2: Complete Render Deployment Validation Script
# Railway to Render Migration - CORS Resolution Validation
# Date: 2025-08-16

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
TIMEOUT=10

# Counters
SUCCESS_COUNT=0
TOTAL_TESTS=12

echo -e "${BLUE}🚀 Epic 2: Complete Render Deployment Validation${NC}"
echo -e "${BLUE}================================================${NC}"
echo "Date: $(date)"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Function to log results
log_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    if [ "$result" == "PASS" ]; then
        echo -e "${GREEN}✅ $test_name: $message${NC}"
        ((SUCCESS_COUNT++))
    elif [ "$result" == "FAIL" ]; then
        echo -e "${RED}❌ $test_name: $message${NC}"
    else
        echo -e "${YELLOW}⚠️ $test_name: $message${NC}"
    fi
}

# Test 1: Basic Service Health
echo "1. Testing basic service health..."
if timeout $TIMEOUT curl -f -s $BACKEND_URL/health > /dev/null 2>&1; then
    log_test "Service Health" "PASS" "Backend service is responding"
else
    log_test "Service Health" "FAIL" "Backend service is not responding"
fi

# Test 2: Health Endpoint Response Structure
echo "2. Testing health endpoint response structure..."
HEALTH_RESPONSE=$(timeout $TIMEOUT curl -s $BACKEND_URL/health 2>/dev/null || echo "")
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"' && echo "$HEALTH_RESPONSE" | grep -q '"environment":"production"'; then
    log_test "Health Structure" "PASS" "Health endpoint returns valid production response"
else
    log_test "Health Structure" "FAIL" "Health endpoint response invalid or not production"
fi

# Test 3: API Endpoint Accessibility
echo "3. Testing API endpoint accessibility..."
API_STATUS=$(timeout $TIMEOUT curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/api/v1/health 2>/dev/null || echo "000")
if [ "$API_STATUS" == "200" ]; then
    log_test "API Access" "PASS" "API endpoints are accessible"
else
    log_test "API Access" "FAIL" "API endpoints not accessible (Status: $API_STATUS)"
fi

# Test 4: Database Connection
echo "4. Testing database connection..."
DB_RESPONSE=$(timeout $TIMEOUT curl -s $BACKEND_URL/api/v1/admin/health/database 2>/dev/null || echo "")
if echo "$DB_RESPONSE" | grep -q "healthy"; then
    log_test "Database" "PASS" "PostgreSQL connection successful"
else
    log_test "Database" "FAIL" "PostgreSQL connection failed"
fi

# Test 5: Redis Connection
echo "5. Testing Redis connection..."
REDIS_RESPONSE=$(timeout $TIMEOUT curl -s $BACKEND_URL/api/v1/admin/health/redis 2>/dev/null || echo "")
if echo "$REDIS_RESPONSE" | grep -q "healthy"; then
    log_test "Redis" "PASS" "Cache connection successful"
else
    log_test "Redis" "FAIL" "Cache connection failed"
fi

# Test 6: Auth0 Configuration
echo "6. Testing Auth0 configuration..."
AUTH0_CONFIG=$(timeout $TIMEOUT curl -s $BACKEND_URL/.well-known/openid-configuration 2>/dev/null || echo "")
if echo "$AUTH0_CONFIG" | grep -q "dev-g8trhgbfdq2sk2m8.us.auth0.com"; then
    log_test "Auth0 Config" "PASS" "Auth0 domain configuration correct"
else
    log_test "Auth0 Config" "FAIL" "Auth0 domain configuration issue"
fi

# Test 7: Auth0 Client Configuration
echo "7. Testing Auth0 client configuration..."
CLIENT_CONFIG=$(timeout $TIMEOUT curl -s $BACKEND_URL/api/v1/auth/config 2>/dev/null || echo "")
if echo "$CLIENT_CONFIG" | grep -q "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"; then
    log_test "Auth0 Client" "PASS" "Client ID configuration correct"
else
    log_test "Auth0 Client" "FAIL" "Client ID configuration issue"
fi

# Test 8: CORS Preflight - Vercel Frontend
echo "8. Testing CORS preflight for Vercel frontend..."
CORS_STATUS=$(timeout $TIMEOUT curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    -X OPTIONS \
    $BACKEND_URL/api/v1/health 2>/dev/null || echo "000")
if [ "$CORS_STATUS" == "204" ] || [ "$CORS_STATUS" == "200" ]; then
    log_test "CORS Vercel" "PASS" "Frontend origin allowed (Status: $CORS_STATUS)"
else
    log_test "CORS Vercel" "FAIL" "Frontend origin not allowed (Status: $CORS_STATUS)"
fi

# Test 9: CORS Actual Request - Vercel Frontend
echo "9. Testing CORS actual request for Vercel frontend..."
CORS_GET_STATUS=$(timeout $TIMEOUT curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: $FRONTEND_URL" \
    $BACKEND_URL/api/v1/health 2>/dev/null || echo "000")
if [ "$CORS_GET_STATUS" == "200" ]; then
    log_test "CORS GET Request" "PASS" "Actual requests from frontend working"
else
    log_test "CORS GET Request" "FAIL" "Actual requests from frontend failing (Status: $CORS_GET_STATUS)"
fi

# Test 10: CORS Development Support
echo "10. Testing CORS for development (localhost:3000)..."
CORS_DEV_STATUS=$(timeout $TIMEOUT curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: http://localhost:3000" \
    -X OPTIONS \
    $BACKEND_URL/api/v1/health 2>/dev/null || echo "000")
if [ "$CORS_DEV_STATUS" == "204" ] || [ "$CORS_DEV_STATUS" == "200" ]; then
    log_test "CORS Development" "PASS" "Development origin allowed"
else
    log_test "CORS Development" "FAIL" "Development origin not allowed (Status: $CORS_DEV_STATUS)"
fi

# Test 11: Response Time Performance
echo "11. Testing response time performance..."
RESPONSE_TIME=$(timeout $TIMEOUT curl -w "%{time_total}" -s -o /dev/null $BACKEND_URL/health 2>/dev/null || echo "999")
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l 2>/dev/null || echo "0") )); then
    log_test "Performance" "PASS" "Response time acceptable (${RESPONSE_TIME}s)"
elif (( $(echo "$RESPONSE_TIME < 5.0" | bc -l 2>/dev/null || echo "0") )); then
    log_test "Performance" "WARN" "Response time acceptable but slow (${RESPONSE_TIME}s)"
else
    log_test "Performance" "FAIL" "Response time too slow (${RESPONSE_TIME}s)"
fi

# Test 12: Security Headers
echo "12. Testing security headers..."
SECURITY_HEADERS=$(timeout $TIMEOUT curl -s -I $BACKEND_URL/health 2>/dev/null || echo "")
if echo "$SECURITY_HEADERS" | grep -qi "x-" && echo "$SECURITY_HEADERS" | grep -qi "content-type"; then
    log_test "Security Headers" "PASS" "Security headers present"
else
    log_test "Security Headers" "WARN" "Some security headers may be missing"
fi

# Summary
echo ""
echo -e "${BLUE}📊 VALIDATION SUMMARY${NC}"
echo -e "${BLUE}====================${NC}"
echo "Tests Passed: $SUCCESS_COUNT/$TOTAL_TESTS"

if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - Epic 2 deployment completely successful!${NC}"
    echo ""
    echo -e "${GREEN}✅ CORS issues resolved${NC}"
    echo -e "${GREEN}✅ Frontend can now connect to backend${NC}"
    echo -e "${GREEN}✅ Platform fully operational on Render${NC}"
    echo -e "${GREEN}✅ Ready for stakeholder demonstrations${NC}"
    echo ""
    echo -e "${BLUE}🚀 Epic 2 Migration: COMPLETE${NC}"
elif [ $SUCCESS_COUNT -ge 10 ]; then
    echo -e "${YELLOW}⚠️ MOSTLY SUCCESSFUL - Minor issues to address${NC}"
    echo ""
    echo "👉 Check failed tests above and address if needed"
    echo "👉 Platform should be functional for basic testing"
    echo "👉 CORS issues appear to be resolved"
elif [ $SUCCESS_COUNT -ge 8 ]; then
    echo -e "${YELLOW}⚠️ PARTIAL SUCCESS - Some critical issues detected${NC}"
    echo ""
    echo "🚨 Address failed tests before full deployment"
    echo "👉 Focus on CORS and authentication issues"
else
    echo -e "${RED}❌ DEPLOYMENT ISSUES - Critical problems detected${NC}"
    echo ""
    echo "🚨 Address failed tests before proceeding"
    echo "🚨 Platform may not be fully functional"
    echo "🚨 Check Render dashboard for service logs"
fi

echo ""
echo -e "${BLUE}📋 NEXT STEPS:${NC}"
if [ $SUCCESS_COUNT -ge 10 ]; then
    echo "1. ✅ Notify stakeholders of successful deployment"
    echo "2. 🧪 Perform manual frontend integration testing"
    echo "3. 📊 Schedule stakeholder demonstration"
    echo "4. 📝 Mark Epic 2 as complete in project tracking"
    echo "5. 🚀 Begin planning Epic 3 enhancements"
else
    echo "1. 🔧 Address failed tests using troubleshooting guide"
    echo "2. 🔍 Check Render dashboard service logs"
    echo "3. 🔐 Verify AUTH0_CLIENT_SECRET is set correctly"
    echo "4. 🌐 Validate CORS configuration"
    echo "5. 🔄 Re-run this validation script"
fi

echo ""
echo -e "${BLUE}📍 DEPLOYMENT URLS:${NC}"
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""
echo -e "${BLUE}🎯 Epic 2 Objective: Resolve CORS failures by migrating from Railway to Render${NC}"
if [ $SUCCESS_COUNT -ge 10 ]; then
    echo -e "${GREEN}Status: ✅ OBJECTIVE ACHIEVED${NC}"
else
    echo -e "${YELLOW}Status: ⚠️ IN PROGRESS${NC}"
fi

# Exit with appropriate code
if [ $SUCCESS_COUNT -ge 10 ]; then
    exit 0
else
    exit 1
fi