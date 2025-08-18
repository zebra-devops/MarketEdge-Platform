#!/usr/bin/env python3
"""
Comprehensive authentication error diagnosis for Epic 2 deployment
Analyzes the difference between direct API testing and frontend authentication flow
"""
import requests
import json
from datetime import datetime

def analyze_auth_flow():
    render_url = "https://marketedge-platform.onrender.com"
    origin = "https://app.zebra.associates"
    
    print("=" * 70)
    print("AUTHENTICATION ERROR FLOW ANALYSIS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Backend URL: {render_url}")
    print(f"Frontend Origin: {origin}")
    print()
    
    # Test 1: Health Check
    print("1. HEALTH CHECK")
    print("-" * 20)
    try:
        health_response = requests.get(f"{render_url}/health", timeout=10)
        print(f"Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"Service Type: {health_data.get('service_type', 'N/A')}")
            print(f"CORS Mode: {health_data.get('cors_mode', 'N/A')}")
            print(f"Emergency Mode: {health_data.get('emergency_mode', 'N/A')}")
        print()
    except Exception as e:
        print(f"Health check failed: {e}")
        print()
    
    # Test 2: CORS Preflight
    print("2. CORS PREFLIGHT ANALYSIS")
    print("-" * 30)
    try:
        preflight_response = requests.options(
            f"{render_url}/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            },
            timeout=10
        )
        
        print(f"Preflight Status: {preflight_response.status_code}")
        
        cors_headers = {}
        for header, value in preflight_response.headers.items():
            if "access-control" in header.lower():
                cors_headers[header] = value
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
        print()
        
    except Exception as e:
        print(f"Preflight test failed: {e}")
        print()
    
    # Test 3: Various Auth Code Formats
    print("3. AUTH CODE VALIDATION TESTING")
    print("-" * 35)
    
    test_codes = [
        # Too short (should fail validation)
        ("short", "Should fail: Code too short"),
        
        # Good length but fake (should reach Auth0 and fail there)
        ("realistic_auth0_authorization_code_that_is_properly_formatted", "Should reach Auth0 exchange"),
        
        # Real-looking Auth0 format
        ("AbCdEf123456_this_looks_like_a_real_auth0_authorization_code_from_oauth_flow", "Real-format test")
    ]
    
    for test_code, description in test_codes:
        print(f"Testing: {description}")
        print(f"Code: {test_code}")
        
        try:
            auth_response = requests.post(
                f"{render_url}/api/v1/auth/login",
                json={
                    "code": test_code,
                    "redirect_uri": f"{origin}/callback",
                    "state": "test_state_parameter"
                },
                headers={
                    "Content-Type": "application/json",
                    "Origin": origin
                },
                timeout=10
            )
            
            print(f"Status: {auth_response.status_code}")
            
            try:
                error_data = auth_response.json()
                print(f"Response: {json.dumps(error_data, indent=2)}")
                
                # Analyze error type
                if "validation error" in str(error_data).lower():
                    print("✓ Validation error (expected for short codes)")
                elif "failed to exchange" in str(error_data).lower():
                    print("✓ Auth0 exchange error (expected for fake codes)")
                elif "internal server error" in str(error_data).lower():
                    print("❌ Internal server error (unexpected)")
                else:
                    print("? Unknown error type")
                    
            except json.JSONDecodeError:
                print(f"Raw response: {auth_response.text}")
            
            print()
            
        except Exception as e:
            print(f"Request failed: {e}")
            print()
    
    # Test 4: Frontend vs Direct API Simulation
    print("4. FRONTEND FLOW SIMULATION")
    print("-" * 30)
    
    # Simulate what the frontend actually sends
    print("Simulating frontend request with realistic headers...")
    
    try:
        frontend_headers = {
            "Content-Type": "application/json",
            "Origin": origin,
            "Referer": f"{origin}/login",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
        
        # Use a real-looking Auth0 authorization code
        realistic_code = "ABCdef123456789_this_is_what_a_real_auth0_code_looks_like_from_the_oauth_callback"
        
        frontend_response = requests.post(
            f"{render_url}/api/v1/auth/login",
            json={
                "code": realistic_code,
                "redirect_uri": f"{origin}/callback",
                "state": "browser_state_parameter"
            },
            headers=frontend_headers,
            timeout=15
        )
        
        print(f"Frontend Simulation Status: {frontend_response.status_code}")
        
        try:
            frontend_error = frontend_response.json()
            print(f"Frontend Response: {json.dumps(frontend_error, indent=2)}")
            
            # Check if this is the 500 error the user is seeing
            if frontend_response.status_code == 500:
                error_detail = frontend_error.get('detail', '')
                error_type = frontend_error.get('type', '')
                
                print(f"❌ 500 ERROR DETECTED!")
                print(f"Error Detail: {error_detail}")
                print(f"Error Type: {error_type}")
                
                if error_type == "internal_error":
                    print("This matches the error pattern from ErrorHandlerMiddleware")
                    print("This suggests the request reaches the backend but fails during processing")
                else:
                    print("Different error type than expected")
                    
        except json.JSONDecodeError:
            print(f"Raw frontend response: {frontend_response.text}")
            
    except Exception as e:
        print(f"Frontend simulation failed: {e}")
    
    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    analyze_auth_flow()