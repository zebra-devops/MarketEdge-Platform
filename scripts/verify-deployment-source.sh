#!/bin/bash

# Verify Deployment Source - Check what's actually deployed vs what should be
# Usage: ./scripts/verify-deployment-source.sh

set -e

echo "=========================================="
echo "🔍 DEPLOYMENT SOURCE VERIFICATION"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check current local staging branch
echo "📍 Local Repository Status:"
echo "----------------------------"
CURRENT_BRANCH=$(git branch --show-current)
LOCAL_STAGING_SHA=$(git rev-parse staging 2>/dev/null || echo "not-found")
REMOTE_STAGING_SHA=$(git rev-parse origin/staging 2>/dev/null || echo "not-found")
HEAD_SHA=$(git rev-parse HEAD)

echo "   Current branch: $CURRENT_BRANCH"
echo "   Local staging:  $LOCAL_STAGING_SHA"
echo "   Remote staging: $REMOTE_STAGING_SHA"
echo "   HEAD commit:    $HEAD_SHA"
echo ""

# Check if local and remote are in sync
if [ "$LOCAL_STAGING_SHA" = "$REMOTE_STAGING_SHA" ]; then
    echo -e "   ${GREEN}✅ Local and remote staging branches IN SYNC${NC}"
else
    echo -e "   ${RED}❌ Local and remote staging branches OUT OF SYNC${NC}"
    echo "      Push required: git push origin staging"
fi
echo ""

# Show recent staging commits
echo "📝 Recent Staging Commits:"
echo "----------------------------"
git log origin/staging --oneline -5
echo ""

# Check for diagnostic code
echo "🔬 Diagnostic Code Presence:"
echo "----------------------------"
DIAGNOSTIC_COUNT=$(git show HEAD:app/core/database.py | grep -c "\[SCHEME-FIX\]" || echo "0")
if [ "$DIAGNOSTIC_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✅ Diagnostic logging present in code${NC}"
    echo "   Found $DIAGNOSTIC_COUNT diagnostic markers"
else
    echo -e "   ${RED}❌ Diagnostic logging NOT FOUND in code${NC}"
fi
echo ""

# Show diagnostic code snippet
echo "📄 Diagnostic Code Snippet:"
echo "----------------------------"
git show HEAD:app/core/database.py | grep -A 2 -B 2 "\[SCHEME-FIX\]" | head -10
echo ""

# Check render.yaml configuration
echo "⚙️  render.yaml Configuration:"
echo "----------------------------"
RENDER_BRANCH=$(grep -A 5 "name: marketedge-platform-staging" render.yaml | grep "branch:" | awk '{print $2}')
RENDER_START_CMD=$(grep -A 5 "name: marketedge-platform-staging" render.yaml | grep "startCommand:" | awk '{print $2}')

echo "   Configured branch: $RENDER_BRANCH"
echo "   Start command:     $RENDER_START_CMD"
echo ""

if [ "$RENDER_BRANCH" = "staging" ]; then
    echo -e "   ${GREEN}✅ render.yaml configured for staging branch${NC}"
else
    echo -e "   ${RED}❌ render.yaml NOT configured for staging branch${NC}"
fi
echo ""

# Final assessment
echo "=========================================="
echo "🎯 ASSESSMENT"
echo "=========================================="
echo ""

if [ "$LOCAL_STAGING_SHA" = "$REMOTE_STAGING_SHA" ] && [ "$DIAGNOSTIC_COUNT" -gt 0 ] && [ "$RENDER_BRANCH" = "staging" ]; then
    echo -e "${GREEN}✅ CODE IS READY FOR DEPLOYMENT${NC}"
    echo ""
    echo "Expected commit SHA in Render logs:"
    echo "   $REMOTE_STAGING_SHA"
    echo ""
    echo "Expected diagnostic log lines:"
    echo "   [DATABASE-INIT] Starting database initialization, DATABASE_URL scheme: postgres"
    echo "   [SCHEME-FIX] original=postgres async=postgresql+asyncpg"
    echo "   [SCHEME-FIX-DETAILS] Transformation applied: postgres -> postgresql+asyncpg"
    echo ""
    echo -e "${YELLOW}🚨 IF THESE LOGS DON'T APPEAR IN RENDER:${NC}"
    echo "   → Render Dashboard branch setting is likely NOT 'staging'"
    echo "   → Service may have been created manually (not from blueprint)"
    echo "   → render.yaml settings are being IGNORED"
    echo ""
    echo "   FIX: Go to Render Dashboard → Settings → Change branch to 'staging'"
else
    echo -e "${RED}❌ DEPLOYMENT NOT READY${NC}"
    echo ""
    if [ "$LOCAL_STAGING_SHA" != "$REMOTE_STAGING_SHA" ]; then
        echo "   • Local and remote staging branches out of sync"
        echo "     Run: git push origin staging"
    fi
    if [ "$DIAGNOSTIC_COUNT" -eq 0 ]; then
        echo "   • Diagnostic code not found in repository"
        echo "     Verify commit: git show HEAD:app/core/database.py"
    fi
    if [ "$RENDER_BRANCH" != "staging" ]; then
        echo "   • render.yaml not configured for staging branch"
        echo "     Edit render.yaml to set branch: staging"
    fi
fi
echo ""

# Show how to monitor deployment
echo "=========================================="
echo "📊 MONITOR DEPLOYMENT"
echo "=========================================="
echo ""
echo "To monitor staging deployment logs:"
echo "   ./scripts/monitor-staging-deployment.sh"
echo ""
echo "To check Render service logs manually:"
echo "   1. Go to: https://dashboard.render.com"
echo "   2. Find: marketedge-platform-staging"
echo "   3. Click: 'Logs' tab"
echo "   4. Look for: [DATABASE-INIT] and [SCHEME-FIX] messages"
echo ""
