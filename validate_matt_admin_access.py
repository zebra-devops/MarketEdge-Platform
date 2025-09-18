#!/usr/bin/env python3
"""
US-AUTH-3: Matt Lindop Admin Access Validation Script

This script validates that matt.lindop@zebra.associates has proper admin access
and can generate valid JWT tokens with admin permissions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.auth.jwt import create_access_token, verify_token, get_user_permissions
from datetime import datetime, timedelta
import json

def validate_matt_admin_access():
    """Comprehensive validation of Matt Lindop's admin access"""
    print("🔍 US-AUTH-3: Validating Matt Lindop Admin Access")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Step 1: Database User Validation
        print("📊 Step 1: Database User Validation")
        user = db.query(User).filter(User.email == 'matt.lindop@zebra.associates').first()
        
        if not user:
            print("❌ CRITICAL: User not found in database")
            return False
            
        print(f"✅ User found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Role: {user.role.value}")
        print(f"   Active: {user.is_active}")
        print(f"   Organization: {user.organisation_id}")
        
        # Validate admin role
        if user.role.value != 'admin':
            print(f"❌ CRITICAL: User role is '{user.role.value}', not 'admin'")
            return False
            
        if not user.is_active:
            print("❌ CRITICAL: User account is inactive")
            return False
            
        print("✅ User has valid admin role and active status")
        
        # Step 2: Organization Validation
        print("\n🏢 Step 2: Organization Validation")
        org = db.query(Organisation).filter(Organisation.id == user.organisation_id).first()
        
        if not org:
            print("❌ CRITICAL: User's organization not found")
            return False
            
        print(f"✅ Organization found: {org.name}")
        print(f"   Industry: {org.industry}")
        print(f"   Active: {org.is_active}")
        
        if not org.is_active:
            print("❌ CRITICAL: User's organization is inactive")
            return False
            
        # Step 3: JWT Token Generation Test
        print("\n🔐 Step 3: JWT Token Generation Test")
        
        # Get user permissions
        tenant_context = {
            "industry": org.industry.value if hasattr(org.industry, 'value') else str(org.industry)
        }
        permissions = get_user_permissions(user.role.value, tenant_context)
        
        print(f"✅ Generated {len(permissions)} permissions for admin user")
        print(f"   Key permissions: {permissions[:5]}")  # Show first 5
        
        # Create access token
        token_data = {
            "sub": str(user.id),
            "email": user.email
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=1),
            tenant_id=str(user.organisation_id),
            user_role=user.role.value,
            permissions=permissions,
            industry=tenant_context["industry"]
        )
        
        print(f"✅ Access token generated successfully")
        print(f"   Token length: {len(access_token)} characters")
        print(f"   Token preview: {access_token[:50]}...")
        
        # Step 4: JWT Token Validation Test
        print("\n🔍 Step 4: JWT Token Validation Test")
        
        payload = verify_token(access_token, expected_type="access")
        
        if not payload:
            print("❌ CRITICAL: Token validation failed")
            return False
            
        print("✅ Token validation successful")
        print(f"   User ID: {payload.get('sub')}")
        print(f"   Role: {payload.get('role')}")
        print(f"   Tenant ID: {payload.get('tenant_id')}")
        print(f"   Industry: {payload.get('industry')}")
        print(f"   Permissions count: {len(payload.get('permissions', []))}")
        
        # Step 5: Admin Permission Validation
        print("\n👑 Step 5: Admin Permission Validation")
        
        expected_admin_permissions = [
            "read:users", "write:users", "delete:users",
            "read:organizations", "write:organizations", "delete:organizations",
            "read:audit_logs", "read:system_metrics",
            "manage:feature_flags", "manage:rate_limits",
            "read:market_edge", "read:causal_edge", "read:value_edge"
        ]
        
        user_permissions = payload.get('permissions', [])
        missing_permissions = []
        
        for perm in expected_admin_permissions:
            if perm not in user_permissions:
                missing_permissions.append(perm)
                
        if missing_permissions:
            print(f"⚠️  WARNING: Missing {len(missing_permissions)} expected admin permissions:")
            for perm in missing_permissions:
                print(f"     - {perm}")
        else:
            print("✅ All expected admin permissions present")
        
        # Step 6: Final Validation Summary
        print("\n📋 Step 6: Validation Summary")
        print("=" * 60)
        
        validation_results = {
            "user_exists": True,
            "has_admin_role": user.role.value == 'admin',
            "is_active": user.is_active,
            "org_exists": org is not None,
            "org_active": org.is_active if org else False,
            "token_generated": access_token is not None,
            "token_validated": payload is not None,
            "has_admin_permissions": len(missing_permissions) == 0,
            "total_permissions": len(user_permissions),
            "missing_permissions_count": len(missing_permissions)
        }
        
        # Check if all critical validations passed
        critical_checks = [
            validation_results['user_exists'],
            validation_results['has_admin_role'], 
            validation_results['is_active'],
            validation_results['org_exists'],
            validation_results['org_active'],
            validation_results['token_generated'],
            validation_results['token_validated']
        ]
        all_valid = all(critical_checks)
        
        print(f"✅ User Database Record: {'VALID' if validation_results['user_exists'] and validation_results['has_admin_role'] and validation_results['is_active'] else 'INVALID'}")
        print(f"✅ Organization Record: {'VALID' if validation_results['org_exists'] and validation_results['org_active'] else 'INVALID'}")
        print(f"✅ JWT Token Generation: {'VALID' if validation_results['token_generated'] else 'INVALID'}")
        print(f"✅ JWT Token Validation: {'VALID' if validation_results['token_validated'] else 'INVALID'}")
        permissions_status = 'VALID' if validation_results['has_admin_permissions'] else f'MISSING {validation_results["missing_permissions_count"]} PERMISSIONS'
        print(f"✅ Admin Permissions: {permissions_status}")
        
        if all_valid:
            print("\n🎉 VALIDATION SUCCESSFUL: Matt Lindop has complete admin access")
            print("   Ready for £925K Zebra Associates opportunity")
            return True
        else:
            print("\n❌ VALIDATION FAILED: Issues found with Matt Lindop's admin access")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR during validation: {str(e)}")
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = validate_matt_admin_access()
    sys.exit(0 if success else 1)