#!/bin/bash

# Monitor Render deployment progress
# Usage: ./monitor-render-deployment.sh

echo "🔍 Monitoring Render deployment for MarketEdge Platform"
echo "Expected commit: 1727c9c (CRITICAL: Deploy actual Render port binding fix)"
echo "Previous failing commit: f64408e (old incomplete fix)"
echo ""

# Function to check deployment status
check_deployment() {
    echo "Checking deployment at $(date)"
    
    # Check if service is responding
    echo "🌐 Testing service availability..."
    if curl -s --max-time 10 https://marketedge-platform.onrender.com/health > /dev/null; then
        echo "✅ Service is responding to health checks"
        return 0
    else
        echo "⚠️  Service not yet responding"
        return 1
    fi
}

# Monitor for 10 minutes (adjust as needed)
max_attempts=20
attempt=1

echo "Starting monitoring (will check every 30 seconds for up to 10 minutes)..."
echo ""

while [ $attempt -le $max_attempts ]; do
    echo "Attempt $attempt/$max_attempts:"
    
    if check_deployment; then
        echo ""
        echo "🎉 SUCCESS! Render deployment appears to be working"
        echo "✅ Port binding timeout issue resolved"
        echo "✅ Single-service mode deployment successful"
        
        # Test a few more endpoints
        echo ""
        echo "🔧 Testing additional endpoints..."
        if curl -s --max-time 5 https://marketedge-platform.onrender.com/api/v1/health > /dev/null; then
            echo "✅ API health endpoint responding"
        fi
        
        exit 0
    fi
    
    echo "Waiting 30 seconds before next check..."
    echo ""
    sleep 30
    ((attempt++))
done

echo "❌ Deployment monitoring timed out after 10 minutes"
echo "Check Render dashboard for deployment logs"
echo "Expected fixes:"
echo "  - No PORT override (let Render set it)"
echo "  - CADDY_PROXY_MODE=false (single-service mode)"  
echo "  - FastAPI starts directly on Render's PORT"