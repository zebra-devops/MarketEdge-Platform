#!/bin/bash

# Railway Environment Configuration Script
# Run this after adding PostgreSQL and Redis services via Railway dashboard

set -e

# Colors for output
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

# Ensure we're in the backend directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

log_info "Configuring Railway environment variables..."

# Generate secure JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Application Configuration
log_info "Setting application configuration..."
railway variables set PROJECT_NAME="Platform Wrapper" || log_warning "Failed to set PROJECT_NAME"
railway variables set PROJECT_VERSION="1.0.0" || log_warning "Failed to set PROJECT_VERSION"
railway variables set ENVIRONMENT="production" || log_warning "Failed to set ENVIRONMENT"
railway variables set DEBUG="false" || log_warning "Failed to set DEBUG"
railway variables set LOG_LEVEL="INFO" || log_warning "Failed to set LOG_LEVEL"
railway variables set PORT="8000" || log_warning "Failed to set PORT"

# JWT Configuration
log_info "Setting JWT configuration..."
railway variables set JWT_SECRET_KEY="$JWT_SECRET" || log_warning "Failed to set JWT_SECRET_KEY"
railway variables set JWT_ALGORITHM="HS256" || log_warning "Failed to set JWT_ALGORITHM"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30" || log_warning "Failed to set ACCESS_TOKEN_EXPIRE_MINUTES"
railway variables set REFRESH_TOKEN_EXPIRE_DAYS="7" || log_warning "Failed to set REFRESH_TOKEN_EXPIRE_DAYS"

# Rate Limiting Configuration
log_info "Setting rate limiting configuration..."
railway variables set RATE_LIMIT_ENABLED="true" || log_warning "Failed to set RATE_LIMIT_ENABLED"
railway variables set RATE_LIMIT_REQUESTS_PER_MINUTE="60" || log_warning "Failed to set RATE_LIMIT_REQUESTS_PER_MINUTE"
railway variables set RATE_LIMIT_BURST_SIZE="10" || log_warning "Failed to set RATE_LIMIT_BURST_SIZE"
railway variables set RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE="1000" || log_warning "Failed to set RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE"
railway variables set RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE="5000" || log_warning "Failed to set RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE"

# Database Configuration
log_info "Setting database configuration..."
railway variables set DATABASE_POOL_SIZE="20" || log_warning "Failed to set DATABASE_POOL_SIZE"
railway variables set DATABASE_MAX_OVERFLOW="30" || log_warning "Failed to set DATABASE_MAX_OVERFLOW"
railway variables set DATABASE_POOL_TIMEOUT="30" || log_warning "Failed to set DATABASE_POOL_TIMEOUT"
railway variables set DATABASE_POOL_RECYCLE="3600" || log_warning "Failed to set DATABASE_POOL_RECYCLE"
railway variables set DATABASE_POOL_PRE_PING="true" || log_warning "Failed to set DATABASE_POOL_PRE_PING"

# Redis Configuration
log_info "Setting Redis configuration..."
railway variables set REDIS_CONNECTION_POOL_SIZE="50" || log_warning "Failed to set REDIS_CONNECTION_POOL_SIZE"
railway variables set REDIS_HEALTH_CHECK_INTERVAL="30" || log_warning "Failed to set REDIS_HEALTH_CHECK_INTERVAL"
railway variables set REDIS_SOCKET_CONNECT_TIMEOUT="5" || log_warning "Failed to set REDIS_SOCKET_CONNECT_TIMEOUT"
railway variables set REDIS_SOCKET_TIMEOUT="2" || log_warning "Failed to set REDIS_SOCKET_TIMEOUT"

# Multi-Tenant Configuration
log_info "Setting multi-tenant configuration..."
railway variables set TENANT_ISOLATION_ENABLED="true" || log_warning "Failed to set TENANT_ISOLATION_ENABLED"
railway variables set TENANT_DB_SCHEMA_ISOLATION="true" || log_warning "Failed to set TENANT_DB_SCHEMA_ISOLATION"
railway variables set MAX_TENANTS_PER_REQUEST="10" || log_warning "Failed to set MAX_TENANTS_PER_REQUEST"

# Configure Redis rate limiting storage URL (after Redis service is added)
log_info "Attempting to configure Redis rate limiting storage URL..."
REDIS_URL=$(railway variables get REDIS_URL 2>/dev/null || echo "")
if [ ! -z "$REDIS_URL" ]; then
    RATE_LIMIT_URL="${REDIS_URL}/1"
    railway variables set RATE_LIMIT_STORAGE_URL="$RATE_LIMIT_URL" || log_warning "Failed to set RATE_LIMIT_STORAGE_URL"
    log_success "Rate limiting storage URL configured: $RATE_LIMIT_URL"
else
    log_warning "REDIS_URL not found. Please add Redis service first, then run this script again."
fi

log_success "Environment variables configuration completed!"

# Display what still needs to be configured
echo ""
echo "⚠️  MANUAL CONFIGURATION STILL REQUIRED:"
echo ""
echo "1. Auth0 Configuration (required for authentication):"
echo "   railway variables set AUTH0_DOMAIN=\"your-tenant.auth0.com\""
echo "   railway variables set AUTH0_CLIENT_ID=\"your_auth0_client_id\""
echo "   railway variables set AUTH0_CLIENT_SECRET=\"your_auth0_client_secret\""
echo "   railway variables set AUTH0_CALLBACK_URL=\"https://your-app.railway.app/callback\""
echo ""
echo "2. CORS Origins (update with your frontend URL):"
echo "   railway variables set CORS_ORIGINS=\"https://your-frontend.railway.app\""
echo ""
echo "3. Optional - Supabase Data Layer:"
echo "   railway variables set DATA_LAYER_SUPABASE__URL=\"https://your-project.supabase.co\""
echo "   railway variables set DATA_LAYER_SUPABASE__KEY=\"your_supabase_anon_key\""
echo ""
echo "🚀 Next Steps:"
echo "1. Deploy your application: railway up"
echo "2. Run database migrations: railway run alembic upgrade head"
echo "3. Test health endpoint: curl https://your-app.railway.app/health"
echo "4. View API docs: https://your-app.railway.app/api/v1/docs"