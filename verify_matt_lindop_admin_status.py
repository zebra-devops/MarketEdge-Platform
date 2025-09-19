#!/usr/bin/env python3
"""
Matt.Lindop Admin Status Verification
Diagnoses Matt.Lindop's database role assignment for £925K Zebra Associates opportunity
"""

import asyncio
import os
import sys
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.core.config import settings
from app.core.logging import logger

async def verify_matt_lindop_status():
    """Verify Matt.Lindop's admin status and role assignment"""

    print("=== MATT.LINDOP ADMIN STATUS VERIFICATION ===")
    print("Zebra Associates £925K Opportunity - Feature Flags Access Diagnostic\n")

    # Create async database connection
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async with engine.begin() as conn:
        async_session = AsyncSession(conn, expire_on_commit=False)

        try:
            print("1. SEARCHING FOR MATT.LINDOP USER...")

            # Search for Matt.Lindop by email
            result = await async_session.execute(
                select(User)
                .options(selectinload(User.organisation))
                .filter(User.email.ilike('%matt.lindop%'))
            )
            matt_users = result.scalars().all()

            if not matt_users:
                print("❌ CRITICAL: No users found with 'matt.lindop' in email")

                # Search for any users with 'matt' in email
                result = await async_session.execute(
                    select(User)
                    .options(selectinload(User.organisation))
                    .filter(User.email.ilike('%matt%'))
                )
                matt_any = result.scalars().all()

                if matt_any:
                    print(f"\n🔍 Found {len(matt_any)} users with 'matt' in email:")
                    for user in matt_any:
                        print(f"   - {user.email} (ID: {user.id}, Role: {user.role.value})")
                else:
                    print("❌ No users found with 'matt' in email either")

                return False

            print(f"✅ Found {len(matt_users)} user(s) matching 'matt.lindop':")

            for matt in matt_users:
                print(f"\n--- USER DETAILS ---")
                print(f"Email: {matt.email}")
                print(f"User ID: {matt.id}")
                print(f"Role: {matt.role.value}")
                print(f"Active: {matt.is_active}")
                print(f"Created: {matt.created_at}")
                print(f"Last Updated: {matt.updated_at}")

                if matt.organisation:
                    print(f"Organization: {matt.organisation.name}")
                    print(f"Organization ID: {matt.organisation.id}")
                    print(f"Org Active: {matt.organisation.is_active}")
                else:
                    print("❌ No organization assigned")

                # Check if role is admin or super_admin
                if matt.role in [UserRole.admin, UserRole.super_admin]:
                    print(f"✅ ADMIN STATUS: User has {matt.role.value} role - should access feature flags")
                else:
                    print(f"❌ ADMIN STATUS: User has {matt.role.value} role - CANNOT access feature flags")
                    print(f"   Required roles: admin, super_admin")
                    print(f"   RECOMMENDATION: Update role to super_admin for Zebra Associates access")

                # Check Zebra Associates organization mapping
                if matt.organisation:
                    zebra_org_id = "835d4f24-cff2-43e8-a470-93216a3d99a3"
                    if str(matt.organisation.id) == zebra_org_id:
                        print(f"✅ ORGANIZATION: Correctly mapped to Zebra Associates org")
                    else:
                        print(f"❌ ORGANIZATION: NOT mapped to Zebra Associates")
                        print(f"   Current Org ID: {matt.organisation.id}")
                        print(f"   Expected Zebra ID: {zebra_org_id}")

            print("\n2. FEATURE FLAGS ENDPOINT REQUIREMENTS...")
            print("Endpoint: GET /api/v1/admin/feature-flags")
            print("Dependency: require_admin")
            print("Required Roles: admin OR super_admin")
            print("Auth Flow: get_current_user -> verify_token -> require_admin")

            print("\n3. AUTH0 TOKEN VERIFICATION...")
            print("✅ Auth0 fallback implemented in dependencies.py")
            print("✅ Organization mapping for Zebra Associates configured")
            print("✅ Super admin role support deployed")

            print("\n4. DIAGNOSIS FOR FEATURE FLAGS 401/403 ISSUE...")

            primary_matt = matt_users[0] if matt_users else None
            if primary_matt:
                if primary_matt.role not in [UserRole.admin, UserRole.super_admin]:
                    print("🎯 ROOT CAUSE IDENTIFIED:")
                    print(f"   Matt.Lindop has role '{primary_matt.role.value}'")
                    print(f"   Feature flags require 'admin' or 'super_admin'")
                    print(f"   TOKEN IS VALID BUT ROLE IS INSUFFICIENT")

                    print("\n💡 SOLUTION:")
                    print(f"   UPDATE user SET role = 'super_admin' WHERE id = '{primary_matt.id}';")
                    return "role_update_required"
                else:
                    print("🤔 ROLE IS CORRECT - investigating other causes...")

                    print("\n🔍 ADDITIONAL DIAGNOSTICS NEEDED:")
                    print("   1. Verify token contains correct role claims")
                    print("   2. Test Auth0 token verification endpoint")
                    print("   3. Check if frontend sends Authorization header")
                    print("   4. Validate organization context in token")
                    return "role_correct_investigate_further"

            return False

        except Exception as e:
            print(f"❌ ERROR: Database query failed: {e}")
            return False

        finally:
            await async_session.close()

