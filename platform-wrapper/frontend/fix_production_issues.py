#!/usr/bin/env python3
"""
Fix production database enum case and verify authentication flow
"""
import requests
import json
import time
from datetime import datetime

def fix_enum_case():
    """Fix database enum case mismatch via emergency endpoint"""
    print("🔧 Fixing database enum case mismatch...")
    
    try:
        # Use the emergency feature flags creation endpoint to ensure scope column exists
        response = requests.post(
            "https://marketedge-platform.onrender.com/api/v1/database/emergency/create-feature-flags-table",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Emergency database fix completed:")
            print(f"   - Created objects: {result.get('created_objects', [])}")
            print(f"   - Business impact: {result.get('business_impact', 'N/A')}")
            return True
        else:
            print(f"❌ Emergency endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Emergency fix failed: {e}")
        return False

def test_admin_verification():
    """Test the admin verification endpoint that was failing"""
    print("\n🔍 Testing admin verification endpoint...")
    
    try:
        response = requests.get(
            "https://marketedge-platform.onrender.com/api/v1/database/verify-admin-access/matt.lindop@zebra.associates",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Admin verification successful:")
            print(f"   - User: {result.get('user', {}).get('email', 'N/A')}")
            print(f"   - Is Admin: {result.get('user', {}).get('is_admin', False)}")
            print(f"   - Business impact: {result.get('business_impact', 'N/A')}")
            return True, result
        else:
            print(f"❌ Admin verification failed: {response.status_code}")
            try:
                error_detail = response.json()
                if 'market_edge' in str(error_detail):
                    print("   🎯 CONFIRMED: Still has enum case mismatch issue")
                print(f"   Error: {error_detail}")
            except:
                print(f"   Raw response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Admin verification test failed: {e}")
        return False, None

def test_cors_headers():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS configuration...")
    
    try:
        # Test with preflight OPTIONS request
        response = requests.options(
            "https://marketedge-platform.onrender.com/api/v1/admin/users",
            headers={
                "Origin": "https://app.zebra.associates",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type"
            },
            timeout=30
        )
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
        }
        
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"   {status} {header}: {value}")
        
        # Check if app.zebra.associates is allowed
        allowed_origin = cors_headers.get("Access-Control-Allow-Origin")
        if allowed_origin == "https://app.zebra.associates":
            print("   ✅ Frontend domain is properly configured in CORS")
            return True
        elif allowed_origin == "*":
            print("   ⚠️ CORS allows all origins (should be more restrictive)")
            return True
        else:
            print(f"   ❌ Frontend domain not in CORS config: {allowed_origin}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_authenticated_endpoint():
    """Test authenticated endpoint without token to verify error response"""
    print("\n🔐 Testing authentication flow...")
    
    try:
        response = requests.get(
            "https://marketedge-platform.onrender.com/api/v1/admin/users",
            headers={"Origin": "https://app.zebra.associates"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 403:
            result = response.json()
            if result.get("detail") == "Not authenticated":
                print("   ✅ Proper 403 response for unauthenticated request")
                
                # Check CORS headers in actual response
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                if cors_origin == "https://app.zebra.associates":
                    print("   ✅ CORS headers present in error response")
                    return True
                else:
                    print(f"   ❌ CORS header missing or wrong: {cors_origin}")
                    return False
            else:
                print(f"   ❌ Unexpected error response: {result}")
                return False
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    print("🚀 PRODUCTION ISSUE FIX SCRIPT")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: matt.lindop@zebra.associates admin access")
    print()
    
    # Step 1: Fix database enum case
    enum_fixed = fix_enum_case()
    
    # Wait a moment for changes to propagate
    if enum_fixed:
        print("\n⏳ Waiting 10 seconds for database changes to propagate...")
        time.sleep(10)
    
    # Step 2: Test admin verification (should now work)
    admin_verified, admin_result = test_admin_verification()
    
    # Step 3: Test CORS configuration
    cors_working = test_cors_headers()
    
    # Step 4: Test authentication flow
    auth_flow_working = test_authenticated_endpoint()
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 30)
    print(f"✅ Database enum fix: {'SUCCESS' if enum_fixed else 'FAILED'}")
    print(f"✅ Admin verification: {'SUCCESS' if admin_verified else 'FAILED'}")
    print(f"✅ CORS configuration: {'SUCCESS' if cors_working else 'FAILED'}")
    print(f"✅ Auth flow test: {'SUCCESS' if auth_flow_working else 'FAILED'}")
    
    if enum_fixed and admin_verified and cors_working and auth_flow_working:
        print("\n🎉 ALL FIXES SUCCESSFUL!")
        print("Next steps:")
        print("1. Have matt.lindop@zebra.associates clear browser cache")
        print("2. Have them log out and log back in to get fresh JWT token")
        print("3. Test admin dashboard access")
        print(f"4. £925K Zebra Associates opportunity should now be unblocked")
    else:
        print(f"\n⚠️  Some issues remain - manual intervention needed")
        
        if not enum_fixed:
            print("- Database enum case fix failed - needs direct database access")
        if not admin_verified:
            print("- Admin verification still failing - enum case issue may persist")
        if not cors_working:
            print("- CORS configuration needs adjustment")
        if not auth_flow_working:
            print("- Authentication flow has issues")

if __name__ == "__main__":
    main()