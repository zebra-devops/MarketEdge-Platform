#!/bin/bash

# Railway CLI and Service Test Script
# This script validates Railway CLI commands and service configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

test_command() {
    local cmd="$1"
    local description="$2"
    
    log_info "Testing: $description"
    
    if eval "$cmd" >/dev/null 2>&1; then
        log_success "$description - PASSED"
        return 0
    else
        log_warning "$description - FAILED"
        return 1
    fi
}

# Test Railway CLI availability and authentication
log_info "=== Railway CLI Tests ==="
test_command "railway --version" "Railway CLI version check"
test_command "railway whoami" "Railway authentication check"

# Test Railway CLI command syntax (dry run)
log_info "=== Railway Command Syntax Tests ==="
test_command "railway add --help" "Railway add command help"
test_command "railway variables --help" "Railway variables command help"
test_command "railway domain --help" "Railway domain command help"

# Test database service addition syntax
log_info "=== Service Addition Tests ==="
log_info "Testing PostgreSQL service syntax (dry run)"
if railway add --help | grep -q "postgres"; then
    log_success "PostgreSQL service option available"
else
    log_warning "PostgreSQL service option not found in help"
fi

log_info "Testing Redis service syntax (dry run)"
if railway add --help | grep -q "redis"; then
    log_success "Redis service option available"
else
    log_warning "Redis service option not found in help"
fi

# Test environment variable syntax
log_info "=== Environment Variable Syntax Tests ==="
log_info "Testing variables --set syntax"
if railway variables --help | grep -q "set"; then
    log_success "Variables --set syntax is supported"
else
    log_warning "Variables --set syntax not found"
fi

if railway variables --help | grep -q "skip-deploys"; then
    log_success "Variables --skip-deploys option is supported"
else
    log_warning "Variables --skip-deploys option not found"
fi

# Test project status and linking
log_info "=== Project Management Tests ==="
test_command "railway list" "List projects"
test_command "railway init --help" "Project initialization help"

# Display results summary
echo ""
log_info "=== Test Summary ==="
echo "All syntax validations completed."
echo ""
echo "Next steps for deployment:"
echo "1. Ensure you have a Dockerfile in the current directory"
echo "2. Initialize or link to a Railway project"
echo "3. Run the deployment script: ./deploy-railway.sh"
echo ""
echo "Monitor deployment with:"
echo "- railway status"
echo "- railway logs"
echo "- railway open (opens dashboard)"