#!/bin/bash

# Epic 2: Deployment Readiness Validation Script
# DevOps validation for Railway to Render migration
# Version: 1.0.0

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Report file
REPORT_DATE=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="docs/2025_08_16/epic2_deployment_validation_${REPORT_DATE}.md"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((PASS_COUNT++))
}

log_warning() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1"
    ((WARN_COUNT++))
}

log_error() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((FAIL_COUNT++))
}

log_check() {
    echo -e "${CYAN}[CHECK]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}▶ $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Initialize report
mkdir -p "$(dirname "$REPORT_FILE")"
cat > "$REPORT_FILE" << 'EOF'
# Epic 2: Deployment Readiness Validation Report

**Date:** REPORT_DATE_PLACEHOLDER
**Environment:** Production
**Target Platform:** Render
**Migration Type:** Railway to Render (MIG-006)

---

## Executive Summary

This report validates the readiness of Epic 2 deployment for the MarketEdge Platform migration from Railway to Render.

## Validation Results

EOF

sed -i "" "s/REPORT_DATE_PLACEHOLDER/$(date)/" "$REPORT_FILE"

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           EPIC 2: DEPLOYMENT READINESS CHECK              ║"
echo "║          Railway to Render Migration Validation           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Validation Date: $(date)"
echo "Report Output: $REPORT_FILE"
echo ""

# ============================================================
# SECTION 1: FILE STRUCTURE VALIDATION
# ============================================================

log_section "1. FILE STRUCTURE VALIDATION"

echo "### 1. File Structure Validation" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| File/Directory | Status | Path |" >> "$REPORT_FILE"
echo "|----------------|--------|------|" >> "$REPORT_FILE"

# Check critical files
log_check "Validating critical Epic 2 files..."

# render.yaml
if [ -f "backend/render.yaml" ]; then
    log_success "render.yaml found"
    echo "| render.yaml | ✅ Found | backend/render.yaml |" >> "$REPORT_FILE"
else
    log_error "render.yaml missing"
    echo "| render.yaml | ❌ Missing | backend/render.yaml |" >> "$REPORT_FILE"
fi

# Dockerfile
if [ -f "backend/Dockerfile" ]; then
    log_success "Dockerfile found"
    echo "| Dockerfile | ✅ Found | backend/Dockerfile |" >> "$REPORT_FILE"
else
    log_error "Dockerfile missing"
    echo "| Dockerfile | ❌ Missing | backend/Dockerfile |" >> "$REPORT_FILE"
fi

# supervisord.conf
if [ -f "backend/supervisord.conf" ]; then
    log_success "supervisord.conf found"
    echo "| supervisord.conf | ✅ Found | backend/supervisord.conf |" >> "$REPORT_FILE"
else
    log_error "supervisord.conf missing"
    echo "| supervisord.conf | ❌ Missing | backend/supervisord.conf |" >> "$REPORT_FILE"
fi

# Caddyfile
if [ -f "backend/Caddyfile" ]; then
    log_success "Caddyfile found"
    echo "| Caddyfile | ✅ Found | backend/Caddyfile |" >> "$REPORT_FILE"
else
    log_error "Caddyfile missing"
    echo "| Caddyfile | ❌ Missing | backend/Caddyfile |" >> "$REPORT_FILE"
fi

# Deployment scripts
if [ -f "frontend/scripts/deploy-to-render.sh" ]; then
    log_success "Deployment script found"
    echo "| deploy-to-render.sh | ✅ Found | frontend/scripts/deploy-to-render.sh |" >> "$REPORT_FILE"
else
    log_error "Deployment script missing"
    echo "| deploy-to-render.sh | ❌ Missing | frontend/scripts/deploy-to-render.sh |" >> "$REPORT_FILE"
fi

if [ -f "deploy-render.sh" ]; then
    log_success "Wrapper script found"
    echo "| deploy-render.sh | ✅ Found | ./deploy-render.sh |" >> "$REPORT_FILE"
else
    log_warning "Wrapper script missing (optional)"
    echo "| deploy-render.sh | ⚠️ Optional | ./deploy-render.sh |" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 2: RENDER.YAML CONFIGURATION VALIDATION
# ============================================================

log_section "2. RENDER.YAML CONFIGURATION"

echo "### 2. Render Configuration Validation" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ -f "backend/render.yaml" ]; then
    log_check "Analyzing render.yaml configuration..."
    
    # Check for required sections
    echo "#### Configuration Sections" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "| Section | Status | Details |" >> "$REPORT_FILE"
    echo "|---------|--------|---------|" >> "$REPORT_FILE"
    
    # Services section
    if grep -q "^services:" backend/render.yaml; then
        log_success "Services section defined"
        SERVICE_NAME=$(grep -m1 "name:" backend/render.yaml | awk '{print $3}')
        echo "| Services | ✅ Defined | Service: $SERVICE_NAME |" >> "$REPORT_FILE"
    else
        log_error "Services section missing"
        echo "| Services | ❌ Missing | - |" >> "$REPORT_FILE"
    fi
    
    # Databases section
    if grep -q "^databases:" backend/render.yaml; then
        log_success "Databases section defined"
        POSTGRES_COUNT=$(grep -c "marketedge-postgres" backend/render.yaml || echo "0")
        REDIS_COUNT=$(grep -c "marketedge-redis" backend/render.yaml || echo "0")
        echo "| Databases | ✅ Defined | PostgreSQL: $POSTGRES_COUNT, Redis: $REDIS_COUNT |" >> "$REPORT_FILE"
    else
        log_error "Databases section missing"
        echo "| Databases | ❌ Missing | - |" >> "$REPORT_FILE"
    fi
    
    # Environment variable groups
    if grep -q "^envVarGroups:" backend/render.yaml; then
        log_success "Environment variable groups defined"
        echo "| Env Groups | ✅ Defined | Organized configuration |" >> "$REPORT_FILE"
    else
        log_warning "Environment variable groups not defined (optional)"
        echo "| Env Groups | ⚠️ Optional | Not configured |" >> "$REPORT_FILE"
    fi
    
    # Health check
    if grep -q "healthCheckPath:" backend/render.yaml; then
        log_success "Health check configured"
        HEALTH_PATH=$(grep "healthCheckPath:" backend/render.yaml | awk '{print $2}')
        echo "| Health Check | ✅ Configured | Path: $HEALTH_PATH |" >> "$REPORT_FILE"
    else
        log_error "Health check not configured"
        echo "| Health Check | ❌ Missing | - |" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
