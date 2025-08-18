#!/bin/bash

echo "========================================="
echo "Auth0 Complete Test Script"
echo "========================================="

# Test 1: Check Auth0 configuration
echo -e "\n1. Checking Auth0 Configuration..."
curl -s "https://marketedge-platform.onrender.com/api/v1/database/auth0-config-check" | python3 -m json.tool | head -20

# Test 2: Get Auth0 login URL
echo -e "\n2. Getting Auth0 Login URL..."
AUTH_URL=$(curl -s "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://app.zebra.associates/callback" | python3 -c "import sys, json; print(json.load(sys.stdin)['auth_url'])")
echo "Auth URL: ${AUTH_URL:0:100}..."

# Test 3: Direct Auth0 test with fake code
echo -e "\n3. Testing Auth0 with fake code (should get 403)..."
curl -s -X POST "https://dev-g8trhgbfdq2sk2m8.us.auth0.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&client_id=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr&client_secret=9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2&code=fake_test&redirect_uri=https://app.zebra.associates/callback" | python3 -m json.tool

echo -e "\n========================================="
echo "MANUAL TEST REQUIRED:"
echo "========================================="
echo "1. Open browser to: https://app.zebra.associates/login"
echo "2. Complete Auth0 login"
echo "3. Get the 'code' from Network tab"
echo "4. Run: ./test_auth0_complete.sh YOUR_CODE"
echo ""

if [ ! -z "$1" ]; then
    echo "Testing with provided code: ${1:0:10}..."
    
    # Test with backend endpoint
    echo -e "\n4. Testing backend with real code..."
    curl -X POST "https://marketedge-platform.onrender.com/api/v1/database/auth0-raw-test" \
      -H "Content-Type: application/json" \
      -d "{\"code\":\"$1\",\"redirect_uri\":\"https://app.zebra.associates/callback\"}" | python3 -m json.tool
    
    # Direct Auth0 test
    echo -e "\n5. Direct Auth0 test with real code..."
    curl -X POST "https://dev-g8trhgbfdq2sk2m8.us.auth0.com/oauth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "grant_type=authorization_code&client_id=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr&client_secret=9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2&code=$1&redirect_uri=https://app.zebra.associates/callback" | python3 -m json.tool
fi