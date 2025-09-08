#!/bin/bash

# Railway Variable Configuration Verification Script
# Comprehensive testing and validation procedures

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
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

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

echo "🔍 Railway Variable Configuration Verification"
echo "=============================================="

# Phase 1: Authentication Check
log_info "Phase 1: Authentication verification..."
if railway whoami >/dev/null 2>&1; then
    RAILWAY_USER=$(railway whoami)
    log_success "Railway CLI authenticated as: $RAILWAY_USER"
else
    log_error "Railway CLI not authenticated"
    exit 1
fi

# Phase 2: Variable Configuration Verification
log_info "Phase 2: Variable configuration verification..."

# Check DATABASE_URL
log_test "Testing DATABASE_URL configuration..."
DB_URL=$(railway variables | grep "^DATABASE_URL" | awk '{print $3}' || echo "")

if [ -n "$DB_URL" ]; then
    if [[ "$DB_URL" == *"\${"* ]]; then
        log_success "✅ DATABASE_URL is correctly configured as reference variable: $DB_URL"
        SCORE_DB=1
    else
        log_error "❌ DATABASE_URL is hardcoded (should be reference): $DB_URL"
        SCORE_DB=0
    fi
else
    log_error "❌ DATABASE_URL not found"
    SCORE_DB=0
fi

# Check REDIS_URL
log_test "Testing REDIS_URL configuration..."
REDIS_URL=$(railway variables | grep "^REDIS_URL" | awk '{print $3}' || echo "")

if [ -n "$REDIS_URL" ]; then
    if [[ "$REDIS_URL" == *"\${"* ]]; then
        log_success "✅ REDIS_URL is correctly configured as reference variable: $REDIS_URL"
        SCORE_REDIS=1
    else
        log_error "❌ REDIS_URL is hardcoded (should be reference): $REDIS_URL"
        SCORE_REDIS=0
    fi
else
    log_error "❌ REDIS_URL not found"
    SCORE_REDIS=0
fi

# Check DATA_LAYER_ENABLED
log_test "Testing DATA_LAYER_ENABLED configuration..."
DATA_LAYER=$(railway variables | grep "^DATA_LAYER_ENABLED" | awk '{print $3}' || echo "")

if [ "$DATA_LAYER" = "false" ]; then
    log_success "✅ DATA_LAYER_ENABLED correctly set to false"
    SCORE_DATA_LAYER=1
elif [ -n "$DATA_LAYER" ]; then
    log_warning "⚠️ DATA_LAYER_ENABLED is set to: $DATA_LAYER (expected: false)"
    SCORE_DATA_LAYER=0.5
else
    log_warning "⚠️ DATA_LAYER_ENABLED not set (will default to false)"
    SCORE_DATA_LAYER=0.5
fi

# Check RATE_LIMIT_STORAGE_URL
log_test "Testing RATE_LIMIT_STORAGE_URL configuration..."
RATE_LIMIT_URL=$(railway variables | grep "^RATE_LIMIT_STORAGE_URL" | awk '{print $3}' || echo "")

if [ -n "$RATE_LIMIT_URL" ]; then
    if [[ "$RATE_LIMIT_URL" == *"\${"* && "$RATE_LIMIT_URL" == *"/1" ]]; then
        log_success "✅ RATE_LIMIT_STORAGE_URL correctly configured: $RATE_LIMIT_URL"
        SCORE_RATE_LIMIT=1
    else
        log_warning "⚠️ RATE_LIMIT_STORAGE_URL may need adjustment: $RATE_LIMIT_URL"
        SCORE_RATE_LIMIT=0.5
    fi
else
    log_warning "⚠️ RATE_LIMIT_STORAGE_URL not found"
    SCORE_RATE_LIMIT=0
fi

# Phase 3: Service Status Verification
log_info "Phase 3: Service status verification..."

log_test "Checking Railway service status..."
railway status || log_warning "Could not retrieve detailed service status"

# Phase 4: Deployment Verification
log_info "Phase 4: Deployment verification..."

log_test "Checking deployment status..."
if railway logs --lines 10 >/dev/null 2>&1; then
    log_success "✅ Deployment logs accessible"
    SCORE_DEPLOYMENT=1
else
    log_warning "⚠️ Could not access deployment logs"
    SCORE_DEPLOYMENT=0
fi

# Phase 5: Health Check Testing (if deployed)
log_info "Phase 5: Application health check testing..."

