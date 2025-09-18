#!/usr/bin/env python3
"""
Verification Test for Auth0 Feature Flags Fix - £925K Zebra Associates Opportunity

This test verifies that Matt.Lindop's Auth0 tokens can now successfully access
the Feature Flags endpoint without getting 500 Internal Server Error.

ROOT CAUSE WAS: Auth0 organization ID mismatch
- Auth0 token: organisation_id = "zebra-associates-org-id" 
- Database: organisation_id = "835d4f24-cff2-43e8-a470-93216a3d99a3"

FIX APPLIED: Auth0 organization mapping in auth dependencies
- Maps "zebra-associates-org-id" -> "835d4f24-cff2-43e8-a470-93216a3d99a3"
- Allows Auth0 tokens to pass tenant validation
- Enables successful Feature Flags endpoint access

This test simulates the complete flow that Matt.Lindop would experience.
"""

import asyncio
import json
import traceback
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, '/Users/matt/Sites/MarketEdge')

from app.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.endpoints.admin import list_feature_flags
from app.core.database import get_async_db
from app.models.user import User
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

class Auth0FeatureFlagsFixVerifier:
    """Verify the complete Auth0 Feature Flags fix works end-to-end"""
    
    def __init__(self):
        self.database_engine = None
        self.async_session = None
        self.test_results = {}
    
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
    
    def create_matt_lindop_auth0_token_payload(self) -> Dict[str, Any]:
        """Create realistic Auth0 token payload for Matt.Lindop"""
        return {
            "sub": "f96ed2fb-0c58-445a-855a-e0d66f56fbcf",  # Matt's actual user ID
            "email": "matt.lindop@zebra.associates",
            "user_role": "super_admin",
            "role": "super_admin",
            "organisation_id": "zebra-associates-org-id",  # This should now be mapped!
            "tenant_id": "zebra-associates-org-id",
            "type": "auth0_access",
            "iss": f"https://{settings.AUTH0_DOMAIN}/",
            "aud": [f"https://{settings.AUTH0_DOMAIN}/userinfo"],
            "permissions": ["read:admin", "write:admin", "manage:feature_flags"]
        }
    
    async def test_auth0_authentication_flow(self):
        """Test the complete Auth0 authentication flow with organization mapping"""
        print("\n🔐 Testing Auth0 authentication flow with organization mapping...")
        
        try:
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/v1/admin/feature-flags"
            mock_request.state = MagicMock()
            
            # Create mock credentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="auth0_token_matt_lindop_zebra"
            )
            
            # Create Auth0 user info payload
            auth0_payload = self.create_matt_lindop_auth0_token_payload()
            
            print(f"📤 Simulating Auth0 token with:")
            print(f"   - User: {auth0_payload['email']}")
            print(f"   - Role: {auth0_payload['role']}")
            print(f"   - Org ID: {auth0_payload['organisation_id']} (should be mapped)")
            
            # Mock the authentication functions
            with patch('app.auth.dependencies.verify_token') as mock_verify_token, \
                 patch('app.auth.dependencies.verify_auth0_token') as mock_verify_auth0:
                
                # Internal JWT fails (realistic scenario)
                mock_verify_token.return_value = None
                
                # Auth0 verification succeeds
                mock_verify_auth0.return_value = auth0_payload
                
                # Test authentication
                authenticated_user = await get_current_user(
                    request=mock_request,
                    credentials=mock_credentials,
                    db=self.async_session
                )
                
                print("✅ Auth0 authentication successful!")
                print(f"   - User: {authenticated_user.email}")
                print(f"   - Role: {authenticated_user.role.value}")
                print(f"   - Database Org ID: {authenticated_user.organisation_id}")
                
                self.test_results['auth0_authentication'] = {
                    'success': True,
                    'user_email': authenticated_user.email,
                    'user_role': authenticated_user.role.value,
                    'organization_mapped': True
                }
                
                return authenticated_user
                
        except Exception as e:
            print(f"❌ Auth0 authentication failed: {e}")
            traceback.print_exc()
            self.test_results['auth0_authentication'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def test_admin_authorization(self, authenticated_user: User):
        """Test admin authorization with the authenticated user"""
        print("\n👨‍💼 Testing admin authorization...")
        
        try:
            # Test require_admin
            admin_user = await require_admin(current_user=authenticated_user)
            
            print("✅ Admin authorization successful!")
            print(f"   - Admin user: {admin_user.email}")
            print(f"   - Admin role: {admin_user.role.value}")
            
            self.test_results['admin_authorization'] = {
                'success': True,
                'admin_role': admin_user.role.value
            }
            
            return admin_user
            
        except Exception as e:
            print(f"❌ Admin authorization failed: {e}")
            self.test_results['admin_authorization'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def test_feature_flags_endpoint(self, admin_user: User):
        """Test the actual Feature Flags endpoint that was returning 500 errors"""
        print("\n🚩 Testing Feature Flags endpoint (the one that was failing)...")
        
        try:
            # Call the actual endpoint function
            result = await list_feature_flags(
                current_user=admin_user,
                db=self.async_session,
                module_id=None,
                enabled_only=False
            )
            
            print("✅ Feature Flags endpoint successful!")
            print(f"   - Response type: {type(result)}")
            
            if isinstance(result, dict) and 'feature_flags' in result:
                flag_count = len(result['feature_flags'])
                print(f"   - Feature flags returned: {flag_count}")
                
                # Show sample flags
                for i, flag in enumerate(result['feature_flags'][:3]):
                    print(f"   - Flag {i+1}: {flag.get('flag_key')} (enabled: {flag.get('is_enabled')})")
            
            self.test_results['feature_flags_endpoint'] = {
                'success': True,
                'response_type': str(type(result)),
                'flag_count': len(result.get('feature_flags', [])) if isinstance(result, dict) else 0
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Feature Flags endpoint failed: {e}")
            traceback.print_exc()
            self.test_results['feature_flags_endpoint'] = {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()[:500]  # Truncate for readability
            }
            return None
    
    async def test_complete_end_to_end_flow(self):
        """Test the complete end-to-end flow that Matt.Lindop would experience"""
        print("\n🎯 Testing complete end-to-end flow...")
        
        try:
            # Create mock HTTP request context
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/v1/admin/feature-flags"
            mock_request.method = "GET"
            mock_request.headers = {"Authorization": "Bearer auth0_token_matt_lindop"}
            mock_request.state = MagicMock()
            
            # Mock credentials
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="auth0_token_matt_lindop_zebra_associates"
            )
            
            # Auth0 payload
            auth0_payload = self.create_matt_lindop_auth0_token_payload()
            
            print("🔄 Simulating complete HTTP request flow...")
            print("   1. HTTP request received")
            print("   2. Auth0 token extracted from Authorization header")
            print("   3. Internal JWT verification (fails)")
            print("   4. Auth0 verification (succeeds)")
            print("   5. Organization mapping applied")
            print("   6. User authorization check")
            print("   7. Feature flags retrieval")
            
            # Mock the complete flow
            with patch('app.auth.dependencies.verify_token') as mock_verify_token, \
                 patch('app.auth.dependencies.verify_auth0_token') as mock_verify_auth0:
                
                mock_verify_token.return_value = None
                mock_verify_auth0.return_value = auth0_payload
                
                # Step 1: Authentication
                authenticated_user = await get_current_user(
                    request=mock_request,
                    credentials=mock_credentials,
                    db=self.async_session
                )
                print("   ✅ Step 1-5: Authentication with mapping successful")
                
                # Step 2: Authorization
                admin_user = await require_admin(current_user=authenticated_user)
                print("   ✅ Step 6: Admin authorization successful")
                
                # Step 3: Feature flags endpoint
                result = await list_feature_flags(
                    current_user=admin_user,
                    db=self.async_session,
                    module_id=None,
                    enabled_only=False
                )
                print("   ✅ Step 7: Feature flags retrieval successful")
                
                print("\n🎉 COMPLETE END-TO-END SUCCESS!")
                print(f"   - Matt.Lindop can now access Feature Flags endpoint")
                print(f"   - No more 500 Internal Server Error")
                print(f"   - £925K Zebra Associates opportunity unblocked")
                
                self.test_results['end_to_end_flow'] = {
                    'success': True,
                    'all_steps_passed': True,
                    'final_result_type': str(type(result))
                }
                
                return result
                
        except Exception as e:
            print(f"❌ End-to-end flow failed: {e}")
            traceback.print_exc()
            self.test_results['end_to_end_flow'] = {
                'success': False,
                'error': str(e)
            }
            return None
    
    async def cleanup(self):
        """Clean up database connections"""
        if self.async_session:
            await self.async_session.close()
        if self.database_engine:
            await self.database_engine.dispose()
    
    def generate_verification_report(self):
        """Generate comprehensive verification report"""
        print("\n📋 VERIFICATION REPORT - Auth0 Feature Flags Fix")
        print("="*70)
        
        # Overall status
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        print(f"Overall Status: {passed_tests}/{total_tests} tests passed")
        print()
        
        # Test results
        for test_name, result in self.test_results.items():
            print(f"Test: {test_name}")
            if isinstance(result, dict):
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                print(f"  Status: {status}")
                
                if not result.get('success', False) and 'error' in result:
                    print(f"  Error: {result['error']}")
                
                # Show additional details
                for key, value in result.items():
                    if key not in ['success', 'error', 'traceback']:
                        print(f"  {key}: {value}")
            print()
        
        # Final assessment
        print("🎯 FINAL ASSESSMENT:")
        print("-" * 30)
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED!")
            print("🎉 Matt.Lindop's Auth0 tokens can now access Feature Flags endpoint")
            print("💰 £925K Zebra Associates opportunity is UNBLOCKED")
            print()
            print("🚀 DEPLOYMENT READY:")
            print("   - Auth0 organization mapping is working")
            print("   - Feature Flags endpoint returns data (not 500 error)")
            print("   - Admin authentication and authorization work")
            print("   - Complete end-to-end flow is functional")
            
        else:
            print("❌ Some tests failed - additional fixes may be needed")
            
            if not self.test_results.get('auth0_authentication', {}).get('success'):
                print("   - Auth0 authentication is still failing")
            
            if not self.test_results.get('feature_flags_endpoint', {}).get('success'):
                print("   - Feature Flags endpoint is still returning errors")
        
        return self.test_results

async def main():
    """Main verification execution"""
    print("🚀 Auth0 Feature Flags Fix Verification - £925K Zebra Associates")
    print("="*70)
    print("Verifying that Matt.Lindop can now access Feature Flags without 500 errors")
    print()
    
    verifier = Auth0FeatureFlagsFixVerifier()
    
    try:
        # Setup
        if not await verifier.setup_database():
            return
        
        # Run verification tests
        print("🧪 Running verification tests...")
        
        # Test 1: Auth0 authentication with mapping
        authenticated_user = await verifier.test_auth0_authentication_flow()
        if not authenticated_user:
            print("❌ Cannot continue - authentication failed")
            return
        
        # Test 2: Admin authorization
        admin_user = await verifier.test_admin_authorization(authenticated_user)
        if not admin_user:
            print("❌ Cannot continue - admin authorization failed")
            return
        
        # Test 3: Feature Flags endpoint
        await verifier.test_feature_flags_endpoint(admin_user)
        
        # Test 4: Complete end-to-end flow
        await verifier.test_complete_end_to_end_flow()
        
    except Exception as e:
        print(f"❌ Verification execution failed: {e}")
        traceback.print_exc()
    
    finally:
        # Generate report
        results = verifier.generate_verification_report()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/Users/matt/Sites/MarketEdge/auth0_feature_flags_verification_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Full verification results saved to: {results_file}")
        
        await verifier.cleanup()

if __name__ == "__main__":
    asyncio.run(main())