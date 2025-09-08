#!/bin/bash

# Force Render Deployment Script
# Critical enum fix must be deployed to production
# Author: DevOps Engineer  
# Date: 2025-08-18

set -e

echo "🚀 FORCE RENDER DEPLOYMENT"
echo "========================="
echo "Critical Fix: e7c70b6 (Enum value mismatch fix)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check current deployment status
check_current_deployment() {
    echo -e "${BLUE}Checking current deployment...${NC}"
    
    CURRENT_HEALTH=$(curl -s https://marketedge-platform.onrender.com/health)
    echo "Current health response: $CURRENT_HEALTH"
    
    # Look for emergency mode - indicates old deployment
    if echo "$CURRENT_HEALTH" | grep -q "emergency_mode"; then
        echo -e "${YELLOW}⚠️  Emergency mode detected - deployment may be outdated${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Service responding normally${NC}"
        return 0
    fi
}

# Function to force deployment via git
force_git_deployment() {
    echo -e "${BLUE}Method 1: Triggering deployment via Git${NC}"
    echo "========================================"
    
    echo "Current branch and commit:"
    git branch --show-current
    git log --oneline -1
    echo ""
    
    echo "Creating deployment trigger commit..."
    git commit --allow-empty -m "🚀 FORCE DEPLOY: Critical enum fix verification (e7c70b6)

CRITICAL FIX DEPLOYMENT:
- Fix: industry=Industry.DEFAULT.value in auth.py line 261  
- Issue: Database enum mismatch causing 500 errors
- Target: Resolve Auth0 authentication failures
- Commit: e7c70b6

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    echo "Pushing to origin main..."
    git push origin main
    
    echo -e "${GREEN}✅ Deployment triggered via Git push${NC}"
    echo ""
}

# Function to provide manual deployment instructions
manual_deployment_instructions() {
    echo -e "${BLUE}Method 2: Manual Render Dashboard Deployment${NC}"
    echo "============================================="
    
    echo "If automatic deployment fails, use manual deployment:"
    echo ""
    echo "1. Go to Render Dashboard:"
    echo "   https://dashboard.render.com"
    echo ""
    echo "2. Find your service 'marketedge-platform'"
    echo ""
    echo "3. Click on the service"
    echo ""
    echo "4. Click 'Manual Deploy' button"
    echo ""  
    echo "5. Select 'Deploy latest commit'"
    echo "   - Should show commit: e7c70b6"
    echo "   - Message: 'CRITICAL FIX: Fix enum value mismatch'"
    echo ""
    echo "6. Click 'Deploy'"
    echo ""
    echo "7. Monitor deployment progress in logs"
    echo ""
}

# Function to monitor deployment progress
monitor_deployment() {
    echo -e "${BLUE}Method 3: Monitoring Deployment Progress${NC}"
    echo "======================================="
    
    echo "After triggering deployment, monitor progress:"
    echo ""
    echo "1. Watch deployment logs (if available via CLI):"
    echo "   # Note: Render CLI not installed, use dashboard"
    echo ""
    echo "2. Monitor health endpoint:"
    echo "   watch -n 10 'curl -s https://marketedge-platform.onrender.com/health'"
    echo ""
    echo "3. Check for service restart:"
    echo "   - Health endpoint will return 503 during restart"
    echo "   - Should return 200 after successful deployment"
    echo ""
    echo "4. Expected deployment time: 3-5 minutes"
    echo ""
}

# Function to verify deployment success
verify_deployment_success() {
    echo -e "${BLUE}Post-Deployment Verification${NC}"
    echo "============================"
    
    echo "After deployment completes, verify the fix:"
    echo ""
    echo "1. Check health endpoint returns 200:"
    echo "   curl https://marketedge-platform.onrender.com/health"
    echo ""
    echo "2. Health response should NOT contain 'emergency_mode'"
    echo ""
    echo "3. Test auth endpoint accessibility:"
    echo "   curl https://marketedge-platform.onrender.com/api/v1/auth0-url"
    echo ""
    echo "4. Critical test - enum fix verification:"
    echo "   - New user creation should work without 500 errors"
    echo "   - Default organization creation should use proper enum"
    echo "   - Auth0 login flow should complete successfully"
    echo ""
    echo "5. Frontend integration test:"
    echo "   - Go to https://app.zebra.associates"
    echo "   - Attempt Auth0 login"
    echo "   - Should complete without 500 server errors"
    echo ""
}

# Function to rollback plan
rollback_plan() {
    echo -e "${BLUE}Rollback Plan (if needed)${NC}"
    echo "========================="
    
    echo "If deployment causes new issues:"
    echo ""
    echo "1. Immediate rollback via Git:"
    echo "   git revert e7c70b6"
    echo "   git push origin main"
    echo ""
    echo "2. Manual rollback via Render:"
    echo "   - Go to deployment history"
    echo "   - Select previous stable deployment"
    echo "   - Click 'Redeploy'"
    echo ""
    echo "3. Emergency fallback:"
    echo "   - Revert to commit before enum fix"
    echo "   - git reset --hard <previous-commit>"
    echo "   - git push --force origin main"
    echo ""
    echo -e "${RED}⚠️  Only use force push in emergencies${NC}"
    echo ""
}

# Main execution
main() {
    echo "Starting forced deployment process..."
    echo ""
    
    # Check if deployment is needed
    if check_current_deployment; then
        echo -e "${YELLOW}Service appears healthy. Verify if enum fix is deployed.${NC}"
        read -p "Continue with deployment? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Deployment cancelled."
            exit 0
        fi
    else
        echo -e "${RED}Service shows emergency mode. Deployment needed.${NC}"
    fi
    
    echo ""
    echo "=== DEPLOYMENT METHODS ==="
    echo ""
    
    # Show all deployment methods
    force_git_deployment
    manual_deployment_instructions  
    monitor_deployment
    verify_deployment_success
    rollback_plan
    
    echo -e "${GREEN}=== DEPLOYMENT INITIATED ===${NC}"
    echo ""
    echo "✅ Git deployment trigger sent"
    echo "⏳ Waiting for Render to pick up changes..."
    echo "🔍 Monitor progress via Render dashboard"
    echo "🎯 Target: Fix Auth0 500 errors with proper enum values"
    echo ""
    echo "Next: Run ./devops_deployment_verification.sh to verify"
    echo ""
}

# Execute main function
main "$@"