#!/bin/bash

# Verify Staging Deployment Script
# Checks if Render staging services are available and configured correctly

echo "======================================"
echo "Render Staging Deployment Verification"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# URLs to test
STAGING_URL="https://marketedge-platform-staging.onrender.com"
PRODUCTION_URL="https://marketedge-platform.onrender.com"

# Function to check service health
check_service() {
    local url=$1
    local name=$2

    echo "Checking $name..."

    # Check if service exists
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url/health")

    if [ "$response" -eq 200 ]; then
        echo -e "${GREEN}✅ $name is running (HTTP $response)${NC}"

        # Get detailed health info
        health_data=$(curl -s "$url/health")

        # Parse key fields if jq is available
        if command -v jq &> /dev/null; then
            echo "  Status: $(echo "$health_data" | jq -r '.status')"
            echo "  Mode: $(echo "$health_data" | jq -r '.mode')"
            echo "  Database: $(echo "$health_data" | jq -r '.database_ready')"
        else
            echo "  Response: $health_data"
        fi
    elif [ "$response" -eq 404 ]; then
        # Check for Render-specific headers
        headers=$(curl -s -I "$url/health" 2>&1)
        if echo "$headers" | grep -q "x-render-routing: no-server"; then
            echo -e "${RED}❌ $name service does not exist on Render${NC}"
            echo "  Action Required: Create service in Render Dashboard"
        else
            echo -e "${YELLOW}⚠️  $name returned 404 (service may exist but endpoint not found)${NC}"
        fi
    else
        echo -e "${RED}❌ $name returned HTTP $response${NC}"
    fi
    echo ""
}

# Function to check Auth0 endpoint
check_auth0() {
    local url=$1
    local name=$2

    echo "Checking $name Auth0 Configuration..."

    auth0_response=$(curl -s "$url/api/v1/auth/auth0-url?redirect_uri=https://staging.zebra.associates/callback")

    if echo "$auth0_response" | grep -q "audience"; then
        echo -e "${GREEN}✅ Auth0 URL endpoint configured correctly${NC}"

        # Check for staging-specific configuration
        if echo "$auth0_response" | grep -q "zebra-app.eu.auth0.com"; then
            echo "  Auth0 Domain: zebra-app.eu.auth0.com (correct)"
        fi
    else
        echo -e "${RED}❌ Auth0 endpoint not properly configured${NC}"
        echo "  Response: $auth0_response"
    fi
    echo ""
}

# Function to test CORS
check_cors() {
    local url=$1
    local origin=$2
    local name=$3

    echo "Checking CORS for $name (Origin: $origin)..."

    cors_header=$(curl -s -I -H "Origin: $origin" "$url/health" | grep -i "access-control-allow-origin")

    if [ -n "$cors_header" ]; then
        echo -e "${GREEN}✅ CORS headers present${NC}"
        echo "  $cors_header"
    else
        echo -e "${YELLOW}⚠️  CORS headers not found${NC}"
        echo "  May need to configure CORS_ORIGINS environment variable"
    fi
    echo ""
}

# Main verification
echo "1. SERVICE AVAILABILITY"
echo "----------------------"
check_service "$PRODUCTION_URL" "Production Service"
check_service "$STAGING_URL" "Staging Service"

echo "2. AUTHENTICATION"
echo "----------------"
if curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/health" | grep -q "200"; then
    check_auth0 "$STAGING_URL" "Staging"
else
    echo -e "${YELLOW}⚠️  Skipping Auth0 check - staging service not available${NC}"
    echo ""
fi

echo "3. CORS CONFIGURATION"
echo "--------------------"
if curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/health" | grep -q "200"; then
    check_cors "$STAGING_URL" "https://staging.zebra.associates" "Staging"
else
    echo -e "${YELLOW}⚠️  Skipping CORS check - staging service not available${NC}"
    echo ""
fi

echo "4. GITHUB WORKFLOW STATUS"
echo "------------------------"
if command -v gh &> /dev/null; then
    echo "Recent staging deployment workflows:"
    gh run list --workflow=staging-deploy.yml --limit=3 | head -4
else
    echo -e "${YELLOW}⚠️  GitHub CLI not installed - cannot check workflow status${NC}"
fi
echo ""

echo "======================================"
echo "SUMMARY"
echo "======================================"

if curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✅ Staging environment is operational${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run staging smoke tests: gh workflow run staging-deploy.yml --ref staging"
    echo "2. Verify frontend at: https://staging.zebra.associates"
    echo "3. Check database migrations in Render logs"
else
    echo -e "${RED}❌ Staging environment not available${NC}"
    echo ""
    echo "Required actions:"
    echo "1. Log into Render Dashboard: https://dashboard.render.com"
    echo "2. Create service: marketedge-platform-staging"
    echo "3. Create database: marketedge-staging-db"
    echo "4. Configure environment variables from render.yaml"
    echo "5. Connect service to Blueprint for future updates"
    echo ""
    echo "See RENDER_DEPLOYMENT_DIAGNOSIS.md for detailed instructions"
fi