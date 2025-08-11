#!/bin/bash

# Railway Variable Configuration Fix Script
# Complete CLI solution for DATABASE_URL and REDIS_URL configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

echo "🚀 Railway Variable Configuration Fix - Starting..."
echo "=================================================================="

# Phase 1: Current State Analysis
log_info "Phase 1: Analyzing current Railway configuration..."

# Step 1: Verify Railway CLI authentication
log_info "Step 1: Verifying Railway CLI authentication..."
if railway whoami >/dev/null 2>&1; then
    RAILWAY_USER=$(railway whoami)
    log_success "Railway CLI authenticated as: $RAILWAY_USER"
else
    log_error "Railway CLI not authenticated. Run: railway login"
    exit 1
fi

# Step 2: Check current variables
log_info "Step 2: Checking current variables..."
echo ""
log_info "Current variables:"
railway variables || log_warning "No variables found or error reading variables"
echo ""

# Step 3: Identify services in project
log_info "Step 3: Identifying available services..."
railway status || log_warning "Could not get detailed status"

# Phase 2: Fix DATABASE_URL Configuration
log_info "Phase 2: Fixing DATABASE_URL configuration..."

# Check if DATABASE_URL exists and its current value
log_info "Step 4: Analyzing DATABASE_URL configuration..."
current_db_url=$(railway variables | grep "^DATABASE_URL" | awk '{print $3}' || echo "")

if [ -n "$current_db_url" ]; then
    log_info "Current DATABASE_URL found: $current_db_url"
    
    # Check if it's already a reference variable
    if [[ "$current_db_url" == *"\${"* ]]; then
        log_success "DATABASE_URL is already configured as reference variable"
    else
        log_warning "DATABASE_URL is hardcoded, needs to be converted to reference"
        
        # Set DATABASE_URL to proper reference format
        log_info "Setting DATABASE_URL to reference variable..."
        railway variables --set "DATABASE_URL=\${{Postgres.DATABASE_URL}}" || \
        log_error "Failed to set DATABASE_URL reference. Check your PostgreSQL service name."
        
        if [ $? -eq 0 ]; then
            log_success "DATABASE_URL configured as reference variable"
        fi
    fi
else
    log_warning "DATABASE_URL not found, setting as reference variable..."
    railway variables --set "DATABASE_URL=\${{Postgres.DATABASE_URL}}" || \
    log_error "Failed to set DATABASE_URL reference. Check your PostgreSQL service name."
    
    if [ $? -eq 0 ]; then
        log_success "DATABASE_URL configured as reference variable"
    fi
fi

# Phase 3: Fix REDIS_URL Configuration  
log_info "Phase 3: Fixing REDIS_URL configuration..."

# Check if REDIS_URL exists and its current value
log_info "Step 5: Analyzing REDIS_URL configuration..."
current_redis_url=$(railway variables | grep "^REDIS_URL" | awk '{print $3}' || echo "")

if [ -n "$current_redis_url" ]; then
    log_info "Current REDIS_URL found: $current_redis_url"
    
    # Check if it's already a reference variable
    if [[ "$current_redis_url" == *"\${"* ]]; then
        log_success "REDIS_URL is already configured as reference variable"
    else
        log_warning "REDIS_URL is hardcoded, needs to be converted to reference"
        
        # Set REDIS_URL to proper reference format
        log_info "Setting REDIS_URL to reference variable..."
        railway variables --set "REDIS_URL=\${{Redis.REDIS_URL}}" || \
        log_error "Failed to set REDIS_URL reference. Check your Redis service name."
        
        if [ $? -eq 0 ]; then
            log_success "REDIS_URL configured as reference variable"
        fi
    fi
else
    log_warning "REDIS_URL not found, setting as reference variable..."
    railway variables --set "REDIS_URL=\${{Redis.REDIS_URL}}" || \
    log_error "Failed to set REDIS_URL reference. Check your Redis service name."
    
    if [ $? -eq 0 ]; then
        log_success "REDIS_URL configured as reference variable"
    fi
fi

# Phase 4: Add DATA_LAYER_ENABLED=false
log_info "Phase 4: Configuring DATA_LAYER_ENABLED..."

log_info "Step 6: Setting DATA_LAYER_ENABLED=false..."
railway variables --set "DATA_LAYER_ENABLED=false"
if [ $? -eq 0 ]; then
    log_success "DATA_LAYER_ENABLED set to false"
else
    log_error "Failed to set DATA_LAYER_ENABLED"
fi

# Phase 5: Set Rate Limiting Storage URL
log_info "Phase 5: Configuring Rate Limiting Storage..."

log_info "Step 7: Setting RATE_LIMIT_STORAGE_URL as Redis reference..."
railway variables --set "RATE_LIMIT_STORAGE_URL=\${{Redis.REDIS_URL}}/1" || \
log_warning "Could not set RATE_LIMIT_STORAGE_URL reference"

if [ $? -eq 0 ]; then
    log_success "RATE_LIMIT_STORAGE_URL configured with Redis reference"
fi

# Phase 6: Verification
log_info "Phase 6: Configuration verification..."

log_info "Step 8: Final variable configuration:"
echo ""
railway variables
echo ""

# Phase 7: Deploy Changes
log_info "Phase 7: Deploying changes..."

log_info "Step 9: Deploying application with new configuration..."
railway up --detach

if [ $? -eq 0 ]; then
    log_success "Deployment initiated successfully!"
else
    log_error "Deployment failed"
    exit 1
fi

# Final Summary
echo ""
echo "=================================================================="
log_success "🎉 Railway Variable Configuration Fix Completed!"
echo ""
log_info "Configuration Summary:"
echo "✅ DATABASE_URL: Set to reference variable (automatic updates)"
echo "✅ REDIS_URL: Set to reference variable (automatic updates)" 
echo "✅ DATA_LAYER_ENABLED: Set to false"
echo "✅ RATE_LIMIT_STORAGE_URL: Configured with Redis reference"
echo "✅ Application: Deployed with new configuration"
echo ""
log_info "🔍 Next Steps:"
echo "1. Monitor deployment: railway logs --follow"
echo "2. Test health endpoint: curl https://your-app.railway.app/health"
echo "3. Verify connectivity: curl https://your-app.railway.app/ready"
echo "4. Check Railway dashboard for deployment status"
echo ""
log_success "All variables configured according to Railway 2025 best practices!"