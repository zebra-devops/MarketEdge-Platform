#!/bin/bash

# Render API Configuration Script
# Purpose: Configure environment variables using Render API when CLI fails

set -e

echo "🔧 RENDER API CONFIGURATION SCRIPT"
echo "=================================="
echo "Purpose: Configure environment variables via Render API"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if user has set RENDER_API_TOKEN
if [ -z "$RENDER_API_TOKEN" ]; then
    print_warning "RENDER_API_TOKEN not set in environment"
    echo ""
    echo "To get your Render API token:"
    echo "1. Go to https://dashboard.render.com/account/settings"
    echo "2. Click 'Generate new token'"
    echo "3. Copy the token"
    echo "4. Export it: export RENDER_API_TOKEN='your_token_here'"
    echo ""
    echo "Alternative: Create a .env file with RENDER_API_TOKEN=your_token"
    echo ""
    
    # Try to load from .env file
    if [ -f ".env" ]; then
        print_status "Loading environment from .env file..."
        export $(grep -v '^#' .env | xargs)
        if [ -n "$RENDER_API_TOKEN" ]; then
            print_success "API token loaded from .env file"
        fi
    fi
fi

# Function to get service ID by name
get_service_id() {
    local service_name=$1
    print_status "Getting service ID for: $service_name"
    
    if [ -z "$RENDER_API_TOKEN" ]; then
        print_error "API token required"
        return 1
    fi
    
    local response=$(curl -s -H "Authorization: Bearer $RENDER_API_TOKEN" \
                     -H "Accept: application/json" \
                     "https://api.render.com/v1/services")
    
    if echo "$response" | jq -e '.[] | select(.name == "'$service_name'") | .id' >/dev/null 2>&1; then
        local service_id=$(echo "$response" | jq -r '.[] | select(.name == "'$service_name'") | .id')
        echo "$service_id"
        return 0
    else
        print_error "Service not found or API call failed"
        return 1
    fi
}

# Function to set environment variable
set_env_var() {
    local service_id=$1
    local key=$2
    local value=$3
    
    print_status "Setting environment variable: $key"
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/render_response \
                     -H "Authorization: Bearer $RENDER_API_TOKEN" \
                     -H "Content-Type: application/json" \
                     -H "Accept: application/json" \
                     -X POST \
                     "https://api.render.com/v1/services/$service_id/env-vars" \
                     -d "{\"key\": \"$key\", \"value\": \"$value\"}")
    
    if [ "$response" = "201" ]; then
        print_success "Environment variable $key set successfully"
        return 0
    else
        print_error "Failed to set $key (HTTP $response)"
        cat /tmp/render_response
        return 1
    fi
}

# Function to trigger deployment
trigger_deployment() {
    local service_id=$1
    
    print_status "Triggering deployment for service: $service_id"
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/render_deploy_response \
                     -H "Authorization: Bearer $RENDER_API_TOKEN" \
                     -H "Content-Type: application/json" \
                     -H "Accept: application/json" \
                     -X POST \
                     "https://api.render.com/v1/services/$service_id/deploys")
    
    if [ "$response" = "201" ]; then
        print_success "Deployment triggered successfully"
        local deploy_id=$(cat /tmp/render_deploy_response | jq -r '.id')
        echo "Deploy ID: $deploy_id"
        return 0
    else
        print_error "Failed to trigger deployment (HTTP $response)"
        cat /tmp/render_deploy_response
        return 1
    fi
}

# Main configuration function
configure_render_service() {
    print_status "Starting Render service configuration..."
    
    # Get service ID for marketedge-platform
    SERVICE_ID=$(get_service_id "marketedge-platform")
    if [ -z "$SERVICE_ID" ]; then
        print_error "Could not get service ID for marketedge-platform"
        return 1
    fi
    
    print_success "Found service ID: $SERVICE_ID"
    
    # Known environment variables
    declare -A ENV_VARS=(
        ["AUTH0_CLIENT_SECRET"]="9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"
        ["AUTH0_DOMAIN"]="dev-g8trhgbfdq2sk2m8.us.auth0.com"
        ["AUTH0_CLIENT_ID"]="mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
        ["CORS_ORIGINS"]='["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]'
        ["PORT"]="8000"
        ["ENVIRONMENT"]="production"
        ["DEBUG"]="false"
        ["LOG_LEVEL"]="INFO"
        ["JWT_ALGORITHM"]="HS256"
        ["ACCESS_TOKEN_EXPIRE_MINUTES"]="30"
        ["RATE_LIMIT_ENABLED"]="true"
        ["RATE_LIMIT_REQUESTS_PER_MINUTE"]="60"
    )
    
    # Set environment variables
    for key in "${!ENV_VARS[@]}"; do
        set_env_var "$SERVICE_ID" "$key" "${ENV_VARS[$key]}" || print_warning "Failed to set $key"
        sleep 1  # Rate limiting
    done
    
    print_status "Environment variable configuration complete"
    
    # Note about database URLs
    print_warning "DATABASE_URL and REDIS_URL must be set manually from Render dashboard"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click on marketedge-postgres database"
    echo "3. Copy 'Internal Database URL'"
    echo "4. Set as DATABASE_URL in marketedge-platform service"
    echo "5. Repeat for marketedge-redis → REDIS_URL"
    
    # Ask if user wants to trigger deployment
    echo ""
    read -p "Do you want to trigger deployment now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        trigger_deployment "$SERVICE_ID"
    else
        print_status "Deployment not triggered - you can deploy manually from dashboard"
    fi
}

# Function to create environment file template
create_env_template() {
    print_status "Creating .env template file..."
    
    cat << 'EOF' > .env.template
# Render API Configuration
RENDER_API_TOKEN=your_render_api_token_here

# Get your token from: https://dashboard.render.com/account/settings
# Generate new token and paste it above

# Service Configuration (Automatically applied)
AUTH0_CLIENT_SECRET=9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2
AUTH0_DOMAIN=dev-g8trhgbfdq2sk2m8.us.auth0.com
AUTH0_CLIENT_ID=mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr
CORS_ORIGINS=["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]
PORT=8000
ENVIRONMENT=production

# Database URLs (Get from Render dashboard)
# DATABASE_URL=postgresql://user:pass@marketedge-postgres:5432/db
# REDIS_URL=redis://marketedge-redis:6379
EOF

    print_success "Created .env.template - copy to .env and add your API token"
}

# Main execution
if [ -n "$RENDER_API_TOKEN" ]; then
    configure_render_service
else
    print_error "Cannot proceed without RENDER_API_TOKEN"
    create_env_template
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.template to .env"
    echo "2. Add your Render API token"
    echo "3. Run this script again"
    exit 1
fi

print_success "Render API configuration complete!"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Manually set DATABASE_URL and REDIS_URL from dashboard"
echo "2. Monitor deployment at: https://dashboard.render.com"
echo "3. Test platform: https://marketedge-platform.onrender.com/health"
echo "4. Run validation: ./validate-render-deployment.sh"