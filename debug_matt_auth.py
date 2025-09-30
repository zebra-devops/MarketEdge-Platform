#!/usr/bin/env python3
"""
Debug Matt.Lindop authentication issue
"""
import asyncio
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import requests
import json

async def debug_auth():
    """Debug authentication flow for Matt.Lindop"""

    # Check database users
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://matt@localhost:5432/platform_wrapper')
    engine = create_engine(DATABASE_URL)

    print("=== DATABASE USER CHECK ===")
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.is_active,
                o.name as org_name
            FROM users u
            LEFT JOIN organisations o ON u.organisation_id = o.id
            WHERE u.email ILIKE '%matt.lindop%'
            ORDER BY u.email
        '''))

        users = result.fetchall()
        for user in users:
            print(f"✓ Found user: {user.email}")
            print(f"  - ID: {user.id}")
            print(f"  - Role: {user.role}")
            print(f"  - Active: {user.is_active}")
            print(f"  - Organisation: {user.org_name}")
            print()

    # Test backend health
    print("=== BACKEND HEALTH CHECK ===")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✓ Backend health: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Backend health failed: {e}")

    # Test unauthenticated admin endpoint (should return 401)
    print("\n=== ADMIN ENDPOINT TEST (unauthenticated) ===")
    try:
        response = requests.get("http://localhost:8000/api/v1/admin/users")
        print(f"✓ Admin endpoint status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ Admin endpoint test failed: {e}")

    print("\n=== AUTHENTICATION DIAGNOSIS ===")
    print("The issue is likely one of these:")
    print("1. Frontend not sending JWT token to backend")
    print("2. JWT token doesn't contain correct user ID (sub claim)")
    print("3. JWT token user ID doesn't match database user ID")
    print("4. Auth0 configuration mismatch between frontend/backend")
    print("\nTo fix:")
    print("1. Check browser dev tools -> Network tab -> Look for Authorization header")
    print("2. Check if /api/v1/auth/me endpoint returns your user data")
    print("3. Verify JWT token sub claim matches your database user ID")

if __name__ == "__main__":
    asyncio.run(debug_auth())