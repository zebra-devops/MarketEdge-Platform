#!/bin/bash

# Preview Environment Status Checker
# For PR #18 - Testing Render Blueprint Configuration

set -e

echo "🔍 Preview Environment Status Check"
echo "===================================="
echo "PR: #18"
echo "Expected URL: https://marketedge-platform-pr-18.onrender.com"
echo ""

# Configuration
PREVIEW_URL="https://marketedge-platform-pr-18.onrender.com"
HEALTH_ENDPOINT="${PREVIEW_URL}/health"
DOCS_ENDPOINT="${PREVIEW_URL}/api/v1/docs"

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2

    echo -n "Checking $name... "

    # Try to connect with timeout
    if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "✅ Available (200 OK)"
        return 0
    else
        local status=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$url")
        if [ "$status" = "000" ]; then
            echo "⏳ Not yet available (connection timeout)"
        else
            echo "❌ Error (HTTP $status)"
        fi
        return 1
    fi
}

# Main checks
echo "1. Service Availability"
echo "-----------------------"
check_endpoint "$PREVIEW_URL" "Base URL"
echo ""

echo "2. Health Endpoint"
echo "------------------"
if check_endpoint "$HEALTH_ENDPOINT" "Health Check"; then
    echo ""
    echo "Health Response:"
    curl -s "$HEALTH_ENDPOINT" | jq '{
        status: .status,
        preview_environment: .preview_environment,
        pr_number: .pr_number,
        version: .version,
        cors_configured: .cors_configured
    }' 2>/dev/null || curl -s "$HEALTH_ENDPOINT"
    echo ""
fi

echo "3. API Documentation"
echo "--------------------"
check_endpoint "$DOCS_ENDPOINT" "API Docs"
echo ""

echo "4. Preview Indicators"
echo "---------------------"
if curl -s --max-time 5 "$HEALTH_ENDPOINT" | jq -e '.preview_environment == true' > /dev/null 2>&1; then
    echo "✅ Preview environment indicator: true"
    PR_NUM=$(curl -s --max-time 5 "$HEALTH_ENDPOINT" | jq -r '.pr_number')
    echo "✅ PR number detected: $PR_NUM"
else
    echo "⏳ Preview indicators not yet available"
fi
echo ""

echo "5. CORS Headers Check"
echo "---------------------"
CORS_HEADER=$(curl -s --max-time 5 -H "Origin: https://test.example.com" -I "$HEALTH_ENDPOINT" 2>/dev/null | grep -i "access-control-allow-origin" || echo "Not found")
if [ "$CORS_HEADER" != "Not found" ]; then
    echo "✅ CORS configured: $CORS_HEADER"
else
    echo "⏳ CORS headers not detected"
fi
echo ""

echo "===================================="
echo "Summary"
echo "===================================="
if curl -s --max-time 5 "$HEALTH_ENDPOINT" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo "🎉 Preview environment is LIVE and HEALTHY!"
    echo "📍 Access at: $PREVIEW_URL"
    echo "📚 API Docs: $DOCS_ENDPOINT"
else
    echo "⏳ Preview environment is still deploying..."
    echo "⏱️  Check again in 2-3 minutes"
    echo "📊 Monitor at: https://dashboard.render.com"
fi
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"