#!/bin/bash

# Auth0 CORS Fix Script for Railway Deployment
# This script updates Railway environment variables to fix Auth0 login issues

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

# Check if railway CLI is available
if ! command -v railway &> /dev/null; then
    log_error "Railway CLI is not installed. Please install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

log_info "Fixing Auth0 CORS and environment configuration on Railway..."

# Update CORS to include Vercel frontend
log_info "Setting CORS origins to include Vercel frontend..."
railway variables set CORS_ORIGINS='["http://localhost:3000","http://localhost:3001","https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"]'

# Ensure production environment settings
log_info "Setting production environment configuration..."
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"

# Auth0 Configuration
log_info "Setting Auth0 configuration..."
railway variables set AUTH0_DOMAIN="dev-g8trhgbfdq2sk2m8.us.auth0.com"
railway variables set AUTH0_CLIENT_ID="mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
railway variables set AUTH0_CLIENT_SECRET="9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"
railway variables set AUTH0_CALLBACK_URL="https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app/callback"

# API Configuration
log_info "Setting API configuration..."
railway variables set API_V1_STR="/api/v1"
railway variables set PROJECT_NAME="Platform Wrapper"
railway variables set PROJECT_VERSION="1.0.0"

log_success "Railway environment variables updated successfully!"

log_info "Redeploying backend to apply changes..."
railway up

log_success "Backend deployment completed!"

echo ""
echo "🚀 Next Steps:"
echo "1. Verify Auth0 Application Settings:"
echo "   - Login to Auth0 Dashboard"
echo "   - Navigate to Applications > Platform Wrapper"
echo "   - Add callback URL: https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app/callback"
echo "   - Add logout URL: https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app"
echo ""
echo "2. Test the login flow:"
echo "   - Visit: https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app/login"
echo "   - Click 'Sign in with Auth0'"
echo "   - Complete authentication"
echo ""
echo "3. Check backend health:"
echo "   - Visit: https://marketedge-backend-production.up.railway.app/health"
echo "   - Should return healthy status"