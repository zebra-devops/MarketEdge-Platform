#!/bin/bash

# Post-Merge Rate Limiting Verification Monitor
# Automated tracking of PR #55 deployment and verification

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
STAGING_URL="https://staging.marketedge.app"
PRODUCTION_URL="https://marketedge-platform.onrender.com"
PR_NUMBER="55"
LOG_FILE="rate_limit_verification_$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "Post-Merge Rate Limiting Verification" | tee -a "$LOG_FILE"
echo "PR #$PR_NUMBER - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Function to check CI status
check_ci_status() {
    echo -e "\n${YELLOW}Checking CI/CD Pipeline Status...${NC}" | tee -a "$LOG_FILE"

    # Check GitHub Actions status for the PR
    gh pr checks $PR_NUMBER 2>&1 | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ CI Pipeline Status Retrieved${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${RED}❌ Failed to get CI status${NC}" | tee -a "$LOG_FILE"
    fi
}

# Function to check staging deployment
check_staging_deployment() {
    echo -e "\n${YELLOW}Checking Staging Deployment...${NC}" | tee -a "$LOG_FILE"

    # Check health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/api/v1/health")

    if [ "$HTTP_CODE" == "200" ]; then
        echo -e "${GREEN}✅ Staging deployment is healthy (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${RED}❌ Staging health check failed (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    fi
}

# Function to run rate limiting verification
verify_rate_limiting() {
    echo -e "\n${YELLOW}Running Rate Limiting Verification...${NC}" | tee -a "$LOG_FILE"

    # Test auth0-url endpoint rate limiting
    echo "Testing /auth0-url endpoint (35 requests)..." | tee -a "$LOG_FILE"

    RESULTS_FILE="rate_limit_results_temp.txt"
    > "$RESULTS_FILE"

    for i in {1..35}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "$STAGING_URL/api/v1/auth/auth0-url?redirect_uri=$STAGING_URL/callback")
        echo "$HTTP_CODE" >> "$RESULTS_FILE"

        # Show progress
        if [ $((i % 5)) -eq 0 ]; then
            echo -n "."
        fi
    done
    echo "" # New line after dots

    # Analyze results
    echo -e "\n${YELLOW}Results Analysis:${NC}" | tee -a "$LOG_FILE"

    COUNT_200=$(grep -c "200" "$RESULTS_FILE" || echo "0")
    COUNT_429=$(grep -c "429" "$RESULTS_FILE" || echo "0")
    COUNT_503=$(grep -c "503" "$RESULTS_FILE" || echo "0")
    COUNT_OTHER=$(grep -vc "200\|429\|503" "$RESULTS_FILE" || echo "0")

    echo "HTTP 200 (Success): $COUNT_200" | tee -a "$LOG_FILE"
    echo "HTTP 429 (Rate Limited): $COUNT_429" | tee -a "$LOG_FILE"
    echo "HTTP 503 (Service Unavailable): $COUNT_503" | tee -a "$LOG_FILE"
    echo "Other responses: $COUNT_OTHER" | tee -a "$LOG_FILE"

    # Check expected behavior (30×200, 5×429)
    if [ "$COUNT_200" -eq 30 ] && [ "$COUNT_429" -eq 5 ] && [ "$COUNT_503" -eq 0 ]; then
        echo -e "${GREEN}✅ Rate limiting working as expected (30×200, 5×429)${NC}" | tee -a "$LOG_FILE"
        RATE_LIMIT_PASS=true
    elif [ "$COUNT_503" -gt 0 ]; then
        echo -e "${RED}❌ Redis appears to be down (503 errors detected)${NC}" | tee -a "$LOG_FILE"
        RATE_LIMIT_PASS=false
    else
        echo -e "${YELLOW}⚠️  Rate limiting behavior unexpected${NC}" | tee -a "$LOG_FILE"
        RATE_LIMIT_PASS=false
    fi

    rm -f "$RESULTS_FILE"
}

