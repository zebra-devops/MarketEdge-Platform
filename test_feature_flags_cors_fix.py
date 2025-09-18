#!/usr/bin/env python3
"""
Test script to verify CORS headers are present on feature flags endpoint responses
including error responses (401, 403, 500).

This specifically tests the £925K Zebra Associates opportunity requirements.
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Test configuration
BACKEND_URL = os.getenv("BACKEND_URL", "https://marketedge-platform.onrender.com")
FRONTEND_ORIGIN = "https://app.zebra.associates"
API_ENDPOINT = f"{BACKEND_URL}/api/v1/admin/feature-flags"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(title: str):
    """Print a formatted section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{GREEN}✅ PASSED{RESET}" if passed else f"{RED}❌ FAILED{RESET}"
    print(f"{test_name}: {status}")
    if details:
        print(f"  {details}")


def check_cors_headers(response: requests.Response, expected_origin: str) -> Dict[str, Any]:
    """Check if CORS headers are present and correct"""
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
    }
    
    issues = []
    
    # Check critical headers
    if cors_headers["Access-Control-Allow-Origin"] != expected_origin:
        issues.append(f"Origin mismatch: expected '{expected_origin}', got '{cors_headers['Access-Control-Allow-Origin']}'")
    
    if cors_headers["Access-Control-Allow-Credentials"] != "true":
        issues.append(f"Credentials not allowed: got '{cors_headers['Access-Control-Allow-Credentials']}'")
    
    return {
        "headers": cors_headers,
        "valid": len(issues) == 0,
        "issues": issues
    }


def test_options_preflight():
    """Test OPTIONS preflight request"""
    print_header("Testing OPTIONS Preflight Request")
    
    try:
        response = requests.options(
            API_ENDPOINT,
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            },
            timeout=30
        )
        
        cors_check = check_cors_headers(response, FRONTEND_ORIGIN)
        
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers Present: {cors_check['valid']}")
        
        if not cors_check['valid']:
            for issue in cors_check['issues']:
                print(f"  {RED}Issue: {issue}{RESET}")
        
        print_result(
            "OPTIONS Preflight",
            response.status_code == 200 and cors_check['valid'],
            f"Status: {response.status_code}, CORS: {cors_check['valid']}"
        )
        
        return response.status_code == 200 and cors_check['valid']
        
    except Exception as e:
        print(f"{RED}Error during OPTIONS test: {e}{RESET}")
        return False


def test_unauthenticated_request():
    """Test unauthenticated request (should return 401 with CORS headers)"""
    print_header("Testing Unauthenticated Request (401)")
    
    try:
        response = requests.get(
            API_ENDPOINT,
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        cors_check = check_cors_headers(response, FRONTEND_ORIGIN)
        
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers Present: {cors_check['valid']}")
        
        if response.status_code == 401:
            print(f"{GREEN}Correctly returned 401 Unauthorized{RESET}")
        else:
            print(f"{YELLOW}Expected 401, got {response.status_code}{RESET}")
        
        if cors_check['valid']:
            print(f"{GREEN}CORS headers present on error response{RESET}")
        else:
            print(f"{RED}CORS headers missing/incorrect on error response{RESET}")
            for issue in cors_check['issues']:
                print(f"  Issue: {issue}")
        
        # Try to parse error message
        try:
            error_body = response.json()
            print(f"Error detail: {error_body.get('detail', 'No detail provided')}")
        except:
            print(f"Response body: {response.text[:200]}")
        
        print_result(
            "401 Response with CORS",
            response.status_code == 401 and cors_check['valid'],
            f"Status: {response.status_code}, CORS: {cors_check['valid']}"
        )
        
        return response.status_code == 401 and cors_check['valid']
        
    except Exception as e:
        print(f"{RED}Error during unauthenticated test: {e}{RESET}")
        return False


def test_invalid_token_request():
    """Test request with invalid token (should return 401 with CORS headers)"""
    print_header("Testing Invalid Token Request (401)")
    
    try:
        response = requests.get(
            API_ENDPOINT,
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token_12345"
            },
            timeout=30
        )
        
        cors_check = check_cors_headers(response, FRONTEND_ORIGIN)
        
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers Present: {cors_check['valid']}")
        
        if response.status_code == 401:
            print(f"{GREEN}Correctly returned 401 Unauthorized{RESET}")
        else:
            print(f"{YELLOW}Expected 401, got {response.status_code}{RESET}")
        
        if cors_check['valid']:
            print(f"{GREEN}CORS headers present on error response{RESET}")
        else:
            print(f"{RED}CORS headers missing/incorrect on error response{RESET}")
            for issue in cors_check['issues']:
                print(f"  Issue: {issue}")
        
        print_result(
            "Invalid Token with CORS",
            response.status_code == 401 and cors_check['valid'],
            f"Status: {response.status_code}, CORS: {cors_check['valid']}"
        )
        
        return response.status_code == 401 and cors_check['valid']
        
    except Exception as e:
        print(f"{RED}Error during invalid token test: {e}{RESET}")
        return False


def test_simulated_500_error():
    """Test endpoint that might trigger 500 error"""
    print_header("Testing Potential 500 Error Scenario")
    
    try:
        # Try to trigger an error by sending malformed data to a POST endpoint
        response = requests.post(
            f"{BACKEND_URL}/api/v1/admin/feature-flags",
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Content-Type": "application/json",
                "Authorization": "Bearer malformed_token"
            },
            json={"invalid": "data", "missing": "required_fields"},
            timeout=30
        )
        
        cors_check = check_cors_headers(response, FRONTEND_ORIGIN)
        
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers Present: {cors_check['valid']}")
        
        if response.status_code >= 400:
            print(f"Error response code: {response.status_code}")
        
        if cors_check['valid']:
            print(f"{GREEN}CORS headers present on error response{RESET}")
        else:
            print(f"{RED}CORS headers missing/incorrect on error response{RESET}")
            for issue in cors_check['issues']:
                print(f"  Issue: {issue}")
        
        # The test passes if CORS headers are present regardless of status code
        print_result(
            "Error Response with CORS",
            cors_check['valid'],
            f"Status: {response.status_code}, CORS: {cors_check['valid']}"
        )
        
        return cors_check['valid']
        
    except Exception as e:
        print(f"{RED}Error during 500 error test: {e}{RESET}")
        return False


def main():
    """Run all CORS tests"""
    print(f"\n{BLUE}🔍 CORS Header Verification for Feature Flags Endpoint{RESET}")
    print(f"{BLUE}Testing for £925K Zebra Associates Opportunity{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend Origin: {FRONTEND_ORIGIN}")
    print(f"Endpoint: {API_ENDPOINT}")
    
    # Run all tests
    results = {
        "OPTIONS Preflight": test_options_preflight(),
        "Unauthenticated (401)": test_unauthenticated_request(),
        "Invalid Token (401)": test_invalid_token_request(),
        "Error Response": test_simulated_500_error(),
    }
    
    # Summary
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! CORS headers are properly configured.{RESET}")
        print(f"{GREEN}The £925K Zebra Associates opportunity is unblocked!{RESET}")
        return 0
    else:
        print(f"\n{RED}⚠️  Some tests failed. CORS configuration needs attention.{RESET}")
        print(f"{YELLOW}Review the middleware ordering in app/main.py{RESET}")
        print(f"{YELLOW}Ensure CORSMiddleware is added FIRST (before ErrorHandlerMiddleware){RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())