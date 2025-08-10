#!/bin/bash

# Railway Deployment Verification Script
# Tests all aspects of the deployed application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the deployment URL
get_service_url() {
    railway domain 2>/dev/null | head -n1 | sed 's/https\?:\/\//https:\/\//' || echo ""
}

# Test endpoint with timeout
test_endpoint() {
    local url=$1
    local endpoint=$2
    local expected_status=${3:-200}
    local timeout=${4:-10}
    
    full_url="${url}${endpoint}"
    
    log_info "Testing: $full_url"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time $timeout "$full_url" 2>/dev/null || echo "HTTPSTATUS:000")
    http_status=$(echo "$response" | grep -o "HTTPSTATUS:.*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTPSTATUS:.*//')
    
    if [ "$http_status" -eq "$expected_status" ]; then
        log_success "✓ $endpoint - Status: $http_status"
        return 0
    else
        log_error "✗ $endpoint - Expected: $expected_status, Got: $http_status"
        if [ ! -z "$body" ] && [ ${#body} -lt 200 ]; then
            echo "  Response: $body"
        fi
        return 1
    fi
}

# Ensure we're in the backend directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

log_info "Starting Railway deployment verification..."
echo ""

# Check if we're connected to Railway
log_info "Checking Railway project connection..."
if ! railway status &>/dev/null; then
    log_error "Not connected to Railway project. Run 'railway link' first."
    exit 1
fi

log_success "Connected to Railway project"
railway status
echo ""

# Get service URL
log_info "Retrieving service URL..."
SERVICE_URL=$(get_service_url)

if [ -z "$SERVICE_URL" ]; then
    log_error "Could not retrieve service URL. Make sure your service is deployed and has a domain."
    log_info "You can set a domain with: railway domain"
    exit 1
fi

log_success "Service URL: $SERVICE_URL"
echo ""

# Test basic endpoints
log_info "Testing basic endpoints..."
failed_tests=0

# Health check
if test_endpoint "$SERVICE_URL" "/health" 200 30; then
    echo ""
else
    ((failed_tests++))
fi

# API documentation
if test_endpoint "$SERVICE_URL" "/api/v1/docs" 200 10; then
    echo ""
else
    ((failed_tests++))
fi

# OpenAPI spec
if test_endpoint "$SERVICE_URL" "/api/v1/openapi.json" 200 10; then
    echo ""
else
    ((failed_tests++))
fi

# Root endpoint
if test_endpoint "$SERVICE_URL" "/" 200 10; then
    echo ""
else
    ((failed_tests++))
fi

# Test database connectivity (through health endpoint with detailed check)
log_info "Testing database connectivity..."
health_response=$(curl -s --max-time 15 "${SERVICE_URL}/health" 2>/dev/null || echo "{}")
if echo "$health_response" | grep -q "database.*healthy\|db.*ok\|status.*ok"; then
    log_success "✓ Database connectivity appears healthy"
else
    log_warning "⚠ Database health status unclear. Response: $health_response"
    ((failed_tests++))
fi
echo ""

# Test Redis connectivity (if rate limiting is enabled)
log_info "Testing Redis connectivity..."
redis_test_response=$(curl -s --max-time 15 "${SERVICE_URL}/api/v1/health" 2>/dev/null || echo "{}")
if echo "$redis_test_response" | grep -q "redis.*healthy\|cache.*ok"; then
    log_success "✓ Redis connectivity appears healthy"
else
    log_warning "⚠ Redis health status unclear. This may be normal if Redis health isn't exposed."
fi
echo ""

# Test rate limiting (make multiple requests)
log_info "Testing rate limiting..."
rate_limit_test() {
    for i in {1..5}; do
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 5 "${SERVICE_URL}/health" 2>/dev/null || echo "HTTPSTATUS:000")
        http_status=$(echo "$response" | grep -o "HTTPSTATUS:.*" | cut -d: -f2)
        if [ "$http_status" -eq 429 ]; then
            log_success "✓ Rate limiting is working (got 429 Too Many Requests)"
            return 0
        fi
    done
    log_warning "⚠ Rate limiting test inconclusive (no 429 responses in 5 requests)"
}

rate_limit_test
echo ""

# Check environment variables
log_info "Checking critical environment variables..."
env_vars=("DATABASE_URL" "JWT_SECRET_KEY" "ENVIRONMENT")
missing_vars=0

for var in "${env_vars[@]}"; do
    if railway variables get "$var" &>/dev/null; then
        log_success "✓ $var is set"
    else
        log_error "✗ $var is missing"
        ((missing_vars++))
    fi
done

if [ $missing_vars -eq 0 ]; then
    log_success "All critical environment variables are configured"
else
    log_warning "$missing_vars critical environment variables are missing"
    ((failed_tests++))
fi
echo ""

# Check Railway service status
log_info "Checking Railway service status..."
if railway logs --tail 10 2>/dev/null | grep -v "No logs found"; then
    log_success "✓ Service is generating logs"
else
    log_warning "⚠ No recent logs found or service may be starting up"
fi
echo ""

# Test multi-tenant endpoints (if available)
log_info "Testing multi-tenant API endpoints..."
api_endpoints=("/api/v1/health" "/api/v1/tenants" "/api/v1/auth/status")

for endpoint in "${api_endpoints[@]}"; do
    # Some endpoints might require authentication, so we allow 401 as acceptable
    if test_endpoint "$SERVICE_URL" "$endpoint" 200 10 || test_endpoint "$SERVICE_URL" "$endpoint" 401 10; then
        continue
    else
        log_warning "⚠ $endpoint not accessible"
    fi
done
echo ""

# Summary
echo "================================="
echo "DEPLOYMENT VERIFICATION SUMMARY"
echo "================================="

if [ $failed_tests -eq 0 ]; then
    log_success "🎉 All tests passed! Deployment appears to be working correctly."
    echo ""
    echo "🔗 Access your application:"
    echo "   • Service URL: $SERVICE_URL"
    echo "   • API Documentation: ${SERVICE_URL}/api/v1/docs"
    echo "   • Health Check: ${SERVICE_URL}/health"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Configure Auth0 for authentication"
    echo "   2. Set up CORS origins for your frontend"
    echo "   3. Run integration tests"
    echo "   4. Configure monitoring and alerts"
else
    log_warning "⚠️  $failed_tests issues found. Deployment may need attention."
    echo ""
    echo "🔧 Common fixes:"
    echo "   • Wait for services to fully start up (can take 2-5 minutes)"
    echo "   • Check Railway dashboard for service status and logs"
    echo "   • Verify environment variables are configured correctly"
    echo "   • Run database migrations: railway run alembic upgrade head"
    echo "   • Check Railway project: https://railway.app/project/$(railway project --id 2>/dev/null || echo 'your-project-id')"
fi

echo ""
log_info "Use 'railway logs' to view application logs"
log_info "Use 'railway shell' to access the service shell"
log_info "Use 'railway variables' to manage environment variables"