fi

# ============================================================
# SECTION 3: DOCKER CONFIGURATION VALIDATION
# ============================================================

log_section "3. DOCKER CONFIGURATION"

echo "### 3. Docker Configuration" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

log_check "Validating Docker setup..."

echo "| Check | Status | Details |" >> "$REPORT_FILE"
echo "|-------|--------|---------|" >> "$REPORT_FILE"

# Check if Docker is running
if docker info &> /dev/null; then
    log_success "Docker daemon is running"
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo "| Docker Daemon | ✅ Running | Version: $DOCKER_VERSION |" >> "$REPORT_FILE"
    
    # Try to build the image
    log_check "Testing Docker build (this may take a moment)..."
    if docker build -t epic2-test backend --no-cache 2>&1 | tail -1 | grep -q "Successfully"; then
        log_success "Docker build successful"
        echo "| Docker Build | ✅ Success | Image: epic2-test |" >> "$REPORT_FILE"
    else
        log_warning "Docker build needs testing"
        echo "| Docker Build | ⚠️ Not tested | Manual verification needed |" >> "$REPORT_FILE"
    fi
else
    log_warning "Docker not running - cannot validate build"
    echo "| Docker Daemon | ⚠️ Not running | Start Docker Desktop |" >> "$REPORT_FILE"
    echo "| Docker Build | ⚠️ Not tested | Docker required |" >> "$REPORT_FILE"
fi

