#!/bin/bash

# Railway Configuration Audit Script
# Epic 1 - MIG-001: Railway Platform Configuration Audit
# Comprehensive audit of current Railway deployment configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Output file for audit report
AUDIT_DATE=$(date +"%Y%m%d_%H%M%S")
AUDIT_REPORT="/Users/matt/Sites/MarketEdge/docs/2025_08_15/migration/railway_config_audit_${AUDIT_DATE}.json"

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

log_audit() {
    echo -e "${CYAN}[AUDIT]${NC} $1"
}

echo "🔍 Railway Configuration Audit - Epic 1 MIG-001"
echo "==============================================="
echo "Audit Date: $(date)"
echo "Audit Report: $AUDIT_REPORT"
echo ""

# Initialize audit report
cat > "$AUDIT_REPORT" << EOF
{
  "audit_metadata": {
    "epic": "MIG-001",
    "audit_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "audit_version": "1.0.0",
    "auditor": "railway-config-audit.sh",
    "platform": "Railway"
  },
  "railway_configuration": {},
  "environment_variables": {},
  "services": {},
  "deployment_config": {},
  "security_assessment": {},
  "migration_blockers": [],
  "recommendations": []
}
EOF

# Function to update JSON report
update_audit_report() {
    local section="$1"
    local key="$2"
    local value="$3"
    
    # Use jq to update the JSON file
    if command -v jq &> /dev/null; then
        jq ".$section.$key = $value" "$AUDIT_REPORT" > "${AUDIT_REPORT}.tmp" && mv "${AUDIT_REPORT}.tmp" "$AUDIT_REPORT"
    else
        log_warning "jq not available - audit report will be incomplete"
    fi
}

# Phase 1: Railway CLI Authentication Status
log_audit "Phase 1: Railway CLI Authentication & Project Status"

RAILWAY_AUTH_STATUS="false"
RAILWAY_USER=""
RAILWAY_PROJECT=""

if command -v railway &> /dev/null; then
    log_success "Railway CLI is installed"
    RAILWAY_VERSION=$(railway --version 2>/dev/null || echo "unknown")
    log_info "Railway CLI Version: $RAILWAY_VERSION"
    
    if railway whoami >/dev/null 2>&1; then
        RAILWAY_USER=$(railway whoami 2>/dev/null || echo "unknown")
        RAILWAY_AUTH_STATUS="true"
        log_success "Railway CLI authenticated as: $RAILWAY_USER"
        
        # Try to get project info
        RAILWAY_PROJECT=$(railway status 2>/dev/null | head -1 || echo "unknown")
        log_info "Current project: $RAILWAY_PROJECT"
    else
        log_warning "Railway CLI not authenticated"
    fi
else
    log_error "Railway CLI not installed"
fi

update_audit_report "railway_configuration" "cli_installed" "true"
update_audit_report "railway_configuration" "cli_version" "\"$RAILWAY_VERSION\""
update_audit_report "railway_configuration" "authenticated" "$RAILWAY_AUTH_STATUS"
update_audit_report "railway_configuration" "user" "\"$RAILWAY_USER\""
update_audit_report "railway_configuration" "project" "\"$RAILWAY_PROJECT\""

# Phase 2: Railway Configuration Files Audit
log_audit "Phase 2: Railway Configuration Files Analysis"

# Check railway.toml
if [ -f "railway.toml" ]; then
    log_success "railway.toml found"
    
    # Parse railway.toml configuration
    BUILDER=$(grep "^builder" railway.toml | cut -d'"' -f2 2>/dev/null || echo "none")
    DOCKERFILE_PATH=$(grep "^dockerfilePath" railway.toml | cut -d'"' -f2 2>/dev/null || echo "none")
    HEALTH_PATH=$(grep "^healthcheckPath" railway.toml | cut -d'"' -f2 2>/dev/null || echo "none")
    HEALTH_TIMEOUT=$(grep "^healthcheckTimeout" railway.toml | cut -d'=' -f2 | tr -d ' ' 2>/dev/null || echo "none")
    START_COMMAND=$(grep "^startCommand" railway.toml | cut -d'"' -f2 2>/dev/null || echo "none")
    
    log_info "Builder: $BUILDER"
    log_info "Dockerfile Path: $DOCKERFILE_PATH"
    log_info "Health Check Path: $HEALTH_PATH"
    log_info "Health Check Timeout: $HEALTH_TIMEOUT"
    log_info "Start Command: $START_COMMAND"
    
    update_audit_report "deployment_config" "builder" "\"$BUILDER\""
    update_audit_report "deployment_config" "dockerfile_path" "\"$DOCKERFILE_PATH\""
    update_audit_report "deployment_config" "health_check_path" "\"$HEALTH_PATH\""
    update_audit_report "deployment_config" "health_check_timeout" "$HEALTH_TIMEOUT"
    update_audit_report "deployment_config" "start_command" "\"$START_COMMAND\""
