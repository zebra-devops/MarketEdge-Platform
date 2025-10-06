#!/bin/bash

# Monitor Staging Deployment Progress
# Polls the staging health endpoint until it becomes available

echo "======================================"
echo "Monitoring Staging Deployment"
echo "======================================"
echo ""
echo "Started at: $(date)"
echo "Checking: https://marketedge-platform-staging.onrender.com/health"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

STAGING_URL="https://marketedge-platform-staging.onrender.com"
MAX_RETRIES=60  # 10 minutes (10 seconds * 60)
RETRY_DELAY=10  # seconds

echo "Deployment usually takes 3-5 minutes..."
echo "Will check every ${RETRY_DELAY} seconds for up to $(($MAX_RETRIES * $RETRY_DELAY / 60)) minutes"
echo ""

attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
    attempt=$((attempt + 1))

    # Check service health
    response=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/health" 2>/dev/null)

    if [ "$response" -eq 200 ]; then
        echo ""
        echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL!${NC}"
        echo "Service is now responding at: $STAGING_URL"
        echo ""

        # Get detailed health info
        health_data=$(curl -s "$STAGING_URL/health")

        if command -v jq &> /dev/null; then
            echo "Service Details:"
            echo "  Status: $(echo "$health_data" | jq -r '.status')"
            echo "  Environment: $(echo "$health_data" | jq -r '.environment')"
            echo "  Database Ready: $(echo "$health_data" | jq -r '.database_ready')"
            echo "  Mode: $(echo "$health_data" | jq -r '.mode')"

            # Check for postgres:// handling
            if echo "$health_data" | jq -r '.database_ready' | grep -q "true"; then
                echo ""
                echo -e "${GREEN}✅ Database connection successful - postgres:// scheme handled correctly${NC}"
            fi
        else
            echo "Health Response: $health_data"
        fi

        echo ""
        echo "Next Steps:"
        echo "1. Check deployment logs in Render Dashboard for any warnings"
        echo "2. Verify database tables: psql \$DATABASE_URL -c '\dt'"
        echo "3. Test Auth0 integration: $STAGING_URL/api/v1/auth/auth0-url?redirect_uri=https://staging.zebra.associates/callback"
        echo "4. Run full verification: ./scripts/verify-staging-deployment.sh"

        exit 0
    elif [ "$response" -eq 502 ] || [ "$response" -eq 503 ]; then
        echo -ne "\r${YELLOW}⏳ Attempt $attempt/$MAX_RETRIES: Service deploying (HTTP $response)...${NC}"
    elif [ "$response" -eq 404 ]; then
        echo -ne "\r${RED}❌ Attempt $attempt/$MAX_RETRIES: Service not found (HTTP 404)${NC}"
    else
        echo -ne "\r${BLUE}🔄 Attempt $attempt/$MAX_RETRIES: HTTP $response${NC}"
    fi

    sleep $RETRY_DELAY
done

echo ""
echo ""
echo -e "${RED}❌ DEPLOYMENT TIMEOUT${NC}"
echo "Service did not become available after $(($MAX_RETRIES * $RETRY_DELAY / 60)) minutes"
echo ""
echo "Troubleshooting:"
echo "1. Check Render Dashboard for deployment logs"
echo "2. Look for postgres:// connection errors"
echo "3. Verify environment variables are set correctly"
echo "4. Check if migrations are running (may take longer on first deploy)"
echo ""
echo "Common issues:"
echo "- DATABASE_URL not set correctly"
echo "- Missing AUTH0_* environment variables"
echo "- Redis connection failure"
echo "- Migration errors on empty database"

exit 1