#!/bin/bash

# Deployment Validation Script
# Runs after each deployment to validate functionality and check for console errors
# Usage: ./scripts/validate-deployment.sh [production-url]

set -e

# Configuration
PRODUCTION_URL="${1:-https://frontend-cdir2vud8-zebraassociates-projects.vercel.app}"
REPORT_DIR="test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/deployment_validation_$TIMESTAMP.json"

echo "🚀 Starting deployment validation for: $PRODUCTION_URL"
echo "📊 Report will be saved to: $REPORT_FILE"

# Create report directory
mkdir -p "$REPORT_DIR"

# Ensure Playwright browsers are installed
echo "📦 Ensuring Playwright browsers are available..."
npx playwright install chromium --with-deps

# Run the production validation tests
echo "🧪 Running production validation tests..."
if npx playwright test e2e/production-validation.spec.ts --reporter=json --output="$REPORT_DIR" > "$REPORT_FILE" 2>&1; then
    echo "✅ All validation tests passed!"
    
    # Parse results for summary
    if command -v jq &> /dev/null; then
        echo "📈 Test Summary:"
        jq -r '.suites[0].tests[] | "  \(.title): \(if .outcome == "expected" then "✅ PASS" else "❌ FAIL" end)"' "$REPORT_FILE" 2>/dev/null || echo "  Summary parsing failed"
    fi
    
    echo ""
    echo "🎉 Deployment validation successful!"
    echo "🌐 Production URL is healthy: $PRODUCTION_URL"
    exit 0
else
    echo "❌ Validation tests failed!"
    
    # Show error summary if possible
    if command -v jq &> /dev/null; then
        echo "🔍 Failed Tests:"
        jq -r '.suites[0].tests[] | select(.outcome != "expected") | "  \(.title): \(.outcome)"' "$REPORT_FILE" 2>/dev/null || echo "  Error details in $REPORT_FILE"
    fi
    
    echo ""
    echo "🚨 Deployment validation failed - review errors above"
    echo "📋 Full report: $REPORT_FILE"
    exit 1
fi