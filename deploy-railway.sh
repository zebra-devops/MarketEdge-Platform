#!/bin/bash

# Railway Deployment Script for Multi-Tenant FastAPI Backend
# This script automates the complete deployment process to Railway

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="platform-wrapper-backend"
BACKEND_DIR="/Users/matt/sites/marketedge/platform-wrapper/backend"

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

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

validate_service_status() {
    local service_type=$1
    log_info "Validating $service_type service status..."
    
    if railway status | grep -q "$service_type"; then
        log_success "$service_type service is available"
        return 0
    else
        log_error "$service_type service is not available"
        return 1
    fi
}

wait_for_deployment() {
    local max_wait=300  # 5 minutes
    local wait_time=0
    local check_interval=15
    
    log_info "Waiting for deployment to complete (max ${max_wait}s)..."
    
    while [ $wait_time -lt $max_wait ]; do
        if railway status | grep -q "Active"; then
            log_success "Deployment completed successfully"
            return 0
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        echo -n "."
    done
    
    log_warning "Deployment may still be in progress after ${max_wait}s. Check Railway dashboard."
    return 1
}

# Check prerequisites
log_info "Checking prerequisites..."
check_command "railway"
check_command "git"

# Ensure we're in the right directory
cd "$BACKEND_DIR"

# Check if Railway is authenticated
log_info "Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    log_error "Not authenticated with Railway. Please run 'railway login' first."
    exit 1
fi

log_success "Railway authentication verified"

# Initialize Railway project if not already done
log_info "Initializing Railway project..."
if [ ! -f "railway.toml" ]; then
    log_warning "railway.toml not found. Creating new Railway project..."
    railway init --name "$PROJECT_NAME"
else
    log_info "Railway project already initialized"
fi

# Add PostgreSQL service
log_info "Adding PostgreSQL database..."
if ! railway add -d postgres 2>/dev/null; then
    log_warning "PostgreSQL service may already exist or failed to add. Checking status..."
    railway status | grep -q "postgres" && log_info "PostgreSQL service confirmed present"
fi

# Add Redis service
log_info "Adding Redis cache..."
if ! railway add -d redis 2>/dev/null; then
    log_warning "Redis service may already exist or failed to add. Checking status..."
    railway status | grep -q "redis" && log_info "Redis service confirmed present"
fi

# Validate services after adding them
log_info "Validating database and cache services..."
validate_service_status "postgres" || log_warning "PostgreSQL service validation failed"
validate_service_status "redis" || log_warning "Redis service validation failed"

# Set environment variables
log_info "Setting environment variables..."

# Wait for services to be ready
log_info "Waiting for services to initialize..."
sleep 10

# Application Configuration
log_info "Setting application configuration..."
railway variables --set "PROJECT_NAME=Platform Wrapper" --skip-deploys
railway variables --set "PROJECT_VERSION=1.0.0" --skip-deploys
railway variables --set "ENVIRONMENT=production" --skip-deploys
railway variables --set "DEBUG=false" --skip-deploys
railway variables --set "LOG_LEVEL=INFO" --skip-deploys

# JWT Configuration (generate secure key)
log_info "Setting JWT configuration..."
JWT_SECRET=$(openssl rand -base64 32)
railway variables --set "JWT_SECRET_KEY=$JWT_SECRET" --skip-deploys
railway variables --set "JWT_ALGORITHM=HS256" --skip-deploys
railway variables --set "ACCESS_TOKEN_EXPIRE_MINUTES=30" --skip-deploys
railway variables --set "REFRESH_TOKEN_EXPIRE_DAYS=7" --skip-deploys

# Rate Limiting Configuration
log_info "Setting rate limiting configuration..."
railway variables --set "RATE_LIMIT_ENABLED=true" --skip-deploys
railway variables --set "RATE_LIMIT_REQUESTS_PER_MINUTE=60" --skip-deploys
railway variables --set "RATE_LIMIT_BURST_SIZE=10" --skip-deploys
railway variables --set "RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE=1000" --skip-deploys
railway variables --set "RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE=5000" --skip-deploys

# Database Configuration
log_info "Setting database configuration..."
railway variables --set "DATABASE_POOL_SIZE=20" --skip-deploys
railway variables --set "DATABASE_MAX_OVERFLOW=30" --skip-deploys
railway variables --set "DATABASE_POOL_TIMEOUT=30" --skip-deploys
railway variables --set "DATABASE_POOL_RECYCLE=3600" --skip-deploys
railway variables --set "DATABASE_POOL_PRE_PING=true" --skip-deploys

