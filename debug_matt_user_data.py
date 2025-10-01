#!/usr/bin/env python3
"""
Debug script to investigate user data disconnect for matt.lindop@zebra.associates
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User, UserRole
from app.models.user_application_access import UserApplicationAccess, ApplicationType
from app.models.organisation import Organisation
from app.core.database import get_async_db

async def main():
    """Main debug function to investigate matt.lindop user data"""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        sys.exit(1)

    # Convert postgres:// to postgresql+asyncpg:// for async
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://')
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

    # Create async engine
    engine = create_async_engine(database_url)

    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("🔍 DEBUGGING USER DATA DISCONNECT FOR matt.lindop@zebra.associates")
    print("=" * 80)

    try:
        async with async_session() as db:
            # 1. Get user data directly from database
            print("1. DIRECT DATABASE QUERY:")
            result = await db.execute(
                text("""
                    SELECT u.id, u.email, u.first_name, u.last_name, u.role,
                           u.organisation_id, u.is_active, u.created_at,
                           o.name as org_name
                    FROM users u
                    LEFT JOIN organisations o ON u.organisation_id = o.id
                    WHERE u.email = 'matt.lindop@zebra.associates'
                """)
            )
            user_row = result.fetchone()

            if user_row:
                print(f"   ✅ User found in database:")
                print(f"   📧 Email: {user_row.email}")
                print(f"   👤 Name: {user_row.first_name} {user_row.last_name}")
                print(f"   🎭 Role: {user_row.role}")
                print(f"   🏢 Organization: {user_row.org_name} ({user_row.organisation_id})")
                print(f"   🔑 Active: {user_row.is_active}")
                print(f"   📅 Created: {user_row.created_at}")
            else:
                print("   ❌ User NOT found in database!")
                return

            print()

            # 2. Check application access directly
            print("2. APPLICATION ACCESS FROM DATABASE:")
            access_result = await db.execute(
                text("""
                    SELECT uaa.application, uaa.has_access, uaa.granted_at, uaa.granted_by
                    FROM user_application_access uaa
                    JOIN users u ON uaa.user_id = u.id
                    WHERE u.email = 'matt.lindop@zebra.associates'
                    ORDER BY uaa.application
                """)
            )
            access_rows = access_result.fetchall()

            if access_rows:
                print("   ✅ Application access records found:")
                for row in access_rows:
                    status = "✅ GRANTED" if row.has_access else "❌ DENIED"
                    print(f"   📱 {row.application}: {status} (granted: {row.granted_at})")
            else:
                print("   ❌ NO application access records found!")

            print()

            # 3. Test what the user management API endpoint returns
            print("3. SIMULATING USER MANAGEMENT API CALL:")
            print("   Testing: /admin/users (super admin endpoint)")

            # Get user with relationships loaded (similar to API)
            from sqlalchemy.orm import joinedload
            from sqlalchemy import select

            query = select(User).options(
                joinedload(User.organisation),
                joinedload(User.application_access),
                joinedload(User.invitations)
            ).filter(User.email == 'matt.lindop@zebra.associates')

            result = await db.execute(query)
            user = result.unique().scalar_one_or_none()

            if user:
                print(f"   ✅ User found via ORM:")
                print(f"   📧 Email: {user.email}")
                print(f"   🎭 Role: {user.role.value if hasattr(user.role, 'value') else user.role}")
                print(f"   🏢 Organization: {user.organisation.name if user.organisation else 'None'}")

                # Check application access via relationships
                print("   📱 Application Access via ORM:")
                if user.application_access:
                    for access in user.application_access:
                        app_name = access.application.value if hasattr(access.application, 'value') else access.application
                        status = "✅ GRANTED" if access.has_access else "❌ DENIED"
                        print(f"      {app_name}: {status}")
                else:
                    print("      ❌ NO application access records via ORM!")

                print()

                # 4. Format the response like the API does
                print("4. FORMATTED API RESPONSE (like _format_user_response):")

                # Get latest invitation status
                invitation_status = "accepted"  # default
                if user.invitations:
                    latest_invitation = max(user.invitations, key=lambda inv: inv.invited_at)
                    invitation_status = latest_invitation.status.value if hasattr(latest_invitation.status, 'value') else latest_invitation.status

                # Get application access - convert to frontend-expected format
                app_access = {}

                # Map from ApplicationType enum to frontend snake_case keys
                enum_to_frontend = {
                    ApplicationType.MARKET_EDGE: "market_edge",
                    ApplicationType.CAUSAL_EDGE: "causal_edge",
                    ApplicationType.VALUE_EDGE: "value_edge"
                }

                for access in user.application_access or []:
                    frontend_key = enum_to_frontend.get(access.application)
                    if frontend_key:
                        app_access[frontend_key] = access.has_access

                # Default access for applications not explicitly set
                for app_type in ApplicationType:
                    frontend_key = enum_to_frontend.get(app_type)
                    if frontend_key and frontend_key not in app_access:
                        app_access[frontend_key] = False

                # This is what the API returns
                api_response = {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role.value if hasattr(user.role, 'value') else user.role,
                    "organisation_id": str(user.organisation_id),
                    "organisation_name": user.organisation.name if user.organisation else None,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "invitation_status": invitation_status,
                    "application_access": app_access
                }

                print(f"   📋 API Response:")
                print(json.dumps(api_response, indent=4, default=str))

            else:
                print("   ❌ User NOT found via ORM!")

            print()

            # 5. Test what the auth endpoint returns (/auth/me)
            print("5. SIMULATING AUTH ENDPOINT RESPONSE (/auth/me):")

            if user:
                # This simulates what getCurrentUser() API call returns
                auth_response = {
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role.value if hasattr(user.role, 'value') else user.role,
                        "organisation_id": str(user.organisation_id),
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                        "application_access": [
                            {
                                "application": access.application.value if hasattr(access.application, 'value') else access.application,
                                "has_access": access.has_access
                            }
                            for access in (user.application_access or [])
                        ]
                    },
                    "tenant": {
                        "id": str(user.organisation_id),
                        "name": user.organisation.name if user.organisation else "Default",
                        "industry": user.organisation.industry if user.organisation else "Technology",
                        "subscription_plan": (user.organisation.subscription_plan.value if hasattr(user.organisation.subscription_plan, 'value') else user.organisation.subscription_plan) if user.organisation else "basic"
                    },
                    "permissions": ["manage:platform", "manage:feature_flags", "manage:super_admin", "admin:market_edge"] if user.role.value == 'super_admin' else []
                }

                print(f"   📋 Auth Endpoint Response:")
                print(json.dumps(auth_response, indent=4, default=str))

            print()

            # 6. Summary and Analysis
            print("6. ANALYSIS AND FINDINGS:")
            print("=" * 40)

            if user_row and user:
                role_from_db = user_row.role
                role_from_api = user.role.value if hasattr(user.role, 'value') else user.role

                print(f"   📊 Role Comparison:")
                print(f"      Database (direct): {role_from_db}")
                print(f"      API (formatted): {role_from_api}")
                print(f"      Match: {'✅' if role_from_db == role_from_api else '❌'}")

                print(f"   📊 Application Access Comparison:")
                print(f"      Direct DB records: {len(access_rows)} applications")
                print(f"      ORM loaded records: {len(user.application_access) if user.application_access else 0} applications")
                print(f"      Formatted for frontend: {len(app_access)} applications")

                if access_rows and user.application_access:
                    print(f"      Details match: {'✅' if len(access_rows) == len(user.application_access) else '❌'}")

                # Check if user should have super_admin role and all applications
                expected_role = "super_admin"
                expected_apps = {"market_edge": True, "causal_edge": True, "value_edge": True}

                print(f"   🎯 Expected vs Actual:")
                print(f"      Expected role: {expected_role}")
                print(f"      Actual role: {role_from_api}")
                print(f"      Role correct: {'✅' if role_from_api == expected_role else '❌'}")

                print(f"      Expected apps: {expected_apps}")
                print(f"      Actual apps: {app_access}")
                print(f"      Apps correct: {'✅' if app_access == expected_apps else '❌'}")

            print()
            print("🔍 INVESTIGATION COMPLETE")

    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())