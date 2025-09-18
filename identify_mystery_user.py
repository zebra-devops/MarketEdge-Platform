#!/usr/bin/env python3
"""
Identify the mystery user causing the super_admin error
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.database import get_async_session_local
from app.models.user import User, UserRole
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def identify_mystery_user():
    """Identify the user with ID ebc9567a-bbf8-4ddf-8eee-7635fba62363"""
    mystery_user_id = "ebc9567a-bbf8-4ddf-8eee-7635fba62363"
    print(f"🔍 Investigating mystery user: {mystery_user_id}")

    async_session_maker = get_async_session_local()
    async with async_session_maker() as db:
        # Find mystery user by ID
        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.id == mystery_user_id)
        )
        mystery_user = result.scalar_one_or_none()

        if not mystery_user:
            print("❌ Mystery user not found in database")
            print("   This could indicate:")
            print("   - User deleted from database")
            print("   - Stale token with old user ID")
            print("   - Error in log message user ID")

            # Let's find users with 'admin' role to see potential candidates
            print(f"\n🔍 Finding users with 'admin' role:")
            admin_result = await db.execute(
                select(User)
                .options(selectinload(User.organisation))
                .filter(User.role == UserRole.admin)
            )
            admin_users = admin_result.scalars().all()

            if admin_users:
                print(f"Found {len(admin_users)} users with 'admin' role:")
                for user in admin_users:
                    print(f"   - {user.email} (ID: {user.id}) - Org: {user.organisation.name if user.organisation else 'None'}")
            else:
                print("   No users found with 'admin' role")

            return

        print(f"✅ Found mystery user:")
        print(f"   - ID: {mystery_user.id}")
        print(f"   - Email: {mystery_user.email}")
        print(f"   - Name: {mystery_user.first_name} {mystery_user.last_name}")
        print(f"   - Current Role: {mystery_user.role.value}")
        print(f"   - Is Active: {mystery_user.is_active}")
        print(f"   - Organisation: {mystery_user.organisation.name if mystery_user.organisation else 'None'}")
        print(f"   - Organisation ID: {mystery_user.organisation_id}")

        # Analyze the role
        if mystery_user.role == UserRole.admin:
            print(f"\n⚠️  Analysis:")
            print(f"   - This user has 'admin' role but tried to access super_admin endpoint")
            print(f"   - Likely tried to access /api/v1/admin/users or /api/v1/organisations endpoints")
            print(f"   - These endpoints require super_admin role specifically")

            print(f"\n🔧 Resolution Options:")
            print(f"   1. Promote user to super_admin role (if business justified)")
            print(f"   2. Direct user to Feature Flags endpoints (only need admin role)")
            print(f"   3. Explain endpoint access requirements")

        elif mystery_user.role == UserRole.super_admin:
            print(f"\n🤔 Unexpected:")
            print(f"   - User has super_admin role but error shows 'admin'")
            print(f"   - Possible token/session synchronization issue")
            print(f"   - User may need to re-authenticate")

if __name__ == "__main__":
    asyncio.run(identify_mystery_user())