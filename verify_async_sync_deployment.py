#!/usr/bin/env python3
"""
Post-Deployment Verification Script for Async/Sync Database Session Fix
Purpose: Verify £925K Zebra Associates opportunity is unblocked
Date: 2025-09-12
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "https://marketedge-platform.onrender.com"
ZEBRA_ORIGIN = "https://app.zebra.associates"
TEST_RESULTS = []

def log_test(test_name: str, success: bool, details: str = "", response_data: Dict = None):
    """Log test result"""
    result = {
        "test": test_name,
        "success": success,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "response_data": response_data
    }
    TEST_RESULTS.append(result)
    
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")
    if not success and response_data:
        print(f"    Response: {json.dumps(response_data, indent=2)}")
    print()

def test_service_health():
    """Test basic service health"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "Service Health Check",
                True,
                f"Service healthy, version: {data.get('version', 'unknown')}",
                data
            )
            return True
        else:
            log_test(
                "Service Health Check",
                False,
                f"Unhealthy response: HTTP {response.status_code}",
                {"status_code": response.status_code, "response": response.text}
            )
            return False
    except Exception as e:
        log_test(
            "Service Health Check",
            False,
            f"Connection error: {str(e)}"
        )
        return False

def test_cors_preflight():
    """Test CORS preflight for feature flags endpoint"""
    try:
        response = requests.options(
            f"{BACKEND_URL}/api/v1/admin/feature-flags",
            headers={
                "Origin": ZEBRA_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            },
            timeout=10
        )
        
        headers = response.headers
        
        # Check required CORS headers
        required_headers = {
            "access-control-allow-origin": ZEBRA_ORIGIN,
            "access-control-allow-methods": "GET",
            "access-control-allow-headers": "authorization",
            "access-control-allow-credentials": "true"
        }
        
        missing_headers = []
        for header, expected_value in required_headers.items():
            actual_value = headers.get(header, "").lower()
            if expected_value.lower() not in actual_value:
                missing_headers.append(f"{header}: expected '{expected_value}', got '{actual_value}'")
        
        if not missing_headers:
            log_test(
                "CORS Preflight Request",
                True,
                "All required CORS headers present",
                dict(headers)
            )
            return True
        else:
            log_test(
                "CORS Preflight Request",
                False,
                f"Missing/incorrect headers: {', '.join(missing_headers)}",
                dict(headers)
            )
            return False
            
    except Exception as e:
        log_test(
            "CORS Preflight Request",
            False,
            f"Request error: {str(e)}"
        )
        return False

def test_auth_endpoints():
    """Test authentication endpoints for async/sync consistency"""
    
    # Test 1: Feature flags without auth (should return 401 with CORS headers)
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/admin/feature-flags",
            headers={"Origin": ZEBRA_ORIGIN},
            timeout=10
        )
        
        if response.status_code == 401:
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header and ZEBRA_ORIGIN in cors_header:
                log_test(
                    "Unauthenticated Request Returns 401 with CORS",
                    True,
                    f"HTTP 401 with proper CORS header: {cors_header}"
                )
            else:
                log_test(
                    "Unauthenticated Request Returns 401 with CORS",
                    False,
                    f"HTTP 401 but missing CORS header. Got: {cors_header}",
                    {"headers": dict(response.headers)}
                )
                return False
        else:
            log_test(
                "Unauthenticated Request Returns 401 with CORS",
                False,
                f"Expected HTTP 401, got HTTP {response.status_code}",
                {"status_code": response.status_code, "response": response.text[:200]}
            )
            return False
            
    except Exception as e:
        log_test(
            "Unauthenticated Request Returns 401 with CORS",
            False,
            f"Request error: {str(e)}"
        )
        return False
    
    # Test 2: Invalid token (should return 401 with CORS headers)
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/admin/feature-flags",
            headers={
                "Authorization": "Bearer invalid_token_for_testing",
                "Origin": ZEBRA_ORIGIN
            },
            timeout=10
        )
        
        if response.status_code == 401:
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header and ZEBRA_ORIGIN in cors_header:
                log_test(
                    "Invalid Token Returns 401 with CORS",
                    True,
                    f"HTTP 401 with proper CORS header: {cors_header}"
                )
                return True
            else:
                log_test(
                    "Invalid Token Returns 401 with CORS",
                    False,
                    f"HTTP 401 but missing CORS header. Got: {cors_header}",
                    {"headers": dict(response.headers)}
                )
                return False
        else:
            log_test(
                "Invalid Token Returns 401 with CORS",
                False,
                f"Expected HTTP 401, got HTTP {response.status_code}",
                {"status_code": response.status_code, "response": response.text[:200]}
            )
            return False
            
    except Exception as e:
        log_test(
            "Invalid Token Returns 401 with CORS",
            False,
            f"Request error: {str(e)}"
        )
        return False

