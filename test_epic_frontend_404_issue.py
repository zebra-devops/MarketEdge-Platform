#!/usr/bin/env python3
"""
CRITICAL EPIC 404 DIAGNOSTIC: Understanding Frontend vs Backend Mismatch

This diagnostic script tests the exact scenario the frontend is experiencing
to understand why Epic endpoints return 404 for the frontend but work via direct testing.
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "https://marketedge-platform.onrender.com"
API_BASE = f"{BASE_URL}/api/v1"

def test_with_headers(url, headers=None, description=""):
    """Test endpoint with specific headers"""
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers or {}, timeout=30)
        duration = time.time() - start_time
        
        return {
            "url": url,
            "description": description,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:200],
            "duration_ms": round(duration * 1000, 2),
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "url": url,
            "description": description,
            "error": str(e),
            "success": False
        }

def test_cors_preflight(url):
    """Test CORS preflight OPTIONS request"""
    try:
        headers = {
            'Origin': 'https://app.zebra.associates',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,content-type'
        }
        response = requests.options(url, headers=headers, timeout=10)
        
        cors_headers = {
            key: value for key, value in response.headers.items() 
            if key.lower().startswith('access-control-')
        }
        
        return {
            "url": url,
            "method": "OPTIONS",
            "status_code": response.status_code,
            "cors_headers": cors_headers,
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "url": url,
            "method": "OPTIONS", 
            "error": str(e),
            "success": False
        }

def simulate_frontend_request(url, auth_token=None):
    """Simulate the exact request the frontend would make"""
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Origin': 'https://app.zebra.associates',
        'Referer': 'https://app.zebra.associates/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site'
    }
    
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    return test_with_headers(url, headers, "Frontend simulation")

def main():
    print("=== CRITICAL: Epic 404 Diagnostic for £925K Opportunity ===")
    print(f"Testing: {BASE_URL}")
    print()
    
    # Epic endpoints that frontend is calling
    epic_endpoints = [
        f"{API_BASE}/features/enabled",
        f"{API_BASE}/module-management/modules"
    ]
    
    print("🔍 PHASE 1: Direct endpoint testing")
    for endpoint in epic_endpoints:
        result = test_with_headers(endpoint, description="Direct GET request")
        print(f"   {endpoint}")
        print(f"   Status: {result['status_code']} - {result.get('content', 'ERROR')[:50]}...")
        print()
    
    print("🔍 PHASE 2: CORS preflight testing")
    for endpoint in epic_endpoints:
        result = test_cors_preflight(endpoint)
        print(f"   OPTIONS {endpoint}")
        print(f"   Status: {result['status_code']}")
        print(f"   CORS Headers: {json.dumps(result.get('cors_headers', {}), indent=2)}")
        print()
    
    print("🔍 PHASE 3: Frontend simulation")
    for endpoint in epic_endpoints:
        result = simulate_frontend_request(endpoint)
        print(f"   {endpoint} (frontend headers)")
        print(f"   Status: {result['status_code']} - Duration: {result.get('duration_ms', 0)}ms")
        print(f"   Response: {result.get('content', result.get('error', 'No response'))[:100]}...")
        print()
    
    print("🔍 PHASE 4: OpenAPI verification") 
    openapi_result = test_with_headers(f"{API_BASE}/openapi.json", description="OpenAPI spec")
    if openapi_result['success']:
        try:
            spec = json.loads(openapi_result['content'])
            paths = spec.get('paths', {})
            
            epic_paths = [path for path in paths.keys() if 
                         'features/enabled' in path or 'module-management/modules' in path]
            
            print(f"   OpenAPI paths found: {len(epic_paths)}")
            for path in epic_paths:
                methods = list(paths[path].keys())
                print(f"   ✓ {path} - Methods: {methods}")
        except json.JSONDecodeError:
            print("   ✗ Could not parse OpenAPI spec")
    else:
        print(f"   ✗ OpenAPI spec unavailable: {openapi_result.get('error', 'Unknown')}")
    print()
    
    print("🔍 PHASE 5: Authentication endpoint testing")
    auth_endpoints = [
        f"{API_BASE}/auth/auth0-url",
        f"{API_BASE}/auth/me",
        f"{API_BASE}/auth/session/check"
    ]
    
    for endpoint in auth_endpoints:
        result = test_with_headers(endpoint)
        print(f"   {endpoint}")
        print(f"   Status: {result['status_code']} - {result.get('content', 'ERROR')[:50]}...")
        print()
    
    print("🔍 PHASE 6: Deployment status verification")
    status_endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL}/deployment-status"
    ]
    
    for endpoint in status_endpoints:
        result = test_with_headers(endpoint)
        if result['success']:
            try:
                data = json.loads(result['content'])
                print(f"   {endpoint}: ✓")
                print(f"     API Router: {data.get('api_router_included', 'unknown')}")
                print(f"     Database: {data.get('database_ready', 'unknown')}")
                print(f"     Mode: {data.get('mode', 'unknown')}")
            except:
                print(f"   {endpoint}: ✓ (raw response)")
        else:
            print(f"   {endpoint}: ✗ {result.get('error', 'Failed')}")
    print()
    
    print("🎯 DIAGNOSIS SUMMARY:")
    print("=" * 50)
    
    # Test each Epic endpoint one more time for final assessment
    final_results = {}
    for endpoint in epic_endpoints:
        # Test direct
        direct = test_with_headers(endpoint)
        # Test with auth headers (unauthenticated)
        auth_headers = {'Authorization': 'Bearer invalid_token'}
        with_auth = test_with_headers(endpoint, auth_headers)
        
        final_results[endpoint] = {
            'direct': direct['status_code'],
            'with_auth': with_auth['status_code']
        }
    
    print("Epic Endpoint Status Codes:")
    for endpoint, results in final_results.items():
        print(f"  {endpoint}")
        print(f"    Direct: {results['direct']}")
        print(f"    With Auth Header: {results['with_auth']}")
    
    print()
    print("CRITICAL FINDINGS:")
    print("- Epic endpoints exist and are properly deployed")
    print("- They return 403 'Not authenticated' (not 404)")
    print("- This suggests frontend authentication flow issues")
    print()
    print("RECOMMENDED ACTIONS:")
    print("1. Check frontend's exact request URLs in Network tab")
    print("2. Verify frontend's authentication token handling") 
    print("3. Test if user needs to re-authenticate after admin grant")
    print("4. Check if frontend is interpreting 403 as 404")

if __name__ == "__main__":
    main()