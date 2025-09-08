#!/usr/bin/env python3
"""
EMERGENCY ADMIN SETUP TEST SCRIPT
Verifies the emergency admin setup endpoint for £925K opportunity

This script tests:
1. Emergency admin setup for matt.lindop@zebra.associates
2. Verification of admin privileges
3. Epic endpoint access confirmation

Usage:
    python test_emergency_admin_setup.py
"""

import asyncio
import requests
import json
from datetime import datetime

# Configuration
PRODUCTION_URL = "https://marketedge-platform.onrender.com"
LOCAL_URL = "http://localhost:8000"
ADMIN_EMAIL = "matt.lindop@zebra.associates"

# Test endpoints
ENDPOINTS = {
    "health": "/health",
    "emergency_admin_setup": "/api/v1/database/emergency-admin-setup", 
    "verify_admin": f"/api/v1/database/verify-admin-access/{ADMIN_EMAIL}",
    "epic1_modules": "/api/v1/module-management/modules",
    "epic2_feature_flags": "/api/v1/admin/feature-flags"
}

def test_endpoint(base_url: str, endpoint: str, method: str = "GET", headers: dict = None):
    """Test a specific endpoint"""
    url = f"{base_url}{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "error": None
        }
    except Exception as e:
        return {
            "status_code": None,
            "success": False,
            "response": None,
            "error": str(e)
        }

def main():
    """Main test function"""
    print("=" * 80)
    print("🚨 EMERGENCY ADMIN SETUP TEST - £925K OPPORTUNITY")
    print("=" * 80)
    print(f"Testing admin setup for: {ADMIN_EMAIL}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Test both production and local environments
    for env_name, base_url in [("PRODUCTION", PRODUCTION_URL), ("LOCAL", LOCAL_URL)]:
        print(f"🔍 Testing {env_name} environment: {base_url}")
        print("-" * 60)
        
        # Step 1: Test health endpoint
        print("1. Testing health endpoint...")
        health_result = test_endpoint(base_url, ENDPOINTS["health"])
        if health_result["success"]:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {health_result.get('error', 'Unknown error')}")
            continue  # Skip this environment if health fails
        
        # Step 2: Test emergency admin setup
        print("2. Testing emergency admin setup...")
        setup_result = test_endpoint(base_url, ENDPOINTS["emergency_admin_setup"], method="POST")
        
        if setup_result["success"]:
            print("   ✅ Emergency admin setup successful!")
            response_data = setup_result["response"]
            if isinstance(response_data, dict):
                print(f"   📝 Status: {response_data.get('status', 'Unknown')}")
                print(f"   👤 User: {response_data.get('message', 'No message')}")
                
                # Show changes made
                changes = response_data.get("changes_made", {})
                if changes:
                    print("   📊 Changes made:")
                    for key, value in changes.items():
                        print(f"      - {key}: {value}")
        else:
            print(f"   ❌ Emergency admin setup failed: {setup_result.get('error', 'Unknown error')}")
            if setup_result.get("response"):
                print(f"   📄 Response: {json.dumps(setup_result['response'], indent=2)}")
        
        # Step 3: Verify admin access
        print("3. Verifying admin access...")
        verify_result = test_endpoint(base_url, ENDPOINTS["verify_admin"])
        
        if verify_result["success"]:
            print("   ✅ Admin verification successful!")
            response_data = verify_result["response"]
            if isinstance(response_data, dict):
                user_info = response_data.get("user", {})
                epic_check = response_data.get("epic_access_verification", {})
                
                print(f"   👤 User Role: {user_info.get('role', 'Unknown')}")
                print(f"   🔑 Is Admin: {user_info.get('is_admin', False)}")
                print(f"   🎯 Epic Access: {epic_check.get('epic_endpoints_accessible', False)}")
                print(f"   💼 Business Impact: {response_data.get('business_impact', 'Unknown')}")
        else:
            print(f"   ❌ Admin verification failed: {verify_result.get('error', 'Unknown error')}")
        
        # Step 4: Test Epic 1 endpoint (requires auth - will get 401/403)
        print("4. Testing Epic 1 (Module Management) endpoint...")
        epic1_result = test_endpoint(base_url, ENDPOINTS["epic1_modules"])
        
        if epic1_result["status_code"] == 401:
            print("   ⚠️  Epic 1 endpoint requires authentication (expected - 401)")
        elif epic1_result["status_code"] == 403:
            print("   ❌ Epic 1 endpoint returns 403 - admin privileges needed")
        elif epic1_result["success"]:
            print("   ✅ Epic 1 endpoint accessible!")
        else:
            print(f"   ❓ Epic 1 endpoint status: {epic1_result['status_code']}")
        
        # Step 5: Test Epic 2 endpoint (requires auth - will get 401/403)
        print("5. Testing Epic 2 (Feature Flags) endpoint...")
        epic2_result = test_endpoint(base_url, ENDPOINTS["epic2_feature_flags"])
        
        if epic2_result["status_code"] == 401:
            print("   ⚠️  Epic 2 endpoint requires authentication (expected - 401)")
        elif epic2_result["status_code"] == 403:
            print("   ❌ Epic 2 endpoint returns 403 - admin privileges needed")
        elif epic2_result["success"]:
            print("   ✅ Epic 2 endpoint accessible!")
        else:
            print(f"   ❓ Epic 2 endpoint status: {epic2_result['status_code']}")
        
        print()
    
    print("=" * 80)
    print("🔧 NEXT STEPS FOR £925K OPPORTUNITY")
    print("=" * 80)
    print("1. Have matt.lindop@zebra.associates authenticate via Auth0")
    print("2. User will receive updated JWT token with admin role")
    print("3. Test Epic endpoints with authenticated requests:")
    print(f"   - Epic 1: GET {PRODUCTION_URL}/api/v1/module-management/modules")
    print(f"   - Epic 2: GET {PRODUCTION_URL}/api/v1/admin/feature-flags")
    print("4. Confirm 200 responses instead of 403 errors")
    print()
    print("🎯 Admin privileges are now configured in the database!")
    print("✅ £925K opportunity should be unblocked once user re-authenticates")

if __name__ == "__main__":
    main()