#!/bin/bash

# Post-deployment validation script for health check fixes
set -e

echo "=== Health Check Fix Validation ==="
echo ""

echo "🔍 Checking Railway deployment status..."
railway status || echo "Warning: Could not get Railway status"
echo ""

echo "📊 Getting recent deployment logs..."
railway logs --deployment 2>/dev/null || echo "Info: No deployment logs available yet"
echo ""

echo "🩺 Testing health endpoint..."
echo "   Running health endpoint test..."

# Create a simple health test that works with Railway environment
cat > temp_health_test.py << 'EOF'
#!/usr/bin/env python3
import urllib.request
import json
import os
import sys

def test_health():
    # Try Railway URL first, then localhost
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    test_urls = []
    
    if railway_url:
        test_urls.append(f"https://{railway_url}/health")
    
    test_urls.extend([
        "http://localhost:8000/health",
        f"http://localhost:{os.getenv('PORT', '8000')}/health"
    ])
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('status') == 'healthy':
                        print(f"✅ SUCCESS: {data}")
                        return True
                    else:
                        print(f"❌ Unhealthy status: {data}")
                else:
                    print(f"❌ HTTP {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
    
    return False

if __name__ == "__main__":
    success = test_health()
    sys.exit(0 if success else 1)
EOF

python3 temp_health_test.py
health_test_result=$?

# Clean up temp file
rm -f temp_health_test.py

echo ""
if [ $health_test_result -eq 0 ]; then
    echo "✅ HEALTH CHECK FIX SUCCESSFUL"
    echo "   The /health endpoint is responding correctly"
    echo ""
    echo "🎉 Deployment health check issues have been resolved!"
    echo ""
    echo "📋 What was fixed:"
    echo "   • Removed blocking database migrations from startup"
    echo "   • Simplified health endpoint (no external dependencies)"
    echo "   • Increased health check timeouts"
    echo "   • Fixed Docker health check timing"
    echo ""
else
    echo "❌ HEALTH CHECK STILL FAILING"
    echo ""
    echo "🔧 Additional troubleshooting steps:"
    echo "   1. Check environment variables: railway variables"
    echo "   2. Check application logs: railway logs"  
    echo "   3. Verify PORT variable is set correctly"
    echo "   4. Run database migrations manually: railway run ./migrate.sh"
    echo ""
    echo "💡 The application may still be starting up. Wait 30-60 seconds and try again."
fi

echo ""
echo "📖 Available commands:"
echo "   railway logs                    - View application logs"
echo "   railway variables               - View environment variables" 
echo "   railway run ./migrate.sh        - Run database migrations"
echo "   railway run python3 test_health_endpoint.py - Test health endpoint"