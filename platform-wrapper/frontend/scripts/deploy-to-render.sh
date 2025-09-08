#!/bin/bash

# Deploy to Render Platform Script
# Epic 2: Railway to Render Migration
# Version: 1.0.0

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
RENDER_YAML="../backend/render.yaml"
DOCKERFILE_PATH="../backend/Dockerfile"
ENVIRONMENT="${1:-staging}"
BRANCH="${2:-main}"

# Auto-detect project structure
if [ -f "backend/render.yaml" ]; then
    RENDER_YAML="backend/render.yaml"
    DOCKERFILE_PATH="backend/Dockerfile"
elif [ -f "../backend/render.yaml" ]; then
    RENDER_YAML="../backend/render.yaml"
    DOCKERFILE_PATH="../backend/Dockerfile"
elif [ -f "render.yaml" ]; then
    RENDER_YAML="render.yaml"
    DOCKERFILE_PATH="Dockerfile"
fi

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Banner
echo "🚀 MarketEdge Platform - Deploy to Render"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Branch: $BRANCH"
echo "Config: $RENDER_YAML"
echo ""

# Step 1: Validate prerequisites
log_step "1/8: Validating prerequisites..."

# Check if render.yaml exists
if [ ! -f "$RENDER_YAML" ]; then
    log_error "render.yaml not found in current directory"
    exit 1
fi

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    log_warning "Render CLI not found. Installing..."
    brew tap render-oss/render
    brew install render
    
    if ! command -v render &> /dev/null; then
        log_error "Failed to install Render CLI"
        log_info "Please install manually: https://render.com/docs/cli"
        exit 1
    fi
fi

log_success "Prerequisites validated"

# Step 2: Validate Docker configuration
log_step "2/8: Validating Docker configuration..."

if [ -f "$DOCKERFILE_PATH" ]; then
    log_info "Dockerfile found at: $DOCKERFILE_PATH"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        log_info "Docker is running - testing build..."
        
        # Get the directory containing the Dockerfile
        DOCKER_CONTEXT=$(dirname "$DOCKERFILE_PATH")
        
        # Test Docker build from the correct context
        if docker build -t marketedge-render-test "$DOCKER_CONTEXT" --progress=plain 2>&1 | tail -5; then
            log_success "Docker build test successful"
        else
            log_warning "Docker build test failed - continuing anyway"
        fi
    else
        log_warning "Docker not running - skipping build test"
    fi
else
    log_error "Dockerfile not found at: $DOCKERFILE_PATH"
    exit 1
fi

# Step 3: Validate render.yaml
log_step "3/8: Validating render.yaml configuration..."

# Basic YAML validation
if python3 -c "import yaml; yaml.safe_load(open('$RENDER_YAML'))" 2>/dev/null; then
    log_success "render.yaml is valid YAML"
else
    log_error "render.yaml has invalid YAML syntax"
    exit 1
fi

# Extract service information
SERVICE_NAME=$(grep -m1 "name:" $RENDER_YAML | awk '{print $3}')
log_info "Service name: $SERVICE_NAME"

# Step 4: Check Git status
log_step "4/8: Checking Git status..."

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    log_warning "You have uncommitted changes:"
    git status --short
    
    read -p "Do you want to commit these changes before deploying? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Deploy: Prepare for Render deployment to $ENVIRONMENT"
        log_success "Changes committed"
    else
        log_warning "Proceeding with uncommitted changes"
    fi
fi

# Step 5: Environment variable preparation
log_step "5/8: Preparing environment variables..."

# Create environment variable documentation
ENV_DOC="docs/$(date +%Y_%m_%d)/render_env_vars_${ENVIRONMENT}.md"
mkdir -p "$(dirname "$ENV_DOC")"

cat > "$ENV_DOC" << EOF
# Render Environment Variables - $ENVIRONMENT
Generated: $(date)
Service: $SERVICE_NAME

## Required Environment Variables

### Auth0 Configuration
- AUTH0_CLIENT_SECRET (Set manually in Render dashboard)

### Database Configuration
- DATABASE_URL (Auto-populated by Render)
- REDIS_URL (Auto-populated by Render)

### Optional Configuration
- SENTRY_DSN
- DATADOG_API_KEY
- SLACK_WEBHOOK_URL

## Setting Variables in Render

1. Navigate to your service dashboard
2. Go to Environment > Environment Variables
3. Add the required secrets manually
4. Save changes and redeploy

EOF

log_success "Environment variable documentation created: $ENV_DOC"

# Step 6: Create deployment checklist
log_step "6/8: Creating deployment checklist..."

CHECKLIST="docs/$(date +%Y_%m_%d)/render_deployment_checklist_${ENVIRONMENT}.md"

cat > "$CHECKLIST" << EOF
# Render Deployment Checklist - $ENVIRONMENT
Date: $(date)
Deployer: $(git config user.name)

