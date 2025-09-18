#!/usr/bin/env python3
"""
Comprehensive 403 Forbidden diagnosis
Test different scenarios to identify the exact cause
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "https://marketedge-platform.onrender.com"

def test_scenario(name, url, headers=None, expected_status=None):
    """Test a specific scenario"""
    print(f"\n🧪 Testing: {name}")
    print(f"   URL: {url}")
    if headers:
        print(f"   Headers: {json.dumps({k: v[:50] + '...' if len(str(v)) > 50 else v for k, v in headers.items()}, indent=6)}")
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers or {}, timeout=10)
        elapsed = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Time: {elapsed:.2f}s")
        
        if expected_status and response.status_code != expected_status:
            print(f"   ⚠️ Expected {expected_status}, got {response.status_code}")
        elif response.status_code == 401:
            print("   ✅ 401 - Correctly requires authentication")
        elif response.status_code == 403:
            print("   ⚠️ 403 - Permission denied (may indicate auth issue)")
        elif response.status_code == 200:
            print("   ✅ 200 - Request successful")
        
        # Show response body
        response_text = response.text[:200] if response.text else "No content"
        print(f"   Response: {response_text}")
        
        return response.status_code, response.text, response.headers
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, None, None

def main():
    """Run comprehensive diagnosis"""
    print("🔍 COMPREHENSIVE 403 FORBIDDEN DIAGNOSIS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print("=" * 70)
    
    scenarios = [
        # Basic endpoints without auth
        ("Health endpoint", f"{BASE_URL}/health"),
        ("Auth me (no token)", f"{BASE_URL}/api/v1/auth/me"),
        ("Admin feature flags (no token)", f"{BASE_URL}/api/v1/admin/feature-flags"),
        ("Admin dashboard stats (no token)", f"{BASE_URL}/api/v1/admin/dashboard/stats"),
        
        # With empty auth header
        ("Admin feature flags (empty auth)", f"{BASE_URL}/api/v1/admin/feature-flags", {"Authorization": ""}),
        ("Admin feature flags (Bearer only)", f"{BASE_URL}/api/v1/admin/feature-flags", {"Authorization": "Bearer"}),
        
        # With malformed tokens
        ("Admin feature flags (invalid token)", f"{BASE_URL}/api/v1/admin/feature-flags", {"Authorization": "Bearer invalid"}),
        ("Admin feature flags (malformed JWT)", f"{BASE_URL}/api/v1/admin/feature-flags", {"Authorization": "Bearer not.a.jwt"}),
        
        # With CORS headers
        ("Admin feature flags (with Origin)", f"{BASE_URL}/api/v1/admin/feature-flags", {
            "Origin": "https://app.zebra.associates"
        }),
        ("Admin feature flags (with Origin + invalid token)", f"{BASE_URL}/api/v1/admin/feature-flags", {
            "Origin": "https://app.zebra.associates",
            "Authorization": "Bearer invalid"
        }),
    ]
    
    results = []
    
    for scenario in scenarios:
        name, url = scenario[0], scenario[1]
        headers = scenario[2] if len(scenario) > 2 else None
        
        status, text, response_headers = test_scenario(name, url, headers)
        
        results.append({
            'name': name,
            'status': status,
            'text': text,
            'cors_headers': {k: v for k, v in (response_headers or {}).items() 
                           if 'access-control' in k.lower()}
        })
    
    # Analyze results
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    
    # Count status codes
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"📊 Status code distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count} occurrences")
    
    # Check for patterns
    print(f"\n🔍 Pattern analysis:")
    
    # Check if all admin endpoints return same status without auth
    admin_no_auth = [r for r in results if 'admin' in r['name'].lower() and 'no token' in r['name'].lower()]
    if admin_no_auth:
        admin_statuses = [r['status'] for r in admin_no_auth]
        if len(set(admin_statuses)) == 1:
            print(f"   ✅ All admin endpoints without auth return: {admin_statuses[0]}")
        else:
            print(f"   ⚠️ Admin endpoints return different statuses: {set(admin_statuses)}")
    
    # Check CORS behavior
    cors_results = [r for r in results if r['cors_headers']]
    if cors_results:
        print(f"   ✅ CORS headers present in {len(cors_results)} responses")
    else:
        print(f"   ⚠️ No CORS headers found in any responses")
    
    # Key findings
    print(f"\n🎯 KEY FINDINGS:")
    
    if status_counts.get(403, 0) > status_counts.get(401, 0):
        print(f"   ⚠️ More 403 than 401 responses suggests auth middleware issue")
        print(f"   💡 Backend may be treating 'no auth' as 'insufficient permissions'")
    
    if status_counts.get(401, 0) > 0:
        print(f"   ✅ Some 401 responses indicate auth validation is working")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    
    if 403 in status_counts:
        print("   1. Check backend auth dependencies.py get_current_user function")
        print("   2. Verify require_admin is not being called before get_current_user")
        print("   3. Check if middleware is incorrectly handling missing tokens")
    
    if cors_results:
        print("   4. CORS appears to be working - focus on authentication")
    
    print("   5. Test with a real Auth0 token from browser to confirm role issues")
    
    # Next steps
    print(f"\n🚀 NEXT STEPS:")
    print("   1. Get real token: Login to https://app.zebra.associates")
    print("   2. Extract token from browser DevTools")
    print("   3. Test with: curl -H 'Authorization: Bearer <real-token>' <admin-endpoint>")
    print("   4. If still 403 with valid token, check user role in database")

if __name__ == "__main__":
    main()