# Function to test authenticated endpoints
test_auth_endpoints() {
    echo -e "\n${YELLOW}Testing Authentication Endpoints...${NC}" | tee -a "$LOG_FILE"

    # Test login endpoint exists
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"test":"data"}' \
        "$STAGING_URL/api/v1/auth/login")

    if [ "$HTTP_CODE" == "401" ] || [ "$HTTP_CODE" == "422" ]; then
        echo -e "${GREEN}✅ Login endpoint responds correctly (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  Login endpoint unexpected response (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    fi

    # Test refresh endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        "$STAGING_URL/api/v1/auth/refresh")

    if [ "$HTTP_CODE" == "401" ] || [ "$HTTP_CODE" == "422" ]; then
        echo -e "${GREEN}✅ Refresh endpoint responds correctly (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  Refresh endpoint unexpected response (HTTP $HTTP_CODE)${NC}" | tee -a "$LOG_FILE"
    fi
}

# Function to generate verification report
generate_report() {
    echo -e "\n${YELLOW}========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}VERIFICATION SUMMARY${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}========================================${NC}" | tee -a "$LOG_FILE"

    echo -e "\n📊 Automated Checklist Status:" | tee -a "$LOG_FILE"
    echo "- [ ] CI Pipeline: Check manually via GitHub" | tee -a "$LOG_FILE"
    echo "- [$([ "$HTTP_CODE" == "200" ] && echo "x" || echo " ")] Staging Health: $([ "$HTTP_CODE" == "200" ] && echo "✅ Healthy" || echo "❌ Issues detected")" | tee -a "$LOG_FILE"
    echo "- [$([ "$RATE_LIMIT_PASS" == "true" ] && echo "x" || echo " ")] Rate Limiting: $([ "$RATE_LIMIT_PASS" == "true" ] && echo "✅ Working correctly" || echo "❌ Issues detected")" | tee -a "$LOG_FILE"
    echo "- [ ] Redis Health: $([ "$COUNT_503" -eq 0 ] && echo "✅ No 503 errors" || echo "❌ 503 errors detected")" | tee -a "$LOG_FILE"

    echo -e "\n📋 Manual Verification Required:" | tee -a "$LOG_FILE"
    echo "1. Check backend logs for rate limit enforcement messages" | tee -a "$LOG_FILE"
    echo "2. Test Zebra Associates login with super_admin role" | tee -a "$LOG_FILE"
    echo "3. Monitor for 24 hours before production deployment" | tee -a "$LOG_FILE"
    echo "4. Configure production environment variables" | tee -a "$LOG_FILE"

    echo -e "\n📁 Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
}

# Function to monitor continuously
continuous_monitor() {
    echo -e "\n${YELLOW}Starting continuous monitoring (press Ctrl+C to stop)...${NC}"

    while true; do
        clear
        echo "========================================"
        echo "LIVE MONITORING - $(date)"
        echo "========================================"

        # Quick health check
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL/api/v1/health")
        echo -e "Staging Health: $([ "$HTTP_CODE" == "200" ] && echo -e "${GREEN}✅ UP${NC}" || echo -e "${RED}❌ DOWN${NC}")"

        # Quick rate limit test (5 requests)
        echo -n "Rate Limiting: "
        RATE_LIMITED=false
        for i in {1..6}; do
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
                "$STAGING_URL/api/v1/auth/auth0-url?redirect_uri=$STAGING_URL/callback")
            if [ "$HTTP_CODE" == "429" ]; then
                RATE_LIMITED=true
                break
            fi
        done

        if [ "$RATE_LIMITED" == "true" ]; then
            echo -e "${GREEN}✅ Active (429 received)${NC}"
        else
            echo -e "${YELLOW}⚠️  May be inactive${NC}"
        fi

        echo -e "\nPress Ctrl+C to stop monitoring..."
        sleep 30
    done
}

# Main execution
main() {
    echo "Select verification mode:"
    echo "1) Full verification (one-time)"
    echo "2) Continuous monitoring"
    echo "3) Quick status check"
    read -p "Enter choice (1-3): " choice

    case $choice in
        1)
            check_ci_status
            check_staging_deployment
            verify_rate_limiting
            test_auth_endpoints
            generate_report
            ;;
        2)
            continuous_monitor
            ;;
        3)
            check_staging_deployment
            echo -e "\n${GREEN}Quick check complete${NC}"
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main