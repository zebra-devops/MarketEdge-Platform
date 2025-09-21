#!/bin/bash

# MarketEdge Platform - Staging Environment Setup Script
# This script configures Render Preview Environments for safe testing

set -e

echo "🚀 MarketEdge Staging Environment Setup"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${RED}❌ Render CLI not found. Please install it first:${NC}"
    echo "npm install -g @render-com/cli"
    exit 1
fi

# Check if logged into Render
if ! render auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged into Render. Please login first:${NC}"
    echo "render auth login"
    exit 1
fi

# Function to set environment variable
set_env_var() {
    local service_name=$1
    local key=$2
    local value=$3
    local is_secret=$4

    echo -e "${BLUE}Setting ${key} for ${service_name}...${NC}"

    if [ "$is_secret" = "true" ]; then
        render env set --service-name="$service_name" --key="$key" --value="$value" --secret
    else
        render env set --service-name="$service_name" --key="$key" --value="$value"
    fi
}

# Function to create staging environment variables
setup_staging_env_vars() {
    echo -e "${GREEN}📦 Setting up staging environment variables...${NC}"

    # Production Auth0 settings (to be configured manually in Render dashboard)
    echo -e "${YELLOW}⚠️  Please manually configure these production Auth0 variables in Render dashboard:${NC}"
    echo "   - AUTH0_DOMAIN"
    echo "   - AUTH0_CLIENT_ID"
    echo "   - AUTH0_CLIENT_SECRET"
    echo "   - AUTH0_AUDIENCE"
    echo ""

    # Staging-specific variables (these will be set automatically for preview environments)
    echo -e "${GREEN}✅ Preview environments will automatically use staging values for:${NC}"
    echo "   - ENVIRONMENT=staging"
    echo "   - ALLOWED_ORIGINS=* (all origins allowed for testing)"
    echo "   - ENABLE_DEBUG_LOGGING=true"
    echo "   - SENTRY_DSN= (disabled for staging)"
    echo ""

    # Ask user to configure Auth0 staging application
    echo -e "${YELLOW}📋 Auth0 Staging Application Setup Required:${NC}"
    echo "1. Create a new Auth0 application for staging"
    echo "2. Set callback URLs to include preview environment URLs:"
    echo "   - https://*-marketedge-backend.onrender.com/auth/callback"
    echo "   - http://localhost:3000/auth/callback (for local testing)"
    echo "3. Update the staging Auth0 values in render.yaml if needed"
    echo ""
}

# Function to validate render.yaml configuration
validate_render_config() {
    echo -e "${GREEN}🔍 Validating render.yaml configuration...${NC}"

    if [ ! -f "render.yaml" ]; then
        echo -e "${RED}❌ render.yaml not found in current directory${NC}"
        exit 1
    fi

    # Check for preview configuration
    if grep -q "previews:" render.yaml; then
        echo -e "${GREEN}✅ Preview environments configured${NC}"
    else
        echo -e "${RED}❌ Preview environments not configured in render.yaml${NC}"
        exit 1
    fi

    # Check for staging environment variables
    if grep -q "previewValue:" render.yaml; then
        echo -e "${GREEN}✅ Staging environment variables configured${NC}"
    else
        echo -e "${YELLOW}⚠️  No staging-specific environment variables found${NC}"
    fi

    echo -e "${GREEN}✅ render.yaml validation complete${NC}"
}

# Function to set up GitHub branch protection
setup_branch_protection() {
    echo -e "${GREEN}🛡️  Setting up GitHub branch protection rules...${NC}"

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}⚠️  GitHub CLI not found. Please install it to set up branch protection${NC}"
        echo "Manual setup required: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches"
        return
    fi

    # Set up main branch protection
    echo "Setting up main branch protection..."
    gh api repos/:owner/:repo/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["render-preview"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        2>/dev/null && echo -e "${GREEN}✅ Branch protection configured${NC}" || echo -e "${YELLOW}⚠️  Branch protection setup failed - configure manually${NC}"
}

# Function to create test feature branch
create_test_branch() {
    echo -e "${GREEN}🌟 Creating test feature branch for staging validation...${NC}"

    # Create a test branch
    git checkout -b feature/staging-environment-test

    # Create a simple test change
    echo "# Staging Environment Test" > STAGING_TEST.md
    echo "This file tests the staging environment setup." >> STAGING_TEST.md
    echo "Created at: $(date)" >> STAGING_TEST.md

    git add STAGING_TEST.md
    git commit -m "test: add staging environment test file

This commit tests the Preview Environment setup by creating
a simple test file that should trigger a preview deployment.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    echo -e "${GREEN}✅ Test branch created: feature/staging-environment-test${NC}"
    echo -e "${BLUE}Push this branch and create a PR to test preview environments:${NC}"
    echo "git push origin feature/staging-environment-test"
}

# Main execution
main() {
    echo -e "${BLUE}Starting staging environment setup...${NC}"

    # Validate configuration
    validate_render_config

    # Setup environment variables
    setup_staging_env_vars

    # Setup branch protection
    setup_branch_protection

    # Create test branch
    read -p "Create test branch for preview environment validation? (y/n): " create_test
    if [ "$create_test" = "y" ] || [ "$create_test" = "Y" ]; then
        create_test_branch
    fi

    echo ""
    echo -e "${GREEN}🎉 Staging Environment Setup Complete!${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Configure Auth0 staging application with preview URLs"
    echo "2. Push test branch and create PR to validate preview environments"
    echo "3. Verify staging environment deploys correctly"
    echo "4. Test database migrations and seeding in staging"
    echo ""
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "- Preview environments automatically deploy for ALL pull requests"
    echo "- Each preview environment gets its own database and Redis instance"
    echo "- Preview environments expire after 7 days"
    echo "- Production environment remains isolated and protected"
    echo ""
}

# Run main function
main "$@"