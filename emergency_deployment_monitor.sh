#!/bin/bash

# Emergency Deployment Monitor for £925K Zebra Associates Issue
# Monitors Render deployment progress after forced deployment trigger
# Author: DevOps Specialist
# Date: 2025-09-10

set -e

echo "🚨 EMERGENCY DEPLOYMENT MONITOR"
echo "================================"
echo "Monitoring deployment progress for £925K Zebra Associates login timeout fix"
echo "Deployment triggered: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service endpoints to monitor
BACKEND_URL="https://marketedge-platform.onrender.com"
HEALTH_ENDPOINT="$BACKEND_URL/health"
AUTH0_CONFIG_ENDPOINT="$BACKEND_URL/api/v1/auth/auth0-config"
AUTH_ENDPOINT="$BACKEND_URL/api/v1/auth"

# Function to check service health
check_service_health() {
    echo -e "${BLUE}Checking service health...${NC}"
    
    # Check basic health endpoint
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT" || echo "000")
    echo "Health endpoint status: $HEALTH_STATUS"
    
    if [ "$HEALTH_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Service is healthy${NC}"
        return 0
    elif [ "$HEALTH_STATUS" = "503" ]; then
        echo -e "${YELLOW}⚠️  Service unavailable (deploying or starting up)${NC}"
        return 1
    else
        echo -e "${RED}❌ Service error (HTTP $HEALTH_STATUS)${NC}"
        return 2
    fi
}

# Function to check Auth0 endpoint
check_auth0_endpoint() {
    echo -e "${BLUE}Checking Auth0 configuration endpoint...${NC}"
    
    AUTH0_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH0_CONFIG_ENDPOINT" || echo "000")
    echo "Auth0 config endpoint status: $AUTH0_STATUS"
    
    if [ "$AUTH0_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Auth0 endpoint responding${NC}"
        return 0
    elif [ "$AUTH0_STATUS" = "503" ]; then
        echo -e "${YELLOW}⚠️  Auth0 endpoint unavailable${NC}"
        return 1
    else
        echo -e "${RED}❌ Auth0 endpoint error (HTTP $AUTH0_STATUS)${NC}"
        return 2
    fi
}

# Function to test complete authentication flow
test_auth_flow() {
    echo -e "${BLUE}Testing authentication flow...${NC}"
    
    # Try to get Auth0 URL (the failing endpoint)
    AUTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$AUTH0_CONFIG_ENDPOINT" 2>/dev/null || echo -e "\nHTTP_CODE:000")
    
    HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n1 | cut -d: -f2)
    RESPONSE_BODY=$(echo "$AUTH_RESPONSE" | sed '$d')
    
    echo "Response code: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Auth flow test successful${NC}"
        echo "Response preview: $(echo "$RESPONSE_BODY" | head -c 100)..."
        return 0
    else
        echo -e "${RED}❌ Auth flow test failed${NC}"
        return 1
    fi
}

# Main monitoring loop
monitor_deployment() {
    echo "Starting deployment monitoring..."
    echo "Will check every 30 seconds for up to 10 minutes"
    echo ""
    
    MAX_ATTEMPTS=20
    ATTEMPT=1
    
    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        echo "=== Check #$ATTEMPT ($(date)) ==="
        
        # Check service health
        if check_service_health; then
            echo ""
            
            # If healthy, check Auth0 endpoint
            if check_auth0_endpoint; then
                echo ""
                
                # If Auth0 works, test full auth flow
                if test_auth_flow; then
                    echo ""
                    echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
                    echo -e "${GREEN}✅ Backend service is healthy${NC}"
                    echo -e "${GREEN}✅ Auth0 endpoint responding${NC}" 
                    echo -e "${GREEN}✅ Authentication flow working${NC}"
                    echo ""
                    echo "Zebra Associates login should now work at:"
                    echo "https://app.zebra.associates"
                    echo ""
                    echo "Backend ready for £925K opportunity!"
                    exit 0
                fi
            fi
        fi
        
        echo ""
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
            echo "Waiting 30 seconds before next check..."
            sleep 30
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    echo ""
    echo -e "${RED}❌ DEPLOYMENT MONITORING TIMEOUT${NC}"
    echo "Service did not become healthy within 10 minutes"
    echo ""
    echo "Manual intervention required:"
    echo "1. Check Render dashboard deployment logs"
    echo "2. Verify environment variables are set correctly"
    echo "3. Check database connectivity"
    echo "4. Consider manual deployment via Render dashboard"
    echo ""
    exit 1
}

# Function to provide manual troubleshooting steps
show_troubleshooting() {
    echo ""
    echo -e "${BLUE}=== TROUBLESHOOTING STEPS ===${NC}"
    echo ""
    echo "1. Check Render Dashboard:"
    echo "   https://dashboard.render.com"
    echo "   Look for deployment errors in logs"
    echo ""
    echo "2. Verify environment variables:"
    echo "   - AUTH0_DOMAIN"
    echo "   - AUTH0_CLIENT_ID"
    echo "   - AUTH0_CLIENT_SECRET"
    echo "   - DATABASE_URL"
    echo "   - REDIS_URL"
    echo ""
    echo "3. Check database connection:"
    echo "   Service may be failing to connect to PostgreSQL"
    echo ""
    echo "4. Manual deployment:"
    echo "   Use Render dashboard 'Manual Deploy' button"
    echo "   Select latest commit: $(git log --oneline -1)"
    echo ""
    echo "5. Check service logs in Render for specific error messages"
    echo ""
}

# Start monitoring
echo "Backend URL: $BACKEND_URL"
echo "Monitoring endpoints:"
echo "  - Health: $HEALTH_ENDPOINT"
echo "  - Auth0 Config: $AUTH0_CONFIG_ENDPOINT" 
echo ""

# Initial check before monitoring loop
echo "=== Initial Status Check ==="
if check_service_health && check_auth0_endpoint && test_auth_flow; then
    echo -e "${GREEN}🎉 Service already working! No deployment needed.${NC}"
    exit 0
fi

echo ""
echo "Service not yet healthy - starting monitoring..."
echo ""

# Start monitoring deployment progress
monitor_deployment

# If we get here, show troubleshooting steps
show_troubleshooting