else
    log_warning "railway.toml not found"
    update_audit_report "deployment_config" "railway_toml_exists" "false"
fi

# Check Dockerfile
if [ -f "Dockerfile" ]; then
    log_success "Dockerfile found"
    
    # Analyze Dockerfile configuration
    BASE_IMAGE=$(head -20 Dockerfile | grep "^FROM" | head -1 | cut -d' ' -f2 2>/dev/null || echo "unknown")
    EXPOSED_PORTS=$(grep "^EXPOSE" Dockerfile | cut -d' ' -f2- 2>/dev/null || echo "none")
    HEALTH_CHECK=$(grep -c "^HEALTHCHECK" Dockerfile 2>/dev/null || echo "0")
    USER_CONFIG=$(grep "^USER" Dockerfile | tail -1 | cut -d' ' -f2 2>/dev/null || echo "root")
    
    log_info "Base Image: $BASE_IMAGE"
    log_info "Exposed Ports: $EXPOSED_PORTS"
    log_info "Health Check Configured: $HEALTH_CHECK"
    log_info "Container User: $USER_CONFIG"
    
    update_audit_report "deployment_config" "base_image" "\"$BASE_IMAGE\""
    update_audit_report "deployment_config" "exposed_ports" "\"$EXPOSED_PORTS\""
    update_audit_report "deployment_config" "health_check_configured" "$HEALTH_CHECK"
    update_audit_report "deployment_config" "container_user" "\"$USER_CONFIG\""
else
    log_error "Dockerfile not found"
    update_audit_report "deployment_config" "dockerfile_exists" "false"
fi

# Phase 3: Environment Variables Assessment
log_audit "Phase 3: Environment Variables Configuration Analysis"

ENV_VARS_COUNT=0
CRITICAL_ENV_MISSING=()
SECURITY_ENV_ISSUES=()

