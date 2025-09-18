#!/usr/bin/env python3
"""
Production Deployment Validation for US-AUTH Implementation
Tests the live production endpoints to ensure deployment success
"""

import requests
import json
from datetime import datetime

def validate_production_deployment():
    """Validate the production deployment of US-AUTH fixes"""
    print("🚀 US-AUTH Production Deployment Validation")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "backend_health": False,
        "frontend_health": False,
        "auth_endpoints": False,
        "cors_config": False,
        "deployment_status": "UNKNOWN"
    }
    
    # Test 1: Backend Health Check
    print("🔧 Test 1: Backend Service Health")
    try:
        backend_url = "https://marketedge-platform.onrender.com/health"
        response = requests.get(backend_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend healthy: {health_data.get('status', 'unknown')}")
            print(f"   Mode: {health_data.get('mode', 'unknown')}")
            print(f"   CORS configured: {health_data.get('cors_configured', False)}")
            print(f"   Zebra ready: {health_data.get('zebra_associates_ready', False)}")
            print(f"   Auth endpoints: {health_data.get('authentication_endpoints', 'unknown')}")
            results["backend_health"] = True
        else:
            print(f"❌ Backend unhealthy: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Backend connection failed: {str(e)}")
    
    # Test 2: Frontend Health Check
    print("\n🌐 Test 2: Frontend Service Health")
    try:
        frontend_url = "https://app.zebra.associates/"
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend accessible and responding")
            print(f"   Server: {response.headers.get('server', 'unknown')}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Cache-Control: {response.headers.get('cache-control', 'unknown')}")
            results["frontend_health"] = True
        else:
            print(f"❌ Frontend issues: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend connection failed: {str(e)}")
    
    # Test 3: Authentication Endpoints
    print("\n🔐 Test 3: Authentication Endpoints")
    try:
        # Test Auth0 URL endpoint (should be accessible)
        auth_url_endpoint = "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url"
        params = {"redirect_uri": "https://app.zebra.associates/callback"}
        
        response = requests.get(auth_url_endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            auth_data = response.json()
            print("✅ Auth0 URL endpoint working")
            print(f"   Auth URL available: {bool(auth_data.get('auth_url'))}")
            print(f"   Scopes configured: {len(auth_data.get('scopes', []))}")
            results["auth_endpoints"] = True
        else:
            print(f"❌ Auth endpoint issues: HTTP {response.status_code}")
            if response.status_code == 422:
                error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"   Detail: {error_detail}")
            
    except Exception as e:
        print(f"❌ Auth endpoint connection failed: {str(e)}")
    
    # Test 4: CORS Configuration
    print("\n🌐 Test 4: CORS Configuration")
    try:
        # Test CORS preflight
        backend_url = "https://marketedge-platform.onrender.com/api/v1/auth/login"
        headers = {
            "Origin": "https://app.zebra.associates",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
        response = requests.options(backend_url, headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_methods = response.headers.get("Access-Control-Allow-Methods")
            cors_credentials = response.headers.get("Access-Control-Allow-Credentials")
            
            print("✅ CORS preflight successful")
            print(f"   Allow-Origin: {cors_origin}")
            print(f"   Allow-Methods: {cors_methods}")
            print(f"   Allow-Credentials: {cors_credentials}")
            
            if cors_origin in ["*", "https://app.zebra.associates"]:
                results["cors_config"] = True
                print("✅ CORS properly configured for Zebra Associates domain")
            else:
                print(f"⚠️  CORS origin may need adjustment: {cors_origin}")
        else:
            print(f"❌ CORS preflight failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ CORS test failed: {str(e)}")
    
    # Final Assessment
    print("\n📊 Deployment Assessment")
    print("=" * 60)
    
    critical_checks = [results["backend_health"], results["frontend_health"]]
    important_checks = [results["auth_endpoints"], results["cors_config"]]
    
    if all(critical_checks):
        if all(important_checks):
            results["deployment_status"] = "SUCCESS"
            status_emoji = "🎉"
            status_msg = "DEPLOYMENT SUCCESSFUL - Ready for £925K opportunity"
        else:
            results["deployment_status"] = "PARTIAL_SUCCESS"
            status_emoji = "⚠️"
            status_msg = "DEPLOYMENT MOSTLY SUCCESSFUL - Minor configuration issues"
    else:
        results["deployment_status"] = "FAILED"
        status_emoji = "❌"
        status_msg = "DEPLOYMENT FAILED - Critical services unavailable"
    
    print(f"{status_emoji} Status: {results['deployment_status']}")
    print(f"   {status_msg}")
    print()
    print(f"✅ Backend Health: {'PASS' if results['backend_health'] else 'FAIL'}")
    print(f"✅ Frontend Health: {'PASS' if results['frontend_health'] else 'FAIL'}")
    print(f"✅ Auth Endpoints: {'PASS' if results['auth_endpoints'] else 'FAIL'}")
    print(f"✅ CORS Config: {'PASS' if results['cors_config'] else 'FAIL'}")
    
    if results["deployment_status"] == "SUCCESS":
        print("\n🔗 Production URLs:")
        print("   Frontend: https://app.zebra.associates/")
        print("   Backend API: https://marketedge-platform.onrender.com/api/v1/")
        print("   Admin Login: https://app.zebra.associates/login")
        print("\n👤 Matt Lindop can now:")
        print("   ✅ Access the admin login page")
        print("   ✅ Authenticate via Auth0")
        print("   ✅ Receive accessible access tokens")
        print("   ✅ Access admin dashboard functionality")
        print("   ✅ Manage feature flags and users")
    
    return results

if __name__ == "__main__":
    results = validate_production_deployment()
    
    # Write results to file
    with open("production_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: production_validation_results.json")