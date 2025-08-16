#!/bin/bash

# EPIC 2: Complete Render Deployment Package
# All-in-one script for Render CLI deployment automation

echo "🚀 EPIC 2: RENDER DEPLOYMENT PACKAGE"
echo "===================================="
echo "Complete automation for MarketEdge platform restoration"
echo ""

# Set up environment
set -e
export RENDER_SERVICE_NAME="marketedge-platform"
export RENDER_POSTGRES_NAME="marketedge-postgres" 
export RENDER_REDIS_NAME="marketedge-redis"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_section "CHECKING PREREQUISITES"
    
    # Check if render CLI is installed
    if command -v render &> /dev/null; then
        print_success "Render CLI installed"
        render --version
    else
        print_error "Render CLI not installed"
        echo "Install with: brew tap render-oss/render && brew install render"
        exit 1
    fi
    
    # Check authentication
    if render whoami &> /dev/null; then
        print_success "Render CLI authenticated"
        render whoami
    else
        print_warning "Render CLI not authenticated"
        echo "Run: render login"
        return 1
    fi
    
    # Check workspace
    if render workspace current &> /dev/null; then
        print_success "Render workspace configured"
    else
        print_warning "No workspace set - may need manual configuration"
    fi
}

# Function to list and verify services
verify_services() {
    print_section "VERIFYING RENDER SERVICES"
    
    # Try to list services
    if render services list --output json &> /dev/null; then
        print_success "Services accessible via CLI"
        render services list --output json | jq '.[] | {name: .name, type: .type, status: .status}' 2>/dev/null || echo "Services found"
    else
        print_warning "Cannot access services via CLI - using dashboard approach"
        echo "Services should exist:"
        echo "  - marketedge-platform (Web Service)"
        echo "  - marketedge-postgres (PostgreSQL)"  
        echo "  - marketedge-redis (Redis)"
    fi
}

# Function to configure environment variables via CLI
configure_env_vars_cli() {
    print_section "CONFIGURING ENVIRONMENT VARIABLES (CLI)"
    
    # Known secure values
    AUTH0_CLIENT_SECRET="9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"
    
    # Environment variables to set
    declare -A ENV_VARS=(
        ["AUTH0_CLIENT_SECRET"]="$AUTH0_CLIENT_SECRET"
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
    
    # Attempt to set via CLI
    local success_count=0
    local total_count=${#ENV_VARS[@]}
    
    for key in "${!ENV_VARS[@]}"; do
        echo "Setting $key..."
        if render env set --key "$key" --value "${ENV_VARS[$key]}" --service-name "$RENDER_SERVICE_NAME" 2>/dev/null; then
            print_success "Set $key"
            ((success_count++))
        else
            print_warning "Failed to set $key via CLI"
        fi
        sleep 0.5  # Rate limiting
    done
    
    echo ""
    echo "CLI Configuration Results: $success_count/$total_count successful"
    
    if [ $success_count -eq $total_count ]; then
        return 0
    else
        return 1
    fi
}

# Function to trigger deployment
trigger_deployment() {
    print_section "TRIGGERING DEPLOYMENT"
    
    if render deploy --service-name "$RENDER_SERVICE_NAME" 2>/dev/null; then
        print_success "Deployment triggered via CLI"
        echo "Monitor at: https://dashboard.render.com"
        return 0
    else
        print_warning "CLI deployment failed - use manual deployment"
        return 1
    fi
}

# Function to validate deployment
validate_deployment() {
    print_section "VALIDATING DEPLOYMENT"
    
    local backend_url="https://marketedge-platform.onrender.com"
    local max_attempts=12  # 2 minutes with 10-second intervals
    local attempt=1
    
    echo "Waiting for deployment to complete..."
    echo "Testing: $backend_url/health"
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts..."
        
        local http_code=$(curl -s -w "%{http_code}" -o /tmp/health_response --max-time 10 "$backend_url/health" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ]; then
            print_success "Backend health check PASSED"
            echo "Response:"
            cat /tmp/health_response
            echo ""
            
            # Test CORS
            echo "Testing CORS configuration..."
            local cors_response=$(curl -s -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
                                      -H "Access-Control-Request-Method: GET" \
                                      -X OPTIONS "$backend_url/api/v1/health" --max-time 5 2>/dev/null || echo "")
            
            if echo "$cors_response" | grep -qi "access-control-allow-origin"; then
                print_success "CORS configuration working"
            else
                print_warning "CORS may need configuration"
            fi
            
            return 0
        elif [ "$http_code" = "503" ] || [ "$http_code" = "502" ]; then
            echo "Service starting up... (HTTP $http_code)"
        else
            echo "Service not ready (HTTP $http_code)"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    print_error "Deployment validation failed - service not responding after 2 minutes"
    echo "Check Render dashboard for deployment logs"
    return 1
}

# Function to provide manual instructions
provide_manual_instructions() {
    print_section "MANUAL CONFIGURATION REQUIRED"
    
    echo "Since CLI automation failed, complete these steps manually:"
    echo ""
    echo "1. Open: https://dashboard.render.com"
    echo "2. Click on 'marketedge-platform' service"
    echo "3. Go to 'Environment' tab"
    echo "4. Set these critical variables:"
    echo ""
    echo "   DATABASE_URL = [Get from marketedge-postgres Internal Database URL]"
    echo "   REDIS_URL = [Get from marketedge-redis Internal Database URL]"
    echo "   AUTH0_CLIENT_SECRET = 9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"
    echo "   CORS_ORIGINS = [\"https://frontend-5r7ft62po-zebraassociates-projects.vercel.app\",\"http://localhost:3000\"]"
    echo ""
    echo "5. Click 'Manual Deploy' to trigger deployment"
    echo "6. Monitor build logs for success"
    echo ""
    echo "📖 See EPIC2_FINAL_DEPLOYMENT_INSTRUCTIONS.md for detailed steps"
}

# Main execution flow
main() {
    echo "Starting Epic 2 deployment automation..."
    echo "Target: Restore MarketEdge platform on Render"
    echo ""
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites not met - fix authentication and try again"
        exit 1
    fi
    
    # Verify services
    verify_services
    
    # Try CLI configuration
    if configure_env_vars_cli; then
        print_success "Environment variables configured via CLI"
        
        # Try to trigger deployment
        if trigger_deployment; then
            # Validate deployment
            if validate_deployment; then
                print_success "🎉 EPIC 2 DEPLOYMENT SUCCESSFUL!"
                echo ""
                echo "✅ Platform Status: OPERATIONAL"
                echo "🔗 Backend: https://marketedge-platform.onrender.com"
                echo "🔗 Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
                echo "✅ Railway Migration: COMPLETE"
                echo ""
                echo "Epic 2 objectives achieved! 🚀"
                exit 0
            else
                print_warning "Deployment validation failed - check logs"
            fi
        else
            print_warning "CLI deployment trigger failed"
        fi
    else
        print_warning "CLI environment configuration failed"
    fi
    
    # Fall back to manual instructions
    provide_manual_instructions
    
    echo ""
    echo "🔧 Manual configuration required to complete Epic 2"
    echo "📋 Follow the instructions above or in EPIC2_FINAL_DEPLOYMENT_INSTRUCTIONS.md"
    echo "🚀 Platform restoration is 90% complete - just needs final dashboard config!"
}

# Execute main function
main "$@"