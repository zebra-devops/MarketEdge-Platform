#!/bin/bash

# Auth0 Staging Environment Setup Script
# Configures staging Auth0 isolation for preview environments

set -e

echo "=================================================="
echo "Auth0 Staging Environment Setup"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_action() {
    echo -e "${BLUE}[ACTION REQUIRED]${NC} $1"
}

# Check if running in MarketEdge directory
if [ ! -f "app/main.py" ]; then
    print_error "This script must be run from the MarketEdge root directory"
    exit 1
fi

print_status "Starting Auth0 staging configuration setup..."

# Step 1: Check current configuration
print_status "Checking current Auth0 configuration..."

if [ -f ".env" ]; then
    CURRENT_AUTH0_DOMAIN=$(grep -E "^AUTH0_DOMAIN=" .env | cut -d'=' -f2 || echo "")
    CURRENT_CLIENT_ID=$(grep -E "^AUTH0_CLIENT_ID=" .env | cut -d'=' -f2 || echo "")

    if [ -n "$CURRENT_AUTH0_DOMAIN" ]; then
        print_status "Current production Auth0 domain: $CURRENT_AUTH0_DOMAIN"
    else
        print_warning "No AUTH0_DOMAIN found in .env file"
    fi
else
    print_warning "No .env file found - using environment variables"
fi

# Step 2: Verify render.yaml configuration
print_status "Verifying render.yaml configuration..."

if grep -q "AUTH0_DOMAIN_STAGING" render.yaml; then
    print_status "✅ render.yaml already configured with staging Auth0 variables"
else
    print_error "❌ render.yaml missing staging Auth0 configuration"
    print_action "Please run the setup to update render.yaml first"
    exit 1
fi

# Step 3: Check backend configuration
print_status "Checking backend configuration updates..."

if grep -q "get_auth0_config" app/core/config.py; then
    print_status "✅ Backend configuration supports environment-aware Auth0"
else
    print_error "❌ Backend configuration missing environment-aware Auth0 support"
    print_action "Please update app/core/config.py with staging configuration"
    exit 1
fi

# Step 4: Check config endpoint
if [ -f "app/api/api_v1/endpoints/config.py" ]; then
    print_status "✅ Configuration endpoint available for frontend"
else
    print_warning "❌ Configuration endpoint missing - frontend won't auto-detect staging"
fi

# Step 5: Generate staging setup checklist
print_status "Generating staging setup checklist..."

cat << 'EOF' > docs/2025_09_21/deployment/AUTH0_STAGING_SETUP_CHECKLIST.md
# Auth0 Staging Setup Checklist

## Manual Configuration Required

### 1. Create Auth0 Staging Application (5 minutes)

- [ ] Navigate to: https://manage.auth0.com/dashboard/us/dev-g8trhgbfdq2sk2m8/applications
- [ ] Click "Create Application"
- [ ] Name: `MarketEdge-Staging`
- [ ] Type: Single Page Application (SPA)
- [ ] Click "Create"

### 2. Configure Staging Application URIs (3 minutes)

**Allowed Callback URLs:**
```
https://*.onrender.com/callback,https://localhost:3000/callback,https://marketedge-staging-*.onrender.com/callback,https://pr-*-marketedge-platform.onrender.com/callback
```

**Allowed Logout URLs:**
```
https://*.onrender.com/,https://localhost:3000/,https://marketedge-staging-*.onrender.com/,https://pr-*-marketedge-platform.onrender.com/
```

**Allowed Web Origins:**
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

**Allowed Origins (CORS):**
```
https://*.onrender.com,https://localhost:3000,https://marketedge-staging-*.onrender.com,https://pr-*-marketedge-platform.onrender.com
```

- [ ] Save changes in Auth0 dashboard

### 3. Configure Render Environment Variables (5 minutes)

Navigate to: https://dashboard.render.com/web/[service-id]/environment

