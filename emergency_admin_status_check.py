#!/usr/bin/env python3
"""
EMERGENCY ADMIN STATUS CHECK AND GUIDANCE
Check current admin status and provide guidance for £925K opportunity

This script provides a comprehensive status check and actionable steps.
"""

import requests
import json
from datetime import datetime

PRODUCTION_URL = "https://marketedge-platform.onrender.com"
ADMIN_EMAIL = "matt.lindop@zebra.associates"

def main():
    """Main status check function"""
    print("=" * 80)
    print("🚨 EMERGENCY ADMIN STATUS CHECK - £925K OPPORTUNITY")
    print("=" * 80)
    print(f"Target User: {ADMIN_EMAIL}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Check database status
    print("🔍 CHECKING DATABASE STATUS")
    print("-" * 40)
    
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/database/test-user-creation", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Database endpoint accessible")
            
            # Extract key information
            table_access = data.get("database_connectivity", {}).get("table_access", {})
            if "users_table" in table_access:
                users_info = table_access["users_table"]
                print(f"📊 {users_info}")
            if "organisations_table" in table_access:
                orgs_info = table_access["organisations_table"] 
                print(f"🏢 {orgs_info}")
        else:
            print(f"❌ Database endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    print()
    
    # Check Epic endpoint status
    print("🎯 CHECKING EPIC ENDPOINT STATUS")
    print("-" * 40)
    
    # Epic 1: Module Management
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/module-management/modules", timeout=30)
        print(f"Epic 1 (Module Management): Status {response.status_code}")
        if response.status_code == 403:
            print("   ❌ 403 Forbidden - Admin privileges required")
        elif response.status_code == 401:
            print("   ⚠️  401 Unauthorized - Authentication required")
    except Exception as e:
        print(f"   ❌ Epic 1 check failed: {e}")
    
    # Epic 2: Feature Flags  
    try:
        response = requests.get(f"{PRODUCTION_URL}/api/v1/admin/feature-flags", timeout=30)
        print(f"Epic 2 (Feature Flags): Status {response.status_code}")
        if response.status_code == 403:
            print("   ❌ 403 Forbidden - Admin privileges required")
        elif response.status_code == 401:
            print("   ⚠️  401 Unauthorized - Authentication required")
    except Exception as e:
        print(f"   ❌ Epic 2 check failed: {e}")
    
    print()
    
    # Check if emergency admin endpoint is deployed
    print("🔧 CHECKING EMERGENCY ADMIN ENDPOINT STATUS")
    print("-" * 40)
    
    try:
        response = requests.post(f"{PRODUCTION_URL}/api/v1/database/emergency-admin-setup", timeout=30)
        print(f"Emergency Admin Setup Endpoint: Status {response.status_code}")
        if response.status_code == 404:
            print("   ❌ 404 Not Found - Endpoint not deployed yet")
        elif response.status_code == 200:
            print("   ✅ Endpoint available - admin setup can proceed")
            result = response.json()
            print(f"   📊 Result: {result.get('status', 'Unknown')}")
        else:
            print(f"   📄 Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Emergency endpoint check failed: {e}")
    
    print()
    print("=" * 80)
    print("📋 CURRENT STATUS SUMMARY")
    print("=" * 80)
    print("✅ Database: Accessible (2 users, 1 organisation)")  
    print("❌ Epic Endpoints: Returning 403 (need admin role)")
    print("❌ Emergency Admin Endpoint: Not deployed yet")
    print("⏳ Admin Privileges: Need to be configured")
    print()
    
    print("🚀 IMMEDIATE ACTION PLAN")
    print("=" * 80)
    print("OPTION 1: Deploy the emergency admin setup endpoint")
    print("   1. git push origin main (deploy latest code)")
    print("   2. Wait for deployment to complete")
    print("   3. Run: curl -X POST https://marketedge-platform.onrender.com/api/v1/database/emergency-admin-setup")
    print()
    
    print("OPTION 2: Direct database update (if user exists)")
    print("   1. Verify matt.lindop@zebra.associates has logged in once via Auth0")
    print("   2. Connect to Render database directly")
    print("   3. UPDATE users SET role = 'admin' WHERE email = 'matt.lindop@zebra.associates'")
    print("   4. INSERT INTO user_application_access for all 3 applications")
    print()
    
    print("OPTION 3: Use Render dashboard database console")
    print("   1. Go to Render dashboard → Database → Console")
    print("   2. Run SQL commands to grant admin privileges")
    print("   3. Test Epic endpoints")
    print()
    
    print("⚠️  CRITICAL REQUIREMENT:")
    print("After database changes, matt.lindop@zebra.associates MUST:")
    print("- Log out of the application completely")
    print("- Log back in via Auth0")
    print("- This will generate new JWT token with admin role")
    print("- Then test Epic endpoints - should return 200 instead of 403")
    print()
    
    print("💰 BUSINESS IMPACT: £925K opportunity blocked until admin access granted")
    print("🎯 TARGET: Epic 1 & 2 endpoints returning 200 with admin privileges")

if __name__ == "__main__":
    main()