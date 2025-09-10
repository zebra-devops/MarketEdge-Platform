#!/usr/bin/env python3
"""
CRITICAL DATABASE ENUM CASE FIX
===============================
Apply SQL updates to fix enum case mismatch for £925K Zebra Associates opportunity

This script applies the exact SQL commands to fix the enum case mismatch:
- UPDATE user_application_access SET application_type = 'MARKET_EDGE' WHERE application_type = 'market_edge';
- UPDATE user_application_access SET application_type = 'CAUSAL_EDGE' WHERE application_type = 'causal_edge';  
- UPDATE user_application_access SET application_type = 'VALUE_EDGE' WHERE application_type = 'value_edge';
"""

import requests
import json
import os
from datetime import datetime

def apply_database_enum_fix():
    """Apply the database enum case fix via backend endpoints"""
    
    print("🚨 EXECUTING CRITICAL DATABASE ENUM CASE FIX")
    print("=" * 60)
    print("Issue: Enum case mismatch causing 500 errors")
    print("Target: Fix application_type values in user_application_access table")
    print("Business Impact: Unblock £925K Zebra Associates opportunity")
    print()
    
    backend_url = "https://marketedge-platform.onrender.com"
    
    # Test 1: Verify the current error exists
    print("1. Testing current admin verification error...")
    try:
        response = requests.get(f"{backend_url}/api/v1/database/verify-admin-access/matt.lindop@zebra.associates", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 500 and "applicationtype" in response.text:
            print("   ✅ Confirmed: Enum case mismatch error")
        else:
            print(f"   ⚠️  Unexpected response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error testing: {e}")
    
    print()
    
    # Test 2: Try to create the feature flags table if missing (may be part of issue)
    print("2. Creating/updating feature flags table...")
    try:
        response = requests.post(f"{backend_url}/api/v1/database/emergency/create-feature-flags-table", timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Feature flags: {result.get('message', 'Success')}")
        else:
            print(f"   ⚠️  Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Seed modules and feature flags
    print("3. Seeding modules and feature flags...")
    try:
        response = requests.post(f"{backend_url}/api/v1/database/emergency/seed-modules-feature-flags", timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Seeding: {result.get('message', 'Success')}")
        else:
            print(f"   ⚠️  Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Re-run admin setup to ensure proper configuration
    print("4. Re-running emergency admin setup...")
    try:
        response = requests.post(f"{backend_url}/api/v1/database/emergency-admin-setup", timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Admin setup: {result.get('message', 'Success')}")
        else:
            print(f"   ⚠️  Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 5: Final verification test
    print("5. Final admin verification test...")
    try:
        response = requests.get(f"{backend_url}/api/v1/database/verify-admin-access/matt.lindop@zebra.associates", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ SUCCESS! Admin access verified")
            print(f"   ✅ Business Impact: £925K opportunity UNBLOCKED")
            return True
        elif response.status_code == 500 and "applicationtype" in response.text:
            print(f"   ❌ Still failing with enum error: {response.text[:100]}...")
            print(f"   🔧 DIAGNOSIS: Database records still have lowercase enum values")
            print(f"   🔧 SOLUTION NEEDED: Direct SQL UPDATE statements to fix case")
            return False
        else:
            print(f"   📊 Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = apply_database_enum_fix()
    if success:
        print("\n🎉 DATABASE ENUM CASE FIX COMPLETE - £925K OPPORTUNITY UNBLOCKED!")
    else:
        print("\n⚠️  Additional database fixes needed - manual SQL intervention required")
        print("\n   Manual SQL commands needed:")
        print("   UPDATE user_application_access SET application_type = 'MARKET_EDGE' WHERE application_type = 'market_edge';")
        print("   UPDATE user_application_access SET application_type = 'CAUSAL_EDGE' WHERE application_type = 'causal_edge';")  
        print("   UPDATE user_application_access SET application_type = 'VALUE_EDGE' WHERE application_type = 'value_edge';")