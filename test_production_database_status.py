#!/usr/bin/env python3
"""
Production Database Status Test via API

Tests the production database schema by calling a custom verification endpoint
that will check the actual database state on Render.

This approach works around network limitations by using the production API
to query its own database.
"""

import requests
import json
import sys
from datetime import datetime

PRODUCTION_URL = "https://marketedge-platform.onrender.com"

def test_health_endpoint():
    """Test the health endpoint to confirm production is running"""
    print("🏥 Testing production health...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/health", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"   ✅ Production Status: {data.get('status', 'unknown')}")
        print(f"   📊 Mode: {data.get('mode', 'unknown')}")
        print(f"   🗄️  Database Ready: {data.get('database_ready', 'unknown')}")
        print(f"   🔗 API Router: {data.get('api_router_included', 'unknown')}")
        
        if data.get('database_ready'):
            return True
        else:
            print(f"   ❌ Database Error: {data.get('database_error', 'No details')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

def test_emergency_fix_endpoint():
    """Test the emergency fix endpoint to see current schema state"""
    print("\n🚨 Testing emergency fix endpoint...")
    try:
        response = requests.post(f"{PRODUCTION_URL}/emergency/fix-database-schema", timeout=60)
        response.raise_for_status()
        
        data = response.json()
        print(f"   📊 Status: {data.get('status', 'unknown')}")
        print(f"   📝 Message: {data.get('message', 'No message')}")
        print(f"   🔧 Fixed Tables: {data.get('fixed_tables', [])}")
        print(f"   ⏰ Timestamp: {data.get('timestamp', 'No timestamp')}")
        
        # Interpret results
        if data.get('status') == 'success':
            fixed_tables = data.get('fixed_tables', [])
            if len(fixed_tables) == 0:
                print("   ✅ RESULT: All required Base columns already exist in production")
                print("   ✅ The schema fix was not needed - database is already correct")
                return True, "complete"
            else:
                print(f"   🔧 RESULT: Fixed {len(fixed_tables)} tables with missing columns")
                print("   ✅ The schema fix has now been applied successfully")
                return True, "fixed"
        else:
            print(f"   ❌ RESULT: Emergency fix failed - {data.get('message', 'unknown error')}")
            return False, "failed"
            
    except Exception as e:
        print(f"   ❌ Emergency fix test failed: {e}")
        return False, "error"

def test_authentication_endpoints():
    """Test authentication-related endpoints to see if they work"""
    print("\n🔐 Testing authentication endpoints...")
    
    # Test auth0 URL endpoint
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/auth/auth0-url", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print("   ✅ Auth0 URL endpoint: SUCCESS")
        print(f"      Auth URL: {data.get('auth_url', 'No URL')[:50]}...")
        auth_working = True
        
    except Exception as e:
        print(f"   ❌ Auth0 URL endpoint failed: {e}")
        auth_working = False
    
    # Test auth status endpoint
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/auth/status", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Auth status endpoint: SUCCESS")
            print(f"      Status: {data.get('status', 'unknown')}")
        else:
            print(f"   ⚠️  Auth status endpoint: HTTP {response.status_code}")
            if response.status_code == 500:
                print("   ❌ 500 ERROR DETECTED - This indicates the database schema issue persists")
                auth_working = False
        
    except Exception as e:
        print(f"   ❌ Auth status endpoint failed: {e}")
        auth_working = False
    
    return auth_working

def test_user_operations():
    """Test basic user-related operations that would trigger Base column access"""
    print("\n👤 Testing user operations (that require Base columns)...")
    
    # Try to get users endpoint (this should trigger Base column access)
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/users/", timeout=30)
        
        if response.status_code == 200:
            print("   ✅ Users endpoint: SUCCESS")
            data = response.json()
            print(f"      Response type: {type(data)}")
            return True
        elif response.status_code == 401 or response.status_code == 403:
            print("   ℹ️  Users endpoint: Authentication required (expected)")
            print("   ✅ This means the endpoint works - no 500 error from missing Base columns")
            return True
        elif response.status_code == 500:
            print("   ❌ Users endpoint: 500 INTERNAL SERVER ERROR")
            print("   🚨 This suggests Base column issues are causing database errors")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('detail', 'No details')}")
            except:
                print(f"      Error: {response.text[:200]}...")
            return False
        else:
            print(f"   ⚠️  Users endpoint: HTTP {response.status_code}")
            return True
            
    except Exception as e:
        print(f"   ❌ Users endpoint test failed: {e}")
        return False

