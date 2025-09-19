#!/usr/bin/env python3
"""
Final diagnosis of Matt.Lindop's Feature Flags authorization issue
"""

import asyncio
import sys
import uuid

# Add the app directory to Python path
sys.path.append('/Users/matt/Sites/MarketEdge')

from app.models.user import User, UserRole
from app.auth.dependencies import require_admin, require_super_admin

def test_authorization_logic():
    """Test the authorization logic with Matt's user data"""

    print("=== FINAL MATT.LINDOP AUTHORIZATION DIAGNOSIS ===")
    print()

    # Create mock user objects for both Matt accounts
    matt_admin = User()
    matt_admin.id = uuid.UUID('6d662e21-d29b-4edd-ac75-5096c8e54c1f')
    matt_admin.email = 'matt.lindop@marketedge.com'
    matt_admin.role = UserRole.admin
    matt_admin.is_active = True
    matt_admin.organisation_id = uuid.UUID('835d4f24-cff2-43e8-a470-93216a3d99a3')

    matt_super = User()
    matt_super.id = uuid.UUID('f96ed2fb-0c58-445a-855a-e0d66f56fbcf')
    matt_super.email = 'matt.lindop@zebra.associates'
    matt_super.role = UserRole.super_admin
    matt_super.is_active = True
    matt_super.organisation_id = uuid.UUID('835d4f24-cff2-43e8-a470-93216a3d99a3')

    print("1. TESTING AUTHORIZATION LOGIC:")
    print("-" * 50)

    # Test require_admin logic
    print("Testing require_admin authorization:")

    # For admin user
    admin_roles = [UserRole.admin, UserRole.super_admin]
    admin_passes_require_admin = matt_admin.role in admin_roles
    print(f"  matt.lindop@marketedge.com (admin): {'✅ PASS' if admin_passes_require_admin else '❌ FAIL'}")

    # For super_admin user
    super_passes_require_admin = matt_super.role in admin_roles
    print(f"  matt.lindop@zebra.associates (super_admin): {'✅ PASS' if super_passes_require_admin else '❌ FAIL'}")

    print()
    print("Testing require_super_admin authorization:")

    # For admin user
    admin_passes_require_super_admin = matt_admin.role == UserRole.super_admin
    print(f"  matt.lindop@marketedge.com (admin): {'✅ PASS' if admin_passes_require_super_admin else '❌ FAIL'}")

    # For super_admin user
    super_passes_require_super_admin = matt_super.role == UserRole.super_admin
    print(f"  matt.lindop@zebra.associates (super_admin): {'✅ PASS' if super_passes_require_super_admin else '❌ FAIL'}")

    print()
    print("2. ERROR MESSAGE ANALYSIS:")
    print("-" * 50)

    # Check which function would log "Super admin role required"
    print("Sources of 'Super admin role required' error:")
    print("  ❌ NOT from require_admin() - logs 'Admin role required'")
    print("  ✅ FROM require_super_admin() - logs 'Super admin role required'")
    print()
    print("Conclusion: The error indicates require_super_admin() is being called")
    print("           NOT the Feature Flags endpoint (which uses require_admin)")

    print()
    print("3. POSSIBLE CAUSES:")
    print("-" * 50)

    print("A. Wrong Endpoint Being Called:")
    print("   - Frontend might be calling wrong admin endpoint")
    print("   - URLs that use require_super_admin:")
    print("     * /api/v1/organisations/* (create, update, list all)")
    print("     * /api/v1/user-management/* (cross-org user management)")
    print("     * /api/v1/database/* (database operations)")
    print()

    print("B. Request Routing Issue:")
    print("   - Frontend calls feature-flags but gets routed elsewhere")
    print("   - Middleware or proxy redirecting requests")
    print("   - CORS preflight hitting wrong endpoint")
    print()

    print("C. Auth0 Token Issue:")
    print("   - Token validation failing, hitting fallback auth logic")
    print("   - Wrong Matt.Lindop account being used")
    print("   - Tenant context mismatch causing re-authorization")

    print()
    print("4. DEBUGGING RECOMMENDATIONS:")
    print("-" * 50)

    print("IMMEDIATE ACTIONS:")
    print("1. Check browser developer tools network tab:")
    print("   - Verify exact URL being called")
    print("   - Check HTTP method (GET vs POST)")
    print("   - Inspect request headers and auth token")
    print()

    print("2. Check server logs for:")
    print("   - Complete stack trace of the error")
    print("   - Which endpoint path is being hit")
    print("   - Which user ID is being used")
    print("   - Auth0 token validation logs")
    print()

    print("3. Test with both Matt accounts:")
    print("   - Force login with matt.lindop@marketedge.com")
    print("   - Force login with matt.lindop@zebra.associates")
    print("   - Compare behavior between accounts")

    print()
    print("5. DEFINITIVE TEST:")
    print("-" * 50)

    print("To prove which endpoint is being called, temporarily add logging:")
    print("1. Add console.log() in frontend before API call")
    print("2. Add logger.info() in Feature Flags endpoint")
    print("3. Add logger.info() in require_admin function")
    print("4. Add logger.info() in require_super_admin function")

    print()
    print("6. EXPECTED RESULTS:")
    print("-" * 50)

    print("✅ BOTH Matt accounts should access Feature Flags successfully")
    print("✅ Feature Flags endpoint uses require_admin (accepts both roles)")
    print("❌ ERROR suggests wrong endpoint or auth flow being used")
    print()
    print("🎯 FOCUS: Identify which endpoint is actually being called")

if __name__ == "__main__":
    test_authorization_logic()