# Redis Configuration
log_info "Setting Redis configuration..."
railway variables --set "REDIS_CONNECTION_POOL_SIZE=50" --skip-deploys
railway variables --set "REDIS_HEALTH_CHECK_INTERVAL=30" --skip-deploys
railway variables --set "REDIS_SOCKET_CONNECT_TIMEOUT=5" --skip-deploys
railway variables --set "REDIS_SOCKET_TIMEOUT=2" --skip-deploys

# Multi-Tenant Configuration
log_info "Setting multi-tenant configuration..."
railway variables --set "TENANT_ISOLATION_ENABLED=true" --skip-deploys
railway variables --set "TENANT_DB_SCHEMA_ISOLATION=true" --skip-deploys
railway variables --set "MAX_TENANTS_PER_REQUEST=10" --skip-deploys

log_success "Environment variables configured"

# Deploy the application
log_info "Deploying application to Railway..."
if railway up --detach; then
    log_success "Deployment initiated successfully"
else
    log_error "Deployment initiation failed"
    exit 1
fi

# Wait for deployment with enhanced monitoring
wait_for_deployment

# Get service URL
log_info "Retrieving service URL..."
SERVICE_URL=$(railway domain 2>/dev/null || echo "")
if [ -z "$SERVICE_URL" ]; then
    log_warning "Could not retrieve service URL. You may need to configure a domain manually."
    log_info "Use 'railway domain' to configure a custom domain or generate a Railway domain"
else
    log_success "Service deployed successfully: $SERVICE_URL"
fi

# Test database connectivity before migrations
log_info "Testing database connectivity..."
if railway variables | grep -q "DATABASE_URL"; then
    log_success "Database URL configured"
    
    # Run database migrations
    log_info "Running database migrations..."
    if railway shell -- alembic upgrade head; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migrations failed. Check logs with: railway logs"
        log_info "You may need to initialize the database schema manually"
    fi
else
    log_warning "DATABASE_URL not found. Database may not be properly configured"
fi

# Test health endpoint
log_info "Testing health endpoint..."
if [ ! -z "$SERVICE_URL" ]; then
    if curl -f "$SERVICE_URL/health" &> /dev/null; then
        log_success "Health check passed"
    else
        log_warning "Health check failed. Service may still be starting up."
    fi
fi

# Display deployment information
echo ""
log_success "Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Configure Auth0 settings:"
echo "   - railway variables --set \"AUTH0_DOMAIN=your-tenant.auth0.com\""
echo "   - railway variables --set \"AUTH0_CLIENT_ID=your_client_id\""
echo "   - railway variables --set \"AUTH0_CLIENT_SECRET=your_client_secret\""
echo ""
echo "2. Configure CORS origins:"
echo "   - railway variables --set \"CORS_ORIGINS=https://your-frontend.railway.app\""
echo ""
echo "3. Configure Supabase (if using):"
echo "   - railway variables --set \"DATA_LAYER_SUPABASE__URL=https://your-project.supabase.co\""
echo "   - railway variables --set \"DATA_LAYER_SUPABASE__KEY=your_anon_key\""
echo ""
echo "4. Set up Redis rate limiting storage URL:"
log_info "Configuring Redis rate limiting storage..."
REDIS_URL=$(railway variables | grep REDIS_URL | cut -d'=' -f2- 2>/dev/null || echo "")
if [ ! -z "$REDIS_URL" ]; then
    RATE_LIMIT_URL="${REDIS_URL}/1"
    railway variables --set "RATE_LIMIT_STORAGE_URL=$RATE_LIMIT_URL"
    echo "   - Rate limiting storage URL configured: $RATE_LIMIT_URL"
else
    echo "   - Configure manually: railway variables --set \"RATE_LIMIT_STORAGE_URL=<REDIS_URL>/1\""
fi
echo ""

if [ ! -z "$SERVICE_URL" ]; then
    echo "Service URL: $SERVICE_URL"
    echo "API Documentation: $SERVICE_URL/api/v1/docs"
    echo "Health Check: $SERVICE_URL/health"
fi

echo ""
log_info "View logs with: railway logs"
log_info "Monitor deployment: railway status"
log_info "Access Railway dashboard: https://railway.app/"

log_success "Railway deployment script completed successfully!"