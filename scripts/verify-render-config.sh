#!/usr/bin/env bash

# verify-render-config.sh
# Verification script for render.yaml configuration
#
# Purpose: Validate that render.yaml is correctly configured and all required
#          secrets are set in Render Dashboard before deployment
#
# Usage:
#   ./scripts/verify-render-config.sh
#   ./scripts/verify-render-config.sh --check-secrets
#   ./scripts/verify-render-config.sh --check-production
#   ./scripts/verify-render-config.sh --check-staging
#
# Exit codes:
#   0 - All checks passed
#   1 - Configuration errors found
#   2 - Missing required secrets
#   3 - Service health check failed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RENDER_YAML="render.yaml"
PRODUCTION_URL="${PRODUCTION_URL:-https://marketedge-platform.onrender.com}"
STAGING_URL="${STAGING_URL:-https://marketedge-platform-staging.onrender.com}"

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# ============================================================================
# Utility Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Check Functions
# ============================================================================

check_render_yaml_exists() {
    print_header "Checking render.yaml File"

    if [ ! -f "$RENDER_YAML" ]; then
        print_error "render.yaml not found in repository root"
        return 1
    fi

    print_success "render.yaml found"
    return 0
}

check_render_yaml_syntax() {
    print_header "Validating render.yaml Syntax"

    # Check if yq is installed
    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - cannot validate YAML syntax"
        print_info "Install yq: brew install yq (macOS) or snap install yq (Linux)"
        return 0
    fi

    # Validate YAML syntax
    if yq eval '.' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "render.yaml has valid YAML syntax"
    else
        print_error "render.yaml has invalid YAML syntax"
        return 1
    fi

    return 0
}

check_required_services() {
    print_header "Checking Required Services"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping service validation"
        return 0
    fi

    # Check production service
    if yq eval '.services[] | select(.name == "marketedge-platform")' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "Production service 'marketedge-platform' defined"
    else
        print_error "Production service 'marketedge-platform' not found"
    fi

    # Check staging service
    if yq eval '.services[] | select(.name == "marketedge-platform-staging")' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "Staging service 'marketedge-platform-staging' defined"
    else
        print_warning "Staging service 'marketedge-platform-staging' not found (expected for staging gate)"
    fi

    return 0
}

check_required_databases() {
    print_header "Checking Database Definitions"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping database validation"
        return 0
    fi

    # Check preview database
    if yq eval '.databases[] | select(.name == "marketedge-preview-db")' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "Preview database 'marketedge-preview-db' defined"
    else
        print_warning "Preview database 'marketedge-preview-db' not defined"
    fi

    # Check staging database
    if yq eval '.databases[] | select(.name == "marketedge-staging-db")' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "Staging database 'marketedge-staging-db' defined"
    else
        print_warning "Staging database 'marketedge-staging-db' not defined"
    fi

    return 0
}

check_critical_env_vars() {
    print_header "Checking Critical Environment Variables"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping environment variable validation"
        return 0
    fi

    # Critical environment variables that MUST be defined
    local critical_vars=(
        "AUTH0_AUDIENCE"
        "AUTH0_DOMAIN"
        "AUTH0_CLIENT_ID"
        "CORS_ORIGINS"
        "JWT_ALGORITHM"
        "DATABASE_URL"
        "REDIS_URL"
    )

    for var in "${critical_vars[@]}"; do
        if yq eval ".services[] | select(.name == \"marketedge-platform\") | .envVars[] | select(.key == \"$var\")" "$RENDER_YAML" > /dev/null 2>&1; then
            print_success "Environment variable '$var' defined"
        else
            if [[ "$var" == "DATABASE_URL" ]] || [[ "$var" == "REDIS_URL" ]]; then
                print_warning "Environment variable '$var' not in render.yaml (should be in Dashboard)"
            else
                print_error "Environment variable '$var' not defined"
            fi
        fi
    done

    return 0
}

