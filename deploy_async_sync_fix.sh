#!/bin/bash

# Deployment Script for Async/Sync Database Session Fix
# Purpose: Deploy critical fix for £925K Zebra Associates opportunity
# Date: 2025-09-12

set -e  # Exit on error

echo "=================================================="
echo "CRITICAL DEPLOYMENT: Async/Sync Database Fix"
echo "Purpose: Unblock £925K Zebra Associates opportunity"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify current branch
echo -e "${YELLOW}Step 1: Verifying current branch...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${RED}ERROR: Not on main branch. Current branch: $CURRENT_BRANCH${NC}"
    echo "Please switch to main branch: git checkout main"
    exit 1
fi
echo -e "${GREEN}✓ On main branch${NC}"
echo ""

# Step 2: Check for uncommitted changes
echo -e "${YELLOW}Step 2: Checking uncommitted changes...${NC}"
if ! git diff --quiet app/auth/dependencies.py; then
    echo -e "${GREEN}✓ Found async/sync fixes in app/auth/dependencies.py${NC}"
else
    echo -e "${RED}WARNING: No changes detected in app/auth/dependencies.py${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 3: Run local tests
echo -e "${YELLOW}Step 3: Running local validation tests...${NC}"
if [ -f "test_feature_flags_cors_fix.py" ]; then
    echo "Running CORS fix validation tests..."
    python3 test_feature_flags_cors_fix.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}✗ Tests failed. Please fix before deploying.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: test_feature_flags_cors_fix.py not found${NC}"
fi
echo ""

# Step 4: Commit changes
echo -e "${YELLOW}Step 4: Committing changes...${NC}"
echo "Staging app/auth/dependencies.py..."
git add app/auth/dependencies.py

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${YELLOW}No changes to commit. Checking if fix is already committed...${NC}"
    LAST_COMMIT=$(git log -1 --oneline)
    echo "Last commit: $LAST_COMMIT"
    read -p "Deploy current HEAD to production? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Creating commit..."
    git commit -m "CRITICAL: Fix async/sync database session mismatch for £925K Zebra

- Fixed async/sync mismatch in get_current_user and require_admin
- Made authentication dependencies use AsyncSession consistently  
- Added backward compatibility with sync versions
- Resolves CORS errors masking 500 errors on feature flags endpoint
- Critical for Matt Lindop accessing https://app.zebra.associates

Issue: Async endpoints receiving sync database sessions
Solution: Consistent async/await pattern with AsyncSession
Impact: Unblocks £925K Zebra Associates opportunity"
    
    echo -e "${GREEN}✓ Changes committed${NC}"
fi
echo ""

# Step 5: Push to remote
echo -e "${YELLOW}Step 5: Pushing to remote repository...${NC}"
echo "Pushing to origin/main..."
git push origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully pushed to remote${NC}"
else
    echo -e "${RED}✗ Failed to push. Please check your credentials and network.${NC}"
    exit 1
fi
echo ""

# Step 6: Trigger deployment
echo -e "${YELLOW}Step 6: Deployment triggered on Render${NC}"
echo "Render will automatically deploy from the main branch."
echo ""

# Step 7: Wait for deployment
echo -e "${YELLOW}Step 7: Waiting for deployment to complete...${NC}"
echo "Estimated time: 5-10 minutes"
echo "You can monitor at: https://dashboard.render.com"
echo ""

# Wait a moment before starting health checks
sleep 30

# Step 8: Health check loop
echo -e "${YELLOW}Step 8: Running health checks...${NC}"
MAX_ATTEMPTS=20
ATTEMPT=0
SUCCESS=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "Attempt $ATTEMPT/$MAX_ATTEMPTS: "
    
    # Try health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://marketedge-platform.onrender.com/health)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Service is healthy${NC}"
        SUCCESS=true
        break
    else
        echo -e "${YELLOW}Service not ready (HTTP $HTTP_CODE), waiting 30s...${NC}"
        sleep 30
    fi
done

if [ "$SUCCESS" = false ]; then
    echo -e "${RED}✗ Deployment health check failed after $MAX_ATTEMPTS attempts${NC}"
    echo "Please check Render dashboard for deployment status"
    exit 1
fi
echo ""

# Step 9: Verify feature flags endpoint
echo -e "${YELLOW}Step 9: Verifying feature flags endpoint...${NC}"
echo "Testing CORS headers on OPTIONS request..."

CORS_CHECK=$(curl -s -X OPTIONS \
    -H "Origin: https://app.zebra.associates" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: authorization" \
    -I https://marketedge-platform.onrender.com/api/v1/admin/feature-flags \
    | grep -i "access-control-allow-origin")

if [ ! -z "$CORS_CHECK" ]; then
    echo -e "${GREEN}✓ CORS headers present${NC}"
else
    echo -e "${RED}✗ CORS headers missing - deployment may need more time${NC}"
fi
echo ""

# Step 10: Final summary
echo "=================================================="
echo -e "${GREEN}DEPLOYMENT COMPLETE${NC}"
echo "=================================================="
echo ""
echo "Next Steps:"
echo "1. Ask Matt Lindop to test feature flags access at https://app.zebra.associates"
echo "2. Monitor logs for any errors: https://dashboard.render.com"
echo "3. Run production validation: python3 production_deployment_validation.py"
echo ""
echo "Rollback Instructions:"
echo "If issues occur, use Render dashboard to rollback to previous deployment"
echo "https://dashboard.render.com > Service > Deploys > Rollback"
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "Time: $(date)"