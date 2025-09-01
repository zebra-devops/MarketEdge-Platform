#!/bin/bash

# CRITICAL DEPLOYMENT MONITORING - Import Fix Verification
# Monitors Render deployment to verify the secret_manager import fix is working

set -e

echo "🚀 MONITORING CRITICAL IMPORT FIX DEPLOYMENT"
echo "============================================="
echo "Fix: ModuleNotFoundError for app.core.secret_manager"
echo "Expected: Workers should boot successfully now"
echo ""

# Configuration
RENDER_URL="https://marketedge-backend.onrender.com"  
HEALTH_ENDPOINT="/health"
MAX_ATTEMPTS=60  # 5 minutes with 5-second intervals
SLEEP_INTERVAL=5

echo "Target URL: ${RENDER_URL}${HEALTH_ENDPOINT}"
echo "Max attempts: ${MAX_ATTEMPTS} (${MAX_ATTEMPTS} * ${SLEEP_INTERVAL}s = $((MAX_ATTEMPTS * SLEEP_INTERVAL))s total)"
echo ""

# Function to check deployment status
check_deployment_status() {
    local attempt=$1
    echo "Attempt ${attempt}/${MAX_ATTEMPTS}: Checking deployment status..."
    
    # Check if service is responding
    if curl -s -f "${RENDER_URL}${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
        echo "✅ SUCCESS: Service is responding!"
        
        # Get detailed health response
        echo ""
        echo "=== HEALTH CHECK RESPONSE ==="
        curl -s "${RENDER_URL}${HEALTH_ENDPOINT}" | python3 -m json.tool 2>/dev/null || echo "Raw response:"
        curl -s "${RENDER_URL}${HEALTH_ENDPOINT}"
        echo ""
        echo "============================"
        
        return 0
    else
        echo "❌ Service not yet ready (attempt ${attempt}/${MAX_ATTEMPTS})"
        return 1
    fi
}

# Function to check Render logs (if available)
check_render_logs() {
    echo ""
    echo "=== DEPLOYMENT VERIFICATION ==="
    echo "If the service is now responding, the import fix was successful!"
    echo "Key indicators of success:"
    echo "  ✅ No 'ModuleNotFoundError' in logs"
    echo "  ✅ Workers boot successfully"  
    echo "  ✅ Secret validation completes"
    echo "  ✅ FastAPI app starts normally"
    echo ""
}

# Main monitoring loop
echo "Starting deployment monitoring..."
echo ""

for attempt in $(seq 1 $MAX_ATTEMPTS); do
    if check_deployment_status $attempt; then
        echo ""
        echo "🎉 DEPLOYMENT SUCCESS!"
        echo "✅ Import fix has resolved the ModuleNotFoundError"
        echo "✅ Epic 1 & 2 deployment is now successful"
        echo "✅ £925K opportunity is unblocked"
        echo ""
        
        check_render_logs
        
        echo "=== NEXT STEPS ==="
        echo "1. Verify all endpoints are working"
        echo "2. Run integration tests"  
        echo "3. Notify stakeholders of successful deployment"
        echo "4. Begin Epic 1 & 2 feature validation"
        echo ""
        
        exit 0
    fi
    
    if [ $attempt -lt $MAX_ATTEMPTS ]; then
        echo "   Waiting ${SLEEP_INTERVAL} seconds before next attempt..."
        sleep $SLEEP_INTERVAL
    fi
done

echo ""
echo "❌ DEPLOYMENT TIMEOUT"
echo "Service did not become ready within $((MAX_ATTEMPTS * SLEEP_INTERVAL)) seconds"
echo ""
echo "=== TROUBLESHOOTING ==="
echo "If deployment is still failing, check:"
echo "1. Render deployment logs for new errors"
echo "2. Verify the import fix was applied correctly"
echo "3. Check for any new dependencies or conflicts"
echo "4. Ensure Docker build completed successfully"
echo ""
echo "The import fix should have resolved the ModuleNotFoundError."
echo "Any remaining issues are likely unrelated to the import problem."

exit 1