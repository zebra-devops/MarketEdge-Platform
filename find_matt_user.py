#!/usr/bin/env python3
"""
Find Matt user variations in the database
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
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy import select

async def find_matt_user():
    """Find Matt user with various email patterns"""

    print("=== FINDING MATT USER VARIATIONS ===")

    # Create async engine for database queries
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))

    async with AsyncSession(engine) as db:

        # Search for users with "matt" in email
        print("1. SEARCHING FOR USERS WITH 'matt' IN EMAIL:")
        print("-" * 50)

        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.email.ilike('%matt%'))
        )
        matt_users = result.scalars().all()

        if matt_users:
            for user in matt_users:
                print(f"✅ Found: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role.value}")
                print(f"   Organisation: {user.organisation.name if user.organisation else 'None'}")
                print(f"   Active: {user.is_active}")
                print()
        else:
            print("❌ No users with 'matt' found")

        # Search for users with "lindop" in email
        print("2. SEARCHING FOR USERS WITH 'lindop' IN EMAIL:")
        print("-" * 50)

        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.email.ilike('%lindop%'))
        )
        lindop_users = result.scalars().all()

        if lindop_users:
            for user in lindop_users:
                print(f"✅ Found: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role.value}")
                print(f"   Organisation: {user.organisation.name if user.organisation else 'None'}")
                print(f"   Active: {user.is_active}")
                print()
        else:
            print("❌ No users with 'lindop' found")

        # Search for users with "zebra" in email
        print("3. SEARCHING FOR USERS WITH 'zebra' IN EMAIL:")
        print("-" * 50)

        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.email.ilike('%zebra%'))
        )
        zebra_users = result.scalars().all()

        if zebra_users:
            for user in zebra_users:
                print(f"✅ Found: {user.email}")
                print(f"   ID: {user.id}")
                print(f"   Role: {user.role.value}")
                print(f"   Organisation: {user.organisation.name if user.organisation else 'None'}")
                print(f"   Active: {user.is_active}")
                print()
        else:
            print("❌ No users with 'zebra' found")

        # List all users to see what exists
        print("4. LISTING ALL USERS IN DATABASE:")
        print("-" * 50)

        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .limit(10)
        )
        all_users = result.scalars().all()

        if all_users:
            for user in all_users:
                print(f"   {user.email} (Role: {user.role.value}, Org: {user.organisation.name if user.organisation else 'None'})")
        else:
            print("❌ No users found in database")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(find_matt_user())