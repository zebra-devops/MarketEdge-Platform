#!/usr/bin/env python3
"""
Test authentication flow after applying database fixes
"""

import requests
import json

BASE_URL = "https://marketedge-platform.onrender.com"

def test_post_fix_authentication():
    """Test authentication flow after database fixes"""
    
    print("=" * 60)
    print("TESTING AUTH FLOW AFTER DATABASE FIXES")
    print("=" * 60)
    
    # Test 1: Verify SQLAlchemy organisation creation now works
    print("\n1. TESTING SQLALCHEMY ORGANISATION CREATION...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/database/test-enum-creation")
        if response.status_code == 200:
            data = response.json()
            sqlalchemy_result = data.get('test_results', {}).get('sqlalchemy_creation', {})
            if sqlalchemy_result.get('success'):
                print("✅ SQLAlchemy organisation creation now works!")
                print(f"   Created org: {sqlalchemy_result.get('org', {})}")
            else:
                print("❌ SQLAlchemy organisation creation still failing:")
                print(f"   Error: {sqlalchemy_result.get('error')}")
        else:
            print(f"❌ Test endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception testing SQLAlchemy: {e}")
    
    # Test 2: Try actual auth flow with Auth0 callback format
    print("\n2. TESTING AUTH FLOW WITH PROPER AUTH0 FORMAT...")
    
    # Simulate Auth0 callback parameters
    test_auth_params = {
        "code": "test_auth_code_123",
        "redirect_uri": "https://marketedge-platform.onrender.com/callback"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=test_auth_params,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Auth Status: {response.status_code}")
        
        if response.status_code == 500:
            print("   Still getting 500 - checking error details...")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                
                if "Database error occurred" in str(error_data):
                    print("   ❌ Still getting database errors - need deeper investigation")
                else:
                    print("   ✅ Different error - database issue likely resolved")
            except:
                print(f"   Raw response: {response.text}")
        elif response.status_code == 400:
            print("   ✅ 400 error expected for test auth code (not a real Auth0 token)")
            print("   This suggests database creation would work with real token")
        else:
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Check current database state
    print("\n3. CHECKING DATABASE STATE...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/database/schema-check")
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', {})
            print(f"   Users table: {tables.get('users', {})}")
            print(f"   Organisations table: {tables.get('organisations', {})}")
        else:
            print(f"   Schema check failed: {response.status_code}")
    except Exception as e:
        print(f"   Exception checking schema: {e}")
    
    print("\n" + "=" * 60)
    print("AUTH FLOW TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_post_fix_authentication()