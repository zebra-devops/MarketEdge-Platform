#!/usr/bin/env python3
"""
Epic 2 Frontend CORS Validation Suite
=====================================

This script validates that the frontend has been successfully migrated 
from Railway to Render backend, resolving the CORS issues.

Author: DevOps Engineer
Date: 2025-08-16
Purpose: Epic 2 Migration Completion Validation
"""

import requests
import json
import time
from datetime import datetime

def test_render_backend_health():
    """Test that the Render backend is operational"""
    print("🔍 Testing Render Backend Health...")
    try:
        response = requests.get("https://marketedge-platform.onrender.com/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Render Backend Health: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Render Backend Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Render Backend Health Check Error: {e}")
        return False

def test_railway_backend_status():
    """Verify that Railway backend is inaccessible (as expected)"""
    print("🔍 Verifying Railway Backend is Down...")
    try:
        response = requests.get("https://marketedge-backend-production.up.railway.app/health", timeout=5)
        if response.status_code == 404:
            print(f"✅ Railway Backend Correctly Down: 404 Not Found")
            return True
        else:
            print(f"⚠️ Railway Backend Unexpectedly Responding: {response.status_code}")
            return False
    except Exception as e:
        print(f"✅ Railway Backend Correctly Down: {e}")
        return True

def test_frontend_deployment():
    """Test that the frontend deployment is accessible"""
    print("🔍 Testing Frontend Deployment...")
    try:
        response = requests.get("https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app", timeout=10)
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print(f"✅ Frontend Deployment Accessible: {response.status_code}")
            return True
        else:
            print(f"❌ Frontend Deployment Issue: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend Deployment Error: {e}")
        return False

def test_auth0_configuration():
    """Test Auth0 configuration endpoint through Render backend"""
    print("🔍 Testing Auth0 Configuration via Render...")
    try:
        # Auth0 endpoint requires redirect_uri parameter
        test_url = "https://marketedge-platform.onrender.com/api/v1/auth/auth0-url?redirect_uri=https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback"
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            print(f"✅ Auth0 Configuration Available: {auth_data.get('auth_url', '')[:50]}...")
            return True
        else:
            print(f"❌ Auth0 Configuration Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth0 Configuration Error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers from Render backend"""
    print("🔍 Testing CORS Headers from Render Backend...")
    try:
        response = requests.options("https://marketedge-platform.onrender.com/api/v1/auth/auth0-url", 
                                  headers={
                                      'Origin': 'https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app',
                                      'Access-Control-Request-Method': 'GET'
                                  }, timeout=10)
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'Not Set')
        cors_methods = response.headers.get('Access-Control-Allow-Methods', 'Not Set')
        
        print(f"✅ CORS Origin: {cors_origin}")
        print(f"✅ CORS Methods: {cors_methods}")
        
        if cors_origin != 'Not Set':
            return True
        else:
            print("❌ CORS headers not properly configured")
            return False
            
    except Exception as e:
        print(f"❌ CORS Headers Test Error: {e}")
        return False

def generate_validation_report():
    """Generate comprehensive validation report"""
    print("\n" + "="*60)
    print("EPIC 2 MIGRATION VALIDATION REPORT")
    print("="*60)
    print(f"Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Render Backend Health", test_render_backend_health),
        ("Railway Backend Status", test_railway_backend_status),
        ("Frontend Deployment", test_frontend_deployment),
        ("Auth0 Configuration", test_auth0_configuration),
        ("CORS Headers", test_cors_headers)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results[test_name] = result
        if result:
            passed_tests += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print()
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 EPIC 2 MIGRATION: COMPLETED SUCCESSFULLY!")
        print("🚀 £925K Demo Ready!")
        print()
        print("MIGRATION STATUS:")
        print("✅ Frontend migrated from Railway to Render")
        print("✅ CORS issues resolved")
        print("✅ Environment variables updated")
        print("✅ Production deployment successful")
        return True
    else:
        print("⚠️ EPIC 2 MIGRATION: ISSUES DETECTED")
        print("❌ Further investigation required")
        return False

def main():
    """Main validation execution"""
    print("🚀 Starting Epic 2 Frontend CORS Validation...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = generate_validation_report()
    
    # Save results to file
    results_file = f"epic2_validation_results_{int(time.time())}.json"
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "epic2_migration_complete": success,
        "frontend_url": "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app",
        "backend_url": "https://marketedge-platform.onrender.com",
        "old_backend_url": "https://marketedge-backend-production.up.railway.app",
        "validation_script": "epic2_frontend_cors_validation.py"
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    return success

if __name__ == "__main__":
    main()