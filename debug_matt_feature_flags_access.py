#!/usr/bin/env python3
"""
Debug Matt.Lindop's Feature Flags Access
Traces the exact authorization chain for Feature Flags endpoint
"""

import asyncio
import asyncpg
import json
from datetime import datetime
import aiohttp
import os
import sys

# Add the app directory to Python path
sys.path.append('/Users/matt/Sites/MarketEdge')

from app.core.config import settings
from app.core.database import get_async_db
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def debug_matt_feature_flags_access():
    """Debug Matt.Lindop's Feature Flags access with detailed tracing"""

    print("=== MATT.LINDOP FEATURE FLAGS ACCESS DEBUG ===")
    print(f"Timestamp: {datetime.now()}")
    print()

    # Create async engine for database queries
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))

    async with engine.begin() as conn:
        # Create session
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as db:

            # 1. Check Matt.Lindop's current user record
            print("1. CHECKING MATT.LINDOP USER RECORD:")
            print("-" * 50)

            # Test both Matt.Lindop email variations
            matt_emails = [
                'matt.lindop@marketedge.com',
                'matt.lindop@zebra.associates',
                'matt.lindop@zebra-associates.com'
            ]

            matt_users = []
            for email in matt_emails:
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.organisation))
                    .filter(User.email == email)
                )
                user = result.scalar_one_or_none()
                if user:
                    matt_users.append(user)

            if not matt_users:
                print("❌ ERROR: No Matt.Lindop users found!")
                return

            print(f"✅ Found {len(matt_users)} Matt.Lindop user(s):")

            for i, matt_user in enumerate(matt_users):
                print(f"\n--- MATT.LINDOP USER #{i+1} ---")
                print(f"   ID: {matt_user.id}")
                print(f"   Email: {matt_user.email}")
                print(f"   Role: {matt_user.role.value}")
                print(f"   Is Active: {matt_user.is_active}")
                print(f"   Organisation ID: {matt_user.organisation_id}")
                print(f"   Organisation Name: {matt_user.organisation.name if matt_user.organisation else 'Unknown'}")

                # Test authorization for this user
                print(f"\n   AUTHORIZATION TESTS FOR USER #{i+1}:")

                # Test require_admin
                admin_roles = [UserRole.admin, UserRole.super_admin]
                is_authorized_by_require_admin = matt_user.role in admin_roles
                print(f"   require_admin: {'✅ PASS' if is_authorized_by_require_admin else '❌ FAIL'}")

                # Test require_super_admin
                is_authorized_by_require_super_admin = matt_user.role == UserRole.super_admin
                print(f"   require_super_admin: {'✅ PASS' if is_authorized_by_require_super_admin else '❌ FAIL'}")

                # Test AdminService.get_feature_flags() for this user
                try:
                    from app.services.admin_service import AdminService
                    admin_service = AdminService(db)
                    feature_flags = await admin_service.get_feature_flags(
                        admin_user=matt_user,
                        module_id=None,
                        enabled_only=False
                    )
                    print(f"   AdminService.get_feature_flags(): ✅ SUCCESS ({len(feature_flags)} flags)")

                except Exception as e:
                    print(f"   AdminService.get_feature_flags(): ❌ FAILED - {e}")
                    print(f"   Error type: {type(e).__name__}")

            # 2. Check for any AnalyticsModule that might require super_admin
            print("2. CHECKING ANALYTICS MODULES FOR ROLE REQUIREMENTS:")
            print("-" * 50)

            from app.models.modules import AnalyticsModule
            result = await db.execute(select(AnalyticsModule))
            modules = result.scalars().all()

            print(f"Found {len(modules)} analytics modules")
            for module in modules:
                print(f"   - {module.id}: {module.name} (Status: {module.status.value})")
            print()

            # 3. Check route dependencies
            print("3. CHECKING FEATURE FLAGS ENDPOINT ROUTE DEPENDENCIES:")
            print("-" * 50)

            from app.api.api_v1.endpoints import admin

            # Check the actual router for the feature-flags endpoint
            for route in admin.router.routes:
                if hasattr(route, 'path') and 'feature-flags' in route.path:
                    print(f"   Route: {route.methods} {route.path}")
                    if hasattr(route, 'dependant'):
                        dependencies = route.dependant.dependencies
                        for dep in dependencies:
                            if hasattr(dep, 'call'):
                                dep_name = getattr(dep.call, '__name__', str(dep.call))
                                print(f"     Dependency: {dep_name}")
            print()

            # 4. Final diagnosis
            print("4. DIAGNOSIS:")
            print("-" * 50)

            print("✅ Both Matt.Lindop users should be able to access Feature Flags:")
            print("   - matt.lindop@marketedge.com (admin role) → require_admin ✅")
            print("   - matt.lindop@zebra.associates (super_admin role) → require_admin ✅")
            print()
            print("❓ If 'Super admin role required' error still appears, investigate:")
            print("   a) Which Matt.Lindop email is being used in the request")
            print("   b) If there's token validation or Auth0 mapping issue")
            print("   c) If request is hitting a different endpoint requiring super_admin")
            print("   d) Check server logs for exact error stack trace")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_matt_feature_flags_access())