if [ "$RAILWAY_AUTH_STATUS" = "true" ]; then
    log_info "Retrieving Railway environment variables..."
    
    # Check for critical environment variables
    CRITICAL_VARS=("DATABASE_URL" "REDIS_URL" "JWT_SECRET_KEY" "AUTH0_DOMAIN" "AUTH0_CLIENT_ID" "AUTH0_CLIENT_SECRET")
    
    for var in "${CRITICAL_VARS[@]}"; do
        if railway variables 2>/dev/null | grep -q "^$var"; then
            VALUE=$(railway variables 2>/dev/null | grep "^$var" | awk '{print $3}' | head -1)
            log_success "$var is configured"
            
            # Security check for hardcoded values
            if [[ "$VALUE" != *"\${"* ]] && [[ "$var" == *"URL" ]]; then
                log_warning "$var appears to be hardcoded (should be service reference)"
                SECURITY_ENV_ISSUES+=("$var: hardcoded_value")
            fi
            
            ENV_VARS_COUNT=$((ENV_VARS_COUNT + 1))
        else
            log_error "$var is missing"
            CRITICAL_ENV_MISSING+=("$var")
        fi
    done
    
    # Count total environment variables
    TOTAL_ENV_VARS=$(railway variables 2>/dev/null | wc -l || echo "0")
    log_info "Total environment variables configured: $TOTAL_ENV_VARS"
    
    update_audit_report "environment_variables" "total_count" "$TOTAL_ENV_VARS"
    update_audit_report "environment_variables" "critical_vars_configured" "$ENV_VARS_COUNT"
    if [ ${#CRITICAL_ENV_MISSING[@]} -gt 0 ]; then
        MISSING_VARS_JSON=$(printf '"%s",' "${CRITICAL_ENV_MISSING[@]}" | sed 's/,$//')
        update_audit_report "environment_variables" "critical_vars_missing" "[$MISSING_VARS_JSON]"
    else
        update_audit_report "environment_variables" "critical_vars_missing" "[]"
    fi
else
    log_warning "Cannot audit environment variables - Railway CLI not authenticated"
    update_audit_report "environment_variables" "audit_status" "\"skipped_auth_required\""
fi

# Phase 4: Services Configuration Audit
log_audit "Phase 4: Railway Services Assessment"

SERVICES_COUNT=0
SERVICES_LIST=()

if [ "$RAILWAY_AUTH_STATUS" = "true" ]; then
    if railway services 2>/dev/null >/dev/null; then
        SERVICES_OUTPUT=$(railway services 2>/dev/null || echo "")
        if [ -n "$SERVICES_OUTPUT" ]; then
            SERVICES_COUNT=$(echo "$SERVICES_OUTPUT" | wc -l)
            log_info "Total services configured: $SERVICES_COUNT"
            
            # Check for required services
            if echo "$SERVICES_OUTPUT" | grep -q -i "postgres"; then
                log_success "PostgreSQL service found"
                SERVICES_LIST+=("postgresql")
            else
                log_error "PostgreSQL service missing"
            fi
            
            if echo "$SERVICES_OUTPUT" | grep -q -i "redis"; then
                log_success "Redis service found"
                SERVICES_LIST+=("redis")
            else
                log_error "Redis service missing"
            fi
        else
            log_warning "No services found or services command failed"
        fi
    else
        log_warning "Cannot retrieve services list"
    fi
    
    update_audit_report "services" "total_count" "$SERVICES_COUNT"
    if [ ${#SERVICES_LIST[@]} -gt 0 ]; then
        SERVICES_JSON=$(printf '"%s",' "${SERVICES_LIST[@]}" | sed 's/,$//')
        update_audit_report "services" "configured_services" "[$SERVICES_JSON]"
    else
        update_audit_report "services" "configured_services" "[]"
    fi
else
    log_warning "Cannot audit services - Railway CLI not authenticated"
    update_audit_report "services" "audit_status" "\"skipped_auth_required\""
fi

# Phase 5: Multi-Service Architecture Assessment
log_audit "Phase 5: Multi-Service Architecture Configuration"

MULTI_SERVICE_READY="false"
SUPERVISORD_CONFIG="false"
CADDY_CONFIG="false"

# Check supervisord configuration
if [ -f "supervisord.conf" ]; then
    log_success "supervisord.conf found"
    SUPERVISORD_CONFIG="true"
    
    # Check for required programs
    if grep -q "program:fastapi" supervisord.conf; then
        log_success "FastAPI service configured in supervisord"
    else
        log_warning "FastAPI service not found in supervisord"
    fi
    
    if grep -q "program:caddy" supervisord.conf; then
        log_success "Caddy service configured in supervisord"
        CADDY_CONFIG="true"
    else
        log_warning "Caddy service not found in supervisord"
    fi
    
    # Security assessment of supervisord config
    if grep -q "user=appuser" supervisord.conf; then
        log_success "Services run as non-root user (appuser)"
    else
        log_warning "Services may be running as root - security concern"
        SECURITY_ENV_ISSUES+=("supervisord: services_run_as_root")
    fi
else
    log_error "supervisord.conf not found"
fi

# Check Caddyfile configuration
if [ -f "Caddyfile" ]; then
    log_success "Caddyfile found"
    
    # Check for CORS configuration
    if grep -q "Access-Control-Allow-Origin" Caddyfile; then
        log_success "CORS configuration found in Caddyfile"
    else
        log_warning "CORS configuration not found in Caddyfile"
    fi
    
    # Check for proxy configuration
    if grep -q "reverse_proxy" Caddyfile; then
        log_success "Reverse proxy configuration found"
    else
        log_warning "Reverse proxy configuration not found"
    fi
    
    # Check for security headers
    if grep -q "auto_https off" Caddyfile; then
        log_info "HTTPS auto-redirect disabled (appropriate for Railway)"
    fi
else
    log_error "Caddyfile not found"
    CADDY_CONFIG="false"
fi

if [ "$SUPERVISORD_CONFIG" = "true" ] && [ "$CADDY_CONFIG" = "true" ]; then
    MULTI_SERVICE_READY="true"
    log_success "Multi-service architecture configuration complete"
else
    log_warning "Multi-service architecture configuration incomplete"
fi

update_audit_report "deployment_config" "multi_service_ready" "$MULTI_SERVICE_READY"
update_audit_report "deployment_config" "supervisord_configured" "$SUPERVISORD_CONFIG"
update_audit_report "deployment_config" "caddy_configured" "$CADDY_CONFIG"

# Phase 6: Security Assessment
log_audit "Phase 6: Security Configuration Assessment"

SECURITY_SCORE=0
SECURITY_ISSUES_COUNT=${#SECURITY_ENV_ISSUES[@]}

# Check for security best practices
if [ -f "Dockerfile" ]; then
    if grep -q "groupadd.*appuser" Dockerfile; then
        log_success "Non-root user creation found in Dockerfile"
        SECURITY_SCORE=$((SECURITY_SCORE + 1))
    fi
    
    if grep -q "chmod.*755" Dockerfile; then
        log_success "Proper file permissions set in Dockerfile"
        SECURITY_SCORE=$((SECURITY_SCORE + 1))
    fi
    
    if grep -q "apt-get clean" Dockerfile; then
        log_success "Package cache cleanup found in Dockerfile"
        SECURITY_SCORE=$((SECURITY_SCORE + 1))
    fi
fi

if [ -f "supervisord.conf" ]; then
    if grep -q "user=appuser" supervisord.conf; then
        log_success "Services run as non-root user"
        SECURITY_SCORE=$((SECURITY_SCORE + 1))
    fi
fi

SECURITY_PERCENTAGE=$((SECURITY_SCORE * 25))
log_info "Security score: $SECURITY_SCORE/4 ($SECURITY_PERCENTAGE%)"

update_audit_report "security_assessment" "score" "$SECURITY_SCORE"
update_audit_report "security_assessment" "percentage" "$SECURITY_PERCENTAGE"
update_audit_report "security_assessment" "issues_count" "$SECURITY_ISSUES_COUNT"
if [ ${#SECURITY_ENV_ISSUES[@]} -gt 0 ]; then
    SECURITY_ISSUES_JSON=$(printf '"%s",' "${SECURITY_ENV_ISSUES[@]}" | sed 's/,$//')
    update_audit_report "security_assessment" "issues" "[$SECURITY_ISSUES_JSON]"
else
    update_audit_report "security_assessment" "issues" "[]"
fi

# Phase 7: Migration Blockers Assessment
log_audit "Phase 7: Migration Blockers Identification"

MIGRATION_BLOCKERS=()

# Check for potential blockers
if [ "$RAILWAY_AUTH_STATUS" = "false" ]; then
    MIGRATION_BLOCKERS+=("Railway CLI not authenticated - cannot export configuration")
fi

if [ ${#CRITICAL_ENV_MISSING[@]} -gt 0 ]; then
    MIGRATION_BLOCKERS+=("Critical environment variables missing: ${CRITICAL_ENV_MISSING[*]}")
fi

if [ ${#SERVICES_LIST[@]} -lt 2 ]; then
    MIGRATION_BLOCKERS+=("Required services not configured (PostgreSQL, Redis)")
fi

if [ "$MULTI_SERVICE_READY" = "false" ]; then
    MIGRATION_BLOCKERS+=("Multi-service architecture configuration incomplete")
fi

if [ ${#SECURITY_ENV_ISSUES[@]} -gt 0 ]; then
    MIGRATION_BLOCKERS+=("Security configuration issues need resolution")
fi

BLOCKERS_COUNT=${#MIGRATION_BLOCKERS[@]}
log_info "Migration blockers identified: $BLOCKERS_COUNT"

for blocker in "${MIGRATION_BLOCKERS[@]}"; do
    log_warning "BLOCKER: $blocker"
done

update_audit_report "migration_blockers" "count" "$BLOCKERS_COUNT"
if [ ${#MIGRATION_BLOCKERS[@]} -gt 0 ]; then
    BLOCKERS_JSON=$(printf '"%s",' "${MIGRATION_BLOCKERS[@]}" | sed 's/,$//')
    update_audit_report "migration_blockers" "issues" "[$BLOCKERS_JSON]"
else
    update_audit_report "migration_blockers" "issues" "[]"
fi

# Phase 8: Recommendations Generation
log_audit "Phase 8: Migration Recommendations"

RECOMMENDATIONS=()

if [ "$RAILWAY_AUTH_STATUS" = "false" ]; then
    RECOMMENDATIONS+=("Authenticate Railway CLI: railway login")
fi

if [ ${#CRITICAL_ENV_MISSING[@]} -gt 0 ]; then
    RECOMMENDATIONS+=("Configure missing environment variables before migration")
fi

if [ ${#SERVICES_LIST[@]} -lt 2 ]; then
    RECOMMENDATIONS+=("Add missing services: railway add --template postgres; railway add --template redis")
fi

if [ "$SECURITY_PERCENTAGE" -lt 75 ]; then
    RECOMMENDATIONS+=("Address security configuration issues before migration")
fi

RECOMMENDATIONS+=("Export Railway configuration: railway variables > railway-env-backup.txt")
RECOMMENDATIONS+=("Create database backup before migration")
RECOMMENDATIONS+=("Test multi-service architecture locally before migration")
RECOMMENDATIONS+=("Validate Render platform compatibility with current configuration")

update_audit_report "recommendations" "count" "${#RECOMMENDATIONS[@]}"
if [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    RECOMMENDATIONS_JSON=$(printf '"%s",' "${RECOMMENDATIONS[@]}" | sed 's/,$//')
    update_audit_report "recommendations" "items" "[$RECOMMENDATIONS_JSON]"
else
    update_audit_report "recommendations" "items" "[]"
fi

# Final Report Summary
echo ""
echo "=============================================="
echo "🎯 RAILWAY CONFIGURATION AUDIT SUMMARY"
echo "=============================================="
echo ""
echo "📊 Configuration Status:"
echo "Railway CLI:         $([ "$RAILWAY_AUTH_STATUS" = "true" ] && echo '✅ AUTHENTICATED' || echo '❌ NOT AUTHENTICATED')"
echo "Configuration Files: $([ -f "railway.toml" ] && echo '✅ PRESENT' || echo '❌ MISSING')"
echo "Multi-Service Setup: $([ "$MULTI_SERVICE_READY" = "true" ] && echo '✅ CONFIGURED' || echo '❌ INCOMPLETE')"
echo "Environment Variables: $ENV_VARS_COUNT/${#CRITICAL_VARS[@]} critical vars configured"
echo "Services:            $SERVICES_COUNT services found"
echo "Security Score:      $SECURITY_SCORE/4 ($SECURITY_PERCENTAGE%)"
echo ""
echo "🚨 Migration Readiness:"
echo "Blockers:            $BLOCKERS_COUNT issues identified"
echo "Recommendations:     ${#RECOMMENDATIONS[@]} actions required"
echo ""

if [ $BLOCKERS_COUNT -eq 0 ]; then
    echo "✅ MIGRATION READY: No critical blockers identified"
elif [ $BLOCKERS_COUNT -le 2 ]; then
    echo "⚠️ MIGRATION CAUTION: Minor blockers need resolution"
else
    echo "❌ MIGRATION BLOCKED: Multiple critical issues require attention"
fi

echo ""
echo "📄 Full audit report saved to: $AUDIT_REPORT"
echo ""
echo "🔄 Next Steps:"
echo "1. Review audit report for detailed findings"
echo "2. Address identified migration blockers"
echo "3. Proceed to Render platform capability validation (MIG-002)"
echo ""

# Set exit code based on blockers
if [ $BLOCKERS_COUNT -eq 0 ]; then
    exit 0
elif [ $BLOCKERS_COUNT -le 2 ]; then
    exit 1
else
    exit 2
fi