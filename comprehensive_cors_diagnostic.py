#!/usr/bin/env python3
"""
Comprehensive CORS diagnostic for MarketEdge platform
Testing all critical CORS configurations for app.zebra.associates
"""

import requests
import json
import time
from typing import Dict, Any, List

def test_cors_endpoint(url: str, origin: str = "https://app.zebra.associates", 
                      method: str = "GET", headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Test CORS for a specific endpoint"""
    if headers is None:
        headers = {}
    
    # First test preflight (OPTIONS)
    preflight_headers = {
        "Origin": origin,
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "authorization,content-type"
    }
    
    preflight_result = {}
    actual_result = {}
    
    try:
        # Preflight request
        preflight_response = requests.options(url, headers=preflight_headers, timeout=30)
        preflight_result = {
            "status": preflight_response.status_code,
            "headers": dict(preflight_response.headers),
            "cors_origin": preflight_response.headers.get("Access-Control-Allow-Origin"),
            "cors_methods": preflight_response.headers.get("Access-Control-Allow-Methods"),
            "cors_headers": preflight_response.headers.get("Access-Control-Allow-Headers"),
            "cors_credentials": preflight_response.headers.get("Access-Control-Allow-Credentials"),
            "success": preflight_response.status_code == 200
        }
        
        # Actual request
        request_headers = {"Origin": origin}
        request_headers.update(headers)
        
        if method == "GET":
            actual_response = requests.get(url, headers=request_headers, timeout=30)
        elif method == "POST":
            actual_response = requests.post(url, headers=request_headers, json={}, timeout=30)
        else:
            actual_response = requests.request(method, url, headers=request_headers, timeout=30)
            
        actual_result = {
            "status": actual_response.status_code,
            "headers": dict(actual_response.headers),
            "cors_origin": actual_response.headers.get("Access-Control-Allow-Origin"),
            "cors_credentials": actual_response.headers.get("Access-Control-Allow-Credentials"),
            "success": actual_response.status_code < 500,
            "response_size": len(actual_response.content)
        }
        
    except requests.RequestException as e:
        preflight_result["error"] = str(e)
        actual_result["error"] = str(e)
    
    return {
        "endpoint": url,
        "origin": origin,
        "method": method,
        "preflight": preflight_result,
        "actual": actual_result,
        "timestamp": time.time()
    }

def main():
    """Run comprehensive CORS diagnostics"""
    print("🌐 Running Comprehensive CORS Diagnostic for app.zebra.associates")
    print("=" * 70)
    
    base_url = "https://marketedge-platform.onrender.com"
    origin = "https://app.zebra.associates"
    
    # Test endpoints
    endpoints = [
        # Health endpoints
        f"{base_url}/health",
        f"{base_url}/cors-test",
        f"{base_url}/deployment-test",
        
        # Auth endpoints
        f"{base_url}/api/v1/auth/me",
        f"{base_url}/api/v1/auth/callback",
        
        # Admin endpoints
        f"{base_url}/api/v1/admin/users",
        f"{base_url}/api/v1/admin/feature-flags",
        f"{base_url}/api/v1/admin/modules",
        
        # Feature flag endpoints
        f"{base_url}/api/v1/feature-flags",
        f"{base_url}/api/v1/feature-flags/cinema",
        
        # Module endpoints
        f"{base_url}/api/v1/modules",
        f"{base_url}/api/v1/module-management/register"
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"Testing: {endpoint}")
        
        # Test GET requests
        result = test_cors_endpoint(endpoint, origin, "GET")
        results.append(result)
        
        # Test POST requests for API endpoints
        if "/api/v1/" in endpoint:
            result_post = test_cors_endpoint(endpoint, origin, "POST", 
                                           {"Content-Type": "application/json"})
            results.append(result_post)
        
        time.sleep(0.5)  # Be nice to the server
    
    # Test with different origins
    test_origins = [
        "https://app.zebra.associates",
        "https://marketedge-frontend.onrender.com",
        "http://localhost:3000",
        "https://unauthorized-origin.com"
    ]
    
    print("\n🔍 Testing different origins...")
    for origin in test_origins:
        result = test_cors_endpoint(f"{base_url}/cors-test", origin, "GET")
        results.append(result)
        time.sleep(0.5)
    
    # Analyze results
    print("\n📊 CORS Analysis Results")
    print("=" * 50)
    
    successful_preflight = 0
    successful_actual = 0
    cors_issues = []
    
    for result in results:
        endpoint = result["endpoint"]
        origin = result["origin"]
        method = result["method"]
        
        preflight = result.get("preflight", {})
        actual = result.get("actual", {})
        
        print(f"\n{method} {endpoint} (Origin: {origin})")
        
        if preflight.get("success"):
            successful_preflight += 1
            print(f"  ✅ Preflight: {preflight['status']}")
            print(f"     Origin: {preflight.get('cors_origin', 'Not set')}")
            print(f"     Methods: {preflight.get('cors_methods', 'Not set')}")
            print(f"     Credentials: {preflight.get('cors_credentials', 'Not set')}")
        else:
            print(f"  ❌ Preflight: {preflight.get('status', 'Failed')} - {preflight.get('error', '')}")
            cors_issues.append(f"Preflight failed for {endpoint} with origin {origin}")
        
        if actual.get("success"):
            successful_actual += 1
            print(f"  ✅ Actual: {actual['status']}")
            print(f"     CORS Origin: {actual.get('cors_origin', 'Not set')}")
        else:
            print(f"  ❌ Actual: {actual.get('status', 'Failed')} - {actual.get('error', '')}")
            cors_issues.append(f"Actual request failed for {endpoint} with origin {origin}")
    
    # Summary
    print(f"\n📈 Summary")
    print(f"Total tests: {len(results)}")
    print(f"Successful preflight requests: {successful_preflight}/{len(results)}")
    print(f"Successful actual requests: {successful_actual}/{len(results)}")
    
    if cors_issues:
        print(f"\n⚠️  Issues found:")
        for issue in cors_issues[:10]:  # Show first 10 issues
            print(f"  - {issue}")
    else:
        print(f"\n✅ All CORS tests passed!")
    
    # Save detailed results
    output_file = f"cors_diagnostic_report_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "summary": {
                "total_tests": len(results),
                "successful_preflight": successful_preflight,
                "successful_actual": successful_actual,
                "issues_count": len(cors_issues)
            },
            "issues": cors_issues,
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Check specific Zebra Associates compatibility
    zebra_results = [r for r in results if r["origin"] == "https://app.zebra.associates"]
    zebra_success = sum(1 for r in zebra_results if r["preflight"].get("success") and r["actual"].get("success"))
    
    print(f"\n🎯 Zebra Associates Compatibility:")
    print(f"   Tests for app.zebra.associates: {len(zebra_results)}")
    print(f"   Successful: {zebra_success}/{len(zebra_results)}")
    
    if zebra_success == len(zebra_results):
        print(f"   ✅ All Zebra Associates CORS requests should work!")
    else:
        print(f"   ⚠️  Some Zebra Associates requests may fail")
    
    return results

if __name__ == "__main__":
    main()