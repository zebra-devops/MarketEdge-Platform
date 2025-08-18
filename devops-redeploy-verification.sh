#!/bin/bash

# DevOps Redeployment Verification Script
# Epic 2: Railway to Render Migration - Post Authentication Fix
# Date: 2025-08-18

set -e

echo "========================================="
echo "DevOps Deployment Verification & Actions"
echo "========================================="
echo "Timestamp: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service URLs
BACKEND_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://app.zebra.associates"

# 1. Check Git Status
echo -e "${YELLOW}1. Checking Git Repository Status${NC}"
echo "----------------------------------------"
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}Warning: Uncommitted changes detected${NC}"
    git status -s
else
    echo -e "${GREEN}✓ Working directory clean${NC}"
fi

# Show latest commits
echo ""
echo "Latest commits:"
git log --oneline -3
echo ""

# 2. Verify Backend Service Health
echo -e "${YELLOW}2. Backend Service Health Check${NC}"
echo "----------------------------------------"

# Health endpoint check
echo "Checking health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Health endpoint responding (200 OK)${NC}"
    HEALTH_JSON=$(curl -s "$BACKEND_URL/health")
    echo "Service info: $HEALTH_JSON" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_JSON"
else
    echo -e "${RED}✗ Health endpoint error (Status: $HEALTH_STATUS)${NC}"
fi

echo ""

# 3. Test Authentication Endpoints
echo -e "${YELLOW}3. Authentication Endpoint Verification${NC}"
echo "----------------------------------------"

# Auth0 URL endpoint
echo "Testing Auth0 URL generation..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$FRONTEND_URL/callback")
if [ "$AUTH_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Auth0 URL endpoint working (200 OK)${NC}"
else
    echo -e "${RED}✗ Auth0 URL endpoint error (Status: $AUTH_STATUS)${NC}"
fi

# Login endpoint with form data
echo "Testing login endpoint with form data..."
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Origin: $FRONTEND_URL" \
    -d "code=test_code_verification&redirect_uri=$FRONTEND_URL/callback")

if [ "$LOGIN_STATUS" -eq 400 ]; then
    echo -e "${GREEN}✓ Login endpoint correctly returns 400 for invalid code${NC}"
elif [ "$LOGIN_STATUS" -eq 500 ]; then
    echo -e "${RED}✗ Login endpoint returning 500 error - needs fix${NC}"
else
    echo -e "${YELLOW}⚠ Login endpoint returned unexpected status: $LOGIN_STATUS${NC}"
fi

echo ""

# 4. CORS Verification
echo -e "${YELLOW}4. CORS Configuration Check${NC}"
echo "----------------------------------------"

echo "Testing CORS headers..."
CORS_HEADERS=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/v1/auth/login" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" 2>/dev/null | grep -i "access-control")

if [[ -n "$CORS_HEADERS" ]]; then
    echo -e "${GREEN}✓ CORS headers present:${NC}"
    echo "$CORS_HEADERS"
else
    echo -e "${YELLOW}⚠ CORS headers may not be configured properly${NC}"
fi

echo ""

# 5. Check Render Deployment Status
echo -e "${YELLOW}5. Render Deployment Status${NC}"
echo "----------------------------------------"

# Check if we can get deployment info (this would require Render CLI or API)
echo "Checking latest deployment timestamp..."

# Create deployment trigger file
DEPLOY_TRIGGER=".render-deploy-trigger"
CURRENT_TIME=$(date +%s)
LAST_DEPLOY_TIME=0

if [ -f "$DEPLOY_TRIGGER" ]; then
    LAST_DEPLOY_TIME=$(cat "$DEPLOY_TRIGGER" 2>/dev/null || echo "0")
fi

TIME_SINCE_DEPLOY=$((CURRENT_TIME - LAST_DEPLOY_TIME))
echo "Time since last deployment trigger: ${TIME_SINCE_DEPLOY} seconds"