check_auth0_audience() {
    print_header "Checking AUTH0_AUDIENCE Configuration"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping AUTH0_AUDIENCE validation"
        return 0
    fi

    # Check if AUTH0_AUDIENCE is defined
    local audience
    audience=$(yq eval '.services[] | select(.name == "marketedge-platform") | .envVars[] | select(.key == "AUTH0_AUDIENCE") | .value' "$RENDER_YAML" 2>/dev/null)

    if [ -z "$audience" ] || [ "$audience" == "null" ]; then
        print_error "AUTH0_AUDIENCE not defined (CRITICAL - required for JWT tokens)"
        print_info "Expected: https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/"
        return 1
    fi

    # Check if it matches expected format
    if [[ "$audience" == *"auth0.com/api/v2/"* ]]; then
        print_success "AUTH0_AUDIENCE correctly configured: $audience"
    else
        print_warning "AUTH0_AUDIENCE format unexpected: $audience"
        print_info "Expected format: https://<tenant>.auth0.com/api/v2/"
    fi

    return 0
}

check_cors_origins() {
    print_header "Checking CORS Configuration"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping CORS validation"
        return 0
    fi

    # Check production CORS origins
    local cors_origins
    cors_origins=$(yq eval '.services[] | select(.name == "marketedge-platform") | .envVars[] | select(.key == "CORS_ORIGINS") | .value' "$RENDER_YAML" 2>/dev/null)

    if [ -z "$cors_origins" ] || [ "$cors_origins" == "null" ]; then
        print_error "CORS_ORIGINS not defined"
        return 1
    fi

    # Check for Vercel wildcard
    if [[ "$cors_origins" == *"*.vercel.app"* ]]; then
        print_success "CORS_ORIGINS includes Vercel wildcard: *.vercel.app"
    else
        print_error "CORS_ORIGINS missing Vercel wildcard: *.vercel.app"
        print_info "Add: https://*.vercel.app to CORS_ORIGINS"
    fi

    # Check for staging domain
    if [[ "$cors_origins" == *"staging.zebra.associates"* ]]; then
        print_success "CORS_ORIGINS includes staging domain"
    else
        print_warning "CORS_ORIGINS missing staging domain: staging.zebra.associates"
    fi

    return 0
}

check_preview_configuration() {
    print_header "Checking Preview Environment Configuration"

    if ! command -v yq &> /dev/null; then
        print_warning "yq not installed - skipping preview configuration validation"
        return 0
    fi

    # Check if preview generation enabled
    local preview_generation
    preview_generation=$(yq eval '.previews.generation' "$RENDER_YAML" 2>/dev/null)

    if [ "$preview_generation" == "automatic" ]; then
        print_success "Preview generation enabled: automatic"
    else
        print_warning "Preview generation not set to automatic: $preview_generation"
    fi

    # Check preview expiry
    local preview_expiry
    preview_expiry=$(yq eval '.previews.expireAfterDays' "$RENDER_YAML" 2>/dev/null)

    if [ "$preview_expiry" == "7" ]; then
        print_success "Preview expiry correctly set: 7 days"
    else
        print_warning "Preview expiry not set to 7 days: $preview_expiry"
    fi

    # Check if preview envVars defined
    if yq eval '.services[] | select(.name == "marketedge-platform") | .previews.envVars[]' "$RENDER_YAML" > /dev/null 2>&1; then
        print_success "Preview-specific environment variables defined"
    else
        print_warning "No preview-specific environment variables defined"
    fi

    return 0
}

check_staging_branch() {
    print_header "Checking Staging Branch"

    # Check if staging branch exists locally
    if git show-ref --verify --quiet refs/heads/staging; then
        print_success "Staging branch exists locally"
    else
        print_warning "Staging branch does not exist locally"
        print_info "Create with: git checkout -b staging && git push origin staging"
    fi

    # Check if staging branch exists on remote
    if git ls-remote --heads origin staging | grep -q staging; then
        print_success "Staging branch exists on remote"
    else
        print_warning "Staging branch does not exist on remote"
        print_info "Push with: git push origin staging"
    fi

    return 0
}

check_secrets_reminder() {
    print_header "Secrets Configuration Reminder"

    print_info "The following secrets MUST be manually configured in Render Dashboard:"
    echo ""
    echo "  Production Service (marketedge-platform):"
    echo "    - AUTH0_CLIENT_SECRET"
    echo "    - AUTH0_ACTION_SECRET"
    echo "    - JWT_SECRET_KEY"
    echo "    - DATABASE_URL"
    echo "    - REDIS_URL"
    echo "    - SENTRY_DSN (optional)"
    echo ""
    echo "  Staging Service (marketedge-platform-staging):"
    echo "    - AUTH0_CLIENT_SECRET (same as production or staging-specific)"
    echo "    - AUTH0_ACTION_SECRET (same as production)"
    echo "    - JWT_SECRET_KEY (MUST BE DIFFERENT from production)"
    echo "    - REDIS_URL"
    echo "    - SENTRY_DSN (optional)"
    echo ""
    echo "  NOTE: DATABASE_URL for staging is auto-injected from staging database"
    echo ""

    print_warning "Secrets cannot be validated via this script (not accessible from git)"
    print_info "Verify secrets in Render Dashboard → Service → Environment tab"

    return 0
}

