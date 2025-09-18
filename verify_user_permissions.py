#!/usr/bin/env python3
"""
Verify Matt Lindop's permissions in production database
Check role, status, and permissions for 403 Forbidden troubleshooting
"""

import asyncio
import asyncpg
import os
import json
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/marketedge')

async def verify_user_permissions():
    """Verify Matt Lindop's permissions and role"""
    print("=" * 70)
    print("PRODUCTION USER PERMISSIONS VERIFICATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now()}")
    print(f"Target User: matt.lindop@zebra.associates")
    print("=" * 70)
    
    try:
        # Connect to database
        print("🔌 Connecting to production database...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Query user details
        print("\n📋 CHECKING USER ACCOUNT")
        print("-" * 40)
        
        user_query = """
        SELECT 
            id,
            email, 
            role,
            is_active,
            is_verified,
            created_at,
            updated_at,
            organisation_id
        FROM users 
        WHERE email = $1
        """
        
        user_result = await conn.fetchrow(user_query, 'matt.lindop@zebra.associates')
        
        if not user_result:
            print("❌ ERROR: User matt.lindop@zebra.associates not found!")
            return False
        
        print(f"✅ User found:")
        print(f"   ID: {user_result['id']}")
        print(f"   Email: {user_result['email']}")
        print(f"   Role: {user_result['role']}")
        print(f"   Active: {user_result['is_active']}")
        print(f"   Verified: {user_result['is_verified']}")
        print(f"   Organisation ID: {user_result['organisation_id']}")
        print(f"   Created: {user_result['created_at']}")
        print(f"   Last Updated: {user_result['updated_at']}")
        
        # Check role requirements
        print("\n🔐 ROLE REQUIREMENTS CHECK")
        print("-" * 40)
        
        required_role = "super_admin"
        actual_role = user_result['role']
        
        if actual_role == required_role:
            print(f"✅ Role matches requirement:")
            print(f"   Required: {required_role}")
            print(f"   Actual: {actual_role}")
            role_check = True
        else:
            print(f"❌ Role mismatch:")
            print(f"   Required: {required_role}")
            print(f"   Actual: {actual_role}")
            role_check = False
        
        # Check organisation details
        print("\n🏢 ORGANISATION CHECK")
        print("-" * 40)
        
        if user_result['organisation_id']:
            org_query = """
            SELECT 
                id,
                name,
                domain,
                is_active,
                subscription_plan,
                industry_type
            FROM organisations 
            WHERE id = $1
            """
            
            org_result = await conn.fetchrow(org_query, user_result['organisation_id'])
            
            if org_result:
                print(f"✅ Organisation found:")
                print(f"   ID: {org_result['id']}")
                print(f"   Name: {org_result['name']}")
                print(f"   Domain: {org_result['domain']}")
                print(f"   Active: {org_result['is_active']}")
                print(f"   Plan: {org_result['subscription_plan']}")
                print(f"   Industry: {org_result['industry_type']}")
            else:
                print(f"❌ Organisation not found for ID: {user_result['organisation_id']}")
        else:
            print("⚠️  No organisation associated with user")
        
        # Check enum values in database
        print("\n📊 DATABASE ENUM VALUES")
        print("-" * 40)
        
        enum_query = """
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'userrole'
        )
        ORDER BY enumsortorder;
        """
        
        enum_results = await conn.fetch(enum_query)
        available_roles = [row['enumlabel'] for row in enum_results]
        
        print(f"Available roles in database:")
        for role in available_roles:
            marker = "✅" if role == actual_role else "  "
            print(f"   {marker} {role}")
        
        # Summary
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        
        checks = [
            ("User exists", user_result is not None),
            ("User active", user_result['is_active'] if user_result else False),
            ("User verified", user_result['is_verified'] if user_result else False),
            ("Role is super_admin", role_check),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ALL CHECKS PASSED!")
            print("User should have proper permissions for admin endpoints.")
        else:
            print("\n⚠️  ISSUES DETECTED!")
            print("User may not have proper permissions for admin endpoints.")
        
        await conn.close()
        return all_passed
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   - Check DATABASE_URL environment variable")
        print("   - Verify database connection from production environment")
        print("   - Ensure user has database access permissions")
        return False

async def test_admin_dependency_logic():
    """Test the admin dependency logic"""
    print("\n" + "=" * 70)
    print("ADMIN DEPENDENCY LOGIC TEST")
    print("=" * 70)
    
    # Simulate the require_admin dependency logic
    print("Testing require_admin dependency logic:")
    
    test_roles = ['super_admin', 'admin', 'analyst', 'viewer']
    allowed_roles = ['admin', 'super_admin']
    
    for role in test_roles:
        allowed = role in allowed_roles
        status = "✅ ALLOWED" if allowed else "❌ FORBIDDEN (403)"
        print(f"   Role '{role}': {status}")
    
    print(f"\n📋 Current require_admin logic:")
    print(f"   Accepts: {allowed_roles}")
    print(f"   Matt Lindop needs: super_admin ✅")

if __name__ == "__main__":
    print("🚀 Starting user permissions verification...")
    
    # Run verification
    result = asyncio.run(verify_user_permissions())
    
    # Test dependency logic
    asyncio.run(test_admin_dependency_logic())
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    
    if result:
        print("✅ User permissions verified - check frontend token handling")
        print("   1. Verify Auth0 token is being sent correctly")
        print("   2. Check Authorization header in browser DevTools")
        print("   3. Test with fresh login session")
    else:
        print("❌ User permissions issues detected")
        print("   1. Fix user role/status issues first")
        print("   2. Re-test after database corrections")
    
    print("\n🎯 Focus: Frontend token attachment in Authorization headers")