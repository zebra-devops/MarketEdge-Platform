#!/usr/bin/env python3
"""
Quick Backend Status Verification Script
========================================
Simple script to verify backend stability and CORS headers are working.
Run this anytime to check if the backend crashes have been fixed.
"""

import requests
import json
from datetime import datetime

def check_backend_status():
    """Quick check of backend status and CORS headers"""
    
    base_url = "https://marketedge-platform.onrender.com"
    headers = {"Origin": "https://app.zebra.associates"}
    
    print("🔍 MarketEdge Backend Status Check")
    print(f"🕐 {datetime.now().isoformat()}")
    print("=" * 50)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "backend_stable": False,
        "cors_working": False,
        "auth_flow_ready": False,
        "tests": []
    }
    
    # Test 1: Health check
    try:
        print("1️⃣ Testing backend health...")
        response = requests.get(f"{base_url}/health", headers=headers, timeout=30)
        
        cors_headers = {
            "allow_origin": response.headers.get("access-control-allow-origin"),
            "allow_credentials": response.headers.get("access-control-allow-credentials")
        }
        
        health_ok = response.status_code == 200
        cors_ok = cors_headers["allow_origin"] is not None
        
        results["tests"].append({
            "test": "health_check",
            "status_code": response.status_code,
            "cors_headers": cors_headers,
            "success": health_ok and cors_ok
        })
        
        if health_ok:
            print("   ✅ Backend responding (200 OK)")
        else:
            print(f"   ❌ Backend error ({response.status_code})")
            
        if cors_ok:
            print("   ✅ CORS headers present")
        else:
            print("   ❌ CORS headers missing")
            
        results["backend_stable"] = health_ok
        
    except Exception as e:
        print(f"   ❌ Health check failed: {str(e)}")
        results["tests"].append({
            "test": "health_check", 
            "error": str(e),
            "success": False
        })
    
    # Test 2: Auth endpoint without credentials (should get 401 with CORS)
    try:
        print("\n2️⃣ Testing auth endpoint CORS...")
        response = requests.get(f"{base_url}/api/v1/admin/feature-flags", headers=headers, timeout=30)
        
        cors_headers = {
            "allow_origin": response.headers.get("access-control-allow-origin"),
            "allow_credentials": response.headers.get("access-control-allow-credentials")
        }
        
        auth_status_ok = response.status_code in [401, 403]  # Expected auth error
        cors_ok = cors_headers["allow_origin"] is not None
        
        results["tests"].append({
            "test": "auth_endpoint_cors",
            "status_code": response.status_code,
            "cors_headers": cors_headers,
            "success": auth_status_ok and cors_ok
        })
        
        if auth_status_ok:
            print(f"   ✅ Auth endpoint responding correctly ({response.status_code})")
        else:
            print(f"   ❌ Unexpected status code ({response.status_code})")
            
        if cors_ok:
            print("   ✅ CORS headers on auth error")
        else:
            print("   ❌ CORS headers missing on auth error")
            
        results["auth_flow_ready"] = auth_status_ok and cors_ok
        
    except Exception as e:
        print(f"   ❌ Auth endpoint test failed: {str(e)}")
        results["tests"].append({
            "test": "auth_endpoint_cors",
            "error": str(e), 
            "success": False
        })
    
    # Test 3: OPTIONS preflight
    try:
        print("\n3️⃣ Testing CORS preflight...")
        response = requests.options(
            f"{base_url}/api/v1/admin/feature-flags", 
            headers={
                **headers,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            },
            timeout=30
        )
        
        preflight_ok = response.status_code == 200
        allow_methods = response.headers.get("access-control-allow-methods", "")
        
        results["tests"].append({
            "test": "cors_preflight",
            "status_code": response.status_code,
            "allow_methods": allow_methods,
            "success": preflight_ok and "GET" in allow_methods
        })
        
        if preflight_ok:
            print("   ✅ Preflight requests working")
        else:
            print(f"   ❌ Preflight failed ({response.status_code})")
            
        if "GET" in allow_methods:
            print("   ✅ Required methods allowed")
        else:
            print("   ❌ Methods not properly configured")
            
        results["cors_working"] = preflight_ok and "GET" in allow_methods
        
    except Exception as e:
        print(f"   ❌ Preflight test failed: {str(e)}")
        results["tests"].append({
            "test": "cors_preflight",
            "error": str(e),
            "success": False
        })
    
    # Overall assessment
    print("\n" + "=" * 50)
    print("📊 OVERALL STATUS")
    print("=" * 50)
    
    backend_stable = results["backend_stable"]
    cors_working = results["cors_working"] 
    auth_ready = results["auth_flow_ready"]
    
    print(f"Backend Stable: {'✅ YES' if backend_stable else '❌ NO'}")
    print(f"CORS Working: {'✅ YES' if cors_working else '❌ NO'}")
    print(f"Auth Flow Ready: {'✅ YES' if auth_ready else '❌ NO'}")
    
    if backend_stable and cors_working and auth_ready:
        print("\n🎉 ALL SYSTEMS GO!")
        print("✅ Backend crashes have been fixed")
        print("✅ CORS headers are working correctly")
        print("✅ Frontend can communicate with backend") 
        print("✅ £925K Zebra Associates opportunity is UNBLOCKED")
    else:
        print("\n⚠️  ISSUES DETECTED")
        if not backend_stable:
            print("❌ Backend may be unstable or down")
        if not cors_working:
            print("❌ CORS configuration issues")
        if not auth_ready:
            print("❌ Authentication flow problems")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backend_status_check_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    return results

if __name__ == "__main__":
    check_backend_status()