check_production_health() {
    print_header "Checking Production Service Health"

    if ! command -v curl &> /dev/null; then
        print_warning "curl not installed - skipping health check"
        return 0
    fi

    print_info "Checking: $PRODUCTION_URL/health"

    # Check if service is reachable
    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" "$PRODUCTION_URL/health" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        print_success "Production service healthy (HTTP 200)"

        # Check response body
        local body
        body=$(echo "$response" | head -n -1)

        if [[ "$body" == *"\"status\":\"healthy\""* ]] || [[ "$body" == *"\"status\": \"healthy\""* ]]; then
            print_success "Production health endpoint returns healthy status"
        else
            print_warning "Production health endpoint response unexpected: $body"
        fi
    elif [ "$http_code" == "000" ]; then
        print_error "Production service unreachable (connection failed)"
        print_info "Service may be cold starting (Render free tier)"
    else
        print_error "Production service unhealthy (HTTP $http_code)"
    fi

    return 0
}

check_staging_health() {
    print_header "Checking Staging Service Health"

    if ! command -v curl &> /dev/null; then
        print_warning "curl not installed - skipping health check"
        return 0
    fi

    print_info "Checking: $STAGING_URL/health"

    # Check if service is reachable
    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" "$STAGING_URL/health" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        print_success "Staging service healthy (HTTP 200)"

        # Check response body
        local body
        body=$(echo "$response" | head -n -1)

        if [[ "$body" == *"\"environment\":\"staging\""* ]] || [[ "$body" == *"\"environment\": \"staging\""* ]]; then
            print_success "Staging environment correctly configured"
        else
            print_warning "Staging environment identifier not found in response"
        fi
    elif [ "$http_code" == "000" ]; then
        print_warning "Staging service unreachable (may not be deployed yet)"
        print_info "Staging service will be created when staging branch is deployed"
    elif [ "$http_code" == "404" ]; then
        print_warning "Staging service not found (may not be deployed yet)"
    else
        print_error "Staging service unhealthy (HTTP $http_code)"
    fi

    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "Render Configuration Verification"
    print_info "Repository: MarketEdge Platform"
    print_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"

    # Parse arguments
    local check_production=false
    local check_staging=false
    local check_secrets=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --check-production)
                check_production=true
                shift
                ;;
            --check-staging)
                check_staging=true
                shift
                ;;
            --check-secrets)
                check_secrets=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--check-production] [--check-staging] [--check-secrets]"
                exit 1
                ;;
        esac
    done

    # Run all checks
    check_render_yaml_exists || true
    check_render_yaml_syntax || true
    check_required_services || true
    check_required_databases || true
    check_critical_env_vars || true
    check_auth0_audience || true
    check_cors_origins || true
    check_preview_configuration || true
    check_staging_branch || true

    # Optional checks
    if [ "$check_secrets" == true ]; then
        check_secrets_reminder || true
    fi

    if [ "$check_production" == true ]; then
        check_production_health || true
    fi

    if [ "$check_staging" == true ]; then
        check_staging_health || true
    fi

    # Summary
    print_header "Verification Summary"
    echo ""
    echo -e "${GREEN}✅ Checks Passed: $CHECKS_PASSED${NC}"
    echo -e "${RED}❌ Checks Failed: $CHECKS_FAILED${NC}"
    echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
    echo ""

    # Exit code
    if [ $CHECKS_FAILED -gt 0 ]; then
        echo -e "${RED}❌ Configuration verification FAILED${NC}"
        echo ""
        echo "Fix the errors above before deploying to Render."
        echo ""
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Configuration verification PASSED with warnings${NC}"
        echo ""
        echo "Review the warnings above. Some may be expected (e.g., staging not deployed yet)."
        echo ""
        exit 0
    else
        echo -e "${GREEN}✅ Configuration verification PASSED${NC}"
        echo ""
        echo "render.yaml is correctly configured and ready for deployment!"
        echo ""
        exit 0
    fi
}

# Run main function
main "$@"
