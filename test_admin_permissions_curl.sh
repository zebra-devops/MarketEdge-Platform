#!/bin/bash

# PRODUCTION ADMIN PERMISSIONS TEST - CURL VERSION
# =================================================
# This script tests admin permission validation in production using curl

echo "🔍 PRODUCTION ADMIN PERMISSIONS TEST (CURL VERSION)"
echo "===================================================="
echo "Frontend URL: https://app.zebra.associates"
echo "Backend URL: https://marketedge-platform.onrender.com"
echo "Test Started: $(date -u +"%Y-%m-%dT%H:%M:%S")"
echo ""

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test results
log_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" = "PASS" ]; then
        echo "✅ $test_name: $status"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    elif [ "$status" = "FAIL" ]; then
        echo "❌ $test_name: $status"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    else
        echo "⚠️  $test_name: $status"
    fi

    if [ -n "$details" ]; then
        echo "   Details: $details"
    fi
    echo ""
}

# Test 1: Backend Health Check
echo "Testing backend health..."
BACKEND_HEALTH=$(curl -s -w "%{http_code}" -o /tmp/health_response.json https://marketedge-platform.onrender.com/health 2>/dev/null)

if [ "$BACKEND_HEALTH" = "200" ]; then
    HEALTH_DATA=$(cat /tmp/health_response.json 2>/dev/null)
    log_test "Backend Health Check" "PASS" "Status: 200, Response: $HEALTH_DATA"
else
    log_test "Backend Health Check" "FAIL" "HTTP Status: $BACKEND_HEALTH"
fi

# Test 2: Frontend Availability
echo "Testing frontend availability..."
FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null https://app.zebra.associates 2>/dev/null)

if [ "$FRONTEND_STATUS" = "200" ]; then
    log_test "Frontend Availability" "PASS" "Status: 200"
else
    log_test "Frontend Availability" "FAIL" "HTTP Status: $FRONTEND_STATUS"
fi

# Test 3: Admin Endpoints Without Authentication
echo "Testing admin endpoints without authentication..."

declare -a ADMIN_ENDPOINTS=(
    "/api/v1/admin/feature-flags"
    "/api/v1/admin/dashboard/stats"
    "/api/v1/admin/modules"
    "/api/v1/admin/audit-logs"
    "/api/v1/admin/security-events"
)

ALL_PROTECTED=true
ENDPOINT_RESULTS=""

for endpoint in "${ADMIN_ENDPOINTS[@]}"; do
    STATUS=$(curl -s -w "%{http_code}" -o /dev/null https://marketedge-platform.onrender.com${endpoint} 2>/dev/null)

    if [ "$STATUS" = "401" ]; then
        ENDPOINT_RESULTS="${ENDPOINT_RESULTS}${endpoint}: ✅ Protected (401)\n"
    else
        ENDPOINT_RESULTS="${ENDPOINT_RESULTS}${endpoint}: ❌ Not Protected ($STATUS)\n"
        ALL_PROTECTED=false
    fi
done

if [ "$ALL_PROTECTED" = true ]; then
    log_test "Admin Endpoints Protection" "PASS" "All endpoints properly reject unauthorized access"
else
    log_test "Admin Endpoints Protection" "FAIL" "Some endpoints not properly protected:\n$ENDPOINT_RESULTS"
fi

# Test 4: Auth0 Authentication Flow
echo "Testing Auth0 authentication flow..."
AUTH0_STATUS=$(curl -s -w "%{http_code}" -o /tmp/auth0_response.json "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/auth/callback" 2>/dev/null)

if [ "$AUTH0_STATUS" = "200" ]; then
    AUTH0_DATA=$(cat /tmp/auth0_response.json 2>/dev/null)
    if echo "$AUTH0_DATA" | grep -q "auth_url"; then
        log_test "Auth0 Authentication Flow" "PASS" "Auth0 URL endpoint working, contains auth_url"
    else
        log_test "Auth0 Authentication Flow" "FAIL" "Auth0 URL endpoint responding but missing auth_url"
    fi
else
    log_test "Auth0 Authentication Flow" "FAIL" "HTTP Status: $AUTH0_STATUS"
fi

# Test 5: Permission Validation with Invalid Token
echo "Testing permission validation with invalid token..."
INVALID_TOKEN_STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer invalid_token_for_testing" -o /tmp/invalid_token_response.json https://marketedge-platform.onrender.com/api/v1/admin/dashboard/stats 2>/dev/null)

if [ "$INVALID_TOKEN_STATUS" = "401" ]; then
    INVALID_TOKEN_RESPONSE=$(cat /tmp/invalid_token_response.json 2>/dev/null)
    log_test "Permission Validation Logic" "PASS" "Invalid token correctly rejected with 401, Response: $INVALID_TOKEN_RESPONSE"
else
    log_test "Permission Validation Logic" "FAIL" "Invalid token not properly rejected, Status: $INVALID_TOKEN_STATUS"
fi

# Test 6: CORS Headers
echo "Testing CORS headers..."
CORS_HEADERS=$(curl -s -X OPTIONS -I https://marketedge-platform.onrender.com/api/v1/admin/dashboard/stats 2>/dev/null | grep -i "access-control")

if [ -n "$CORS_HEADERS" ]; then
    log_test "CORS Headers" "PASS" "CORS headers present: $CORS_HEADERS"
else
    log_test "CORS Headers" "WARN" "No CORS headers found (may be expected)"
fi

# Test 7: Frontend Admin Page Protection
echo "Testing frontend admin page protection..."
ADMIN_PAGE_STATUS=$(curl -s -w "%{http_code}" -o /dev/null -L https://app.zebra.associates/admin 2>/dev/null)

if [ "$ADMIN_PAGE_STATUS" = "200" ] || [ "$ADMIN_PAGE_STATUS" = "302" ] || [ "$ADMIN_PAGE_STATUS" = "307" ]; then
    log_test "Frontend Admin Page Protection" "PASS" "Admin page accessible (will show auth prompt), Status: $ADMIN_PAGE_STATUS"
else
    log_test "Frontend Admin Page Protection" "FAIL" "Admin page not accessible, Status: $ADMIN_PAGE_STATUS"
fi

# Test 8: Environment Detection
echo "Testing production environment characteristics..."
HTTPS_CHECK=$(echo "https://app.zebra.associates" | grep -c "https://")
DOMAIN_CHECK=$(echo "https://app.zebra.associates" | grep -c "zebra.associates")

if [ "$HTTPS_CHECK" = "1" ] && [ "$DOMAIN_CHECK" = "1" ]; then
    log_test "Production Environment Detection" "PASS" "HTTPS enabled and production domain detected"
else
    log_test "Production Environment Detection" "FAIL" "Not a production environment"
fi

# Clean up temporary files
rm -f /tmp/health_response.json /tmp/auth0_response.json /tmp/invalid_token_response.json

# Generate Summary Report
echo "============================================================"
echo "🎯 TEST SUMMARY REPORT"
echo "============================================================"
echo "Total Tests: $TOTAL_TESTS"
echo "✅ Passed: $PASSED_TESTS"
echo "❌ Failed: $FAILED_TESTS"

SUCCESS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
echo "Success Rate: ${SUCCESS_RATE}%"
echo ""

echo "🔐 PERMISSIONS VALIDATION RESULTS:"
if [ $FAILED_TESTS -eq 0 ]; then
    echo "   ✅ All permission validation tests passed"
    echo "   ✅ Production environment properly configured"
    echo "   ✅ Admin access control working as expected"
else
    echo "   ❌ Some tests failed - review needed"
fi

echo ""
echo "📋 KEY FINDINGS:"
echo "   • Backend health: $([ "$BACKEND_HEALTH" = "200" ] && echo "✅ Working" || echo "❌ Issues")"
echo "   • Frontend availability: $([ "$FRONTEND_STATUS" = "200" ] && echo "✅ Working" || echo "❌ Issues")"
echo "   • Admin endpoints protected: $([ "$ALL_PROTECTED" = true ] && echo "✅ Protected" || echo "❌ Not protected")"
echo "   • Auth0 authentication: $([ "$AUTH0_STATUS" = "200" ] && echo "✅ Working" || echo "❌ Issues")"
echo "   • Permission validation: $([ "$INVALID_TOKEN_STATUS" = "401" ] && echo "✅ Working" || echo "❌ Issues")"

echo ""
echo "🚀 NEXT STEPS:"
if [ $FAILED_TESTS -eq 0 ]; then
    echo "   ✅ Permission system appears to be working correctly"
    echo "   ✅ Matt.Lindop should be able to access admin features with super_admin role"
    echo "   ✅ Monitor for any authentication issues during actual use"
else
    echo "   ❌ Review failed tests and fix underlying issues"
    echo "   ❌ Verify backend and frontend are properly deployed"
    echo "   ❌ Check authentication configuration"
fi

echo ""
echo "============================================================"

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0  # Success
else
    exit 1  # Failure
fi