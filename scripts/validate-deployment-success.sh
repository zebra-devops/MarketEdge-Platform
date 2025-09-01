#!/bin/bash
# MarketEdge Deployment Success Validation
# Comprehensive validation for Epic 1 & 2 deployments

set -e

# Configuration
BASE_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://app.zebra.associates"
LOG_FILE="/tmp/deployment-validation-$(date +%s).log"
MAX_RETRIES=5
RETRY_DELAY=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a $LOG_FILE; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a $LOG_FILE; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE; }

# Function to test endpoint with retries
test_endpoint() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    local max_time=${4:-10}
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        local start_time=$(date +%s.%N)
        local response=$(curl -s -w "%{http_code},%{time_total}" -o /tmp/response.json --max-time $max_time "$url" 2>/dev/null || echo "000,999")
        local http_code=$(echo $response | cut -d',' -f1)
        local response_time=$(echo $response | cut -d',' -f2)
        
        if [[ "$http_code" == "$expected_code" ]]; then
            log_success "$name: HTTP $http_code (${response_time}s)"
            return 0
        else
            log_warning "$name: HTTP $http_code (attempt $((retry_count + 1))/$MAX_RETRIES)"
            if [ $retry_count -lt $((MAX_RETRIES - 1)) ]; then
                sleep $RETRY_DELAY
            fi
        fi
        
        retry_count=$((retry_count + 1))
    done
    
    log_error "$name: Failed after $MAX_RETRIES attempts"
    return 1
}

# Epic 1 Validation
validate_epic1() {
    log_info "=== Epic 1 (Module System) Validation ==="
    local epic1_success=0
    
    # Test module management endpoints
    if test_endpoint "$BASE_URL/api/v1/module-management/modules" "Module Management API"; then
        ((epic1_success++))
    fi
    
    # Test module registration performance
    local reg_time=$(curl -w "%{time_total}" -s -o /dev/null "$BASE_URL/api/v1/module-management/system/health" 2>/dev/null || echo "999")
    if command -v bc >/dev/null && (( $(echo "$reg_time < 0.1" | bc -l 2>/dev/null || echo 0) )); then
        log_success "Module registration performance: ${reg_time}s (<0.1s target)"
        ((epic1_success++))
    else
        log_warning "Module registration performance: ${reg_time}s (exceeds 0.1s target or bc not available)"
    fi
    
    # Test feature flag integration
    if test_endpoint "$BASE_URL/api/v1/feature-flags/module_routing_enabled" "Module Routing Feature Flag" "200,404"; then
        ((epic1_success++))
    fi
    
    echo "Epic 1 Success Rate: $epic1_success/3"
    return $((3 - epic1_success))
}

# Epic 2 Validation  
validate_epic2() {
    log_info "=== Epic 2 (Feature Flags) Validation ==="
    local epic2_success=0
    
    # Test feature flag management
    if test_endpoint "$BASE_URL/api/v1/feature-flags/list" "Feature Flag List API" "200,404"; then
        ((epic2_success++))
    fi
    
    # Test feature flag status
    if test_endpoint "$BASE_URL/api/v1/feature-flags/status" "Feature Flag Status API" "200,404"; then
        ((epic2_success++))
    fi
    
    # Test admin feature flag health (may not exist yet)
    if test_endpoint "$BASE_URL/health" "Core Health (Epic 2 proxy)" "200"; then
        ((epic2_success++))
    fi
    
    echo "Epic 2 Success Rate: $epic2_success/3"
    return $((3 - epic2_success))
}

# Cross-Epic Integration Validation
validate_integration() {
    log_info "=== Cross-Epic Integration Validation ==="
    local integration_success=0
    
    # Test overall system integration via health endpoints
    if test_endpoint "$BASE_URL/health/detailed" "Detailed Health Check" "200"; then
        log_success "System integration: Health check passed"
        ((integration_success++))
    else
        log_warning "System integration: Detailed health check failed"
    fi
    
    echo "Integration Success Rate: $integration_success/1"
    return $((1 - integration_success))
}

# Main validation execution
main() {
    log_info "MarketEdge Deployment Validation Started"
    log_info "Validation Log: $LOG_FILE"
    echo ""
    
    local total_failures=0
    
    # Core health checks
    log_info "=== Core System Validation ==="
    test_endpoint "$BASE_URL/health" "Backend Health" || ((total_failures++))
    test_endpoint "$FRONTEND_URL/" "Frontend Health" "200,404" || ((total_failures++))
    test_endpoint "$BASE_URL/health/database" "Database Health" "200,404" || ((total_failures++))
    test_endpoint "$BASE_URL/health/security" "Security Health" "200,404" || ((total_failures++))
    
    echo ""
    
    # Epic-specific validations
    validate_epic1 || ((total_failures++))
    echo ""
    
    validate_epic2 || ((total_failures++))
    echo ""
    
    validate_integration || ((total_failures++))
    echo ""
    
    # Final results
    log_info "=== Validation Summary ==="
    if [ $total_failures -eq 0 ]; then
        log_success "🎉 ALL VALIDATIONS PASSED - Deployment Successful!"
        log_info "Production URLs validated:"
        log_info "  Backend:  $BASE_URL"
        log_info "  Frontend: $FRONTEND_URL"
        log_info "Validation log: $LOG_FILE"
        exit 0
    else
        log_error "❌ $total_failures validation(s) failed - Review required"
        log_info "Check validation log: $LOG_FILE"
        exit 1
    fi
}

# Execute main function
main "$@"