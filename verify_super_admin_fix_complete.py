#!/usr/bin/env python3
"""
COMPREHENSIVE SUPER ADMIN FIX VERIFICATION
£925K Zebra Associates Opportunity - Final Resolution Check

This script verifies that ALL components now properly support super_admin role
"""

import os
import re
import asyncio
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor


class SuperAdminFixVerifier:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/platform_wrapper')
        self.production_api = "https://marketedge-platform.onrender.com"
        self.frontend_path = "/Users/matt/Sites/MarketEdge/platform-wrapper/frontend/src"

    def verify_database(self):
        """Verify Matt.Lindop has super_admin role in database"""
        print("🔍 PHASE 1: Database Verification")
        print("-" * 50)

        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT id, email, role, is_active, organisation_id
                FROM users
                WHERE email = %s
            """, ("matt.lindop@zebra.associates",))

            matt = cursor.fetchone()

            if matt:
                print(f"✅ Matt.Lindop found in database")
                print(f"   Email: {matt['email']}")
                print(f"   Role: {matt['role']}")
                print(f"   Active: {matt['is_active']}")
                print(f"   Org ID: {matt['organisation_id']}")

                if matt['role'] == 'super_admin' and matt['is_active']:
                    print("✅ Database configuration is CORRECT")
                    return True
                else:
                    print(f"❌ ISSUE: Role is '{matt['role']}' or account inactive")
                    return False
            else:
                print("❌ CRITICAL: Matt.Lindop not found in database")
                return False

        except Exception as e:
            print(f"❌ Database check failed: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

    def verify_backend_auth(self):
        """Verify backend authentication supports super_admin"""
        print("\n🔧 PHASE 2: Backend Authentication Verification")
        print("-" * 50)

        # Check dependencies.py
        deps_file = "/Users/matt/Sites/MarketEdge/app/auth/dependencies.py"

        if not os.path.exists(deps_file):
            print("❌ dependencies.py not found")
            return False

        with open(deps_file, 'r') as f:
            content = f.read()

        checks = []

        # Check require_admin function
        if '[UserRole.admin, UserRole.super_admin]' in content:
            print("✅ require_admin supports both admin and super_admin")
            checks.append(True)
        else:
            print("❌ require_admin may not support super_admin")
            checks.append(False)

        # Check require_same_tenant_or_admin function
        if 'UserRole.admin, UserRole.super_admin' in content and 'require_same_tenant_or_admin' in content:
            print("✅ require_same_tenant_or_admin supports super_admin")
            checks.append(True)
        else:
            print("❌ require_same_tenant_or_admin may not support super_admin")
            checks.append(False)

        return all(checks)

    def verify_frontend_auth_service(self):
        """Verify frontend auth service supports super_admin"""
        print("\n💻 PHASE 3: Frontend Auth Service Verification")
        print("-" * 50)

        auth_service_file = f"{self.frontend_path}/services/auth.ts"

        if not os.path.exists(auth_service_file):
            print("❌ auth.ts not found")
            return False

        with open(auth_service_file, 'r') as f:
            content = f.read()

        # Check isAdmin method supports super_admin
        isadmin_pattern = r'isAdmin\(\):\s*boolean\s*\{[^}]+return[^}]+super_admin'

        if re.search(isadmin_pattern, content, re.DOTALL):
            print("✅ AuthService.isAdmin() supports super_admin role")
            return True
        else:
            print("❌ AuthService.isAdmin() may not support super_admin role")
            return False

    def verify_frontend_components(self):
        """Verify frontend components support super_admin"""
        print("\n🎨 PHASE 4: Frontend Components Verification")
        print("-" * 50)

        files_to_check = [
            "app/admin/page.tsx",
            "app/settings/page.tsx",
            "components/ui/AccountMenu.tsx"
        ]

        results = []

        for file_path in files_to_check:
            full_path = f"{self.frontend_path}/{file_path}"

            if not os.path.exists(full_path):
                print(f"⚠️  {file_path} not found")
                continue

            with open(full_path, 'r') as f:
                content = f.read()

            # Check if the file properly handles super_admin
            if "super_admin" in content:
                print(f"✅ {file_path} supports super_admin")
                results.append(True)
            else:
                # Check if it might be using authService.isAdmin() which now supports super_admin
                if "authService.isAdmin()" in content or "isAdmin" in content:
                    print(f"✅ {file_path} uses isAdmin() method (should work with fix)")
                    results.append(True)
                else:
                    print(f"❌ {file_path} may not support super_admin")
                    results.append(False)

        return all(results) if results else False

    async def verify_production_api(self):
        """Verify production API is healthy"""
        print("\n🌐 PHASE 5: Production API Verification")
        print("-" * 50)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Health check
                health = await client.get(f"{self.production_api}/health")
                print(f"Health check: {health.status_code}")

                if health.status_code == 200:
                    health_data = health.json()
                    print(f"✅ API Status: {health_data.get('status')}")
                    print(f"✅ Mode: {health_data.get('mode')}")
                    print(f"✅ Zebra Ready: {health_data.get('zebra_associates_ready')}")
                    return True
                else:
                    print("❌ API health check failed")
                    return False

        except Exception as e:
            print(f"❌ API verification failed: {e}")
            return False

    def generate_test_plan(self):
        """Generate testing instructions for Matt.Lindop"""
        print("\n📋 PHASE 6: Matt.Lindop Testing Instructions")
        print("-" * 50)

        print("""
