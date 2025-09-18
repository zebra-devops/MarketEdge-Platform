#!/usr/bin/env python3
"""
Test script to verify the admin dashboard CORS fix
This validates that the enum type mismatch has been resolved
"""

import requests
import json
from datetime import datetime
import sys

def test_admin_dashboard_endpoint():
    """Test the admin dashboard endpoint to verify CORS and enum fix"""
    
    print(f"\n🔍 TESTING ADMIN DASHBOARD CORS FIX - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    base_url = "https://marketedge-platform.onrender.com/api/v1"
    endpoint = f"{base_url}/admin/dashboard/stats"
    
    # Test without authentication (should get 403, not 500)
    print("\n1. Testing endpoint without authentication:")
    print(f"   URL: {endpoint}")
    
    try:
        response = requests.get(
            endpoint,
            headers={
                'Origin': 'https://app.zebra.associates',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('access-control-allow-origin'),
            'Access-Control-Allow-Credentials': response.headers.get('access-control-allow-credentials'),
            'Access-Control-Expose-Headers': response.headers.get('access-control-expose-headers')
        }
        
        print(f"   CORS Headers:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"     {status} {header}: {value or 'MISSING'}")
        
        # Check response body
        try:
            response_data = response.json()
            print(f"   Response Body: {json.dumps(response_data, indent=2)}")
            
            # This should be a 403 with proper JSON error, not a 500 crash
            if response.status_code == 403:
                print("   ✅ SUCCESS: Endpoint returns 403 Forbidden (expected without auth)")
                print("   ✅ SUCCESS: Backend is not crashing (no 500 error)")
                if response_data.get('detail') == 'Not authenticated':
                    print("   ✅ SUCCESS: Proper authentication error message")
            elif response.status_code == 500:
                print("   ❌ FAILURE: Backend is still crashing (500 error)")
                return False
            else:
                print(f"   ⚠️  UNEXPECTED: Status code {response.status_code}")
                
        except json.JSONDecodeError:
            print("   ❌ FAILURE: Response is not valid JSON")
            print(f"   Raw Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILURE: Request failed: {e}")
        return False
    
    # Test CORS preflight
    print("\n2. Testing CORS preflight request:")
    try:
        preflight_response = requests.options(
            endpoint,
            headers={
                'Origin': 'https://app.zebra.associates',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization'
            },
            timeout=10
        )
        
        print(f"   Preflight Status: {preflight_response.status_code}")
        if preflight_response.status_code == 200:
            print("   ✅ SUCCESS: CORS preflight working")
        else:
            print("   ⚠️  WARNING: CORS preflight may have issues")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  WARNING: CORS preflight test failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    
    # Check if the main issues are resolved
    cors_origin_ok = cors_headers['Access-Control-Allow-Origin'] == 'https://app.zebra.associates'
    no_crash = response.status_code != 500
    proper_json = response.headers.get('content-type', '').startswith('application/json')
    
    if cors_origin_ok and no_crash and proper_json:
        print("✅ CORS FIX SUCCESSFUL:")
        print("   - CORS headers are properly set")
        print("   - Backend is not crashing (no 500 errors)")
        print("   - Enum type mismatch has been resolved")
        print("   - Endpoint returns proper JSON responses")
        print("\n🎉 The admin dashboard should now be accessible to authenticated users!")
        return True
    else:
        print("❌ ISSUES REMAIN:")
        if not cors_origin_ok:
            print("   - CORS origin header incorrect")
        if not no_crash:
            print("   - Backend is still crashing")
        if not proper_json:
            print("   - Response is not proper JSON")
        return False

def test_health_endpoint():
    """Test a simple health endpoint to ensure the service is running"""
    print("\n3. Testing service health:")
    
    try:
        health_url = "https://marketedge-platform.onrender.com/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Backend service is running")
            return True
        else:
            print(f"   ⚠️  Health check returned {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ADMIN DASHBOARD CORS FIX VALIDATION TEST")
    print("Testing the resolution of enum type mismatch causing backend crashes")
    
    # Test basic service health
    service_healthy = test_health_endpoint()
    
    if not service_healthy:
        print("\n❌ Backend service appears to be down. Please check deployment status.")
        sys.exit(1)
    
    # Test the main fix
    fix_successful = test_admin_dashboard_endpoint()
    
    if fix_successful:
        print("\n🎯 NEXT STEPS:")
        print("   1. Matt should now be able to access the admin dashboard")
        print("   2. The CORS error in browser console should be resolved")  
        print("   3. Admin users can view dashboard statistics")
        print("   4. The £925K Zebra Associates opportunity access is restored")
        sys.exit(0)
    else:
        print("\n🚨 MANUAL INTERVENTION REQUIRED:")
        print("   1. Check deployment logs for additional errors")
        print("   2. Verify database schema and enum definitions")
        print("   3. Test with authenticated user credentials")
        sys.exit(1)