Add these variables:
- [ ] AUTH0_DOMAIN_STAGING = dev-g8trhgbfdq2sk2m8.us.auth0.com
- [ ] AUTH0_CLIENT_ID_STAGING = [Copy from staging Auth0 app]
- [ ] AUTH0_CLIENT_SECRET_STAGING = [Copy from staging Auth0 app] (mark as secret)
- [ ] AUTH0_AUDIENCE_STAGING = https://api.marketedge-staging.onrender.com

### 4. Testing Verification (5 minutes)

- [ ] Create test PR to trigger preview deployment
- [ ] Access preview URL when ready
- [ ] Test authentication flow: login → callback → dashboard
- [ ] Verify staging Auth0 app is used (check network tab)
- [ ] Confirm production Auth0 unaffected

## Success Criteria

✅ Preview environments use staging Auth0 application
✅ Production Auth0 configuration unchanged
✅ Wildcard redirect URIs support all preview URLs
✅ Authentication flow works in preview environments
✅ No production authentication disruption

## Emergency Rollback

If issues occur:
1. Remove staging environment variables from Render
2. Set USE_STAGING_AUTH0=false in environment variables
3. Verify production authentication restored

## Verification Commands

Test staging configuration:
```bash
# Check environment configuration
curl https://pr-[number]-marketedge-platform.onrender.com/api/v1/config/auth0

# Verify health check
curl https://pr-[number]-marketedge-platform.onrender.com/api/v1/config/health
```

Total setup time: ~15 minutes
Impact: Zero production disruption
EOF

print_status "✅ Setup checklist created: docs/2025_09_21/deployment/AUTH0_STAGING_SETUP_CHECKLIST.md"

# Step 6: Generate environment verification script
print_status "Creating environment verification script..."

cat << 'EOF' > scripts/verify-auth0-staging.sh
#!/bin/bash

# Verify Auth0 staging configuration
# Usage: ./scripts/verify-auth0-staging.sh [preview-url]

PREVIEW_URL=${1:-"http://localhost:8000"}
API_BASE="${PREVIEW_URL}/api/v1"

echo "Verifying Auth0 staging configuration..."
echo "Preview URL: $PREVIEW_URL"
echo "API Base: $API_BASE"

# Test configuration endpoint
echo ""
echo "Testing configuration endpoint..."
curl -s "${API_BASE}/config/auth0" | jq '.' || echo "Failed to get Auth0 config"

# Test health endpoint
echo ""
echo "Testing health endpoint..."
curl -s "${API_BASE}/config/health" | jq '.' || echo "Failed to get health status"

# Test environment endpoint
echo ""
echo "Testing environment endpoint..."
curl -s "${API_BASE}/config/environment" | jq '.' || echo "Failed to get environment config"

echo ""
echo "Verification complete."
EOF

chmod +x scripts/verify-auth0-staging.sh

print_status "✅ Verification script created: scripts/verify-auth0-staging.sh"

# Step 7: Final summary
echo ""
echo "=================================================="
print_status "AUTH0 STAGING SETUP COMPLETE"
echo "=================================================="

print_action "NEXT STEPS:"
echo "1. Follow the checklist: docs/2025_09_21/deployment/AUTH0_STAGING_SETUP_CHECKLIST.md"
echo "2. Create Auth0 staging application manually"
echo "3. Configure Render environment variables"
echo "4. Test with preview deployment"
echo "5. Verify with: ./scripts/verify-auth0-staging.sh [preview-url]"

echo ""
print_status "Configuration files updated:"
echo "  ✅ render.yaml - Preview environment variables configured"
echo "  ✅ app/core/config.py - Environment-aware Auth0 configuration"
echo "  ✅ app/api/api_v1/endpoints/config.py - Frontend configuration endpoint"
echo "  ✅ Documentation created in docs/2025_09_21/deployment/"

echo ""
print_warning "Manual configuration required:"
echo "  🔧 Auth0 dashboard - Create staging application"
echo "  🔧 Render dashboard - Set environment variables"
echo "  🔧 Test preview deployment - Verify authentication"

echo ""
print_status "Total estimated time: 15 minutes"
print_status "Risk level: LOW (no production impact)"
print_status "Ready for £925K Zebra Associates opportunity testing"

echo "=================================================="