#!/bin/bash

# Test Authentication Rate Limiting
# This script verifies that rate limiting is enforced on auth endpoints

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
ENDPOINT="${BASE_URL}/api/v1/auth/auth0-url"
RATE_LIMIT=10
REQUESTS=12

echo "=========================================="
echo "Authentication Rate Limiting Test"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Endpoint: $ENDPOINT"
echo "  Rate Limit: $RATE_LIMIT requests per 5 minutes"
echo "  Test Requests: $REQUESTS"
echo ""
echo "Testing rate limit enforcement..."
echo ""

# Counter for successful and rate-limited requests
SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0

# Make requests
for i in $(seq 1 $REQUESTS); do
    echo -n "Request $i/$REQUESTS: "

    # Make request and capture HTTP status code
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "${ENDPOINT}?redirect_uri=http://localhost:3000/callback" \
        -H "Content-Type: application/json" \
        --max-time 5 \
        2>/dev/null)

    # Check status code
    if [ "$STATUS_CODE" = "200" ]; then
        echo "✓ Success (200 OK)"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    elif [ "$STATUS_CODE" = "429" ]; then
        echo "✗ Rate Limited (429 Too Many Requests)"
        RATE_LIMITED_COUNT=$((RATE_LIMITED_COUNT + 1))
    else
        echo "? Unexpected status: $STATUS_CODE"
    fi

    # Small delay between requests
    sleep 0.1
done

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo "  Successful Requests: $SUCCESS_COUNT"
echo "  Rate Limited: $RATE_LIMITED_COUNT"
echo ""

# Verify results
if [ $RATE_LIMITED_COUNT -gt 0 ]; then
    echo "✓ PASS: Rate limiting is working"
    echo "  (Blocked $RATE_LIMITED_COUNT requests after $SUCCESS_COUNT successful)"
    exit 0
else
    echo "⚠ WARNING: No rate limiting detected"
    echo "  This could mean:"
    echo "  - RATE_LIMIT_ENABLED=false in environment"
    echo "  - Redis is not available"
    echo "  - Rate limiter not properly configured"
    echo ""
    echo "  To enable rate limiting:"
    echo "  1. Set RATE_LIMIT_ENABLED=true"
    echo "  2. Ensure Redis is running: redis-cli ping"
    echo "  3. Restart the application"
    exit 1
fi
