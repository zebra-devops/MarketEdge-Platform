#!/usr/bin/env python3
"""
Check Matt Lindop's current role in the database
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

async def check_matt_role():
    """Check Matt Lindop's current role in the database"""
    print("🔍 Checking Matt Lindop's current role...")

    async_session_maker = get_async_session_local()
    async with async_session_maker() as db:
        # Find Matt by email
        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.email == "matt.lindop@zebra.associates")
        )
        matt = result.scalar_one_or_none()

        if not matt:
            print("❌ Matt Lindop not found in database")
            return

        print(f"✅ Found Matt Lindop:")
        print(f"   - ID: {matt.id}")
        print(f"   - Email: {matt.email}")
        print(f"   - Name: {matt.first_name} {matt.last_name}")
        print(f"   - Current Role: {matt.role.value}")
        print(f"   - Is Active: {matt.is_active}")
        print(f"   - Organisation: {matt.organisation.name if matt.organisation else 'None'}")
        print(f"   - Organisation ID: {matt.organisation_id}")

        # Check what roles are available
        print(f"\n📋 Available UserRole enum values:")
        for role in UserRole:
            marker = "🎯" if role == matt.role else "   "
            print(f"{marker} {role.value}")

        # Check if matt.role is super_admin
        is_super_admin = matt.role == UserRole.super_admin
        print(f"\n🔐 Role Analysis:")
        print(f"   - Has super_admin role: {is_super_admin}")
        print(f"   - Has admin role: {matt.role == UserRole.admin}")
        print(f"   - Current role enum: UserRole.{matt.role.name}")

        # Check if we need to update role
        if matt.role == UserRole.admin:
            print(f"\n⚠️  Issue Identified:")
            print(f"   - Matt has 'admin' role but needs 'super_admin' for Feature Flags access")
            print(f"   - The error message was incorrect - super_admin IS a valid role")
            print(f"   - Solution: Update Matt's role from 'admin' to 'super_admin'")

            # Offer to update the role
            response = input("\n🤔 Update Matt's role to super_admin? (y/n): ")
            if response.lower() == 'y':
                matt.role = UserRole.super_admin
                await db.commit()
                print(f"✅ Updated Matt's role to super_admin")
            else:
                print(f"❌ Role not updated")

        elif matt.role == UserRole.super_admin:
            print(f"\n✅ Matt already has super_admin role")
            print(f"   - The issue might be elsewhere in the authentication flow")
        else:
            print(f"\n⚠️  Unexpected role: {matt.role.value}")

if __name__ == "__main__":
    asyncio.run(check_matt_role())