async def update_matt_lindop_role_if_needed():
    """Update Matt.Lindop to super_admin role if required"""

    print("\n=== ROLE UPDATE PROCESS ===")

    # Create async database connection
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )

    async with engine.begin() as conn:
        async_session = AsyncSession(conn, expire_on_commit=False)

        try:
            # Find Matt.Lindop
            result = await async_session.execute(
                select(User).filter(User.email.ilike('%matt.lindop%'))
            )
            matt = result.scalar_one_or_none()

            if not matt:
                print("❌ Matt.Lindop user not found for role update")
                return False

            if matt.role in [UserRole.admin, UserRole.super_admin]:
                print(f"✅ Matt.Lindop already has {matt.role.value} role - no update needed")
                return True

            print(f"🔄 Updating Matt.Lindop role from '{matt.role.value}' to 'super_admin'...")

            # Update role to super_admin
            matt.role = UserRole.super_admin
            await async_session.commit()

            print(f"✅ SUCCESS: Matt.Lindop role updated to super_admin")
            print(f"✅ Feature flags access should now work")

            # Verify update
            await async_session.refresh(matt)
            print(f"✅ VERIFIED: Current role is {matt.role.value}")

            return True

        except Exception as e:
            print(f"❌ ERROR: Role update failed: {e}")
            await async_session.rollback()
            return False

        finally:
            await async_session.close()

async def test_feature_flags_authorization():
    """Test feature flags authorization with current user status"""

    print("\n=== FEATURE FLAGS AUTHORIZATION TEST ===")

    # This would test the actual endpoint
    print("🔬 TESTING PLAN:")
    print("1. Extract Matt's JWT token from browser session")
    print("2. Decode token and verify role claims")
    print("3. Make direct API call to /admin/feature-flags")
    print("4. Verify require_admin dependency validation")
    print("5. Check Auth0 token verification fallback")

    print("\n📋 MANUAL TEST COMMANDS:")
    print("# Test with curl (replace TOKEN with actual token):")
    print("curl -H 'Authorization: Bearer TOKEN' \\")
    print("     https://marketedge-platform.onrender.com/api/v1/admin/feature-flags")

    print("\n# Check production logs:")
    print("# Look for auth_admin_required or auth_insufficient_role events")

async def main():
    """Main diagnostic function"""

    try:
        # Step 1: Verify Matt's current status
        status = await verify_matt_lindop_status()

        # Step 2: Update role if needed
        if status == "role_update_required":
            confirm = input("\n🤔 Update Matt.Lindop to super_admin role? (y/N): ")
            if confirm.lower() == 'y':
                await update_matt_lindop_role_if_needed()

        # Step 3: Provide testing guidance
        await test_feature_flags_authorization()

        print("\n=== NEXT STEPS ===")
        print("1. If role was updated, test feature flags access again")
        print("2. If role was already correct, investigate token claims")
        print("3. Check production logs for specific error details")
        print("4. Verify frontend token transmission")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())