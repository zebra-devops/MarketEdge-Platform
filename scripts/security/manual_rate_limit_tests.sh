#!/bin/bash
# Manual Rate Limiting Security Tests
# Focuses on verifying security fixes work despite 405 errors

set -e

BACKEND_URL="http://localhost:8000"
LOG_FILE="/tmp/backend_test.log"

echo "=========================================="
echo "Manual Rate Limiting Security Verification"
echo "=========================================="
echo ""

# Test 1: IP Spoofing Prevention via Logs
echo "Test 1: IP Spoofing Prevention"
echo "=========================================="
echo "Making requests with X-Forwarded-For header..."

# Clear previous logs
: > /tmp/test_ips.log

# Request 1: Spoofed IP from "trusted" source
curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "X-Forwarded-For: 1.1.1.1, 8.8.8.8" \
  -H "Content-Type: application/json" \
  -d '{"code":"test","redirect_uri":"http://localhost:3000/callback"}' \
  > /dev/null 2>&1

sleep 0.5

# Request 2: No spoofing
curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"code":"test","redirect_uri":"http://localhost:3000/callback"}' \
  > /dev/null 2>&1

echo "Checking backend logs for client IP detection..."
echo ""

# Extract last 2 client_ip entries from logs
grep '"client_ip"' "$LOG_FILE" | tail -2 | while read -r line; do
  echo "$line" | grep -o '"client_ip": "[^"]*"'
done

echo ""
echo "Expected behavior:"
echo "- First request should show: \"client_ip\": \"8.8.8.8\" (trusted proxy)"
echo "- Second request should show: \"client_ip\": \"127.0.0.1\" (direct)"
echo ""

# Test 3: Redis Namespace Isolation
echo "Test 3: Redis Namespace Isolation"
echo "=========================================="

# Check environment in backend
ENV_VAR=$(grep "ENV_NAME" .env 2>/dev/null || echo "ENV_NAME=development")
echo "Environment variable: $ENV_VAR"
echo ""

# Make a request to trigger rate limiting
curl -s -X GET "$BACKEND_URL/health" > /dev/null 2>&1
sleep 0.5

echo "Checking Redis for rate limit keys..."
REDIS_KEYS=$(redis-cli keys "*")

if [ -z "$REDIS_KEYS" ]; then
    echo "⚠️  No Redis keys found - rate limiter may not be writing to Redis"
    echo "   This could be because:"
    echo "   1. Rate limiter is using in-memory storage"
    echo "   2. Keys have very short TTL"
    echo "   3. Rate limiter disabled for development"
else
    echo "Found keys:"
    echo "$REDIS_KEYS" | grep -E "(development|staging|production)" || echo "No namespaced keys"
fi

echo ""

# Test 4: Rate Limiter Initialization
echo "Test 4: Rate Limiter Configuration"
echo "=========================================="
echo "Checking backend startup logs for rate limiter init..."
echo ""

grep "auth_rate_limiter_init" "$LOG_FILE" | head -1 | python3 -m json.tool 2>/dev/null || \
  grep "auth_rate_limiter_init" "$LOG_FILE" | head -1

echo ""

# Test 5: Check if rate limiter is actually enforcing limits
echo "Test 5: Rate Limiting Enforcement"
echo "=========================================="
echo "Making rapid requests to test rate limiting..."

# Clear Redis
redis-cli flushdb > /dev/null

# Make 15 rapid requests to /health (should all succeed as no limit on health)
SUCCESS=0
for i in {1..15}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESS++))
    fi
    echo -n "."
done
echo " Done ($SUCCESS/15 succeeded)"

echo ""
echo "Note: /health endpoint may not have rate limiting (by design)"
echo "      Auth endpoints return 405 due to API router import failure"
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "✅ Test 1: Check logs above for IP spoofing prevention"
echo "❓ Test 3: Redis namespace isolation (keys may not persist)"
echo "ℹ️  Test 4: Rate limiter configuration shown above"
echo "ℹ️  Test 5: Health endpoint test completed"
echo ""
echo "BLOCKER IDENTIFIED:"
echo "- API router import failure prevents testing actual auth endpoints"
echo "- Error: cannot import name 'verify_auth0_token' from 'app.auth.auth0'"
echo "- Recommendation: Fix import issue first, then re-run tests"
echo ""
