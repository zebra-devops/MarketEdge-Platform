#!/bin/bash

# Vercel Environment Variables Fix Script
# This script ensures Vercel deployment has correct environment variables

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

# Check if vercel CLI is available
if ! command -v vercel &> /dev/null; then
    log_error "Vercel CLI is not installed. Please install it first:"
    echo "npm install -g vercel"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

log_info "Setting Vercel environment variables for production..."

# Set production environment variables
log_info "Setting API base URL..."
vercel env add NEXT_PUBLIC_API_BASE_URL production
echo "https://marketedge-backend-production.up.railway.app"

log_info "Setting Auth0 domain..."
vercel env add NEXT_PUBLIC_AUTH0_DOMAIN production  
echo "dev-g8trhgbfdq2sk2m8.us.auth0.com"

log_info "Setting Auth0 client ID..."
vercel env add NEXT_PUBLIC_AUTH0_CLIENT_ID production
echo "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"

log_success "Environment variables set! Now deploying..."

# Redeploy to apply environment variables
vercel --prod

log_success "Frontend deployment completed!"

echo ""
echo "🔍 Verification Steps:"
echo "1. Check environment variables are loaded:"
echo "   - Open browser console on https://frontend-jitpuqzpd-zebraassociates-projects.vercel.app/login"
echo "   - Look for console logs showing Auth0 Domain and Client ID"
echo ""
echo "2. Test API connection:"
echo "   - Frontend should now call https://marketedge-backend-production.up.railway.app/api/v1/auth/auth0-url"
echo "   - No more Railway project URLs in network requests"