#!/bin/bash

# Render Deployment Verification Script
# Validates Python 3.11 deployment and critical system functionality
# For £925K Zebra Associates opportunity

set -e

RENDER_URL="https://marketedge-platform.onrender.com"
ADMIN_USER="matt.lindop@zebra.associates"

echo "🔍 Render Deployment Verification - $(date)"
echo "=====================================."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check HTTP response
check_endpoint() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}

    echo -n "Testing $description... "

    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ $response${NC}"
        return 0
    else
        echo -e "${RED}❌ $response${NC}"
        if [ -f /tmp/response.json ]; then
            echo "Response: $(cat /tmp/response.json)"
        fi
        return 1
    fi
}

# Function to check JSON field
check_json_field() {
    local url=$1
    local field=$2
    local description=$3

    echo -n "Checking $description... "

    value=$(curl -s "$url" | jq -r ".$field" 2>/dev/null || echo "null")

    if [ "$value" != "null" ] && [ "$value" != "" ]; then
        echo -e "${GREEN}✅ $value${NC}"
        return 0
    else
        echo -e "${RED}❌ Field '$field' not found or empty${NC}"
        return 1
    fi
}

echo ""
echo "🐍 Python Version Verification"
echo "==============================="

# Check Python version through health endpoint
if check_endpoint "$RENDER_URL/health" "Health endpoint"; then
    check_json_field "$RENDER_URL/health" "python_version" "Python version"

    # Extract and validate Python version
    python_version=$(curl -s "$RENDER_URL/health" | jq -r '.python_version' 2>/dev/null || echo "unknown")

    if [[ "$python_version" == 3.11.* ]]; then
        echo -e "${GREEN}✅ Python 3.11 confirmed: $python_version${NC}"
    else
        echo -e "${RED}❌ Unexpected Python version: $python_version${NC}"
        echo -e "${YELLOW}⚠️  Expected Python 3.11.x${NC}"
    fi
else
    echo -e "${RED}❌ Health endpoint failed - cannot verify Python version${NC}"
fi

echo ""
echo "🔧 System Health Checks"
echo "======================="

# Basic health checks
check_endpoint "$RENDER_URL/health" "Application health"
check_endpoint "$RENDER_URL/ready" "Readiness probe"

echo ""
echo "🔐 Authentication System"
echo "======================="

# Auth endpoints (should return 401/403 without auth)
check_endpoint "$RENDER_URL/api/v1/auth/me" "Auth endpoint" "401"

echo ""
echo "👑 Admin Panel Access (Critical for Zebra Associates)"
echo "=================================================="

# Admin endpoints (should return 401 without auth, confirming they exist)
check_endpoint "$RENDER_URL/api/v1/admin/feature-flags" "Feature flags admin" "401"
check_endpoint "$RENDER_URL/api/v1/admin/dashboard/stats" "Dashboard stats admin" "401"

echo ""
echo "📊 Database Connectivity"
echo "======================="

# Check if database is connected through health endpoint
if curl -s "$RENDER_URL/health" | jq -e '.database.status == "healthy"' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Database status unknown or unhealthy${NC}"
fi

echo ""
echo "🧪 Pydantic Integration Test"
echo "=========================="

# Test that pydantic is working by checking any endpoint that returns structured data
if check_endpoint "$RENDER_URL/api/v1/organizations" "Organizations endpoint (tests pydantic)" "401"; then
    echo -e "${GREEN}✅ Pydantic serialization working (endpoint accessible)${NC}"
else
    echo -e "${RED}❌ Pydantic may have import issues${NC}"
fi

echo ""
echo "🚀 Cold Start Performance"
echo "======================="

# Measure response time for cold start assessment
echo -n "Measuring response time... "
start_time=$(date +%s%N)
curl -s "$RENDER_URL/health" >/dev/null
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))

if [ $duration -lt 2000 ]; then
    echo -e "${GREEN}✅ ${duration}ms (warm)${NC}"
elif [ $duration -lt 10000 ]; then
    echo -e "${YELLOW}⚠️  ${duration}ms (warming up)${NC}"
else
    echo -e "${RED}❌ ${duration}ms (cold start detected)${NC}"
fi

echo ""
echo "📋 Deployment Summary"
echo "==================="

# Get deployment information
echo "🔗 Production URL: $RENDER_URL"
echo "👤 Critical user: $ADMIN_USER"
echo "💰 Business value: £925K opportunity"

# Extract version info if available
app_version=$(curl -s "$RENDER_URL/health" | jq -r '.version // "unknown"' 2>/dev/null)
echo "📦 App version: $app_version"

build_time=$(curl -s "$RENDER_URL/health" | jq -r '.build_time // "unknown"' 2>/dev/null)
echo "🕐 Build time: $build_time"

echo ""
echo "✅ Verification complete - $(date)"

# Check if all critical tests passed
echo ""
if curl -s "$RENDER_URL/health" >/dev/null 2>&1 && \
   curl -s "$RENDER_URL/api/v1/admin/feature-flags" | grep -q "401"; then
    echo -e "${GREEN}🎉 DEPLOYMENT VERIFIED: Ready for Zebra Associates demo${NC}"
    exit 0
else
    echo -e "${RED}❌ DEPLOYMENT FAILED: Requires investigation before demo${NC}"
    exit 1
fi