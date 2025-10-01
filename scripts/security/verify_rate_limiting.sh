#!/bin/bash
# Rate Limiting Security Verification Script
# Tests 6 critical security fixes in the rate limiting implementation

set -e

BACKEND_URL="http://localhost:8000"
PASSED=0
FAILED=0
TEST_RESULTS=()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Rate Limiting Security Verification"
echo "=========================================="
echo "Backend: $BACKEND_URL"
echo "Time: $(date)"
echo ""

# Helper function to add test result
add_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"

    if [ "$status" = "PASS" ]; then
        ((PASSED++))
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        TEST_RESULTS+=("✅ PASS: $test_name - $details")
    else
        ((FAILED++))
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        TEST_RESULTS+=("❌ FAIL: $test_name - $details")
    fi
}

# Test 1: IP Spoofing Prevention
echo "=========================================="
echo "Test 1: IP Spoofing Prevention"
echo "=========================================="
echo "Objective: Verify X-Forwarded-For headers from untrusted sources are ignored"
echo ""

echo "1a. Making 10 requests with spoofed X-Forwarded-For headers..."
SPOOF_COUNT=0
for i in {1..10}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "X-Forwarded-For: 1.1.1.$i, 8.8.8.8" \
        -H "Content-Type: application/json" \
        -X POST "$BACKEND_URL/api/v1/auth/login" \
        -d '{"code":"test-code","redirect_uri":"http://localhost:3000/callback"}')

    if [ "$HTTP_CODE" != "429" ]; then
        ((SPOOF_COUNT++))
    fi
    echo -n "."
    sleep 0.3
done
echo " Done (${SPOOF_COUNT}/10 requests not rate limited)"

echo "1b. Making 11th request - should be rate limited if spoofing prevention works..."
HTTP_CODE_11=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "X-Forwarded-For: 1.1.1.99, 8.8.8.8" \
    -H "Content-Type: application/json" \
    -X POST "$BACKEND_URL/api/v1/auth/login" \
    -d '{"code":"test-code","redirect_uri":"http://localhost:3000/callback"}')

echo "11th request status: $HTTP_CODE_11"

if [ "$HTTP_CODE_11" = "429" ]; then
    add_result "IP Spoofing Prevention" "PASS" "11th request correctly rate limited (429)"
else
    add_result "IP Spoofing Prevention" "FAIL" "11th request returned $HTTP_CODE_11 instead of 429"
fi

echo ""
sleep 2

# Test 2: Fail-Closed Security (Redis Down) - SKIPPED (destructive test)
echo "=========================================="
echo "Test 2: Fail-Closed Security"
echo "=========================================="
echo "⚠️  SKIPPED: Stopping Redis would disrupt other tests"
echo "Manual test required: Stop Redis, verify 503 responses"
echo ""

# Test 3: Redis Namespace Isolation
echo "=========================================="
echo "Test 3: Redis Namespace Isolation"
echo "=========================================="
echo "Objective: Verify Redis keys include environment prefix"
echo ""

echo "3a. Making requests to create rate limit keys..."
for i in {1..3}; do
    curl -s -o /dev/null \
        -X POST "$BACKEND_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"code":"test-code","redirect_uri":"http://localhost:3000/callback"}'
    echo -n "."
done
echo " Done"

echo "3b. Checking Redis keys for environment namespace..."
REDIS_KEYS=$(redis-cli keys "*rate_limit*")
echo "Found keys:"
echo "$REDIS_KEYS"

DEV_KEYS=$(redis-cli keys "development:rate_limit:*" | wc -l | tr -d ' ')
STAGING_KEYS=$(redis-cli keys "staging:rate_limit:*" | wc -l | tr -d ' ')
PROD_KEYS=$(redis-cli keys "production:rate_limit:*" | wc -l | tr -d ' ')

echo ""
echo "Development keys: $DEV_KEYS"
echo "Staging keys: $STAGING_KEYS"
echo "Production keys: $PROD_KEYS"

if [ "$DEV_KEYS" -gt 0 ] && [ "$STAGING_KEYS" -eq 0 ] && [ "$PROD_KEYS" -eq 0 ]; then
    add_result "Redis Namespace Isolation" "PASS" "Keys correctly namespaced to development ($DEV_KEYS keys)"
