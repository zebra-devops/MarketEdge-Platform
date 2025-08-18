#!/usr/bin/env python3
"""
Debug script to identify the exact database constraint causing 500 errors
in the Auth0 authentication flow.
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://marketedge-platform.onrender.com"

def test_auth0_database_constraints():
    """Test to identify specific database constraint failures."""
    
    print("🔍 Auth0 Database Constraint Analysis")
    print("=" * 60)
    
    # Step 1: Verify backend health
    try:
        print("1. Testing backend health...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Backend healthy: {response.json()}")
        else:
            print(f"   ❌ Backend unhealthy: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Backend unreachable: {e}")
        return
    
    # Step 2: Test Auth0 URL generation
    try:
        print("\n2. Testing Auth0 URL generation...")
        params = {"redirect_uri": "https://app.zebra.associates/callback"}
        response = requests.get(f"{BASE_URL}/api/v1/auth/auth0-url", params=params, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Auth0 URL generation successful")
        else:
            print(f"   ❌ Auth0 URL failed: {response.status_code} - {response.text[:200]}")
            return
    except Exception as e:
        print(f"   ❌ Auth0 URL generation error: {e}")
        return
    
    # Step 3: Test authentication with form data (like production)
    try:
        print("\n3. Testing authentication endpoint (form data)...")
        
        # Use form data exactly like the frontend does
        form_data = {
            "code": "test_debug_code_12345",
            "redirect_uri": "https://app.zebra.associates/callback",
            "state": "test_state_debug"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=form_data,
            headers=headers,
            timeout=10
        )
        
        print(f"   📊 Status Code: {response.status_code}")
        print(f"   📝 Response Headers: {dict(response.headers)}")
        print(f"   📄 Response Body: {response.text[:500]}...")
        
        if response.status_code == 500:
            print("\n🚨 CRITICAL: 500 Error Detected!")
            try:
                error_data = response.json()
                print(f"   🔍 Error Type: {error_data.get('type', 'unknown')}")
                print(f"   🔍 Error Detail: {error_data.get('detail', 'unknown')}")
                if 'error_details' in error_data:
                    print(f"   🔍 Database Error Details: {error_data['error_details']}")
            except:
                print(f"   🔍 Raw Error Response: {response.text}")
        elif response.status_code == 400:
            print("   ✅ Expected 400 error for invalid Auth0 code")
        else:
            print(f"   ⚠️  Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
    
    # Step 4: Test database connection directly
    try:
        print("\n4. Testing database connection...")
        response = requests.get(f"{BASE_URL}/api/v1/database/test-connection", timeout=10)
        if response.status_code == 200:
            db_info = response.json()
            print(f"   ✅ Database connection successful: {db_info}")
        else:
            print(f"   ❌ Database connection failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Database test error: {e}")
    
    print(f"\n{'='*60}")
    print("Analysis Complete")
    print(f"Timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_auth0_database_constraints()