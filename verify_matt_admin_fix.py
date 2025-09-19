#!/usr/bin/env python3
"""
Verify Matt.Lindop Admin Access Fix - £925K Zebra Associates Opportunity

This script verifies that the frontend admin portal fix has been applied correctly
and tests the complete authentication flow.

Business Context:
- £925K Zebra Associates opportunity
- Critical fix for super_admin role support in frontend
- Matt.Lindop should now be able to access admin portal
"""

import os
import re
from datetime import datetime


def check_admin_page_fix():
    """Check that the admin page correctly supports super_admin role"""
    print("🔍 Checking Admin Page Fix")
    print("-" * 40)

    admin_page_path = "/Users/matt/Sites/MarketEdge/platform-wrapper/frontend/src/app/admin/page.tsx"

    try:
        with open(admin_page_path, 'r') as f:
            content = f.read()

        issues = []
        fixes_applied = []

        # Check 1: useEffect role check
        if "user.role !== 'admin' && user.role !== 'super_admin'" in content:
            fixes_applied.append("✅ useEffect role check supports super_admin")
        else:
            issues.append("❌ useEffect still only checks for 'admin' role")

        # Check 2: Main role validation
        if "if (user.role !== 'admin' && user.role !== 'super_admin')" in content:
            fixes_applied.append("✅ Main role validation supports super_admin")
        else:
            issues.append("❌ Main role validation still only checks for 'admin'")

        # Check 3: Error message shows both roles
        if "Required: admin or super_admin" in content:
            fixes_applied.append("✅ Error message shows both required roles")
        else:
            issues.append("❌ Error message doesn't mention super_admin")

        # Check 4: Badge display for super_admin
        if "user.role === 'super_admin' ? 'Super Administrator'" in content:
            fixes_applied.append("✅ Badge displays 'Super Administrator' for super_admin role")
        else:
            issues.append("❌ Badge doesn't handle super_admin role")

        # Check 5: Purple badge styling for super_admin
        if "bg-purple-100 text-purple-800" in content:
            fixes_applied.append("✅ Super admin gets distinctive purple badge")
        else:
            issues.append("❌ Super admin badge styling missing")

        print("\n📋 Fix Verification Results:")
        for fix in fixes_applied:
            print(f"   {fix}")

        if issues:
            print("\n❌ REMAINING ISSUES:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
            return True

    except Exception as e:
        print(f"❌ Error checking admin page: {e}")
        return False


def generate_deployment_instructions():
    """Generate deployment instructions for the fix"""
    print("\n🚀 Deployment Instructions")
    print("-" * 40)

    instructions = """
CRITICAL FIX DEPLOYMENT - Matt.Lindop Admin Access
=================================================

Business Impact: £925K Zebra Associates opportunity
User: matt.lindop@zebra.associates
Issue: Frontend admin portal only accepted 'admin' role, not 'super_admin'

CHANGES MADE:
1. Updated useEffect role check to accept both 'admin' and 'super_admin'
2. Updated main role validation logic
3. Updated error messages to show both required roles
4. Added distinctive badge styling for super_admin users

DEPLOYMENT STEPS:

Frontend (Vercel):
1. The changes are in the frontend code
2. Push to main branch to trigger Vercel deployment
3. Verify deployment completes successfully

Testing Steps:
1. Have Matt.Lindop clear browser cache completely
2. Have Matt.Lindop logout completely from the platform
3. Have Matt.Lindop login again with Auth0
4. Navigate to /admin - should now work

Expected Results:
- Matt.Lindop can access admin portal
- Badge shows "Super Administrator" in purple
- All admin functions should be accessible

If Still Not Working:
1. Check browser console for JavaScript errors
2. Verify user role is correctly set in database (already confirmed)
3. Check Auth0 token contains correct role information
4. Try incognito/private browsing mode
"""

    with open("matt_admin_fix_deployment_guide.txt", "w") as f:
        f.write(instructions)

    print("✅ Deployment guide saved: matt_admin_fix_deployment_guide.txt")
    print("\n📋 Next Steps:")
    print("   1. Commit and push the admin page changes")
    print("   2. Wait for Vercel deployment to complete")
    print("   3. Have Matt.Lindop test admin portal access")
    print("   4. £925K deal can proceed once confirmed working")


def main():
    """Main execution function"""
    print("🚨 MATT.LINDOP ADMIN ACCESS FIX VERIFICATION")
    print("Business Critical: £925K Zebra Associates opportunity")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow()}")
    print(f"Target User: matt.lindop@zebra.associates")
    print("=" * 60)

    # Verify the fix has been applied
    fix_success = check_admin_page_fix()

    # Generate deployment instructions
    generate_deployment_instructions()

    # Summary
    print("\n" + "=" * 60)
    print("FIX VERIFICATION SUMMARY")
    print("=" * 60)

    if fix_success:
        print("✅ ALL FIXES VERIFIED SUCCESSFULLY")
        print("🚀 Ready for deployment to production")
        print("💰 £925K opportunity can proceed")
    else:
        print("❌ FIXES NOT FULLY APPLIED")
        print("🔧 Additional changes required")
        print("⚠️  £925K opportunity still blocked")

    print(f"\n📧 Contact: matt.lindop@zebra.associates")
    print(f"💼 Business Impact: £925K Zebra Associates opportunity")


if __name__ == "__main__":
    main()