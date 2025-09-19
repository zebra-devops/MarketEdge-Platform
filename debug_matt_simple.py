#!/usr/bin/env python3
"""
Simple Matt.Lindop Admin Access Debug - £925K Zebra Associates Opportunity

Focuses on direct database queries and API testing without async complexity
"""

import json
import os
import sys
import asyncio
import httpx
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class SimpleMattDebugger:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/platform_wrapper')
        self.production_api = "https://marketedge-platform.onrender.com"

    def debug_database_direct(self):
        """Direct PostgreSQL connection to check Matt's status"""
        print("🔍 Phase 1: Direct Database Check")
        print("-" * 40)

        try:
            # Connect to database
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Find Matt.Lindop
            cursor.execute("""
                SELECT u.id, u.email, u.first_name, u.last_name, u.role,
                       u.is_active, u.organisation_id, o.name as org_name
                FROM users u
                LEFT JOIN organisations o ON u.organisation_id = o.id
                WHERE u.email = %s
            """, ("matt.lindop@zebra.associates",))

            matt_record = cursor.fetchone()

            if matt_record:
                print(f"✅ Found Matt.Lindop in database:")
                print(f"   ID: {matt_record['id']}")
                print(f"   Email: {matt_record['email']}")
                print(f"   Role: {matt_record['role']}")
                print(f"   Active: {matt_record['is_active']}")
                print(f"   Org ID: {matt_record['organisation_id']}")
                print(f"   Org Name: {matt_record['org_name']}")

                # Critical checks
                if matt_record['role'] != 'super_admin':
                    print(f"❌ CRITICAL: Role is '{matt_record['role']}', expected 'super_admin'")
                    print("🔧 FIX NEEDED: Update role to super_admin")
                    return "role_not_super_admin"

                if not matt_record['is_active']:
                    print("❌ CRITICAL: Account is inactive")
                    print("🔧 FIX NEEDED: Activate account")
                    return "account_inactive"

                if not matt_record['org_name']:
                    print("❌ CRITICAL: No organisation assigned")
                    print("🔧 FIX NEEDED: Assign to Zebra Associates organisation")
                    return "no_organisation"

                print("✅ Database state looks correct!")
                return "database_ok"

            else:
                print("❌ CRITICAL: Matt.Lindop not found in database")
                print("🔧 FIX NEEDED: Create user account")
                return "user_not_found"

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return f"database_error: {e}"
        finally:
            if 'conn' in locals():
                conn.close()

    async def test_production_api(self):
        """Test production API endpoints"""
        print("\n🌐 Phase 2: Production API Test")
        print("-" * 40)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test health endpoint
                health_response = await client.get(f"{self.production_api}/health")
                print(f"Health check: {health_response.status_code}")

                if health_response.status_code != 200:
                    print("❌ Production API not responding properly")
                    return "api_down"

                print("✅ Production API is responding")

                # Test admin endpoint without auth (should get 401)
                admin_response = await client.get(f"{self.production_api}/api/v1/admin/dashboard/stats")
                print(f"Admin endpoint test: {admin_response.status_code}")

                if admin_response.status_code == 401:
                    print("✅ Admin endpoint properly requires authentication")
                    return "api_ok"
                else:
                    print(f"❌ Unexpected response from admin endpoint: {admin_response.status_code}")
                    return "api_config_issue"

        except Exception as e:
            print(f"❌ API test failed: {e}")
            return f"api_error: {e}"

    def check_auth_dependencies(self):
        """Check authentication dependency configuration"""
        print("\n🔐 Phase 3: Auth Configuration Check")
        print("-" * 40)

        try:
            # Read auth dependencies file
            auth_deps_path = "/Users/matt/Sites/MarketEdge/app/auth/dependencies.py"
            with open(auth_deps_path, 'r') as f:
                auth_code = f.read()

            # Check for super_admin support
            if 'UserRole.super_admin' in auth_code:
                print("✅ super_admin role found in auth dependencies")
            else:
                print("❌ super_admin role not found in auth dependencies")
                return "auth_config_missing_super_admin"

            # Check require_admin function
            if 'UserRole.admin, UserRole.super_admin' in auth_code:
                print("✅ require_admin supports both admin and super_admin")
            else:
                print("❌ require_admin may not support super_admin")
                return "require_admin_config_issue"

            print("✅ Authentication configuration looks correct")
            return "auth_config_ok"

        except Exception as e:
            print(f"❌ Auth config check failed: {e}")
            return f"auth_config_error: {e}"

    def generate_fix_script(self, issues):
        """Generate SQL fix script based on identified issues"""
        print("\n🔧 Phase 4: Generate Fix Script")
        print("-" * 40)

        if "role_not_super_admin" in issues:
            fix_script = """
-- Fix Matt.Lindop role to super_admin
UPDATE users
SET role = 'super_admin', updated_at = NOW()
WHERE email = 'matt.lindop@zebra.associates';

-- Verify the update
SELECT id, email, role, is_active, organisation_id
FROM users
WHERE email = 'matt.lindop@zebra.associates';
"""
            print("📝 SQL Fix Script Generated:")
            print(fix_script)

            with open("fix_matt_role.sql", "w") as f:
                f.write(fix_script)
            print("✅ Fix script saved to: fix_matt_role.sql")

        if "account_inactive" in issues:
            activate_script = """
-- Activate Matt.Lindop account
UPDATE users
SET is_active = true, updated_at = NOW()
WHERE email = 'matt.lindop@zebra.associates';
"""
            print("📝 Account Activation Script:")
            print(activate_script)

    async def run_debug(self):
        """Run all debugging phases"""
        print("🚨 MATT.LINDOP ADMIN ACCESS DEBUG")
        print("Business Critical: £925K Zebra Associates opportunity")
        print("=" * 60)

        issues = []

        # Phase 1: Database check
        db_result = self.debug_database_direct()
        if db_result != "database_ok":
            issues.append(db_result)

        # Phase 2: API check
        api_result = await self.test_production_api()
        if api_result != "api_ok":
            issues.append(api_result)

        # Phase 3: Auth config check
        auth_result = self.check_auth_dependencies()
        if auth_result != "auth_config_ok":
            issues.append(auth_result)

        # Phase 4: Generate fixes
        if issues:
            self.generate_fix_script(issues)

        # Summary
        print("\n" + "=" * 60)
        print("DEBUG SUMMARY")
        print("=" * 60)

        if issues:
            print("❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")

            print("\n🔧 NEXT STEPS:")
            if "role_not_super_admin" in str(issues):
                print("   1. Run the generated SQL fix script")
                print("   2. Have Matt.Lindop logout and login again")
                print("   3. Test admin portal access")

        else:
            print("✅ All systems check out!")
            print("💡 If Matt still can't access admin portal:")
            print("   1. Clear browser cache completely")
            print("   2. Logout and login again")
            print("   3. Try incognito/private browsing mode")
            print("   4. Check browser console for JavaScript errors")

        print(f"\n📧 Contact: matt.lindop@zebra.associates")
        print(f"💰 Business Impact: £925K opportunity")


async def main():
    debugger = SimpleMattDebugger()
    await debugger.run_debug()


if __name__ == "__main__":
    asyncio.run(main())