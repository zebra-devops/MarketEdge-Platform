#!/bin/bash

# MarketEdge Authentication Diagnosis Execution Script
# 
# This script runs comprehensive Playwright E2E authentication testing
# to diagnose the persistent 500 "Database error occurred" issues.
#
# Usage: ./run-auth-diagnosis.sh

set -e

echo "=================================================="
echo "MarketEdge Authentication Diagnosis Suite"
echo "=================================================="
echo "Timestamp: $(date)"
echo "Backend URL: https://marketedge-platform.onrender.com"
echo "Frontend URL: https://frontend-cdir2vud8-zebraassociates-projects.vercel.app"
echo "=================================================="

# Change to frontend directory where Playwright is configured
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend

echo ""
echo "🔧 PREPARATION PHASE"
echo "===================="

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx not found. Please install Node.js and npm"
    exit 1
fi

# Install Playwright if not already installed
echo "📦 Checking Playwright installation..."
if ! npx playwright --version &> /dev/null; then
    echo "Installing Playwright..."
    npm install @playwright/test
    npx playwright install
else
    echo "✅ Playwright is installed"
fi

# Create test results directory
echo "📁 Creating test results directory..."
mkdir -p test-results

# Set environment variables for testing
export PLAYWRIGHT_BASE_URL="https://frontend-cdir2vud8-zebraassociates-projects.vercel.app"
export NODE_ENV="test"

echo ""
echo "🧪 DIAGNOSTIC TEST EXECUTION"
echo "============================="

# Run the comprehensive authentication diagnosis tests
echo "1️⃣ Running Authentication Database Diagnosis Tests..."
echo "   This will test the complete authentication flow and identify database issues"

npx playwright test e2e/auth-database-diagnosis.spec.ts \
    --reporter=json \
    --output-dir=test-results \
    --project=chromium || true

echo ""
echo "2️⃣ Running Auth0 Token Simulation Tests..."
echo "   This will simulate realistic Auth0 token processing scenarios"

npx playwright test e2e/auth0-token-simulation.spec.ts \
    --reporter=json \
    --output-dir=test-results \
    --project=chromium || true

echo ""
echo "3️⃣ Running Backend API Direct Tests..."
echo "   This will test backend endpoints directly without frontend interaction"

# Also run the Python diagnostic script if available
if command -v python3 &> /dev/null; then
    echo ""
    echo "4️⃣ Running Python Diagnostic Script..."
    cd /Users/matt/Sites/MarketEdge
    
    # Install aiohttp if needed
    if ! python3 -c "import aiohttp" &> /dev/null; then
        echo "📦 Installing aiohttp..."
        pip3 install aiohttp || pip install aiohttp
    fi
    
    python3 auth-diagnostic-runner.py || true
    
    cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
fi

echo ""
echo "📊 RESULTS ANALYSIS"
echo "==================="

# Check for test results
if [ -f "test-results/results.json" ]; then
    echo "✅ Playwright test results available"
    
    # Extract key information from results
    if command -v jq &> /dev/null; then
        echo ""
        echo "📋 Test Summary:"
        jq -r '.suites[] | .title' test-results/results.json 2>/dev/null || echo "   Results available in test-results/results.json"
    fi
else
    echo "⚠️  No results.json found - check individual test outputs"
fi

# Check for diagnostic reports
echo ""
echo "📁 Generated Reports:"
echo "===================="

if [ -f "test-results/auth-diagnostic-report.json" ]; then
    echo "✅ Auth Diagnostic Report: test-results/auth-diagnostic-report.json"
fi

if [ -f "test-results/auth0-simulation-report.json" ]; then
    echo "✅ Auth0 Simulation Report: test-results/auth0-simulation-report.json"
fi

if [ -f "/Users/matt/Sites/MarketEdge/auth_diagnostic_report_*.json" ]; then
    echo "✅ Python Diagnostic Report: $(ls -t /Users/matt/Sites/MarketEdge/auth_diagnostic_report_*.json | head -1)"
fi

# Check for screenshots
if ls test-results/*.png 1> /dev/null 2>&1; then
    echo "📸 Screenshots captured:"
    ls test-results/*.png | sed 's/^/   /'
fi

echo ""
echo "🎯 ACTIONABLE RECOMMENDATIONS"
echo "============================="

# Try to extract key findings from the diagnostic reports
if [ -f "test-results/auth-diagnostic-report.json" ]; then
    echo "📋 From Playwright Authentication Diagnosis:"
    
    if command -v jq &> /dev/null; then
        # Extract recommendations if available
        if jq -e '.recommendations' test-results/auth-diagnostic-report.json &> /dev/null; then
            jq -r '.recommendations[]? | "   • [" + .priority + "] " + .area + ": " + .issue' test-results/auth-diagnostic-report.json 2>/dev/null || echo "   See full report for recommendations"
        fi
    else
        echo "   Full details available in test-results/auth-diagnostic-report.json"
    fi
fi

echo ""
echo "🔍 MANUAL REVIEW REQUIRED"
echo "========================="
echo ""
echo "Please review the following files for detailed analysis:"
echo "   • test-results/auth-diagnostic-report.json - Playwright diagnosis"
echo "   • test-results/auth0-simulation-report.json - Auth0 simulation results"
echo "   • test-results/*.png - Visual screenshots of issues"
echo "   • test-results/results.json - Raw Playwright test results"

# Try to provide immediate diagnosis based on common patterns
echo ""
echo "🚨 IMMEDIATE DIAGNOSIS CHECK"
echo "==========================="

# Check if any 500 errors were detected
if grep -q "500" test-results/*.json 2>/dev/null; then
    echo "❌ 500 ERRORS DETECTED: Database operation failures confirmed"
    echo "   🔍 Check for enum constraint violations in organization creation"
    echo "   🔍 Verify Industry and SubscriptionPlan enum values match database schema"
else
    echo "✅ No 500 errors detected in test results"
fi

# Check for specific error patterns
if grep -q -i "database error occurred" test-results/*.json 2>/dev/null; then
    echo "🚨 CRITICAL: 'Database error occurred' message confirmed"
    echo "   🎯 Focus on database operations in authentication flow"
fi

if grep -q -i "enum" test-results/*.json 2>/dev/null; then
    echo "🚨 CRITICAL: Enum constraint violations detected"
    echo "   🎯 Fix enum value mismatches between code and database"
fi

echo ""
echo "=================================================="
echo "AUTHENTICATION DIAGNOSIS COMPLETE"
echo "=================================================="
echo "Timestamp: $(date)"
echo ""
echo "Next Steps:"
echo "1. Review the generated reports above"
echo "2. Focus on database enum constraint issues if 500 errors detected"
echo "3. Fix enum values in organization creation logic"
echo "4. Re-run tests to verify fixes"
echo "=================================================="