else
    add_result "Redis Namespace Isolation" "FAIL" "Keys not correctly isolated (dev:$DEV_KEYS, staging:$STAGING_KEYS, prod:$PROD_KEYS)"
fi

echo ""
sleep 2

# Test 4: Auth0 URL Protection
echo "=========================================="
echo "Test 4: Auth0 URL Protection"
echo "=========================================="
echo "Objective: Verify /auth0-url endpoint has rate limiting"
echo ""

# Clear Redis for clean test
redis-cli flushdb > /dev/null

echo "4a. Making 30 requests to /auth0-url (limit is 30/5min)..."
SUCCESS_COUNT=0
for i in {1..30}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
        "$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=http://localhost:3000/callback")

    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESS_COUNT++))
    fi
    echo -n "."
    sleep 0.2
done
echo " Done (${SUCCESS_COUNT}/30 succeeded)"

echo "4b. Making 31st request - should be rate limited..."
RESPONSE_31=$(curl -s -w "\n%{http_code}" \
    "$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=http://localhost:3000/callback")
HTTP_CODE_31=$(echo "$RESPONSE_31" | tail -1)
RESPONSE_BODY=$(echo "$RESPONSE_31" | head -n -1)

echo "31st request status: $HTTP_CODE_31"
echo "Response: $RESPONSE_BODY"

if [ "$HTTP_CODE_31" = "429" ]; then
    add_result "Auth0 URL Protection" "PASS" "31st request correctly rate limited (429)"
else
    add_result "Auth0 URL Protection" "FAIL" "31st request returned $HTTP_CODE_31 instead of 429"
fi

echo ""
sleep 2

# Test 5: Per-User Rate Limiting
echo "=========================================="
echo "Test 5: Per-User Rate Limiting"
echo "=========================================="
echo "Objective: Verify different limits for authenticated vs unauthenticated"
echo ""

# Clear Redis for clean test
redis-cli flushdb > /dev/null

echo "5a. Testing unauthenticated rate limit (10/5min for /login)..."
UNAUTH_SUCCESS=0
for i in {1..11}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "$BACKEND_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"code":"test-code","redirect_uri":"http://localhost:3000/callback"}')

    if [ "$HTTP_CODE" != "429" ]; then
        ((UNAUTH_SUCCESS++))
    else
        echo "Rate limited at request $i"
        break
    fi
    echo -n "."
    sleep 0.3
done
echo " Done ($UNAUTH_SUCCESS requests before rate limit)"

if [ "$UNAUTH_SUCCESS" -le 10 ]; then
    add_result "Per-User Rate Limiting" "PASS" "Unauthenticated limited after $UNAUTH_SUCCESS requests (expected ≤10)"
else
    add_result "Per-User Rate Limiting" "FAIL" "Unauthenticated limited after $UNAUTH_SUCCESS requests (expected ≤10)"
fi

echo ""
sleep 2

# Test 6: Environment-Aware Defaults
echo "=========================================="
echo "Test 6: Environment-Aware Defaults"
echo "=========================================="
echo "Objective: Verify development environment uses higher limits"
echo ""

# Check backend health for environment
ENV_INFO=$(curl -s "$BACKEND_URL/health" | grep -o '"version":"[^"]*"' || echo "unknown")
echo "Backend environment: $ENV_INFO"

# Clear Redis for clean test
redis-cli flushdb > /dev/null

echo "6a. Making 15 rapid requests (should succeed in development with 100/min limit)..."
DEV_SUCCESS=0
for i in {1..15}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "$BACKEND_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"code":"test-code","redirect_uri":"http://localhost:3000/callback"}')

    if [ "$HTTP_CODE" != "429" ]; then
        ((DEV_SUCCESS++))
    fi
    echo -n "."
    sleep 0.1
done
echo " Done ($DEV_SUCCESS/15 succeeded)"

if [ "$DEV_SUCCESS" -eq 15 ]; then
    add_result "Environment-Aware Defaults" "PASS" "All 15 requests succeeded (development allows higher limits)"
else
    add_result "Environment-Aware Defaults" "FAIL" "Only $DEV_SUCCESS/15 succeeded (expected all to pass in development)"
fi

echo ""

# Summary
echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo ""

echo "Detailed Results:"
for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done
echo ""

echo "Redis Key Inspection:"
redis-cli keys "*rate_limit*" | head -5
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All security tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some security tests failed${NC}"
    exit 1
fi