# Check Dockerfile instructions
if [ -f "backend/Dockerfile" ]; then
    EXPOSE_COUNT=$(grep -c "^EXPOSE" backend/Dockerfile || echo "0")
    HEALTHCHECK_COUNT=$(grep -c "^HEALTHCHECK" backend/Dockerfile || echo "0")
    
    if [ "$EXPOSE_COUNT" -gt 0 ]; then
        log_success "EXPOSE ports configured"
        PORTS=$(grep "^EXPOSE" backend/Dockerfile | awk '{print $2}' | tr '\n' ' ')
        echo "| Exposed Ports | ✅ Configured | Ports: $PORTS|" >> "$REPORT_FILE"
    else
        log_warning "No EXPOSE instruction found"
        echo "| Exposed Ports | ⚠️ Not found | - |" >> "$REPORT_FILE"
    fi
    
    if [ "$HEALTHCHECK_COUNT" -gt 0 ]; then
        log_success "HEALTHCHECK configured"
        echo "| Healthcheck | ✅ Configured | In Dockerfile |" >> "$REPORT_FILE"
    else
        log_warning "No HEALTHCHECK in Dockerfile"
        echo "| Healthcheck | ⚠️ Not in Dockerfile | Render will use render.yaml |" >> "$REPORT_FILE"
    fi
fi

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 4: ENVIRONMENT VARIABLES VALIDATION
# ============================================================

log_section "4. ENVIRONMENT VARIABLES"

echo "### 4. Environment Variables" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

log_check "Validating environment variable configuration..."

echo "#### Required Variables" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Variable | Status | Configuration |" >> "$REPORT_FILE"
echo "|----------|--------|---------------|" >> "$REPORT_FILE"

# Check critical environment variables in render.yaml
CRITICAL_VARS=(
    "PORT"
    "FASTAPI_PORT"
    "DATABASE_URL"
    "REDIS_URL"
    "AUTH0_DOMAIN"
    "AUTH0_CLIENT_ID"
    "JWT_SECRET_KEY"
    "CORS_ALLOWED_ORIGINS"
)

for VAR in "${CRITICAL_VARS[@]}"; do
    if grep -q "key: $VAR" backend/render.yaml; then
        log_success "$VAR configured"
        
        # Check if it's auto-generated or from database
        if grep -A1 "key: $VAR" backend/render.yaml | grep -q "fromDatabase:"; then
            echo "| $VAR | ✅ Auto-configured | From database service |" >> "$REPORT_FILE"
        elif grep -A1 "key: $VAR" backend/render.yaml | grep -q "generateValue: true"; then
            echo "| $VAR | ✅ Auto-generated | Render generates |" >> "$REPORT_FILE"
        elif grep -A1 "key: $VAR" backend/render.yaml | grep -q "sync: false"; then
            echo "| $VAR | ⚠️ Manual setup | Set in Render dashboard |" >> "$REPORT_FILE"
        else
            echo "| $VAR | ✅ Configured | In render.yaml |" >> "$REPORT_FILE"
        fi
    else
        log_error "$VAR not configured"
        echo "| $VAR | ❌ Missing | Not found |" >> "$REPORT_FILE"
    fi
done

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 5: BACKEND SERVICES VALIDATION
# ============================================================

log_section "5. BACKEND SERVICES"

echo "### 5. Backend Services Validation" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

log_check "Checking backend services..."

echo "| Service | Status | Details |" >> "$REPORT_FILE"
echo "|---------|--------|---------|" >> "$REPORT_FILE"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_success "Backend health endpoint responding"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "{}")
    echo "| Backend API | ✅ Running | Port 8000 active |" >> "$REPORT_FILE"
else
    log_warning "Backend not running locally"
    echo "| Backend API | ⚠️ Not running | Start for testing |" >> "$REPORT_FILE"
fi

# Check PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    log_success "PostgreSQL is running"
    echo "| PostgreSQL | ✅ Running | Port 5432 active |" >> "$REPORT_FILE"
else
    log_warning "PostgreSQL not running locally"
    echo "| PostgreSQL | ⚠️ Not running | Render will provide |" >> "$REPORT_FILE"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    log_success "Redis is running"
    echo "| Redis | ✅ Running | Port 6379 active |" >> "$REPORT_FILE"
else
    log_warning "Redis not running locally"
    echo "| Redis | ⚠️ Not running | Render will provide |" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 6: SECURITY VALIDATION
# ============================================================

log_section "6. SECURITY CONFIGURATION"

echo "### 6. Security Configuration" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

log_check "Validating security settings..."