## Pre-Deployment
- [ ] Docker build tested locally
- [ ] render.yaml validated
- [ ] Environment variables documented
- [ ] Git changes committed
- [ ] Branch is up to date with remote

## Render Account Setup
- [ ] Render account created
- [ ] Team members invited
- [ ] Billing configured
- [ ] Service tier selected (Standard for production)

## Service Configuration
- [ ] GitHub repository connected
- [ ] Auto-deploy from branch: $BRANCH
- [ ] Build settings configured
- [ ] Health check endpoint verified (/health)

## Database Setup
- [ ] PostgreSQL database created
- [ ] Redis instance created
- [ ] Connection strings verified
- [ ] Backup strategy configured

## Environment Variables
- [ ] AUTH0_CLIENT_SECRET set
- [ ] JWT_SECRET_KEY generated
- [ ] CORS origins configured
- [ ] Rate limiting configured

## DNS and SSL
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] CORS origins updated with final domain

## Post-Deployment Validation
- [ ] Service is running (green status)
- [ ] Health check passing
- [ ] Logs reviewed for errors
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Auth0 integration working
- [ ] CORS requests successful
- [ ] Rate limiting functional

## Monitoring Setup
- [ ] Log aggregation configured
- [ ] Alerts configured
- [ ] Performance baselines established
- [ ] Error tracking enabled

## Documentation
- [ ] Deployment notes updated
- [ ] Team notified of deployment
- [ ] Runbook updated
- [ ] Known issues documented

EOF

log_success "Deployment checklist created: $CHECKLIST"

# Step 7: Generate deployment commands
log_step "7/8: Generating deployment commands..."

DEPLOY_COMMANDS="docs/$(date +%Y_%m_%d)/render_deploy_commands_${ENVIRONMENT}.sh"

cat > "$DEPLOY_COMMANDS" << 'EOF'
#!/bin/bash

# Render Deployment Commands
# Execute these commands to deploy to Render

echo "=== Manual Deployment Steps for Render ==="
echo ""
echo "1. Create Render account (if not already done):"
echo "   https://dashboard.render.com/register"
echo ""
echo "2. Install Render CLI (if not installed):"
echo "   brew tap render-oss/render && brew install render"
echo ""
echo "3. Login to Render:"
echo "   render login"
echo ""
echo "4. Create new Blueprint deployment:"
echo "   render blueprint launch"
echo "   - Select your render.yaml file"
echo "   - Choose your GitHub repository"
echo "   - Configure environment variables"
echo ""
echo "5. Or deploy via GitHub:"
echo "   a. Push render.yaml to your repository"
echo "   b. Go to https://dashboard.render.com"
echo "   c. Click 'New' > 'Blueprint'"
echo "   d. Connect your GitHub repository"
echo "   e. Render will auto-detect render.yaml"
echo ""
echo "6. Set required environment variables in dashboard:"
echo "   - AUTH0_CLIENT_SECRET"
echo "   - Any other sensitive variables"
echo ""
echo "7. Monitor deployment:"
echo "   - Check build logs"
echo "   - Verify health checks"
echo "   - Test endpoints"
echo ""
echo "8. Custom domain setup (optional):"
echo "   - Add custom domain in Render dashboard"
echo "   - Update DNS records"
echo "   - Update CORS_ALLOWED_ORIGINS"
echo ""
EOF

chmod +x "$DEPLOY_COMMANDS"
log_success "Deployment commands generated: $DEPLOY_COMMANDS"

# Step 8: Final summary
log_step "8/8: Deployment preparation complete!"

echo ""
echo "=========================================="
echo "📋 DEPLOYMENT SUMMARY"
echo "=========================================="
echo ""
echo "✅ Configuration validated"
echo "✅ Documentation generated"
echo "✅ Deployment checklist created"
echo ""
echo "📄 Generated Files:"
echo "   - $ENV_DOC"
echo "   - $CHECKLIST"
echo "   - $DEPLOY_COMMANDS"
echo ""
echo "🚀 Next Steps:"
echo "1. Review the deployment checklist"
echo "2. Set up Render account if needed"
echo "3. Execute deployment commands"
echo "4. Configure environment variables in Render dashboard"
echo "5. Monitor deployment progress"
echo ""
echo "📖 Documentation:"
echo "   - Render Docs: https://render.com/docs"
echo "   - Blueprint Reference: https://render.com/docs/blueprint-spec"
echo ""
echo "⚠️  Important Reminders:"
echo "   - Set AUTH0_CLIENT_SECRET manually in Render"
echo "   - Verify database connection strings"
echo "   - Update CORS origins with production domain"
echo "   - Configure custom domain if needed"
echo ""

log_success "Ready to deploy to Render!"

# Option to open Render dashboard
read -p "Open Render dashboard in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://dashboard.render.com"
fi

exit 0