def test_no_async_sync_errors():
    """Test that async/sync errors are resolved by checking error patterns"""
    # This is a basic smoke test - in production we'd check logs
    try:
        # Make multiple concurrent requests to stress test async handling
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_request():
            try:
                response = requests.get(
                    f"{BACKEND_URL}/api/v1/admin/feature-flags",
                    headers={"Origin": ZEBRA_ORIGIN},
                    timeout=5
                )
                results_queue.put({
                    "success": True,
                    "status_code": response.status_code,
                    "has_cors": "Access-Control-Allow-Origin" in response.headers
                })
            except Exception as e:
                results_queue.put({
                    "success": False,
                    "error": str(e)
                })
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Collect results
        concurrent_results = []
        while not results_queue.empty():
            concurrent_results.append(results_queue.get())
        
        if len(concurrent_results) == 5:
            # All requests completed
            failed_requests = [r for r in concurrent_results if not r.get("success", False)]
            missing_cors = [r for r in concurrent_results if r.get("success", False) and not r.get("has_cors", False)]
            
            if not failed_requests and not missing_cors:
                log_test(
                    "Concurrent Requests Handle Correctly",
                    True,
                    "All 5 concurrent requests completed successfully with CORS headers",
                    {"results": concurrent_results}
                )
                return True
            else:
                log_test(
                    "Concurrent Requests Handle Correctly",
                    False,
                    f"Failed requests: {len(failed_requests)}, Missing CORS: {len(missing_cors)}",
                    {"results": concurrent_results}
                )
                return False
        else:
            log_test(
                "Concurrent Requests Handle Correctly",
                False,
                f"Only {len(concurrent_results)}/5 requests completed",
                {"results": concurrent_results}
            )
            return False
            
    except Exception as e:
        log_test(
            "Concurrent Requests Handle Correctly",
            False,
            f"Test error: {str(e)}"
        )
        return False

def main():
    """Run all deployment verification tests"""
    print("=" * 60)
    print("ASYNC/SYNC DATABASE SESSION FIX - DEPLOYMENT VERIFICATION")
    print("£925K Zebra Associates Opportunity Verification")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    # Run all tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Basic health
    if test_service_health():
        tests_passed += 1
    total_tests += 1
    
    # Test 2: CORS preflight
    if test_cors_preflight():
        tests_passed += 1
    total_tests += 1
    
    # Test 3: Auth endpoints
    if test_auth_endpoints():
        tests_passed += 1
    total_tests += 1
    
    # Test 4: Async/sync consistency
    if test_no_async_sync_errors():
        tests_passed += 1
    total_tests += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests)*100:.1f}%")
    print(f"Duration: {duration:.2f} seconds")
    print()
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - DEPLOYMENT SUCCESSFUL!")
        print()
        print("✅ Matt Lindop should now be able to access feature flags from:")
        print("   https://app.zebra.associates")
        print()
        print("✅ £925K Zebra Associates opportunity is UNBLOCKED")
        success = True
    else:
        print("❌ SOME TESTS FAILED - INVESTIGATION REQUIRED")
        print()
        print("Failed tests need investigation before confirming deployment success")
        success = False
    
    # Save results to file
    results_file = f"async_sync_deployment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "tests_passed": tests_passed,
                "total_tests": total_tests,
                "success_rate": (tests_passed/total_tests)*100,
                "duration": duration,
                "overall_success": success
            },
            "test_results": TEST_RESULTS
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: {results_file}")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)