# Get Railway public URL
log_test "Attempting to get Railway application URL..."
RAILWAY_URL=$(railway status 2>/dev/null | grep -o 'https://[^[:space:]]*' || echo "")

if [ -n "$RAILWAY_URL" ]; then
    log_info "Found Railway URL: $RAILWAY_URL"
    
    # Test health endpoint
    log_test "Testing /health endpoint..."
    if curl -s --max-time 10 "$RAILWAY_URL/health" >/dev/null 2>&1; then
        log_success "✅ Health endpoint accessible"
        SCORE_HEALTH=1
    else
        log_warning "⚠️ Health endpoint not accessible (may still be deploying)"
        SCORE_HEALTH=0
    fi
    
    # Test ready endpoint
    log_test "Testing /ready endpoint..."
    if curl -s --max-time 10 "$RAILWAY_URL/ready" >/dev/null 2>&1; then
        log_success "✅ Ready endpoint accessible"
        SCORE_READY=1
    else
        log_warning "⚠️ Ready endpoint not accessible (may indicate connectivity issues)"
        SCORE_READY=0
    fi
else
    log_warning "⚠️ Could not determine Railway application URL"
    SCORE_HEALTH=0
    SCORE_READY=0
fi

# Phase 6: Configuration Summary Report
log_info "Phase 6: Configuration summary report..."

echo ""
echo "=============================================="
echo "🎯 RAILWAY VARIABLE CONFIGURATION REPORT"
echo "=============================================="
echo ""

# Configuration Status
echo "📊 Configuration Status:"
echo "DATABASE_URL:         $([ $SCORE_DB -eq 1 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "REDIS_URL:           $([ $SCORE_REDIS -eq 1 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "DATA_LAYER_ENABLED:  $([ $SCORE_DATA_LAYER -eq 1 ] && echo '✅ PASS' || echo '⚠️ WARN')"
echo "RATE_LIMIT_URL:      $([ $SCORE_RATE_LIMIT -eq 1 ] && echo '✅ PASS' || echo '⚠️ WARN')"
echo ""

# Application Status  
echo "🚀 Application Status:"
echo "Deployment:          $([ $SCORE_DEPLOYMENT -eq 1 ] && echo '✅ ACTIVE' || echo '⚠️ UNKNOWN')"
echo "Health Check:        $([ $SCORE_HEALTH -eq 1 ] && echo '✅ PASS' || echo '⚠️ FAIL/PENDING')"
echo "Ready Check:         $([ $SCORE_READY -eq 1 ] && echo '✅ PASS' || echo '⚠️ FAIL/PENDING')"
echo ""

# Overall Score Calculation
TOTAL_SCORE=$(echo "$SCORE_DB + $SCORE_REDIS + $SCORE_DATA_LAYER + $SCORE_RATE_LIMIT + $SCORE_DEPLOYMENT + $SCORE_HEALTH + $SCORE_READY" | bc)
MAX_SCORE=7
PERCENTAGE=$(echo "scale=0; $TOTAL_SCORE * 100 / $MAX_SCORE" | bc)

echo "📈 Overall Configuration Score: $TOTAL_SCORE/$MAX_SCORE ($PERCENTAGE%)"
echo ""

# Recommendations
if [ $SCORE_DB -eq 0 ]; then
    echo "🔧 ACTION REQUIRED:"
    echo "   - Fix DATABASE_URL: railway variables set DATABASE_URL=\"\${{Postgres.DATABASE_URL}}\""
fi

if [ $SCORE_REDIS -eq 0 ]; then
    echo "🔧 ACTION REQUIRED:"
    echo "   - Fix REDIS_URL: railway variables set REDIS_URL=\"\${{Redis.REDIS_URL}}\""
fi

if [ $PERCENTAGE -lt 70 ]; then
    echo ""
    echo "❌ CONFIGURATION NEEDS ATTENTION"
    echo "   Run: ./fix-railway-variables.sh"
elif [ $PERCENTAGE -lt 90 ]; then
    echo ""
    echo "⚠️ CONFIGURATION MOSTLY CORRECT"
    echo "   Minor adjustments may be needed"
else
    echo ""
    echo "✅ CONFIGURATION EXCELLENT"
    echo "   Railway variables properly configured!"
fi

echo ""
echo "🔍 Troubleshooting Commands:"
echo "   View variables: railway variables"
echo "   View logs:      railway logs --follow"
echo "   View status:    railway status"
echo "   Redeploy:       railway up --detach"
echo ""

exit 0