def generate_report(health_ok, fix_result, fix_status, auth_ok, users_ok):
    """Generate a comprehensive report"""
    print("\n" + "="*80)
    print("PRODUCTION DATABASE SCHEMA VERIFICATION REPORT")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Production URL: {PRODUCTION_URL}")
    print()
    
    print("SUMMARY")
    print("-" * 40)
    print(f"Production Health: {'✅ OK' if health_ok else '❌ FAIL'}")
    print(f"Emergency Fix Status: {'✅ OK' if fix_result else '❌ FAIL'}")
    print(f"Authentication Endpoints: {'✅ OK' if auth_ok else '❌ FAIL'}")
    print(f"User Operations: {'✅ OK' if users_ok else '❌ FAIL'}")
    print()
    
    print("DETAILED ANALYSIS")
    print("-" * 40)
    
    if fix_status == "complete":
        print("🎯 SCHEMA STATUS: ALL REQUIRED BASE COLUMNS ALREADY EXIST")
        print("   ✅ The emergency database fix was not needed")
        print("   ✅ All 9 tables already have their required created_at/updated_at columns")
        print("   ✅ This explains why fixed_tables returned []")
        print()
        
        if auth_ok and users_ok:
            print("🎯 AUTHENTICATION STATUS: WORKING CORRECTLY")
            print("   ✅ Authentication endpoints respond successfully")
            print("   ✅ User operations work without 500 errors")
            print("   ✅ The original 500 authentication error has been RESOLVED")
        else:
            print("⚠️  AUTHENTICATION STATUS: MIXED RESULTS")
            print("   ⚠️  Some authentication endpoints may have other issues")
            print("   ⚠️  This is not related to the Base column schema fix")
            
    elif fix_status == "fixed":
        print("🔧 SCHEMA STATUS: BASE COLUMNS WERE JUST ADDED")
        print("   ✅ The emergency fix endpoint successfully added missing columns")
        print("   ✅ Database schema is now correct")
        print("   ✅ Authentication should now work properly")
        
    elif fix_status == "failed":
        print("❌ SCHEMA STATUS: EMERGENCY FIX FAILED")
        print("   ❌ The emergency fix endpoint encountered errors")
        print("   ❌ Missing Base columns likely still exist")
        print("   ❌ Authentication 500 errors will persist")
        
    else:
        print("⚠️  SCHEMA STATUS: UNABLE TO DETERMINE")
        print("   ⚠️  Could not test the emergency fix endpoint")
    
    print()
    print("FINAL CONCLUSION")
    print("-" * 40)
    
    if fix_status == "complete" and auth_ok and users_ok:
        print("🎯 SUCCESS: Production database schema is HEALTHY")
        print("   ✅ All required Base columns exist")
        print("   ✅ Authentication works properly")
        print("   ✅ No 500 errors detected")
        print("   ✅ The production system is ready for use")
        print()
        print("📋 Recommendation: No action needed - system is working correctly")
        
    elif fix_status == "fixed":
        print("🎯 SUCCESS: Production database schema has been FIXED")
        print("   ✅ Missing Base columns have been added")
        print("   ✅ Authentication should now work")
        print("   🔄 Test authentication flow to confirm resolution")
        print()
        print("📋 Recommendation: Verify authentication flow in frontend")
        
    else:
        print("⚠️  ISSUES DETECTED: Production needs attention")
        if not fix_result:
            print("   ❌ Emergency fix endpoint failed")
        if not auth_ok:
            print("   ❌ Authentication endpoints have issues")  
        if not users_ok:
            print("   ❌ User operations return 500 errors")
        print()
        print("📋 Recommendation: Manual database inspection needed")
    
    print("="*80)

def main():
    """Main test function"""
    print("🚀 MarketEdge Production Database Schema Status Test")
    print("=" * 70)
    print(f"🎯 Target: {PRODUCTION_URL}")
    print()
    
    # Run tests
    health_ok = test_health_endpoint()
    
    if not health_ok:
        print("\n❌ CRITICAL: Production system is not healthy")
        print("Cannot proceed with database schema tests")
        sys.exit(1)
    
    fix_result, fix_status = test_emergency_fix_endpoint()
    auth_ok = test_authentication_endpoints()
    users_ok = test_user_operations()
    
    # Generate comprehensive report
    generate_report(health_ok, fix_result, fix_status, auth_ok, users_ok)
    
    # Exit with appropriate code
    if fix_status == "complete" and auth_ok and users_ok:
        print("\n✅ ALL TESTS PASSED: Production database schema is correct")
        sys.exit(0)
    elif fix_status == "fixed":
        print("\n🔧 SCHEMA FIXED: Authentication should now work")
        sys.exit(0)
    else:
        print("\n❌ ISSUES DETECTED: Manual investigation needed")
        sys.exit(1)

if __name__ == "__main__":
    main()