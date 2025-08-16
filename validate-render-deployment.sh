#!/bin/bash

echo "🔍 VALIDATING RENDER DEPLOYMENT"
echo "==============================="

BACKEND_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"

echo "Testing backend health..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response "$BACKEND_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ Backend health check: PASSED"
    cat /tmp/health_response
else
    echo "❌ Backend health check: FAILED (HTTP $HEALTH_RESPONSE)"
fi

echo ""
echo "Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: X-Requested-With" \
    -X OPTIONS "$BACKEND_URL/api/v1/health")

if echo "$CORS_RESPONSE" | grep -q "access-control-allow-origin"; then
    echo "✅ CORS configuration: WORKING"
else
    echo "❌ CORS configuration: FAILED"
    echo "Response: $CORS_RESPONSE"
fi

echo ""
echo "Testing Redis connection..."
REDIS_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/redis_response "$BACKEND_URL/api/v1/health/redis")
if [ "$REDIS_RESPONSE" = "200" ]; then
    echo "✅ Redis connection: WORKING"
else
    echo "❌ Redis connection: FAILED"
fi

echo ""
echo "Testing database connection..."
DB_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/db_response "$BACKEND_URL/api/v1/health/database")
if [ "$DB_RESPONSE" = "200" ]; then
    echo "✅ Database connection: WORKING"
else
    echo "❌ Database connection: FAILED"
fi

echo ""
echo "Testing Auth0 configuration..."
AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/auth_response "$BACKEND_URL/.well-known/jwks.json")
if [ "$AUTH_RESPONSE" = "200" ]; then
    echo "✅ Auth0 JWKS endpoint: ACCESSIBLE"
else
    echo "❌ Auth0 JWKS endpoint: FAILED"
fi

echo ""
echo "🎯 FINAL VALIDATION SUMMARY:"
echo "=============================="
if [ "$HEALTH_RESPONSE" = "200" ] && [ "$REDIS_RESPONSE" = "200" ] && [ "$DB_RESPONSE" = "200" ]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL! Platform is operational."
    echo "🔗 Backend URL: $BACKEND_URL"
    echo "🔗 Frontend URL: $FRONTEND_URL"
    echo "✅ Epic 2 Migration: COMPLETE"
else
    echo "⚠️  DEPLOYMENT ISSUES DETECTED"
    echo "Review the individual test results above"
    echo "Check Render service logs for detailed error information"
fi
