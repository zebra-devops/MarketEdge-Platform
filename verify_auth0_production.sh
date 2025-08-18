#!/bin/bash

# Auth0 Production Configuration Verification
# Purpose: Verify Auth0 is properly configured in production
# Date: 2025-08-18

echo "========================================="
echo "Auth0 Production Configuration Check"
echo "========================================="

BACKEND_URL="https://marketedge-platform.onrender.com"

# Test 1: Check if Auth0 URL generation works (doesn't require secret)
echo "1. Testing Auth0 URL generation (no secret required)..."
AUTH_URL_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback")
if echo "$AUTH_URL_RESPONSE" | grep -q "auth_url"; then
    echo "✅ Auth0 URL generation working"
    echo "$AUTH_URL_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'  Domain: {data[\"auth_url\"].split(\"/\")[2]}')"
else
    echo "❌ Auth0 URL generation failed"
fi

echo ""

# Test 2: Test with various auth code patterns
echo "2. Testing different authorization code patterns..."

# Test with a short test code
echo "  Testing short test code..."
SHORT_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: https://app.zebra.associates" \
    -d "code=test123&redirect_uri=https://app.zebra.associates/callback" \
    -w "\n%{http_code}")
STATUS_SHORT=$(echo "$SHORT_RESPONSE" | tail -n1)
echo "  Short code status: $STATUS_SHORT"

# Test with a realistic-length test code
echo "  Testing realistic-length test code..."
LONG_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: https://app.zebra.associates" \
    -d "code=test_auth_code_with_proper_length_1234567890&redirect_uri=https://app.zebra.associates/callback" \
    -w "\n%{http_code}")
STATUS_LONG=$(echo "$LONG_RESPONSE" | tail -n1)
echo "  Long code status: $STATUS_LONG"

# Test with Auth0-like code pattern
echo "  Testing Auth0-pattern code..."
AUTH0_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: https://app.zebra.associates" \
    -d "code=sAAizkCJKe_test&redirect_uri=https://app.zebra.associates/callback" \
    -w "\n%{http_code}")
STATUS_AUTH0=$(echo "$AUTH0_RESPONSE" | tail -n1)
echo "  Auth0-pattern code status: $STATUS_AUTH0"

echo ""

# Test 3: Check error response content
echo "3. Analyzing error responses..."
ERROR_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: https://app.zebra.associates" \
    -d "code=analyze_error&redirect_uri=https://app.zebra.associates/callback")
echo "  Error response: $ERROR_RESPONSE"

echo ""

# Test 4: Verify CORS headers
echo "4. Verifying CORS configuration..."
CORS_TEST=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/v1/auth/login" \
    -H "Origin: https://app.zebra.associates" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" 2>&1 | grep -i "access-control-allow-origin")
if [[ -n "$CORS_TEST" ]]; then
    echo "✅ CORS headers present: $CORS_TEST"
else
    echo "❌ CORS headers missing"
fi

echo ""

# Summary
echo "========================================="
echo "ANALYSIS SUMMARY"
echo "========================================="

if [[ "$STATUS_SHORT" == "400" && "$STATUS_LONG" == "400" && "$STATUS_AUTH0" == "400" ]]; then
    echo "✅ ALL TESTS PASSED - Auth0 configuration appears correct"
    echo "   All test codes properly return 400 errors"
    echo "   This suggests AUTH0_CLIENT_SECRET is configured"
    echo ""
    echo "IMPORTANT: If real Auth0 codes still return 500:"
    echo "1. The error may be in user creation/database operations"
    echo "2. Check Render logs for specific error details"
    echo "3. Verify database connection in production"
elif [[ "$STATUS_SHORT" == "500" || "$STATUS_LONG" == "500" || "$STATUS_AUTH0" == "500" ]]; then
    echo "⚠️ WARNING - 500 errors detected"
    echo "   This suggests AUTH0_CLIENT_SECRET may be missing"
    echo ""
    echo "ACTION REQUIRED:"
    echo "1. Log into Render dashboard"
    echo "2. Navigate to Environment Variables"
    echo "3. Ensure AUTH0_CLIENT_SECRET is set"
    echo "4. Restart the service after adding the secret"
else
    echo "❓ UNEXPECTED RESULTS"
    echo "   Status codes: Short=$STATUS_SHORT, Long=$STATUS_LONG, Auth0=$STATUS_AUTH0"
    echo "   Further investigation needed"
fi

echo ""
echo "Next step: Check Render deployment logs for detailed error messages"
echo "========================================="