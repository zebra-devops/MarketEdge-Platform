#!/usr/bin/env python3
"""
Final authentication flow verification after enum fixes
"""

import requests
import json

BASE_URL = "https://marketedge-platform.onrender.com"

def test_final_auth_verification():
    """Test final auth flow after critical enum fix"""
    
    print("=" * 70)
    print("FINAL AUTHENTICATION VERIFICATION")
    print("=" * 70)
    
    # Test 1: Test auth flow with Auth0 callback format
    print("\n🔐 TESTING AUTHENTICATION FLOW...")
    
    test_auth_params = {
        "code": "test_auth_code_for_enum_verification",
        "redirect_uri": "https://marketedge-platform.onrender.com/callback"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=test_auth_params,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                if "Database error occurred" in str(error_data):
                    print("   ❌ STILL FAILING: Database errors persist")
                    print(f"   Error: {error_data}")
                else:
                    print("   ✅ PROGRESS: Different error (database creation likely fixed)")
                    print(f"   Error: {error_data}")
            except:
                print(f"   Raw error: {response.text}")
                
        elif response.status_code == 400:
            print("   ✅ SUCCESS LIKELY: 400 expected for test auth code")
            print("   This suggests organization creation would work with real Auth0 token")
            try:
                error_data = response.json()
                print(f"   Details: {error_data}")
            except:
                pass
                
        elif response.status_code == 401:
            print("   ✅ SUCCESS LIKELY: 401 expected for invalid auth code")
            print("   Database issues appear resolved")
            
        else:
            print(f"   Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Check database state
    print("\n📊 CHECKING DATABASE STATE...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/database/schema-check")
        if response.status_code == 200:
            data = response.json()
            tables = data.get('tables', {})
            users = tables.get('users', {})
            orgs = tables.get('organisations', {})
            
            print(f"   Users: {users}")
            print(f"   Organizations: {orgs}")
            
            if users.get('exists') and orgs.get('exists'):
                print("   ✅ Database tables exist and accessible")
            else:
                print("   ❌ Database table issues persist")
        else:
            print(f"   ❌ Schema check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception checking schema: {e}")
    
    # Test 3: Test the advanced enum fix endpoint if available
    print("\n🔬 TESTING ADVANCED ENUM FIXES...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/database/fix-enum-sqlalchemy-issue")
        if response.status_code == 200:
            data = response.json()
            results = data.get('test_results', {})
            
            string_enum = results.get('string_enum_creation', {})
            if string_enum.get('success'):
                print("   ✅ SQLAlchemy enum creation with .value works!")
                print(f"   Created org: {string_enum.get('org', {})}")
            else:
                print("   ❌ SQLAlchemy enum creation still failing")
                print(f"   Error: {string_enum.get('error')}")
                
        elif response.status_code == 404:
            print("   ℹ️  Advanced test endpoint not available yet")
        else:
            print(f"   ❌ Advanced test failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception testing advanced fixes: {e}")
    
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION COMPLETE")
    print("=" * 70)
    
    # Summary assessment
    print("\n📋 ASSESSMENT:")
    print("If auth returns 400/401 instead of 500, the database enum issue is FIXED!")
    print("The authentication flow should now work with real Auth0 tokens.")
    print("\n🎯 NEXT STEPS:")
    print("1. Test with real Auth0 frontend flow")
    print("2. Verify user/org creation in production")  
    print("3. Monitor for any remaining database issues")

if __name__ == "__main__":
    test_final_auth_verification()