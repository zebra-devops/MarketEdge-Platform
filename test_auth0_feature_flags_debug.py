#!/usr/bin/env python3
"""
Auth0 Feature Flags Debug Test
Comprehensive test for Matt.Lindop's feature flags access issue
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.auth.auth0 import auth0_client
from app.auth.dependencies import verify_auth0_token, get_current_user
from app.core.config import settings

async def test_auth0_token_verification():
    """Test Auth0 token verification directly"""

    print("=== AUTH0 TOKEN VERIFICATION TEST ===")

    # Test with example token format
    test_token_prefix = "eyJhbGciOiJIUzI1NiIs"

    print(f"Token format detected: JWT (starts with {test_token_prefix})")
    print(f"Token length: 417 characters")
    print("Token source: Matt.Lindop browser authService")

    print("\n1. TESTING AUTH0 CLIENT CONFIGURATION...")
    print(f"Auth0 Domain: {settings.AUTH0_DOMAIN}")
    print(f"Auth0 Client ID: {settings.AUTH0_CLIENT_ID[:8]}...")
    print(f"Auth0 Base URL: https://{settings.AUTH0_DOMAIN}")

    # Test Auth0 client initialization
    try:
        client = auth0_client
        print("✅ Auth0 client initialized successfully")
    except Exception as e:
        print(f"❌ Auth0 client initialization failed: {e}")
        return False

    print("\n2. AUTH0 TOKEN VERIFICATION FLOW...")
    print("Testing Auth0 userinfo endpoint connectivity...")

    # Test Auth0 connectivity (without real token)
    try:
        async with httpx.AsyncClient(timeout=30) as http_client:
            # Test Auth0 domain reachability
            response = await http_client.get(f"https://{settings.AUTH0_DOMAIN}/.well-known/openid_configuration")
            if response.status_code == 200:
                print("✅ Auth0 domain reachable")
                config = response.json()
                print(f"   - Userinfo endpoint: {config.get('userinfo_endpoint')}")
                print(f"   - Token endpoint: {config.get('token_endpoint')}")
            else:
                print(f"❌ Auth0 domain not reachable: {response.status_code}")

    except Exception as e:
        print(f"❌ Auth0 connectivity test failed: {e}")

    print("\n3. SIMULATED TOKEN VERIFICATION...")
    print("Simulating verify_auth0_token() function call...")

    # This simulates what happens when Matt's token is processed
    print("Expected flow:")
    print("  1. dependencies.get_current_user() called")
    print("  2. verify_token() fails (internal JWT)")
    print("  3. verify_auth0_token() called as fallback")
    print("  4. auth0_client.get_user_info() called")
    print("  5. User info returned with role claims")
    print("  6. require_admin() checks role")

    print("\n4. FEATURE FLAGS ENDPOINT REQUIREMENTS...")
    print("Endpoint: /api/v1/admin/feature-flags")
    print("Auth dependency chain:")
    print("  - HTTPBearer() extracts token")
    print("  - get_current_user() verifies token")
    print("  - require_admin() checks role")
    print("Required role: admin OR super_admin")

    return True

async def simulate_feature_flags_request():
    """Simulate the feature flags request flow"""

    print("\n=== FEATURE FLAGS REQUEST SIMULATION ===")

    print("1. REQUEST PROCESSING FLOW...")
    print("   GET /api/v1/admin/feature-flags")
    print("   Headers: Authorization: Bearer <matt_token>")

    print("\n2. DEPENDENCY RESOLUTION...")
    print("   a) HTTPBearer extracts token from Authorization header")
    print("   b) get_current_user(credentials, db) called")
    print("   c) verify_token(token, 'access') called")
    print("   d) If verify_token fails -> verify_auth0_token(token) called")
    print("   e) Auth0 userinfo API called")
    print("   f) User claims extracted")
    print("   g) Database user lookup by user_id")
    print("   h) require_admin(user) validates role")

    print("\n3. POTENTIAL FAILURE POINTS...")
    failure_points = [
        "Token not sent by frontend",
        "Token expired or invalid",
        "Auth0 userinfo API unreachable",
        "User not found in database",
        "User has insufficient role",
        "Organization context mismatch",
        "CORS issues masking real errors"
    ]

    for i, point in enumerate(failure_points, 1):
        print(f"   {i}. {point}")

    print("\n4. DEBUGGING RECOMMENDATIONS...")
    debug_steps = [
        "Check browser Network tab for Authorization header",
        "Verify token expiration in browser session",
        "Test Auth0 userinfo endpoint directly",
        "Check production logs for specific error",
        "Verify Matt.Lindop has super_admin role in database",
        "Test with curl bypassing frontend",
        "Check for CORS middleware order issues"
    ]

    for i, step in enumerate(debug_steps, 1):
        print(f"   {i}. {step}")

async def generate_test_commands():
    """Generate test commands for debugging"""

    print("\n=== PRODUCTION DEBUG COMMANDS ===")

    print("1. DIRECT API TEST (requires real token):")
    print("```bash")
    print("# Extract token from browser and test directly")
    print("curl -H 'Authorization: Bearer <MATT_TOKEN>' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     https://marketedge-platform.onrender.com/api/v1/admin/feature-flags")
    print("```")

    print("\n2. AUTH0 USERINFO TEST:")
    print("```bash")
    print("# Test Auth0 userinfo endpoint")
    print("curl -H 'Authorization: Bearer <MATT_TOKEN>' \\")
    print(f"     https://{settings.AUTH0_DOMAIN}/userinfo")
    print("```")

    print("\n3. DATABASE ROLE CHECK:")
    print("```sql")
    print("-- Check Matt.Lindop's role in production")
    print("SELECT id, email, role, is_active, organisation_id")
    print("FROM users")
    print("WHERE email ILIKE '%matt.lindop%';")
    print("```")

    print("\n4. PRODUCTION LOG ANALYSIS:")
    print("```bash")
    print("# Look for authentication events")
    print("# Search for: auth_admin_required, auth_insufficient_role")
    print("# Check Render logs or application logs")
    print("```")

    print("\n5. FRONTEND TOKEN CHECK:")
    print("```javascript")
    print("// Browser console check")
    print("console.log('Token:', localStorage.getItem('access_token'));")
    print("console.log('Token length:', localStorage.getItem('access_token')?.length);")
    print("```")

async def production_verification_steps():
    """List production verification steps"""

    print("\n=== PRODUCTION VERIFICATION CHECKLIST ===")

    verification_steps = [
        {
            "step": "Database Role Verification",
            "command": "Run verify_matt_lindop_admin_status.py",
            "expected": "Matt.Lindop has super_admin role",
            "action": "Update role if needed"
        },
        {
            "step": "Auth0 Token Validation",
            "command": "Test Auth0 userinfo endpoint",
            "expected": "Valid user info with role claims",
            "action": "Check token expiration and permissions"
        },
        {
            "step": "Feature Flags Endpoint Test",
            "command": "Direct curl to admin/feature-flags",
            "expected": "200 OK with feature flags data",
            "action": "Fix authorization if 401/403"
        },
        {
            "step": "Frontend Token Transmission",
            "command": "Check browser Network tab",
            "expected": "Authorization header present",
            "action": "Fix frontend token management"
        },
        {
            "step": "Production Logs Analysis",
            "command": "Check authentication logs",
            "expected": "Successful admin authentication",
            "action": "Fix identified authentication issues"
        }
    ]

    for i, step in enumerate(verification_steps, 1):
        print(f"\n{i}. {step['step']}:")
        print(f"   Command: {step['command']}")
        print(f"   Expected: {step['expected']}")
        print(f"   Action: {step['action']}")

async def main():
    """Main test function"""

    print("🔍 AUTH0 FEATURE FLAGS DEBUG TEST")
    print("Analyzing Matt.Lindop's £925K Zebra Associates opportunity access issue")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Test Auth0 integration
    await test_auth0_token_verification()

    # Simulate request flow
    await simulate_feature_flags_request()

    # Generate debug commands
    await generate_test_commands()

    # Production verification
    await production_verification_steps()

    print("\n" + "=" * 60)
    print("🎯 SUMMARY OF LIKELY ISSUES:")
    print("1. Matt.Lindop role might not be super_admin in database")
    print("2. Auth0 token claims might not include required role")
    print("3. Frontend might not be sending Authorization header")
    print("4. Token might be expired or invalid")
    print("5. Organization context mismatch")

    print("\n🚀 RECOMMENDED IMMEDIATE ACTIONS:")
    print("1. Run verify_matt_lindop_admin_status.py")
    print("2. Check Matt's token in browser developer tools")
    print("3. Test feature flags endpoint with curl")
    print("4. Review production authentication logs")

if __name__ == "__main__":
    asyncio.run(main())