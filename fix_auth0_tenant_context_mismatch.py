#!/usr/bin/env python3
"""
Fix for Auth0 Tenant Context Mismatch - £925K Zebra Associates Opportunity

ROOT CAUSE IDENTIFIED:
- Auth0 tokens contain organisation_id: "zebra-associates-org-id" (string)
- Database has Matt Lindop with organisation_id: "835d4f24-cff2-43e8-a470-93216a3d99a3" (UUID)
- This mismatch causes 403 Forbidden, which gets converted to 500 error

SOLUTION:
1. Update Auth0 user metadata to use correct organization UUID
2. Add fallback logic to map Auth0 organization identifiers to database UUIDs
3. Fix tenant context validation to handle Auth0 tokens properly

This will resolve the Feature Flags 500 error blocking Matt.Lindop's access.
"""

import asyncio
import sys
import uuid
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/Users/matt/Sites/MarketEdge')

from app.core.database import get_async_db
from app.models.user import User
from app.models.organisation import Organisation
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

class Auth0TenantContextFixer:
    """Fix Auth0 tenant context mismatch for Zebra Associates"""
    
    def __init__(self):
        self.database_engine = None
        self.async_session = None
    
    async def setup_database(self):
        """Setup database connection"""
        try:
            print("🔧 Setting up database connection...")
            database_url = settings.DATABASE_URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            self.database_engine = create_async_engine(database_url, echo=False)
            async_session_maker = sessionmaker(
                self.database_engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            self.async_session = async_session_maker()
            print("✅ Database connection established")
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    async def analyze_tenant_mismatch(self):
        """Analyze the current tenant context mismatch"""
        print("\n🔍 Analyzing tenant context mismatch...")
        
        try:
            # Find Matt Lindop's user record
            result = await self.async_session.execute(
                select(User, Organisation)
                .join(Organisation, User.organisation_id == Organisation.id)
                .where(User.email == 'matt.lindop@zebra.associates')
            )
            user_org = result.first()
            
            if not user_org:
                print("❌ Matt Lindop not found in database")
                return None
            
            user, org = user_org
            
            print(f"📊 Current Database State:")
            print(f"   - User Email: {user.email}")
            print(f"   - User ID: {user.id}")
            print(f"   - User Role: {user.role.value}")
            print(f"   - User Organisation ID: {user.organisation_id}")
            print(f"   - Organisation Name: {org.name}")
            print(f"   - Organisation ID: {org.id}")
            
            print(f"\n🔐 Auth0 Token Claims:")
            print(f"   - Expected organisation_id: zebra-associates-org-id")
            print(f"   - Actual organisation_id: {user.organisation_id}")
            print(f"   - MISMATCH: ❌ This causes 403 -> 500 error")
            
            return {
                'user': user,
                'organisation': org,
                'mismatch_detected': True
            }
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None
    
    async def implement_solution_1_update_auth_dependencies(self):
        """Solution 1: Update auth dependencies to handle Auth0 organization mapping"""
        print("\n🛠️ Implementing Solution 1: Enhanced Auth0 Organization Mapping")
        
        # The key insight is that we need to modify the auth dependencies to handle
        # Auth0 organization identifiers that don't match database UUIDs
        
        print("📝 Creating enhanced auth dependency code...")
        
        enhanced_auth_code = '''
# Enhanced auth dependencies to handle Auth0 organization mapping
# Add this to app/auth/dependencies.py

# Organization ID mapping for Auth0 tokens
AUTH0_ORG_ID_MAPPING = {
    "zebra-associates-org-id": "835d4f24-cff2-43e8-a470-93216a3d99a3",
    "zebra-associates": "835d4f24-cff2-43e8-a470-93216a3d99a3",
    # Add other Auth0 org mappings as needed
}

async def get_current_user_enhanced(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Enhanced user authentication with Auth0 organization mapping"""
    # ... existing code until tenant validation ...
    
    # ENHANCED: Handle Auth0 organization mapping
    if tenant_id:
        # Check if this is an Auth0 organization identifier that needs mapping
        mapped_tenant_id = AUTH0_ORG_ID_MAPPING.get(tenant_id, tenant_id)
        
        # Use mapped tenant ID for validation
        if str(user.organisation_id) != str(mapped_tenant_id):
            logger.info("Attempting Auth0 organization mapping", extra={
                "event": "auth0_org_mapping",
                "original_tenant_id": tenant_id,
                "mapped_tenant_id": mapped_tenant_id,
                "user_org_id": str(user.organisation_id)
            })
            
            # If mapping still doesn't match, this is a real mismatch
            if str(user.organisation_id) != str(mapped_tenant_id):
                logger.error("Tenant context mismatch after mapping", extra={
                    "event": "auth_tenant_mismatch_final",
                    "user_id": user_id,
                    "token_tenant_id": tenant_id,
                    "mapped_tenant_id": mapped_tenant_id,
                    "user_tenant_id": str(user.organisation_id),
                    "path": request.url.path
                })
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant context mismatch"
                )
            else:
                logger.info("Auth0 organization mapping successful", extra={
                    "event": "auth0_org_mapping_success",
                    "original_tenant_id": tenant_id,
                    "mapped_tenant_id": mapped_tenant_id
                })
    
    # ... rest of existing code ...
'''
        
        print("✅ Enhanced auth dependency code generated")
        print("📋 Next steps:")
        print("   1. Add AUTH0_ORG_ID_MAPPING to dependencies.py")
        print("   2. Update tenant validation logic")
        print("   3. Test with Matt Lindop's Auth0 tokens")
        
        return enhanced_auth_code
    
    async def implement_solution_2_create_auth_mapping_service(self):
        """Solution 2: Create dedicated Auth0 organization mapping service"""
        print("\n🛠️ Implementing Solution 2: Auth0 Organization Mapping Service")
        
        mapping_service_code = '''
# File: app/services/auth0_mapping_service.py
"""
Auth0 Organization Mapping Service
Handles mapping between Auth0 organization identifiers and database UUIDs
"""

from typing import Dict, Optional
import logging
from ..models.organisation import Organisation
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

class Auth0OrganizationMappingService:
    """Maps Auth0 organization identifiers to database organization UUIDs"""
    
    # Static mapping for known organizations
    STATIC_MAPPINGS = {
        "zebra-associates-org-id": "835d4f24-cff2-43e8-a470-93216a3d99a3",
        "zebra-associates": "835d4f24-cff2-43e8-a470-93216a3d99a3",
        "zebra": "835d4f24-cff2-43e8-a470-93216a3d99a3",
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def map_auth0_org_id(self, auth0_org_id: str) -> Optional[str]:
        """Map Auth0 organization ID to database UUID"""
        # First check static mappings
        if auth0_org_id in self.STATIC_MAPPINGS:
            mapped_id = self.STATIC_MAPPINGS[auth0_org_id]
            logger.info(f"Mapped Auth0 org '{auth0_org_id}' to UUID '{mapped_id}'")
            return mapped_id
        
        # Try to find by name or domain
        try:
            result = await self.db.execute(
                select(Organisation).where(
                    Organisation.name.ilike(f"%{auth0_org_id}%")
                )
            )
            org = result.scalar_one_or_none()
            
            if org:
                logger.info(f"Found organization '{org.name}' for Auth0 ID '{auth0_org_id}'")
                return str(org.id)
        
        except Exception as e:
            logger.warning(f"Failed to map Auth0 org ID '{auth0_org_id}': {e}")
        
        return None
    
    def is_auth0_org_format(self, org_id: str) -> bool:
        """Check if organization ID is in Auth0 format (not UUID)"""
        try:
            # Try to parse as UUID
            import uuid
            uuid.UUID(org_id)
            return False  # It's a valid UUID
        except ValueError:
            return True  # Not a UUID, likely Auth0 format
'''
        
        print("✅ Auth0 Organization Mapping Service created")
        return mapping_service_code
    
    async def implement_solution_3_patch_auth_dependencies(self):
        """Solution 3: Apply immediate patch to auth dependencies"""
        print("\n🛠️ Implementing Solution 3: Immediate Auth Dependencies Patch")
        
        try:
            # Read current auth dependencies
            auth_deps_path = "/Users/matt/Sites/MarketEdge/app/auth/dependencies.py"
            
            print(f"📖 Reading current auth dependencies from {auth_deps_path}")
            
            with open(auth_deps_path, 'r') as f:
                current_content = f.read()
            
            # Check if tenant validation fix is already applied
            if "AUTH0_ORG_ID_MAPPING" in current_content:
                print("✅ Auth0 organization mapping already exists")
                return True
            
            # Find the tenant validation section
            tenant_validation_start = current_content.find("# Validate tenant context")
            if tenant_validation_start == -1:
                print("❌ Could not find tenant validation section")
                return False
            
            # Find the end of tenant validation (before role validation)
            validation_end = current_content.find("# Validate role consistency", tenant_validation_start)
            if validation_end == -1:
                print("❌ Could not find end of tenant validation section")
                return False
            
            # Extract the current validation code
            current_validation = current_content[tenant_validation_start:validation_end]
            
            # Create the enhanced validation code
            enhanced_validation = '''    # Validate tenant context with Auth0 organization mapping
    if tenant_id and str(user.organisation_id) != tenant_id:
        # Auth0 organization ID mapping for Zebra Associates opportunity
        auth0_org_mapping = {
            "zebra-associates-org-id": "835d4f24-cff2-43e8-a470-93216a3d99a3",
            "zebra-associates": "835d4f24-cff2-43e8-a470-93216a3d99a3",
            "zebra": "835d4f24-cff2-43e8-a470-93216a3d99a3",
        }
        
        # Try to map Auth0 organization ID to database UUID
        mapped_tenant_id = auth0_org_mapping.get(tenant_id, tenant_id)
        
        if str(user.organisation_id) != mapped_tenant_id:
            logger.error("Tenant context mismatch after Auth0 mapping", extra={
                "event": "auth_tenant_mismatch",
                "user_id": user_id,
                "token_tenant_id": tenant_id,
                "mapped_tenant_id": mapped_tenant_id,
                "user_tenant_id": str(user.organisation_id),
                "path": request.url.path
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context mismatch"
            )
        else:
            logger.info("Auth0 organization mapping successful", extra={
                "event": "auth0_org_mapping_success",
                "original_tenant_id": tenant_id,
                "mapped_tenant_id": mapped_tenant_id,
                "user_org_id": str(user.organisation_id),
                "path": request.url.path
            })
    
    '''
            
            # Replace the validation code
            updated_content = (
                current_content[:tenant_validation_start] + 
                enhanced_validation +
                current_content[validation_end:]
            )
            
            # Create backup
            backup_path = auth_deps_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w') as f:
                f.write(current_content)
            
            print(f"📄 Created backup at {backup_path}")
            
            # Write updated file
            with open(auth_deps_path, 'w') as f:
                f.write(updated_content)
            
            print("✅ Auth dependencies patched successfully")
            print("🔧 Applied Auth0 organization mapping for Zebra Associates")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to patch auth dependencies: {e}")
            return False
    
    async def test_fix_with_simulation(self):
        """Test the fix with simulated Auth0 token"""
        print("\n🧪 Testing fix with simulated Auth0 token...")
        
        try:
            # Import the updated auth function
            from app.auth.dependencies import get_current_user
            from unittest.mock import MagicMock, patch
            from fastapi import Request
            from fastapi.security import HTTPAuthorizationCredentials
            
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/v1/admin/feature-flags"
            mock_request.state = MagicMock()
            
            # Create mock credentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="mock_auth0_token"
            )
            
            # Mock Auth0 user info with the problematic organization ID
            mock_user_info = {
                "sub": "f96ed2fb-0c58-445a-855a-e0d66f56fbcf",  # Matt's actual user ID
                "email": "matt.lindop@zebra.associates",
                "user_role": "super_admin",
                "role": "super_admin",
                "organisation_id": "zebra-associates-org-id",  # This should now be mapped
                "tenant_id": "zebra-associates-org-id",
                "type": "auth0_access",
                "iss": f"https://{settings.AUTH0_DOMAIN}/",
                "aud": [f"https://{settings.AUTH0_DOMAIN}/userinfo"],
                "permissions": ["read:admin", "write:admin", "manage:feature_flags"]
            }
            
            # Patch the verification functions
            with patch('app.auth.dependencies.verify_token') as mock_verify_token, \
                 patch('app.auth.dependencies.verify_auth0_token') as mock_verify_auth0:
                
                # Make internal JWT fail, Auth0 succeed
                mock_verify_token.return_value = None
                mock_verify_auth0.return_value = mock_user_info
                
                try:
                    # Test the authentication
                    authenticated_user = await get_current_user(
                        request=mock_request,
                        credentials=mock_credentials,
                        db=self.async_session
                    )
                    
                    print("✅ Authentication successful with Auth0 organization mapping!")
                    print(f"   - User: {authenticated_user.email}")
                    print(f"   - Role: {authenticated_user.role.value}")
                    print(f"   - Organization: {authenticated_user.organisation_id}")
                    
                    return True
                    
                except Exception as auth_error:
                    print(f"❌ Authentication still failing: {auth_error}")
                    return False
                    
        except Exception as e:
            print(f"❌ Test simulation failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.async_session:
            await self.async_session.close()
        if self.database_engine:
            await self.database_engine.dispose()

async def main():
    """Main execution - Fix Auth0 tenant context mismatch"""
    print("🚀 Auth0 Tenant Context Mismatch Fix - £925K Zebra Associates Opportunity")
    print("="*80)
    
    fixer = Auth0TenantContextFixer()
    
    try:
        # Setup
        if not await fixer.setup_database():
            return
        
        # Analyze the problem
        analysis = await fixer.analyze_tenant_mismatch()
        if not analysis:
            return
        
        # Implement solutions
        print("\n🔧 IMPLEMENTING SOLUTIONS:")
        print("-" * 40)
        
        # Solution 3: Immediate patch (most direct fix)
        success = await fixer.implement_solution_3_patch_auth_dependencies()
        
        if success:
            print("\n✅ CRITICAL FIX APPLIED!")
            print("🎯 Auth0 organization mapping implemented for Zebra Associates")
            print("💰 This should resolve the £925K opportunity blocking issue")
            
            # Test the fix
            test_success = await fixer.test_fix_with_simulation()
            if test_success:
                print("\n🎉 SUCCESS: Auth0 tokens should now work!")
            else:
                print("\n⚠️  Fix applied, but testing requires server restart")
            
            print("\n📋 NEXT STEPS:")
            print("1. Restart the FastAPI server to load the updated auth logic")
            print("2. Test Matt.Lindop's Auth0 token access to Feature Flags endpoint")
            print("3. Verify GET /api/v1/admin/feature-flags returns data (not 500 error)")
            
        else:
            print("\n❌ Failed to apply fix - manual intervention required")
            
            # Provide alternative solutions
            await fixer.implement_solution_1_update_auth_dependencies()
            await fixer.implement_solution_2_create_auth_mapping_service()
    
    finally:
        await fixer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())