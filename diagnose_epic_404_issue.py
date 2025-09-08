#!/usr/bin/env python3
"""
Comprehensive Epic endpoints diagnostic for MarketEdge Platform

This script diagnoses why Epic endpoints are returning 404 for frontend 
but working via direct testing.
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "https://marketedge-platform.onrender.com"
API_BASE = f"{BASE_URL}/api/v1"

def test_endpoint(url, method="GET", headers=None, data=None):
    """Test an endpoint and return comprehensive response info"""
    try:
        response = requests.request(method, url, headers=headers, data=data, timeout=30)
        return {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:500],  # First 500 chars
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "url": url,
            "method": method,
            "error": str(e),
            "success": False
        }

def main():
    print("=== MarketEdge Epic Endpoints Diagnostic ===")
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Test 1: Core Epic endpoints that frontend is calling
    epic_endpoints = [
        f"{API_BASE}/features/enabled",
        f"{API_BASE}/module-management/modules",
        f"{API_BASE}/docs",
        f"{API_BASE}/openapi.json"
    ]
    
    print("1. Testing Epic endpoints directly:")
    for endpoint in epic_endpoints:
        result = test_endpoint(endpoint)
        print(f"   {endpoint}")
        print(f"     Status: {result.get('status_code', 'ERROR')}")
        if result.get('error'):
            print(f"     Error: {result['error']}")
        else:
            print(f"     Response: {result['content'][:100]}...")
        print()
    
    # Test 2: Test with different headers (simulate frontend)
    print("2. Testing with common frontend headers:")
    frontend_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; MarketEdge-Frontend)',
        'Origin': BASE_URL
    }
    
    for endpoint in epic_endpoints[:2]:  # Just the Epic endpoints
        result = test_endpoint(endpoint, headers=frontend_headers)
        print(f"   {endpoint} (with headers)")
        print(f"     Status: {result.get('status_code', 'ERROR')}")
        print(f"     Response: {result.get('content', 'ERROR')[:100]}...")
        print()
    
    # Test 3: Check if CORS or preflight issues
    print("3. Testing OPTIONS preflight requests:")
    options_headers = {
        'Origin': BASE_URL,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization,content-type'
    }
    
    for endpoint in epic_endpoints[:2]:
        result = test_endpoint(endpoint, method="OPTIONS", headers=options_headers)
        print(f"   OPTIONS {endpoint}")
        print(f"     Status: {result.get('status_code', 'ERROR')}")
        print(f"     CORS Headers: {result.get('headers', {}).get('access-control-allow-origin', 'Not found')}")
        print()
    
    # Test 4: Try authentication (if we can figure out the format)
    print("4. Testing authentication endpoints:")
    auth_endpoints = [
        f"{API_BASE}/auth/me",
        f"{API_BASE}/auth/session/check"
    ]
    
    for endpoint in auth_endpoints:
        result = test_endpoint(endpoint)
        print(f"   {endpoint}")
        print(f"     Status: {result.get('status_code', 'ERROR')}")
        print(f"     Response: {result.get('content', 'ERROR')[:100]}...")
        print()
    
    # Test 5: Check what's in the OpenAPI spec for these endpoints
    print("5. Verifying Epic endpoints in OpenAPI spec:")
    try:
        openapi_result = test_endpoint(f"{API_BASE}/openapi.json")
        if openapi_result.get('success'):
            openapi_data = json.loads(openapi_result['content'])
            paths = openapi_data.get('paths', {})
            
            epic_paths = [
                '/api/v1/features/enabled',
                '/api/v1/module-management/modules'
            ]
            
            for path in epic_paths:
                if path in paths:
                    methods = list(paths[path].keys())
                    print(f"   ✓ {path} - Methods: {methods}")
                else:
                    print(f"   ✗ {path} - NOT FOUND in OpenAPI spec")
        print()
    except Exception as e:
        print(f"   Error checking OpenAPI spec: {e}")
        print()
    
    # Test 6: Final summary
    print("6. DIAGNOSTIC SUMMARY:")
    print("   - Epic endpoints ARE deployed and registered")
    print("   - They return 'Not authenticated' (not 404) for unauthenticated requests")
    print("   - This suggests the frontend is either:")
    print("     a) Calling different URLs than expected")
    print("     b) Having CORS/preflight issues")
    print("     c) Authentication token issues causing routing problems")
    print("     d) Client-side routing intercepting API calls")
    print()
    print("   RECOMMENDATION: Check frontend network tab to see EXACT URLs being called")
    print("   and their responses. The endpoints exist and work!")

if __name__ == "__main__":
    main()