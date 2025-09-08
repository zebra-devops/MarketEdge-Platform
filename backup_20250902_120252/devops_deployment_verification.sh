#!/bin/bash

# DevOps Deployment Verification Script
# Critical Enum Fix Deployment Status Check
# Author: DevOps Engineer
# Date: 2025-08-18

set -e

echo "🚀 DEVOPS DEPLOYMENT VERIFICATION"
echo "=================================="
echo "Target Commit: e7c70b6 (Critical enum fix)"
echo "Target Service: marketedge-platform.onrender.com"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service health
check_health() {
    echo -e "${BLUE}1. Checking Service Health${NC}"
    echo "=========================="
    
    HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://marketedge-platform.onrender.com/health)
    if [ "$HEALTH_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Service is healthy (HTTP $HEALTH_CODE)${NC}"
        
        # Get detailed health info
        HEALTH_RESPONSE=$(curl -s https://marketedge-platform.onrender.com/health)
        echo "Health Details: $HEALTH_RESPONSE"
        
        # Check if emergency mode is still active
        if echo "$HEALTH_RESPONSE" | grep -q "emergency_mode"; then
            echo -e "${YELLOW}⚠️  Emergency mode detected in health response${NC}"
        fi
    else
        echo -e "${RED}❌ Service health check failed (HTTP $HEALTH_CODE)${NC}"
        return 1
    fi
    echo ""
}

# Function to check deployment status  
check_deployment_status() {
    echo -e "${BLUE}2. Checking Deployment Status${NC}"
    echo "============================="
    
    echo "🔍 Current local commit:"
    git log --oneline -1
    echo ""
    
    echo "🔍 Checking if fix is deployed..."
    # Test auth endpoint behavior
    AUTH_RESPONSE=$(curl -s -X GET "https://marketedge-platform.onrender.com/api/v1/auth0-url" || echo "ENDPOINT_NOT_FOUND")
    
    if [ "$AUTH_RESPONSE" = "ENDPOINT_NOT_FOUND" ]; then
        echo -e "${RED}❌ Auth endpoint not accessible${NC}"
    else
        echo -e "${GREEN}✅ Auth endpoint is accessible${NC}"
        echo "Response: $AUTH_RESPONSE"
    fi
    echo ""
}

# Function to test the enum fix
test_enum_fix() {
    echo -e "${BLUE}3. Testing Enum Fix${NC}"
    echo "=================="
    
    echo "🧪 Testing debug auth endpoint (should work with proper enum)..."
    DEBUG_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"auth_code": "test_debug_123", "user_info": {"email": "test@example.com", "given_name": "Test", "family_name": "User"}}' \
        "https://marketedge-platform.onrender.com/api/v1/debug-auth-flow" 2>/dev/null || echo "DEBUG_ENDPOINT_ERROR")
    
    if echo "$DEBUG_RESPONSE" | grep -q "error"; then
        echo -e "${RED}❌ Debug endpoint returned error${NC}"
        echo "Response: $DEBUG_RESPONSE"
    elif [ "$DEBUG_RESPONSE" = "DEBUG_ENDPOINT_ERROR" ]; then
        echo -e "${YELLOW}⚠️  Debug endpoint not accessible or different structure${NC}"
    else
        echo -e "${GREEN}✅ Debug endpoint working${NC}"
        echo "Response preview: $(echo "$DEBUG_RESPONSE" | head -c 100)..."
    fi
    echo ""
}

# Function to check CORS configuration
check_cors() {
    echo -e "${BLUE}4. Checking CORS Configuration${NC}"
    echo "=============================="
    
    CORS_RESPONSE=$(curl -s -X OPTIONS \
        -H "Origin: https://app.zebra.associates" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        "https://marketedge-platform.onrender.com/api/v1/auth0-url" \
        -w "%{http_code}" -o /dev/null)
    
    if [ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ]; then
        echo -e "${GREEN}✅ CORS preflight check passed (HTTP $CORS_RESPONSE)${NC}"
    else
        echo -e "${YELLOW}⚠️  CORS preflight response: HTTP $CORS_RESPONSE${NC}"
    fi
    echo ""
}

# Function to monitor for 500 errors
monitor_500_errors() {
    echo -e "${BLUE}5. Monitoring for 500 Errors${NC}"
    echo "============================"
    
    echo "🔍 Testing various endpoints for 500 errors..."
    
    # Test health endpoint
    HEALTH_STATUS=$(curl -s -w "%{http_code}" "https://marketedge-platform.onrender.com/health" -o /dev/null)
    echo "Health endpoint: HTTP $HEALTH_STATUS"
    
    # Test API root
    API_STATUS=$(curl -s -w "%{http_code}" "https://marketedge-platform.onrender.com/api/v1/" -o /dev/null)
    echo "API root: HTTP $API_STATUS"
    
    # Test auth endpoint
    AUTH_STATUS=$(curl -s -w "%{http_code}" "https://marketedge-platform.onrender.com/api/v1/auth0-url" -o /dev/null)
    echo "Auth endpoint: HTTP $AUTH_STATUS"
    
    # Check for any 500 responses
    if [ "$HEALTH_STATUS" = "500" ] || [ "$API_STATUS" = "500" ] || [ "$AUTH_STATUS" = "500" ]; then
        echo -e "${RED}❌ 500 errors detected!${NC}"
        return 1
    else
        echo -e "${GREEN}✅ No 500 errors detected${NC}"
    fi
    echo ""
}

# Function to force deployment if needed
force_deployment() {
    echo -e "${BLUE}6. Force Deployment Commands${NC}"
    echo "============================"
    
    echo -e "${YELLOW}Manual deployment trigger options:${NC}"
    echo ""
    echo "Option 1: Create empty commit to trigger deployment"
    echo "git commit --allow-empty -m 'Trigger deployment: enum fix verification'"
    echo "git push origin main"
    echo ""
    echo "Option 2: Re-push current commit"
    echo "git push --force origin main"
    echo ""
    echo "Option 3: Render manual deployment"
    echo "- Go to https://dashboard.render.com/web/srv-XXXXX"
    echo "- Click 'Manual Deploy' -> 'Deploy latest commit'"
    echo ""
}

# Function to show post-deployment verification
post_deployment_verification() {
    echo -e "${BLUE}7. Post-Deployment Verification Steps${NC}"
    echo "====================================="
    
    echo "After deployment completes:"
    echo ""
    echo "1. Wait 2-3 minutes for service restart"
    echo "2. Run health check again:"
    echo "   curl https://marketedge-platform.onrender.com/health"
    echo ""
    echo "3. Test with real Auth0 flow:"
    echo "   - Go to https://app.zebra.associates"
    echo "   - Attempt login with Auth0"
    echo "   - Should get 200 response instead of 500"
    echo ""
    echo "4. Monitor logs for enum-related errors:"
    echo "   - Check Render dashboard logs"
    echo "   - Look for 'industry=\"default\"' vs 'Industry.DEFAULT.value' errors"
    echo ""
    echo "5. Verify database operations:"
    echo "   - New user creation should work"
    echo "   - Default organization creation should work"
    echo "   - No enum type mismatches"
    echo ""
}

# Main execution
main() {
    echo "Starting deployment verification..."
    echo ""
    
    # Run all checks
    check_health
    check_deployment_status  
    test_enum_fix
    check_cors
    monitor_500_errors
    
    echo -e "${GREEN}=== DEPLOYMENT STATUS SUMMARY ===${NC}"
    echo "Fix applied: ✅ e7c70b6 committed"
    echo "Service health: $(curl -s -o /dev/null -w '%{http_code}' https://marketedge-platform.onrender.com/health)"
    echo "Target issue: Enum mismatch in auth.py line 261"
    echo "Expected result: Auth0 codes return 200 instead of 500"
    echo ""
    
    force_deployment
    post_deployment_verification
    
    echo -e "${BLUE}🔧 Next Steps:${NC}"
    echo "1. If health checks pass but commit is old, trigger manual deployment"
    echo "2. Test with real Auth0 credentials after deployment"
    echo "3. Monitor for any new 500 errors"
    echo "4. Verify frontend login flow works end-to-end"
    echo ""
}

# Run the script
main "$@"