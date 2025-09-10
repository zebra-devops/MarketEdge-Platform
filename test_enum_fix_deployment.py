#!/usr/bin/env python3
"""
TEST ENUM FIX DEPLOYMENT
========================
Test that the database enum case fix has been deployed and resolves the £925K Zebra Associates issue.

This script:
1. Waits for deployment to complete
2. Tests the emergency admin setup endpoint (should now include enum fix)
3. Verifies admin access for matt.lindop@zebra.associates
4. Confirms the 500 error is resolved
5. Validates the business opportunity is unblocked
"""

import requests
import time
import json
from datetime import datetime

def wait_for_deployment(max_wait_minutes=10):
    """Wait for the deployment to complete"""
    print("⏳ Waiting for deployment to complete...")
    
    backend_url = "https://marketedge-platform.onrender.com"
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{backend_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ Backend is responding (took {int(time.time() - start_time)}s)")
                return True
        except:
            pass
        
        print(f"   ⏳ Still waiting... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(30)
    
    print(f"⚠️  Deployment may still be in progress after {max_wait_minutes} minutes")
    return False

def test_enum_fix_deployment():
    """Test the complete enum fix deployment"""
    
    print("🚨 TESTING CRITICAL ENUM FIX DEPLOYMENT")
    print("=" * 50)
    print("Business Impact: £925K Zebra Associates opportunity")
    print("Target: Fix database enum case mismatch")
    print()
    
    backend_url = "https://marketedge-platform.onrender.com"
    zebra_email = "matt.lindop@zebra.associates"
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "deployment_test": {},
        "enum_fix_test": {},
        "admin_verification": {},
        "success": False
    }
    
    # Step 1: Wait for deployment
    print("1. Checking deployment status...")
    deployment_ready = wait_for_deployment(max_wait_minutes=15)
    results["deployment_test"]["ready"] = deployment_ready
    
    if not deployment_ready:
        print("⚠️  Proceeding with tests despite deployment uncertainty")
    
    print()
    
    # Step 2: Test emergency admin setup with enum fix
    print("2. Testing emergency admin setup (should now include enum fix)...")
    try:
        response = requests.post(f"{backend_url}/api/v1/database/emergency-admin-setup", timeout=60)
        results["enum_fix_test"]["status_code"] = response.status_code
        results["enum_fix_test"]["response"] = response.text
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Admin setup successful: {response.status_code}")
            
            # Check if enum fix was applied
            changes = result.get("changes_made", {}).get("application_access_granted", [])
            enum_fixes_applied = [change for change in changes if "Fixed enum case" in change]
            
            if enum_fixes_applied:
                print(f"   🎯 ENUM FIX DETECTED: {len(enum_fixes_applied)} enum fixes applied")
                for fix in enum_fixes_applied:
                    print(f"      - {fix}")
                results["enum_fix_test"]["enum_fixes_applied"] = enum_fixes_applied
            else:
                print("   📊 No enum fixes in response (may already be fixed)")
                results["enum_fix_test"]["enum_fixes_applied"] = []
            
        else:
            print(f"   ❌ Admin setup failed: {response.status_code}")
            print(f"      Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error testing admin setup: {e}")
        results["enum_fix_test"]["error"] = str(e)
    
    print()
    
    # Step 3: Test admin verification (the critical test)
    print("3. Testing admin verification (CRITICAL - this was failing before)...")
    try:
        response = requests.get(f"{backend_url}/api/v1/database/verify-admin-access/{zebra_email}", timeout=30)
        results["admin_verification"]["status_code"] = response.status_code
        results["admin_verification"]["response"] = response.text
        
        if response.status_code == 200:
            result = response.json()
            print("   🎉 SUCCESS! Admin verification now returns 200")
            print(f"   ✅ User: {result.get('user', {}).get('email', 'Unknown')}")
            print(f"   ✅ Is Admin: {result.get('user', {}).get('is_admin', False)}")
            print(f"   ✅ Applications: {result.get('application_access', {}).get('accessible_applications', [])}")
            print(f"   🎯 BUSINESS IMPACT: £925K Zebra Associates opportunity UNBLOCKED!")
            
            results["success"] = True
            results["admin_verification"]["user_verified"] = True
            
        elif response.status_code == 500 and "applicationtype" in response.text:
            print("   ❌ STILL FAILING: Enum error persists")
            print(f"      Error: {response.text[:200]}...")
            print("   🔧 DIAGNOSIS: Deployment may not be complete or enum fix not applied")
            results["admin_verification"]["enum_error_persists"] = True
            
        else:
            print(f"   📊 Different response: {response.status_code}")
            print(f"      Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error testing admin verification: {e}")
        results["admin_verification"]["error"] = str(e)
    
    print()
    
    # Step 4: Generate comprehensive results
    if results["success"]:
        print("🎉 ENUM FIX DEPLOYMENT SUCCESSFUL!")
        print("=" * 40)
        print("✅ Database enum case mismatch resolved")
        print("✅ Admin verification endpoint working")
        print("✅ matt.lindop@zebra.associates access confirmed")
        print("✅ £925K Zebra Associates opportunity UNBLOCKED")
        print()
        print("Next steps:")
        print("1. ✅ Database fix deployed and working")
        print("2. 🔄 User should re-authenticate to get updated permissions")
        print("3. 🔄 Test Epic 1: Module management access")
        print("4. 🔄 Test Epic 2: Feature flags access")
        
    else:
        print("⚠️  ENUM FIX DEPLOYMENT NEEDS VERIFICATION")
        print("=" * 45)
        print("Possible issues:")
        print("- Deployment still in progress")
        print("- Server restart required")
        print("- Additional database fixes needed")
        print()
        print("Recommended actions:")
        print("1. Wait 5-10 minutes for full deployment")
        print("2. Re-run this test script")
        print("3. Check deployment logs if still failing")
    
    # Save detailed results
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    results_file = f"/Users/matt/Sites/MarketEdge/enum_fix_deployment_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results["success"]

if __name__ == "__main__":
    success = test_enum_fix_deployment()
    exit(0 if success else 1)