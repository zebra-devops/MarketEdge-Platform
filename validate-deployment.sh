#!/bin/bash

# Railway Deployment Validation Script
# Validates the complete deployment setup before running

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

validation_errors=0

validate_requirement() {
    local check_command="$1"
    local requirement_name="$2"
    local fix_instruction="$3"
    
    log_info "Validating: $requirement_name"
    
    if eval "$check_command" >/dev/null 2>&1; then
        log_success "$requirement_name - PASSED"
    else
        log_error "$requirement_name - FAILED"
        echo "  Fix: $fix_instruction"
        ((validation_errors++))
    fi
}

echo "=========================================="
echo "Railway Deployment Validation"
echo "=========================================="
echo ""

# Check prerequisites
log_info "=== Prerequisites Check ==="
validate_requirement "command -v railway" "Railway CLI installed" "Install with: curl -fsSL https://railway.app/install.sh | sh"
validate_requirement "command -v docker" "Docker installed" "Install Docker from: https://docker.com/get-started"
validate_requirement "command -v git" "Git installed" "Install Git from: https://git-scm.com"

# Check Railway authentication
log_info "=== Railway Authentication ==="
validate_requirement "railway whoami" "Railway authenticated" "Run: railway login"

# Check Railway CLI version
log_info "=== Railway CLI Version ==="
RAILWAY_VERSION=$(railway --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "")
if [ ! -z "$RAILWAY_VERSION" ]; then
    log_success "Railway CLI version: $RAILWAY_VERSION"
    
    # Check if version is compatible (4.0+)
    MAJOR_VERSION=$(echo $RAILWAY_VERSION | cut -d. -f1)
    if [ "$MAJOR_VERSION" -ge 4 ]; then
        log_success "Railway CLI version is compatible (4.0+)"
    else
        log_warning "Railway CLI version may be outdated. Recommend upgrading to 4.6.1+"
    fi
else
    log_error "Could not determine Railway CLI version"
    ((validation_errors++))
fi

# Check project files
log_info "=== Project Files Check ==="
validate_requirement "[ -f Dockerfile ]" "Dockerfile exists" "Create Dockerfile for containerized deployment"
validate_requirement "[ -f requirements.txt ]" "requirements.txt exists" "Create requirements.txt with Python dependencies"
validate_requirement "[ -f deploy-railway.sh ]" "deploy-railway.sh exists" "Deployment script is missing"
validate_requirement "[ -f railway.toml ]" "railway.toml exists" "Will be created during deployment initialization"

# Check deployment script permissions
if [ -f deploy-railway.sh ]; then
    validate_requirement "[ -x deploy-railway.sh ]" "deploy-railway.sh is executable" "Run: chmod +x deploy-railway.sh"
fi

# Check Railway project status
log_info "=== Railway Project Status ==="
if railway status >/dev/null 2>&1; then
    log_success "Railway project is linked"
    log_info "Current project status:"
    railway status 2>/dev/null || log_warning "Could not retrieve project status"
else
    log_warning "No Railway project linked - will be created during deployment"
fi

# Validate Railway CLI command syntax
log_info "=== Railway CLI Command Validation ==="
validate_requirement "railway add --help | grep -q 'database'" "Railway add command supports databases" "Update Railway CLI"
validate_requirement "railway variables --help | grep -q 'set'" "Railway variables supports --set flag" "Update Railway CLI"
validate_requirement "railway domain --help" "Railway domain command available" "Update Railway CLI"

# Check for common issues
log_info "=== Common Issues Check ==="

# Check if in correct directory
if [ ! -f "app/main.py" ] && [ ! -f "main.py" ]; then
    log_warning "FastAPI main application file not found. Ensure you're in the correct directory."
fi

# Check Docker functionality
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        log_success "Docker daemon is running"
    else
        log_warning "Docker daemon is not running. Start Docker before deployment."
    fi
fi

# Display results
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [ $validation_errors -eq 0 ]; then
    log_success "All validations passed! Ready for deployment."
    echo ""
    echo "Next steps:"
    echo "1. Run deployment: ./deploy-railway.sh"
    echo "2. Monitor deployment: railway logs"
    echo "3. Check status: railway status"
    echo "4. Access dashboard: railway open"
else
    log_error "Found $validation_errors validation errors."
    echo ""
    echo "Please fix the issues above before running deployment."
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Command Reference"
echo "=========================================="
echo ""
echo "# Deploy application"
echo "./deploy-railway.sh"
echo ""
echo "# Monitor deployment"
echo "railway logs"
echo ""
echo "# Check service status"
echo "railway status"
echo ""
echo "# Connect to database"
echo "railway connect postgres"
echo ""
echo "# Connect to Redis"
echo "railway connect redis"
echo ""
echo "# Open Railway dashboard"
echo "railway open"
echo ""
echo "# View environment variables"
echo "railway variables"
echo ""
echo "# Generate or configure domain"
echo "railway domain"
echo ""

log_success "Validation completed successfully!"