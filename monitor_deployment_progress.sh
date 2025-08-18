#!/bin/bash

# Monitor Deployment Progress Script  
# Tracks Render deployment of critical enum fix
# Author: DevOps Engineer
# Date: 2025-08-18

set -e

echo "📊 DEPLOYMENT PROGRESS MONITOR"
echo "=============================="
echo "Monitoring: marketedge-platform.onrender.com"
echo "Target Fix: e7c70b6 enum value mismatch"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MAX_CHECKS=30  # 30 checks * 10 seconds = 5 minutes max
CHECK_INTERVAL=10
HEALTH_URL="https://marketedge-platform.onrender.com/health"

# Function to check deployment status
check_deployment_status() {
    local attempt=$1
    
    echo -e "${BLUE}Check $attempt/$MAX_CHECKS - $(date '+%H:%M:%S')${NC}"
    echo "================================="
    
    # Check service health
    HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    HEALTH_RESPONSE=$(curl -s "$HEALTH_URL" 2>/dev/null || echo "{\"error\":\"unreachable\"}")
    
    echo "Health Status: HTTP $HEALTH_CODE"
    
    case $HEALTH_CODE in
        "200")
            echo -e "${GREEN}✅ Service responding${NC}"
            
            # Check if emergency mode is gone
            if echo "$HEALTH_RESPONSE" | grep -q "emergency_mode"; then
                echo -e "${YELLOW}⚠️  Still in emergency mode (old deployment)${NC}"
                echo "Response: $HEALTH_RESPONSE"
                return 1  # Continue monitoring
            else
                echo -e "${GREEN}🎉 Emergency mode cleared! Deployment successful!${NC}"
                echo "Response: $HEALTH_RESPONSE"
                return 0  # Success
            fi
            ;;
        "503")
            echo -e "${YELLOW}🔄 Service restarting (deployment in progress)${NC}"
            return 1  # Continue monitoring
            ;;
        "502"|"504")
            echo -e "${YELLOW}🔄 Gateway timeout (service starting)${NC}"
            return 1  # Continue monitoring
            ;;
        "000")
            echo -e "${RED}❌ Service unreachable${NC}"
            return 1  # Continue monitoring
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unexpected response: HTTP $HEALTH_CODE${NC}"
            echo "Response: $HEALTH_RESPONSE"
            return 1  # Continue monitoring
            ;;
    esac
}

# Function to test auth endpoints after deployment
test_auth_endpoints() {
    echo -e "${BLUE}Testing Auth Endpoints${NC}"
    echo "====================="
    
    # Test auth0-url endpoint
    AUTH_URL_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://marketedge-platform.onrender.com/api/v1/auth0-url" 2>/dev/null)
    echo "Auth0 URL endpoint: HTTP $AUTH_URL_CODE"
    
    if [ "$AUTH_URL_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Auth0 URL endpoint working${NC}"
    else
        echo -e "${YELLOW}ℹ️  Auth0 URL endpoint: HTTP $AUTH_URL_CODE${NC}"
    fi
    
    # Test debug auth endpoint  
    DEBUG_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST -H "Content-Type: application/json" \
        -d '{"auth_code":"test","user_info":{"email":"test@example.com"}}' \
        "https://marketedge-platform.onrender.com/api/v1/debug-auth-flow" 2>/dev/null)
    echo "Debug auth endpoint: HTTP $DEBUG_AUTH_CODE"
    
    if [ "$DEBUG_AUTH_CODE" = "200" ] || [ "$DEBUG_AUTH_CODE" = "400" ]; then
        echo -e "${GREEN}✅ Debug auth endpoint working (expected 200/400)${NC}"
    else
        echo -e "${YELLOW}ℹ️  Debug auth endpoint: HTTP $DEBUG_AUTH_CODE${NC}"
    fi
    echo ""
}

# Function to show final deployment summary
show_deployment_summary() {
    local success=$1
    
    echo ""
    echo "================================="
    echo -e "${BLUE}📋 DEPLOYMENT SUMMARY${NC}"
    echo "================================="
    
    if [ "$success" = "true" ]; then
        echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
        echo ""
        echo "🎯 Critical enum fix deployed successfully"
        echo "🔧 Fix: industry=Industry.DEFAULT.value in auth.py"
        echo "🚀 Service no longer in emergency mode"
        echo "✨ Auth0 authentication should now work properly"
        echo ""
        echo -e "${GREEN}Next Steps:${NC}"
        echo "1. Test real Auth0 login flow"
        echo "2. Verify no 500 errors on user creation"
        echo "3. Monitor application logs"
        echo "4. Validate frontend integration"
        
    else
        echo -e "${RED}❌ DEPLOYMENT STATUS UNCLEAR${NC}"
        echo ""
        echo "⚠️  Service responding but status unclear"
        echo "🔍 Manual verification needed"
        echo ""
        echo -e "${YELLOW}Manual Checks Needed:${NC}"
        echo "1. Check Render dashboard deployment logs"
        echo "2. Verify latest commit deployed"
        echo "3. Test auth endpoints manually"
        echo "4. Check for any error logs"
    fi
    
    echo ""
    echo "📊 Service Status: $(curl -s -o /dev/null -w '%{http_code}' "$HEALTH_URL")"
    echo "🔗 Service URL: https://marketedge-platform.onrender.com"
    echo "📱 Dashboard: https://dashboard.render.com"
    echo ""
}

# Main monitoring loop
main() {
    echo "Starting deployment monitoring..."
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    local attempt=1
    local deployment_successful=false
    
    while [ $attempt -le $MAX_CHECKS ]; do
        if check_deployment_status $attempt; then
            deployment_successful=true
            break
        fi
        
        echo "⏳ Waiting ${CHECK_INTERVAL}s for next check..."
        echo ""
        
        sleep $CHECK_INTERVAL
        attempt=$((attempt + 1))
    done
    
    if [ "$deployment_successful" = "true" ]; then
        echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
        test_auth_endpoints
        show_deployment_summary "true"
    else
        echo -e "${YELLOW}⏰ Monitoring timeout reached${NC}"
        show_deployment_summary "false"
    fi
    
    echo "=== MONITORING COMPLETE ==="
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Monitoring stopped by user${NC}"; exit 0' INT

# Run main function
main "$@"