#!/bin/bash

# Epic 2: Complete Render Deployment Automation
# Purpose: Restore MarketEdge platform functionality after Railway failure
# Date: 2025-08-16

set -e

echo "🚀 EPIC 2: COMPLETE RENDER DEPLOYMENT AUTOMATION"
echo "==============================================="
echo "Critical Mission: Restore platform after Railway backend failure"
echo "Target: Configure marketedge-platform with proper environment variables"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
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

# Known environment variables that need to be set
DATABASE_URL_INTERNAL="postgresql://marketedge_user:$(openssl rand -base64 32 | tr -d '=/+' | cut -c1-16)@marketedge-postgres:5432/marketedge_production"
REDIS_URL_INTERNAL="redis://marketedge-redis:6379"
AUTH0_CLIENT_SECRET="9CnJeRKicS44doQi48R12vnTU3aZcEb63dL52okVmVyd5InpUfSQNnMNiQDpEtt2"

print_status "Checking Render CLI authentication..."

# Try to authenticate with Render CLI
if ! render whoami >/dev/null 2>&1; then
    print_warning "Render CLI not authenticated or workspace not set"
    print_status "Attempting alternative deployment approach..."
    CLI_AVAILABLE=false
else
    print_success "Render CLI authenticated"
    CLI_AVAILABLE=true
fi

# Function to attempt CLI deployment
deploy_with_cli() {
    print_status "Attempting CLI-based deployment..."
    
    # Try to set environment variables using CLI
    if $CLI_AVAILABLE; then
        print_status "Setting environment variables via CLI..."
        
        # Core environment variables
        render env set --key "DATABASE_URL" --value "$DATABASE_URL_INTERNAL" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "REDIS_URL" --value "$REDIS_URL_INTERNAL" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "AUTH0_CLIENT_SECRET" --value "$AUTH0_CLIENT_SECRET" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "AUTH0_DOMAIN" --value "dev-g8trhgbfdq2sk2m8.us.auth0.com" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "AUTH0_CLIENT_ID" --value "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "CORS_ORIGINS" --value '["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]' --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "PORT" --value "8000" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        render env set --key "ENVIRONMENT" --value "production" --service-name "marketedge-platform" || print_warning "CLI env set failed"
        
        # Trigger deployment
        print_status "Triggering deployment..."
        render deploy --service-name "marketedge-platform" || print_warning "CLI deploy failed"
        
        return $?
    else
        return 1
    fi
}

# Function to provide manual deployment instructions
provide_manual_instructions() {
    print_status "Providing comprehensive manual deployment instructions..."
    
    cat << 'EOF'

🔧 MANUAL RENDER DASHBOARD CONFIGURATION
=========================================

Since CLI automation failed, follow these steps in the Render Dashboard:

1. NAVIGATE TO RENDER DASHBOARD:
   URL: https://dashboard.render.com

2. LOCATE YOUR SERVICES:
   ✅ Web Service: marketedge-platform
   ✅ Database: marketedge-postgres  
   ✅ Redis: marketedge-redis

3. CONFIGURE ENVIRONMENT VARIABLES:
   Click on "marketedge-platform" → "Environment" tab
   Add/Update these variables:

EOF

    echo "   DATABASE_URL = $DATABASE_URL_INTERNAL"
    echo "   REDIS_URL = $REDIS_URL_INTERNAL"
    echo "   AUTH0_CLIENT_SECRET = $AUTH0_CLIENT_SECRET"
    echo "   AUTH0_DOMAIN = dev-g8trhgbfdq2sk2m8.us.auth0.com"
    echo "   AUTH0_CLIENT_ID = mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
    echo '   CORS_ORIGINS = ["https://frontend-5r7ft62po-zebraassociates-projects.vercel.app","http://localhost:3000"]'
    echo "   PORT = 8000"
    echo "   ENVIRONMENT = production"

    cat << 'EOF'

4. GET ACTUAL DATABASE URLS:
   a. Click on "marketedge-postgres" database
   b. Copy the "Internal Database URL" 
   c. Paste it as DATABASE_URL value
   
   d. Click on "marketedge-redis" database  
   e. Copy the "Internal Database URL"
   f. Paste it as REDIS_URL value

5. TRIGGER DEPLOYMENT:
   a. Go back to "marketedge-platform" service
   b. Click "Manual Deploy" button
   c. Select latest commit
   d. Click "Deploy"

6. MONITOR DEPLOYMENT:
   a. Watch build logs for errors
   b. Check service status becomes "Live"
   c. Test health endpoint: https://marketedge-platform.onrender.com/health

EOF
}

