#!/usr/bin/env python3
"""
Production Database Test
Tests database operations on production by hitting a test endpoint
"""

import requests
import json
import time

PRODUCTION_URL = "https://marketedge-platform.onrender.com"

def test_database_endpoint():
    """Test if we can create a simple database test endpoint"""
    print("=" * 60)
    print("PRODUCTION DATABASE CONNECTIVITY TEST")
    print("=" * 60)
    
    # Check if there's already a database test endpoint
    test_endpoints = [
        "/api/v1/admin/health",
        "/api/v1/health",
        "/ready",
        "/health"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"\nTesting endpoint: {endpoint}")
            response = requests.get(f"{PRODUCTION_URL}{endpoint}", timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                # Look for database information
                if 'database' in data or 'services' in data:
                    print("✅ Found database information in response")
                    return data
            elif response.status_code == 404:
                print("❌ Endpoint not found")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    return None

def test_auth_endpoint_with_minimal_data():
    """Test auth endpoint to see what specific error we get"""
    print("\n" + "=" * 40)
    print("AUTH ENDPOINT ERROR ANALYSIS")
    print("=" * 40)
    
    try:
        # Use minimal test data to trigger database operations
        test_data = {
            "code": "test_code_minimal",
            "redirect_uri": "https://app.zebra.associates/callback"
        }
        
        print(f"\nTesting auth endpoint with minimal data...")
        response = requests.post(
            f"{PRODUCTION_URL}/api/v1/auth/login",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Analyze the error
            if "detail" in data:
                if "Database error occurred" in data["detail"]:
                    print("🔍 FOUND THE ISSUE: Database error during auth")
                    print("   This confirms database operations are failing")
                elif "Failed to exchange authorization code" in data["detail"]:
                    print("✅ Auth flow reached Auth0 exchange step")
                    print("   This means database operations are working!")
                    print("   The error is at the Auth0 token exchange level")
                else:
                    print(f"🔍 Different error: {data['detail']}")
                    
        except json.JSONDecodeError:
            print(f"Non-JSON response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_cors_debug():
    """Test CORS debug endpoint for additional information"""
    print("\n" + "=" * 40)
    print("CORS DEBUG ENDPOINT")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{PRODUCTION_URL}/cors-debug",
            headers={
                "Origin": "https://app.zebra.associates",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"CORS Debug: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS debug failed: {e}")

def main():
    """Run all production tests"""
    print(f"Testing production deployment at: {PRODUCTION_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Database endpoints
    db_info = test_database_endpoint()
    
    # Test 2: Auth endpoint analysis
    test_auth_endpoint_with_minimal_data()
    
    # Test 3: CORS debug
    test_cors_debug()
    
    print("\n" + "=" * 60)
    print("PRODUCTION TEST COMPLETE")
    print("=" * 60)
    
    # Summary
    if db_info and "database" in str(db_info):
        print("✅ Database connectivity confirmed")
    else:
        print("⚠️ Database connectivity uncertain")

if __name__ == "__main__":
    main()