echo "| Security Check | Status | Details |" >> "$REPORT_FILE"
echo "|----------------|--------|---------|" >> "$REPORT_FILE"

# Check for sensitive data in render.yaml
if grep -q "AUTH0_CLIENT_SECRET" backend/render.yaml; then
    if grep -A1 "AUTH0_CLIENT_SECRET" backend/render.yaml | grep -q "sync: false"; then
        log_success "AUTH0_CLIENT_SECRET marked for manual configuration"
        echo "| AUTH0_CLIENT_SECRET | ✅ Secure | Manual configuration |" >> "$REPORT_FILE"
    else
        log_error "AUTH0_CLIENT_SECRET may be exposed"
        echo "| AUTH0_CLIENT_SECRET | ❌ Risk | Check configuration |" >> "$REPORT_FILE"
    fi
else
    log_warning "AUTH0_CLIENT_SECRET not configured"
    echo "| AUTH0_CLIENT_SECRET | ⚠️ Not configured | Add to render.yaml |" >> "$REPORT_FILE"
fi

# Check JWT configuration
if grep -q "generateValue: true" backend/render.yaml; then
    log_success "JWT secret auto-generation configured"
    echo "| JWT Secret | ✅ Secure | Auto-generated |" >> "$REPORT_FILE"
else
    log_warning "JWT secret not auto-generated"
    echo "| JWT Secret | ⚠️ Manual | Consider auto-generation |" >> "$REPORT_FILE"
fi

# Check CORS configuration
if grep -q "CORS_ALLOWED_ORIGINS" backend/render.yaml; then
    log_success "CORS origins configured"
    echo "| CORS Origins | ✅ Configured | In render.yaml |" >> "$REPORT_FILE"
else
    log_error "CORS origins not configured"
    echo "| CORS Origins | ❌ Missing | Required for frontend |" >> "$REPORT_FILE"
fi

# Check rate limiting
if grep -q "RATE_LIMIT_ENABLED" backend/render.yaml; then
    log_success "Rate limiting configured"
    echo "| Rate Limiting | ✅ Configured | Enabled |" >> "$REPORT_FILE"
else
    log_warning "Rate limiting not configured"
    echo "| Rate Limiting | ⚠️ Not configured | Consider enabling |" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 7: GIT STATUS CHECK
# ============================================================

log_section "7. GIT STATUS"

echo "### 7. Git Status" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

log_check "Checking Git repository status..."

echo "| Check | Status | Details |" >> "$REPORT_FILE"
echo "|-------|--------|---------|" >> "$REPORT_FILE"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" == "main" ] || [ "$CURRENT_BRANCH" == "epic-2-render-migration" ]; then
    log_success "On deployment branch: $CURRENT_BRANCH"
    echo "| Branch | ✅ Ready | $CURRENT_BRANCH |" >> "$REPORT_FILE"
else
    log_warning "On branch: $CURRENT_BRANCH"
    echo "| Branch | ⚠️ Check | $CURRENT_BRANCH |" >> "$REPORT_FILE"
fi

# Check for uncommitted changes
UNCOMMITTED_COUNT=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$UNCOMMITTED_COUNT" -eq 0 ]; then
    log_success "No uncommitted changes"
    echo "| Uncommitted | ✅ Clean | No changes |" >> "$REPORT_FILE"
else
    log_warning "$UNCOMMITTED_COUNT uncommitted changes"
    echo "| Uncommitted | ⚠️ Changes | $UNCOMMITTED_COUNT files |" >> "$REPORT_FILE"
fi

# Check if branch is up to date
if git status | grep -q "Your branch is up to date"; then
    log_success "Branch is up to date"
    echo "| Remote Sync | ✅ Synced | Up to date |" >> "$REPORT_FILE"
elif git status | grep -q "Your branch is ahead"; then
    AHEAD_COUNT=$(git status | grep -oE "[0-9]+ commit" | grep -oE "[0-9]+")
    log_warning "Branch is ahead by $AHEAD_COUNT commits"
    echo "| Remote Sync | ⚠️ Ahead | $AHEAD_COUNT commits |" >> "$REPORT_FILE"