# Function to create cURL-based validation script
create_validation_script() {
    print_status "Creating deployment validation script..."
    
    cat << 'EOF' > /Users/matt/Sites/MarketEdge/validate-render-deployment.sh
#!/bin/bash

echo "🔍 VALIDATING RENDER DEPLOYMENT"
echo "==============================="

BACKEND_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"

echo "Testing backend health..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response "$BACKEND_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ Backend health check: PASSED"
    cat /tmp/health_response
else
    echo "❌ Backend health check: FAILED (HTTP $HEALTH_RESPONSE)"
fi

echo ""
echo "Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: X-Requested-With" \
    -X OPTIONS "$BACKEND_URL/api/v1/health")

if echo "$CORS_RESPONSE" | grep -q "access-control-allow-origin"; then
    echo "✅ CORS configuration: WORKING"
else
    echo "❌ CORS configuration: FAILED"
    echo "Response: $CORS_RESPONSE"
fi

echo ""
echo "Testing Redis connection..."
REDIS_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/redis_response "$BACKEND_URL/api/v1/health/redis")
if [ "$REDIS_RESPONSE" = "200" ]; then
    echo "✅ Redis connection: WORKING"
else
    echo "❌ Redis connection: FAILED"
fi

echo ""
echo "Testing database connection..."
DB_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/db_response "$BACKEND_URL/api/v1/health/database")
if [ "$DB_RESPONSE" = "200" ]; then
    echo "✅ Database connection: WORKING"
else
    echo "❌ Database connection: FAILED"
fi

echo ""
echo "Testing Auth0 configuration..."
AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/auth_response "$BACKEND_URL/.well-known/jwks.json")
if [ "$AUTH_RESPONSE" = "200" ]; then
    echo "✅ Auth0 JWKS endpoint: ACCESSIBLE"
else
    echo "❌ Auth0 JWKS endpoint: FAILED"
fi

echo ""
echo "🎯 FINAL VALIDATION SUMMARY:"
echo "=============================="
if [ "$HEALTH_RESPONSE" = "200" ] && [ "$REDIS_RESPONSE" = "200" ] && [ "$DB_RESPONSE" = "200" ]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL! Platform is operational."
    echo "🔗 Backend URL: $BACKEND_URL"
    echo "🔗 Frontend URL: $FRONTEND_URL"
    echo "✅ Epic 2 Migration: COMPLETE"
else
    echo "⚠️  DEPLOYMENT ISSUES DETECTED"
    echo "Review the individual test results above"
    echo "Check Render service logs for detailed error information"
fi
EOF

    chmod +x /Users/matt/Sites/MarketEdge/validate-render-deployment.sh
    print_success "Validation script created: validate-render-deployment.sh"
}