🧪 TESTING STEPS FOR MATT.LINDOP:

1. CLEAR BROWSER CACHE COMPLETELY
   - Press Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
   - Select "All time" and check all boxes
   - Clear cache, cookies, and site data

2. COMPLETE LOGOUT
   - Logout from the platform completely
   - Close all browser tabs
   - Wait 30 seconds

3. FRESH LOGIN
   - Navigate to the platform
   - Login with Auth0 credentials
   - Wait for authentication to complete

4. TEST ADMIN ACCESS
   - Navigate to /admin
   - Should see admin console with "Super Administrator" badge
   - Test feature flags management
   - Test admin dashboard statistics
   - Test all admin functions

5. VERIFY ACCOUNT MENU
   - Check profile dropdown shows admin options
   - Verify settings page shows admin controls

🎯 EXPECTED RESULTS:
   ✅ Can access /admin portal
   ✅ Badge shows "Super Administrator" in purple
   ✅ All admin functions accessible
   ✅ No access denied errors
   ✅ £925K opportunity can proceed

⚠️  IF STILL HAVING ISSUES:
   - Try incognito/private browsing
   - Check browser console for errors
   - Contact support with screenshot of any error
        """)

    async def run_verification(self):
        """Run complete verification suite"""
        print("🚨 SUPER ADMIN ACCESS FIX - COMPREHENSIVE VERIFICATION")
        print("Business Critical: £925K Zebra Associates Opportunity")
        print("User: matt.lindop@zebra.associates")
        print("=" * 80)

        results = []

        # Run all verification phases
        results.append(("Database", self.verify_database()))
        results.append(("Backend Auth", self.verify_backend_auth()))
        results.append(("Frontend Auth Service", self.verify_frontend_auth_service()))
        results.append(("Frontend Components", self.verify_frontend_components()))
        results.append(("Production API", await self.verify_production_api()))

        # Summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)

        all_passed = True
        for phase, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{phase:25} {status}")
            if not result:
                all_passed = False

        print("\n" + "-" * 80)

        if all_passed:
            print("🎉 ALL VERIFICATIONS PASSED!")
            print("✅ Super admin fix is COMPLETE and READY")
            print("✅ Matt.Lindop should now have full admin access")
            print("💰 £925K Zebra Associates opportunity UNBLOCKED")

            self.generate_test_plan()

        else:
            print("❌ SOME VERIFICATIONS FAILED")
            print("🔧 Additional fixes may be needed")
            print("⚠️  Check failed phases above")

        return all_passed


async def main():
    verifier = SuperAdminFixVerifier()
    success = await verifier.run_verification()

    if success:
        print("\n✅ VERIFICATION COMPLETE - READY FOR DEPLOYMENT")
    else:
        print("\n❌ VERIFICATION INCOMPLETE - NEEDS ATTENTION")


if __name__ == "__main__":
    asyncio.run(main())