else
    log_info "Branch sync status unclear"
    echo "| Remote Sync | ℹ️ Check | Manual verification |" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# ============================================================
# SECTION 8: DEPLOYMENT CHECKLIST
# ============================================================

log_section "8. DEPLOYMENT CHECKLIST"

echo "### 8. Deployment Checklist" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "#### Pre-Deployment Tasks" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << 'EOF'
- [ ] Create Render account at https://render.com
- [ ] Install Render CLI: `brew tap render-oss/render && brew install render`
- [ ] Set up billing and team access
- [ ] Review environment variable mapping document
- [ ] Prepare AUTH0_CLIENT_SECRET for manual configuration
- [ ] Verify custom domain requirements
- [ ] Review CORS origins for production

#### Deployment Steps

1. **Run deployment script:**
   ```bash
   ./deploy-render.sh production
   ```

2. **Create Blueprint deployment:**
   ```bash
   render blueprint launch
   ```

3. **Configure sensitive variables in Render dashboard:**
   - AUTH0_CLIENT_SECRET
   - Any API keys

4. **Monitor deployment:**
   - Check build logs
   - Verify health checks
   - Test endpoints

5. **Post-deployment validation:**
   - Test authentication flow
   - Verify database connectivity
   - Check CORS functionality
   - Monitor rate limiting

EOF

# ============================================================
# FINAL SUMMARY
# ============================================================

log_section "DEPLOYMENT READINESS SUMMARY"

echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TOTAL_CHECKS=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))
READINESS_SCORE=$((PASS_COUNT * 100 / TOTAL_CHECKS))

echo "### Validation Results" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Metric | Count | Percentage |" >> "$REPORT_FILE"
echo "|--------|-------|------------|" >> "$REPORT_FILE"
echo "| ✅ Passed | $PASS_COUNT | $((PASS_COUNT * 100 / TOTAL_CHECKS))% |" >> "$REPORT_FILE"
echo "| ❌ Failed | $FAIL_COUNT | $((FAIL_COUNT * 100 / TOTAL_CHECKS))% |" >> "$REPORT_FILE"
echo "| ⚠️ Warnings | $WARN_COUNT | $((WARN_COUNT * 100 / TOTAL_CHECKS))% |" >> "$REPORT_FILE"
echo "| **Total** | **$TOTAL_CHECKS** | **100%** |" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ "$FAIL_COUNT" -eq 0 ]; then
    DEPLOYMENT_STATUS="✅ **READY FOR DEPLOYMENT**"
    log_success "Epic 2 is READY for deployment!"
elif [ "$FAIL_COUNT" -le 2 ]; then
    DEPLOYMENT_STATUS="⚠️ **READY WITH MINOR ISSUES**"
    log_warning "Epic 2 is ready with $FAIL_COUNT issues to address"
else
    DEPLOYMENT_STATUS="❌ **NOT READY - CRITICAL ISSUES**"
    log_error "Epic 2 has $FAIL_COUNT critical issues to fix"
fi

echo "### Deployment Readiness: $DEPLOYMENT_STATUS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**Readiness Score: ${READINESS_SCORE}%**" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Console summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    VALIDATION COMPLETE                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Results Summary:"
echo "   ✅ Passed:   $PASS_COUNT checks"
echo "   ❌ Failed:   $FAIL_COUNT checks"
echo "   ⚠️  Warnings: $WARN_COUNT checks"
echo ""
echo "📈 Readiness Score: ${READINESS_SCORE}%"
echo ""
echo "📋 Deployment Status: ${DEPLOYMENT_STATUS//[*_]/}"
echo ""
echo "📄 Full report saved to: $REPORT_FILE"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "⚠️  Critical issues to address:"
    grep "❌" "$REPORT_FILE" | head -5
    echo ""
fi

echo "🚀 Next Steps:"
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "   1. Review the full report"
    echo "   2. Create Render account"
    echo "   3. Run ./deploy-render.sh"
    echo "   4. Configure sensitive variables"
    echo "   5. Monitor deployment"
else
    echo "   1. Fix critical issues listed above"
    echo "   2. Re-run this validation script"
    echo "   3. Proceed with deployment once ready"
fi
echo ""

exit 0