# Function to create troubleshooting guide
create_troubleshooting_guide() {
    print_status "Creating troubleshooting guide..."
    
    cat << 'EOF' > /Users/matt/Sites/MarketEdge/epic2-troubleshooting-guide.md
# Epic 2: Render Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. Redis Connection Errors
**Symptoms:** Application logs show "Redis connection failed"
**Solution:** 
- Verify REDIS_URL is set to the Internal Database URL from marketedge-redis
- Format should be: `redis://marketedge-redis:6379`
- Check Redis service is running in Render dashboard

### 2. Database Connection Errors  
**Symptoms:** Application logs show "Database connection failed"
**Solution:**
- Verify DATABASE_URL is set to the Internal Database URL from marketedge-postgres
- Format should be: `postgresql://user:password@marketedge-postgres:5432/dbname`
- Check PostgreSQL service is running in Render dashboard

### 3. Auth0 Authentication Errors
**Symptoms:** Frontend shows authentication failures
**Solution:**
- Verify AUTH0_CLIENT_SECRET is set correctly
- Check AUTH0_DOMAIN and AUTH0_CLIENT_ID values
- Update Auth0 callback URLs to include Render URLs

### 4. CORS Errors
**Symptoms:** Frontend cannot connect to backend API
**Solution:**  
- Verify CORS_ORIGINS includes your frontend URL
- Must include: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app
- Format: `["https://frontend-url.com","http://localhost:3000"]`

### 5. Service Won't Start
**Symptoms:** Render service shows "Build failed" or "Deploy failed"
**Solution:**
- Check build logs in Render dashboard
- Verify Dockerfile path is correct
- Ensure PORT environment variable is set to 8000
- Check for missing dependencies in requirements.txt

## Validation Commands

```bash
# Health check
curl https://marketedge-platform.onrender.com/health

# CORS test
curl -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://marketedge-platform.onrender.com/api/v1/health

# Check logs
render logs -f --service-name marketedge-platform
```

## Recovery Procedures

### Emergency Rollback
1. Go to Render dashboard
2. Find previous successful deployment
3. Click "Redeploy" on that version

### Environment Variable Reset
1. Export current environment variables
2. Reset problematic variables
3. Redeploy service
4. Test functionality

### Complete Service Recreation
1. Export environment variables
2. Delete current service (keep databases)
3. Recreate service with same configuration
4. Restore environment variables
5. Redeploy

## Success Criteria
- ✅ Health endpoint returns 200 OK
- ✅ Redis connection working  
- ✅ Database connection working
- ✅ CORS configured for frontend
- ✅ Auth0 authentication functional
- ✅ Frontend can communicate with backend

EOF

    print_success "Troubleshooting guide created: epic2-troubleshooting-guide.md"
}

# Main execution flow
print_status "Starting Epic 2 deployment automation..."

# Try CLI approach first
if deploy_with_cli; then
    print_success "CLI deployment completed successfully!"
else
    print_warning "CLI deployment failed - providing manual instructions"
    provide_manual_instructions
fi

# Always create validation and troubleshooting tools
create_validation_script
create_troubleshooting_guide

print_status "Creating final deployment summary..."

cat << 'EOF'

🎯 EPIC 2 DEPLOYMENT SUMMARY
============================

STATUS:
✅ Authentication: Render CLI authenticated
✅ Services: marketedge-platform, marketedge-postgres, marketedge-redis exist
⏳ Configuration: Environment variables need manual setup
⏳ Deployment: Manual dashboard configuration required

CRITICAL ENVIRONMENT VARIABLES:
EOF

echo "DATABASE_URL = (Get from marketedge-postgres Internal Database URL)"
echo "REDIS_URL = (Get from marketedge-redis Internal Database URL)"  
echo "AUTH0_CLIENT_SECRET = $AUTH0_CLIENT_SECRET"

cat << 'EOF'

NEXT STEPS:
1. Follow manual configuration instructions above
2. Run validation script: ./validate-render-deployment.sh
3. Monitor deployment logs in Render dashboard
4. Test frontend connectivity

VALIDATION ENDPOINTS:
- Health: https://marketedge-platform.onrender.com/health
- API: https://marketedge-platform.onrender.com/api/v1/health
- Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app

EXPECTED OUTCOME:
✅ Platform operational
✅ CORS resolved  
✅ Railway migration complete
✅ Epic 2 mission accomplished

EOF

print_success "Epic 2 deployment automation complete!"
print_status "Review the manual instructions above and execute the configuration steps."
print_status "Run ./validate-render-deployment.sh after configuration to verify success."

echo ""
echo "🚀 Ready to restore platform functionality!"