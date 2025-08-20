#!/bin/bash
# Verify JWT configuration fix

echo "🔍 Testing API endpoints after JWT fix..."

# Test organization endpoints that were returning 403
endpoints=(
    "/api/v1/organisations/current"
    "/api/v1/organisations/industries" 
    "/api/v1/organisations/accessible"
    "/api/v1/tools/"
)

base_url="https://marketedge-platform.onrender.com"

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $endpoint"
    
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
        -H "Authorization: Bearer test_token_will_be_replaced" \
        -H "Origin: https://app.zebra.associates" \
        "$base_url$endpoint")
    
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    
    if [ "$http_status" = "401" ] || [ "$http_status" = "422" ]; then
        echo "✅ $endpoint: Authentication working (expected 401/422 for test token)"
    elif [ "$http_status" = "403" ]; then
        echo "❌ $endpoint: Still getting 403 - JWT config issue"
    else
        echo "ℹ️  $endpoint: Status $http_status"
    fi
    
    echo "---"
done

echo "🏁 Verification complete!"
echo "If you see 401/422 errors instead of 403, the JWT fix worked!"