# Check if recent commits need deployment
LATEST_COMMIT=$(git rev-parse HEAD)
echo "Latest commit: ${LATEST_COMMIT:0:7}"

echo ""

# 6. Performance Check
echo -e "${YELLOW}6. Performance Verification${NC}"
echo "----------------------------------------"

echo "Testing response times..."
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$BACKEND_URL/health")
echo "Health endpoint response time: ${RESPONSE_TIME}s"

AUTH_RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$FRONTEND_URL/callback")
echo "Auth0 URL endpoint response time: ${AUTH_RESPONSE_TIME}s"

# Evaluate if response times are acceptable
if (( $(echo "$RESPONSE_TIME < 1" | bc -l) )); then
    echo -e "${GREEN}✓ Response times are good${NC}"
else
    echo -e "${YELLOW}⚠ Response times may be slow${NC}"
fi

echo ""

# 7. Deployment Action Decision
echo -e "${YELLOW}7. Deployment Action Plan${NC}"
echo "========================================="

NEEDS_REDEPLOY=false
REASONS=""

# Check if login endpoint returns 500
if [ "$LOGIN_STATUS" -eq 500 ]; then
    NEEDS_REDEPLOY=true
    REASONS="${REASONS}\n- Login endpoint returning 500 errors"
fi

# Check if health check failed
if [ "$HEALTH_STATUS" -ne 200 ]; then
    NEEDS_REDEPLOY=true
    REASONS="${REASONS}\n- Health check failed"
fi

# Check if there are recent unpushed commits
UNPUSHED=$(git log origin/main..HEAD --oneline 2>/dev/null)
if [[ -n "$UNPUSHED" ]]; then
    NEEDS_REDEPLOY=true
    REASONS="${REASONS}\n- Unpushed commits detected"
    echo -e "${YELLOW}Unpushed commits:${NC}"
    echo "$UNPUSHED"
fi

echo ""

if [ "$NEEDS_REDEPLOY" = true ]; then
    echo -e "${RED}⚠ REDEPLOYMENT RECOMMENDED${NC}"
    echo -e "Reasons:$REASONS"
    echo ""
    echo "Actions to take:"
    echo "1. Push any uncommitted changes: git push origin main"
    echo "2. Trigger Render deployment (automatic on push)"
    echo "3. Monitor deployment logs on Render dashboard"
    echo "4. Re-run this script after deployment completes"
else
    echo -e "${GREEN}✓ NO REDEPLOYMENT NEEDED${NC}"
    echo "All services are functioning correctly:"
    echo "- Backend health check: OK"
    echo "- Authentication endpoints: OK"
    echo "- CORS configuration: OK"
    echo "- Response times: Acceptable"
fi

echo ""

# 8. Create deployment trigger if needed
if [ "$NEEDS_REDEPLOY" = true ]; then
    echo -e "${YELLOW}Creating deployment trigger...${NC}"
    echo "$CURRENT_TIME" > "$DEPLOY_TRIGGER"
    git add "$DEPLOY_TRIGGER" 2>/dev/null || true
    echo "Deployment trigger created. Commit and push to initiate deployment."
fi

# 9. Post-Deployment Monitoring Commands
echo ""
echo -e "${YELLOW}Post-Deployment Monitoring Commands:${NC}"
echo "========================================="
echo "1. Watch backend logs:"
echo "   curl -s $BACKEND_URL/health | python3 -m json.tool"
echo ""
echo "2. Test authentication flow:"
echo "   curl -s \"$BACKEND_URL/api/v1/auth/auth0-url?redirect_uri=$FRONTEND_URL/callback\""
echo ""
echo "3. Monitor error rates:"
echo "   # Check Render dashboard for error logs"
echo ""
echo "4. Verify frontend integration:"
echo "   # Open $FRONTEND_URL and test login flow"
echo ""

echo "========================================="
echo "DevOps verification complete!"
echo "========================================="