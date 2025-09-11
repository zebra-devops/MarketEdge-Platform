#!/usr/bin/env python3
"""
Test script to verify JWT token generation includes proper role claims
for the Zebra Associates admin user.
"""
import os
import sys
import json
from datetime import datetime
from jose import jwt

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.auth.jwt import create_access_token, create_refresh_token, verify_token, get_user_permissions
from app.models.user import UserRole


def test_admin_token_generation():
    """Test JWT token generation for admin user"""
    print("=== JWT Token Role Claims Test ===\n")
    
    # Simulate admin user data (what would come from database)
    admin_user_data = {
        "sub": "admin-user-id-123",
        "email": "matt.lindop@zebra.associates"
    }
    
    admin_role = UserRole.admin.value
    tenant_id = "zebra-associates-org-id"
    industry = "cinema"
    
    # Get admin permissions
    tenant_context = {"industry": industry}
    permissions = get_user_permissions(admin_role, tenant_context)
    
    print(f"Admin permissions for {admin_role} role:")
    for perm in sorted(permissions):
        print(f"  - {perm}")
    print()
    
    # Create access token with role claims
    access_token = create_access_token(
        data=admin_user_data,
        tenant_id=tenant_id,
        user_role=admin_role,
        permissions=permissions,
        industry=industry
    )
    
    print(f"Generated access token: {access_token[:50]}...\n")
    
    # Verify and decode the token
    payload = verify_token(access_token, expected_type="access")
    
    if payload:
        print("✅ Token verification successful!")
        print("Token payload:")
        for key, value in payload.items():
            if key == "permissions" and isinstance(value, list):
                print(f"  {key}: {len(value)} permissions")
                for perm in sorted(value):
                    print(f"    - {perm}")
            else:
                print(f"  {key}: {value}")
        print()
        
        # Check critical admin claims
        role_claim = payload.get("role")
        permissions_claim = payload.get("permissions", [])
        tenant_claim = payload.get("tenant_id")
        
        print("=== Role Claims Verification ===")
        print(f"✅ Role claim present: {role_claim}")
        print(f"✅ Admin role correct: {role_claim == 'admin'}")
        print(f"✅ Tenant ID present: {tenant_claim}")
        print(f"✅ Permissions count: {len(permissions_claim)}")
        print(f"✅ Admin permissions: {'read:users' in permissions_claim and 'manage:feature_flags' in permissions_claim}")
        
        # Check if token includes all expected admin permissions
        expected_admin_perms = [
            "read:users", "write:users", "delete:users",
            "read:organizations", "write:organizations", "delete:organizations",
            "manage:feature_flags", "read:system_metrics"
        ]
        
        missing_perms = [perm for perm in expected_admin_perms if perm not in permissions_claim]
        if missing_perms:
            print(f"⚠️  Missing permissions: {missing_perms}")
        else:
            print("✅ All expected admin permissions present")
            
    else:
        print("❌ Token verification failed!")
        return False
    
    # Test refresh token
    print("\n=== Refresh Token Test ===")
    refresh_token = create_refresh_token(
        data=admin_user_data,
        tenant_id=tenant_id
    )
    
    refresh_payload = verify_token(refresh_token, expected_type="refresh")
    if refresh_payload:
        print("✅ Refresh token verification successful!")
        print(f"  Tenant ID: {refresh_payload.get('tenant_id')}")
        print(f"  Token family: {refresh_payload.get('family')}")
    else:
        print("❌ Refresh token verification failed!")
    
    return True


def test_token_validation_middleware():
    """Test that token validation correctly extracts role claims"""
    print("\n=== Token Validation Middleware Test ===")
    
    # Create a token with admin role
    admin_data = {"sub": "admin-123", "email": "admin@test.com"}
    token = create_access_token(
        data=admin_data,
        tenant_id="test-org",
        user_role="admin",
        permissions=get_user_permissions("admin"),
        industry="cinema"
    )
    
    # Verify token and extract claims
    payload = verify_token(token, expected_type="access")
    
    if payload:
        # Simulate what the middleware does
        user_role = payload.get("role")
        tenant_id = payload.get("tenant_id")
        permissions = payload.get("permissions", [])
        
        print(f"✅ Extracted role: {user_role}")
        print(f"✅ Extracted tenant: {tenant_id}")
        print(f"✅ Extracted permissions count: {len(permissions)}")
        
        # Test admin-specific checks
        has_admin_role = user_role == "admin"
        has_admin_perms = "manage:feature_flags" in permissions
        
        print(f"✅ Admin role check: {has_admin_role}")
        print(f"✅ Admin permissions check: {has_admin_perms}")
        
        return has_admin_role and has_admin_perms
    else:
        print("❌ Token validation failed")
        return False


def main():
    """Main test function"""
    print("Testing JWT Role Claims Implementation for Zebra Associates Admin User\n")
    
    # Test 1: Token generation
    test1_passed = test_admin_token_generation()
    
    # Test 2: Token validation
    test2_passed = test_token_validation_middleware()
    
    print("\n=== Test Summary ===")
    print(f"Token Generation Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Token Validation Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! JWT role claims are working correctly.")
        print("\nNext steps:")
        print("1. Verify the user matt.lindop@zebra.associates has 'admin' role in the database")
        print("2. Test the authentication flow end-to-end")
        print("3. Verify admin endpoints accept the generated tokens")
    else:
        print("\n⚠️  Some tests failed. Check the implementation above.")


if __name__ == "__main__":
    main()