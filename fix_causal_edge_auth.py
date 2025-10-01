#!/usr/bin/env python3
"""
Fix Causal Edge Authentication Issues

This script creates the necessary database entries for testing
the Causal Edge application without going through full Auth0 flow.
"""

import asyncio
import asyncpg
import json
import uuid
from datetime import datetime, timedelta
import os
import sys
import jwt

# Add the app directory to Python path
sys.path.insert(0, '/Users/matt/Sites/MarketEdge')

from app.core.config import settings

async def fix_causal_edge_auth():
    """Fix authentication and feature flag issues for Causal Edge testing"""

    print("=== Fixing Causal Edge Authentication Issues ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not configured")
        return

    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgres://', 1)

    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    try:
        # Step 1: Create test user if not exists
        print("\n1. Creating test user...")

        # Check if test user exists
        user_email = "test@causaledge.dev"
        user_row = await conn.fetchrow(
            "SELECT id, organisation_id, role FROM users WHERE email = $1",
            user_email
        )

        if not user_row:
            # Get or create default organization
            org_row = await conn.fetchrow(
                "SELECT id FROM organisations WHERE name = 'Default' LIMIT 1"
            )

            if not org_row:
                # Create default organization
                org_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO organisations (id, name, industry, subscription_plan, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                """, org_id, "Default", "technology", "basic")
                print("   ✅ Default organization created")
            else:
                org_id = org_row['id']

            # Create test user
            user_id = uuid.uuid4()
            await conn.execute("""
                INSERT INTO users (id, email, first_name, last_name, organisation_id, role, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """, user_id, user_email, "Test", "User", org_id, "admin", True)
            print(f"   ✅ Test user created: {user_email}")
        else:
            user_id = user_row['id']
            org_id = user_row['organisation_id']
            print(f"   ✅ Test user exists: {user_email}")

        # Step 2: Grant CAUSAL_EDGE application access
        print("\n2. Granting CAUSAL_EDGE application access...")

        # Check if access record exists
        access_row = await conn.fetchrow(
            "SELECT id FROM user_application_access WHERE user_id = $1 AND application = $2",
            user_id, "CAUSAL_EDGE"
        )

        if not access_row:
            await conn.execute("""
                INSERT INTO user_application_access (id, user_id, application, has_access, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
            """, uuid.uuid4(), user_id, "CAUSAL_EDGE", True)
            print("   ✅ CAUSAL_EDGE application access granted")
        else:
            print("   ✅ CAUSAL_EDGE application access already exists")

        # Step 3: Enable causal_edge_enabled feature flag
        print("\n3. Enabling causal_edge_enabled feature flag...")

        # Check if feature flag exists
        flag_row = await conn.fetchrow(
            "SELECT id, is_enabled FROM feature_flags WHERE name = $1",
            "causal_edge_enabled"
        )

        if not flag_row:
            await conn.execute("""
                INSERT INTO feature_flags (
                    id, flag_key, name, description, is_enabled, rollout_percentage,
                    scope, status, config, allowed_sectors, blocked_sectors, metadata,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
            """,
                uuid.uuid4(), "causal_edge_enabled", "causal_edge_enabled",
                "Enable Causal Edge application", True, 100,
                "GLOBAL", "ACTIVE", "{}", "[]", "[]", "{}",
            )
            print("   ✅ causal_edge_enabled feature flag created and enabled")
        elif not flag_row['is_enabled']:
            await conn.execute(
                "UPDATE feature_flags SET is_enabled = $1, updated_at = NOW() WHERE name = $2",
                True, "causal_edge_enabled"
            )
            print("   ✅ causal_edge_enabled feature flag enabled")
        else:
            print("   ✅ causal_edge_enabled feature flag already enabled")

        # Step 4: Create test JWT token
        print("\n4. Creating test JWT token...")

        from app.auth.jwt import create_access_token, get_user_permissions

        # Get user permissions
        permissions = get_user_permissions("admin", {"industry": "technology"})

        # Create access token
        token_data = {
            "sub": str(user_id),
            "email": user_email
        }

        access_token = create_access_token(
            data=token_data,
            tenant_id=str(org_id),
            user_role="admin",
            permissions=permissions,
            industry="technology"
        )

        print("   ✅ Test JWT token created")
        print(f"   Token length: {len(access_token)}")

        # Step 5: Test the token
        print("\n5. Testing the token...")

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/causal-edge/experiments",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Origin": "http://localhost:3000"
                },
                json={
                    "name": "Test Experiment",
                    "experiment_type": "PRICING",
                    "hypothesis": "Testing causal edge functionality",
                    "success_metrics": ["revenue", "conversion_rate"]
                }
            )

            print(f"   Status: {response.status_code}")
            if response.status_code == 201:
                print("   ✅ Experiment created successfully!")
                result = response.json()
                print(f"   Experiment ID: {result.get('id')}")
            else:
                print(f"   Response: {response.text[:200]}...")

        # Step 6: Output token for frontend testing
        print("\n6. Frontend Testing Instructions:")
        print("   Copy this token to your browser's localStorage:")
        print(f"   localStorage.setItem('access_token', '{access_token}')")
        print()
        print("   Or test directly with curl:")
        test_data = {"name": "Frontend Test", "experiment_type": "PRICING", "hypothesis": "Testing", "success_metrics": ["revenue"]}
        print(f"   curl -X POST 'http://localhost:8000/api/v1/causal-edge/experiments' \\")
        print(f"        -H 'Authorization: Bearer {access_token}' \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -H 'Origin: http://localhost:3000' \\")
        print(f"        -d '{json.dumps(test_data)}'")

        await conn.close()

        print("\n=== FIX COMPLETED ===")
        print("✅ Test user created with admin role")
        print("✅ CAUSAL_EDGE application access granted")
        print("✅ causal_edge_enabled feature flag enabled")
        print("✅ Test JWT token generated")
        print()
        print("🔧 Next steps:")
        print("1. Copy the token to localStorage in your browser")
        print("2. Refresh the frontend application")
        print("3. Try creating an experiment - it should work now!")

    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_causal_edge_auth())