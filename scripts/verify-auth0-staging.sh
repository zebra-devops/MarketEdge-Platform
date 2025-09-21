#!/bin/bash

# Verify Auth0 staging configuration
# Usage: ./scripts/verify-auth0-staging.sh [preview-url]

PREVIEW_URL=${1:-"http://localhost:8000"}
API_BASE="${PREVIEW_URL}/api/v1"

echo "Verifying Auth0 staging configuration..."
echo "Preview URL: $PREVIEW_URL"
echo "API Base: $API_BASE"

# Test configuration endpoint
echo ""
echo "Testing configuration endpoint..."
curl -s "${API_BASE}/config/auth0" | jq '.' || echo "Failed to get Auth0 config"

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s "${API_BASE}/config/health" | jq '.' || echo "Failed to get health status"

# Test environment endpoint
echo ""
echo "Testing environment endpoint..."
curl -s "${API_BASE}/config/environment" | jq '.' || echo "Failed to get environment config"

echo ""
echo "Verification complete."
