#!/usr/bin/env python3
"""
Comprehensive Auth0 Feature Flags 500 Error Diagnostic Tool

Debugging the exact cause of 500 Internal Server Error when Matt.Lindop's
Auth0 tokens try to access GET /api/v1/admin/feature-flags endpoint.

This test will reveal:
1. Where in the auth flow the failure occurs
2. Database connection and async session issues
3. Auth0 token validation problems
4. Feature flags service errors
5. AdminService errors

Key areas to investigate:
- Auth0 token verification fallback functionality
- Async/sync database session mismatches
- Feature flags table existence and data
- AdminService.get_feature_flags() execution
- AuditService logging capability
"""

import asyncio
import httpx
import json
import traceback
import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.insert(0, '/Users/matt/Sites/MarketEdge')

# Import after setting path
from app.auth.dependencies import get_current_user, require_admin, verify_auth0_token
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService
from app.core.database import get_async_db
from app.models.user import User, UserRole
from app.models.feature_flags import FeatureFlag
from app.models.organisation import Organisation
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

class Auth0TokenDebugger:
    """Comprehensive debugger for Auth0 token 500 errors"""
    
    def __init__(self):
        self.results = {}
        self.database_engine = None
        self.async_session = None
        
    async def setup_database(self):
        """Setup database connection for testing"""
        try:
            print("📊 Setting up database connection...")
            
            # Use the same database URL as the app
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
            traceback.print_exc()
            self.results['database_setup'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_database_connectivity(self):
        """Test basic database connectivity and required tables"""
        print("\n🔍 Testing database connectivity and table structure...")
        
        try:
            # Test basic connection
            result = await self.async_session.execute(text("SELECT 1"))
            print("✅ Basic database query successful")
            
            # Check required tables exist
            tables_to_check = [
                'users', 
                'organisations', 
                'feature_flags', 
                'audit_logs'
            ]
            
            table_status = {}
            for table in tables_to_check:
                try:
                    result = await self.async_session.execute(
                        text(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                    )
                    count = result.scalar()
                    table_status[table] = {'exists': True, 'count': count}
                    print(f"✅ Table '{table}' exists with {count} records")
                except Exception as e:
                    table_status[table] = {'exists': False, 'error': str(e)}
                    print(f"❌ Table '{table}' check failed: {e}")
            
            self.results['database_tables'] = table_status
            return True
            
        except Exception as e:
            print(f"❌ Database connectivity test failed: {e}")
            self.results['database_connectivity'] = {'success': False, 'error': str(e)}
            return False
    
    def create_mock_auth0_token(self) -> str:
        """Create a realistic Auth0 token structure for Matt.Lindop"""
        # This simulates what Matt.Lindop's Auth0 token would look like
        return "mock_auth0_token_matt_lindop_super_admin_zebra_associates"
    
    def create_mock_auth0_user_info(self) -> Dict[str, Any]:
        """Create mock Auth0 user info response for Matt.Lindop"""
        return {
            "sub": "auth0|matt_lindop_zebra_id",
            "email": "matt.lindop@zebra.associates",
            "user_role": "super_admin",
            "role": "super_admin", 
            "organisation_id": "zebra-associates-org-id",
            "tenant_id": "zebra-associates-org-id",
            "type": "auth0_access",
            "iss": f"https://{settings.AUTH0_DOMAIN}/",
            "aud": [f"https://{settings.AUTH0_DOMAIN}/userinfo"],
            "permissions": ["read:admin", "write:admin", "manage:feature_flags"]
        }
    
    async def test_auth0_verification_function(self):
        """Test the Auth0 token verification function directly"""
        print("\n🔐 Testing Auth0 token verification function...")
        
        try:
            # Create mock token and expected response
            mock_token = self.create_mock_auth0_token()
            mock_user_info = self.create_mock_auth0_user_info()
            
            # Patch the auth0_client.get_user_info method
            with patch('app.auth.auth0.auth0_client.get_user_info') as mock_get_user_info:
                mock_get_user_info.return_value = mock_user_info
                
                # Test the verify_auth0_token function
                payload = await verify_auth0_token(mock_token)
                
                if payload:
                    print("✅ Auth0 token verification function works")
                    print(f"   - Returned payload: {json.dumps(payload, indent=2)}")
                    self.results['auth0_verification'] = {
                        'success': True, 
                        'payload': payload
                    }
                    return payload
                else:
                    print("❌ Auth0 token verification returned None")
                    self.results['auth0_verification'] = {
                        'success': False, 
                        'error': 'verify_auth0_token returned None'
                    }
                    return None
                    
        except Exception as e:
            print(f"❌ Auth0 verification test failed: {e}")
            traceback.print_exc()
            self.results['auth0_verification'] = {'success': False, 'error': str(e)}
            return None
    
    async def create_test_user_and_org(self):
        """Create test user and organization for Matt.Lindop"""
        print("\n👤 Creating test user and organization...")
        
        try:
            # Check if test user already exists
            result = await self.async_session.execute(
                select(User).where(User.email == "matt.lindop@zebra.associates")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("✅ Test user already exists")
                self.results['test_user'] = {
                    'created': False,
                    'user_id': str(existing_user.id),
                    'role': existing_user.role.value
                }
                return existing_user
            
            # Create test organization
            test_org = Organisation(
                id=uuid.UUID("12345678-1234-5678-9abc-123456789012"),
                name="Zebra Associates Test",
                domain="zebra.associates",
                sic_code="59140",  # Cinema industry
                subscription_plan="enterprise",
                is_active=True
            )
            
            # Create test user
            test_user = User(
                id=uuid.UUID("87654321-4321-8765-dcba-210987654321"),
                email="matt.lindop@zebra.associates",
                first_name="Matt",
                last_name="Lindop",
                organisation_id=test_org.id,
                role=UserRole.super_admin,
                is_active=True
            )
            
            self.async_session.add(test_org)
            self.async_session.add(test_user)
            await self.async_session.commit()
            await self.async_session.refresh(test_user)
            
            print(f"✅ Created test user: {test_user.email} with role: {test_user.role.value}")
            self.results['test_user'] = {
                'created': True,
                'user_id': str(test_user.id),
                'role': test_user.role.value
            }
            return test_user
            
        except Exception as e:
            await self.async_session.rollback()
            print(f"❌ Failed to create test user: {e}")
            traceback.print_exc()
            self.results['test_user'] = {'success': False, 'error': str(e)}
            return None
    
    async def test_get_current_user_auth_flow(self, test_user: User):
        """Test the get_current_user authentication flow with Auth0 token"""
        print("\n🔄 Testing get_current_user authentication flow...")
        
        try:
            # Create mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/v1/admin/feature-flags"
            mock_request.state = MagicMock()
            
            # Create mock credentials with Auth0 token
            mock_credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=self.create_mock_auth0_token()
            )
            
            # Patch the Auth0 verification to return our test user info
            mock_user_info = self.create_mock_auth0_user_info()
            mock_user_info['sub'] = str(test_user.id)  # Use actual test user ID
            
            # Patch both the JWT verification (to fail) and Auth0 verification (to succeed)
            with patch('app.auth.dependencies.verify_token') as mock_verify_token, \
                 patch('app.auth.dependencies.verify_auth0_token') as mock_verify_auth0:
                
                # Make internal JWT verification fail (simulating real scenario)
                mock_verify_token.return_value = None
                
                # Make Auth0 verification succeed
                mock_verify_auth0.return_value = mock_user_info
                
                # Test get_current_user function
                try:
                    authenticated_user = await get_current_user(
                        request=mock_request,
                        credentials=mock_credentials,
                        db=self.async_session
                    )
                    
                    print("✅ get_current_user authentication successful")
                    print(f"   - User: {authenticated_user.email}")
                    print(f"   - Role: {authenticated_user.role.value}")
                    print(f"   - Active: {authenticated_user.is_active}")
                    
                    self.results['get_current_user'] = {
                        'success': True,
                        'user_email': authenticated_user.email,
                        'user_role': authenticated_user.role.value,
                        'auth0_fallback_used': True
                    }
                    
                    return authenticated_user
                    
                except HTTPException as http_exc:
                    print(f"❌ get_current_user raised HTTPException: {http_exc.status_code} - {http_exc.detail}")
                    self.results['get_current_user'] = {
                        'success': False,
                        'error_type': 'HTTPException',
                        'status_code': http_exc.status_code,
                        'detail': http_exc.detail
                    }
                    return None
                    
        except Exception as e:
            print(f"❌ get_current_user test failed: {e}")
            traceback.print_exc()
            self.results['get_current_user'] = {'success': False, 'error': str(e)}
            return None
    
    async def test_require_admin_function(self, test_user: User):
        """Test the require_admin function with the authenticated user"""
        print("\n👨‍💼 Testing require_admin function...")
        
        try:
            # Test require_admin dependency
            admin_user = await require_admin(current_user=test_user)
            
            print("✅ require_admin function successful")
            print(f"   - Admin user: {admin_user.email}")
            print(f"   - Admin role: {admin_user.role.value}")
            
            self.results['require_admin'] = {
                'success': True,
                'admin_user': admin_user.email,
                'admin_role': admin_user.role.value
            }
            
            return admin_user
            
        except HTTPException as http_exc:
            print(f"❌ require_admin raised HTTPException: {http_exc.status_code} - {http_exc.detail}")
            self.results['require_admin'] = {
                'success': False,
                'error_type': 'HTTPException',
                'status_code': http_exc.status_code,
                'detail': http_exc.detail
            }
            return None
            
        except Exception as e:
            print(f"❌ require_admin test failed: {e}")
            self.results['require_admin'] = {'success': False, 'error': str(e)}
            return None
    
    async def create_test_feature_flags(self):
        """Create some test feature flags for testing"""
        print("\n🚩 Creating test feature flags...")
        
        try:
            # Check if feature flags already exist
            result = await self.async_session.execute(select(FeatureFlag))
            existing_flags = result.scalars().all()
            
            if existing_flags:
                print(f"✅ Found {len(existing_flags)} existing feature flags")
                self.results['test_feature_flags'] = {
                    'created': False,
                    'existing_count': len(existing_flags)
                }
                return existing_flags
            
            # Get test user for created_by field
            result = await self.async_session.execute(
                select(User).where(User.email == "matt.lindop@zebra.associates")
            )
            test_user = result.scalar_one_or_none()
            
            if not test_user:
                print("❌ Test user not found for creating feature flags")
                return []
            
            # Create test feature flags
            test_flags = [
                FeatureFlag(
                    flag_key="zebra_cinema_analytics",
                    name="Zebra Cinema Analytics",
                    description="Advanced cinema analytics for Zebra Associates",
                    is_enabled=True,
                    rollout_percentage=100,
                    created_by=test_user.id,
                    config={"industry": "cinema", "tier": "enterprise"}
                ),
                FeatureFlag(
                    flag_key="admin_dashboard_v2",
                    name="Admin Dashboard V2",
                    description="New admin dashboard interface",
                    is_enabled=True,
                    rollout_percentage=50,
                    created_by=test_user.id,
                    config={"ui_version": "v2"}
                )
            ]
            
            for flag in test_flags:
                self.async_session.add(flag)
            
            await self.async_session.commit()
            
            print(f"✅ Created {len(test_flags)} test feature flags")
            self.results['test_feature_flags'] = {
                'created': True,
                'flag_count': len(test_flags)
            }
            
            return test_flags
            
        except Exception as e:
            await self.async_session.rollback()
            print(f"❌ Failed to create test feature flags: {e}")
            traceback.print_exc()
            self.results['test_feature_flags'] = {'success': False, 'error': str(e)}
            return []
    
    async def test_admin_service_get_feature_flags(self, admin_user: User):
        """Test AdminService.get_feature_flags() directly"""
        print("\n⚙️ Testing AdminService.get_feature_flags()...")
        
        try:
            # Create AdminService instance
            admin_service = AdminService(self.async_session)
            
            print("   - Created AdminService instance")
            
            # Test get_feature_flags method
            feature_flags = await admin_service.get_feature_flags(
                admin_user=admin_user,
                module_id=None,
                enabled_only=False
            )
            
            print("✅ AdminService.get_feature_flags() successful")
            print(f"   - Retrieved {len(feature_flags)} feature flags")
            
            for flag in feature_flags[:3]:  # Show first 3 flags
                print(f"   - Flag: {flag.get('flag_key')} (enabled: {flag.get('is_enabled')})")
            
            self.results['admin_service_get_feature_flags'] = {
                'success': True,
                'flag_count': len(feature_flags),
                'flags_sample': feature_flags[:2] if feature_flags else []
            }
            
            return feature_flags
            
        except Exception as e:
            print(f"❌ AdminService.get_feature_flags() failed: {e}")
            traceback.print_exc()
            self.results['admin_service_get_feature_flags'] = {
                'success': False, 
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return None
    
    async def test_audit_service_functionality(self, admin_user: User):
        """Test AuditService logging functionality"""
        print("\n📝 Testing AuditService functionality...")
        
        try:
            # Create AuditService instance
            audit_service = AuditService(self.async_session)
            
            print("   - Created AuditService instance")
            
            # Test logging an action
            from app.models.audit_log import AuditAction
            await audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.READ,
                resource_type="feature_flags",
                description="Test audit log from diagnostic tool",
                success=True
            )
            
            await self.async_session.commit()
            
            print("✅ AuditService.log_action() successful")
            
            self.results['audit_service'] = {'success': True}
            return True
            
        except Exception as e:
            await self.async_session.rollback()
            print(f"❌ AuditService test failed: {e}")
            traceback.print_exc()
            self.results['audit_service'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_full_endpoint_simulation(self, admin_user: User):
        """Simulate the full /admin/feature-flags endpoint execution"""
        print("\n🎯 Simulating full /admin/feature-flags endpoint...")
        
        try:
            # Import the actual admin router function
            from app.api.api_v1.endpoints.admin import list_feature_flags
            
            print("   - Imported list_feature_flags function")
            
            # Execute the endpoint function directly
            result = await list_feature_flags(
                current_user=admin_user,
                db=self.async_session,
                module_id=None,
                enabled_only=False
            )
            
            print("✅ Full endpoint simulation successful")
            print(f"   - Response: {json.dumps(result, indent=2, default=str)}")
            
            self.results['full_endpoint_simulation'] = {
                'success': True,
                'response': result
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Full endpoint simulation failed: {e}")
            traceback.print_exc()
            self.results['full_endpoint_simulation'] = {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            return None
    
    async def test_http_request_simulation(self):
        """Simulate an actual HTTP request to the feature flags endpoint"""
        print("\n🌐 Testing HTTP request simulation...")
        
        # This would require the FastAPI app to be running, so we'll skip for now
        # but document how to test it manually
        
        test_curl_command = f"""
        # Test command to run manually:
        curl -X GET "http://localhost:8000/api/v1/admin/feature-flags" \\
             -H "Authorization: Bearer {self.create_mock_auth0_token()}" \\
             -H "Content-Type: application/json" \\
             -v
        """
        
        print(f"💡 Manual HTTP test command:")
        print(test_curl_command)
        
        self.results['http_simulation'] = {
            'manual_test_provided': True,
            'curl_command': test_curl_command.strip()
        }
    
    async def cleanup(self):
        """Clean up database connections and test data"""
        print("\n🧹 Cleaning up...")
        
        try:
            if self.async_session:
                await self.async_session.close()
            
            if self.database_engine:
                await self.database_engine.dispose()
                
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def generate_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📋 COMPREHENSIVE DIAGNOSTIC REPORT")
        print("="*80)
        
        # Overall success status
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results.values() 
                              if isinstance(result, dict) and result.get('success', False))
        
        print(f"Overall Status: {successful_tests}/{total_tests} tests passed")
        print()
        
        # Detailed results
        for test_name, result in self.results.items():
            print(f"Test: {test_name}")
            if isinstance(result, dict):
                if result.get('success', False):
                    print("  Status: ✅ PASSED")
                else:
                    print("  Status: ❌ FAILED")
                    if 'error' in result:
                        print(f"  Error: {result['error']}")
                
                # Print additional details
                for key, value in result.items():
                    if key not in ['success', 'error']:
                        print(f"  {key}: {value}")
            else:
                print(f"  Result: {result}")
            print()
        
        # Recommendations
        print("🔧 RECOMMENDATIONS:")
        print("-" * 40)
        
        if not self.results.get('database_connectivity', {}).get('success', False):
            print("1. ❌ Database connectivity failed - check DATABASE_URL and connection")
        
        if not self.results.get('auth0_verification', {}).get('success', False):
            print("2. ❌ Auth0 verification failed - check auth0_client.get_user_info()")
        
        if not self.results.get('get_current_user', {}).get('success', False):
            print("3. ❌ get_current_user failed - check async session handling")
        
        if not self.results.get('admin_service_get_feature_flags', {}).get('success', False):
            print("4. ❌ AdminService.get_feature_flags() failed - this is likely the root cause!")
            
        print()
        print("🎯 ROOT CAUSE ANALYSIS:")
        print("-" * 30)
        
        # Determine most likely root cause
        if self.results.get('admin_service_get_feature_flags', {}).get('success', False):
            print("✅ AdminService works - issue is likely in auth flow")
        elif not self.results.get('database_connectivity', {}).get('success', False):
            print("❌ Database connectivity issue - fix database connection first")
        elif not self.results.get('auth0_verification', {}).get('success', False):
            print("❌ Auth0 verification issue - auth0_client.get_user_info() not working")
        else:
            admin_error = self.results.get('admin_service_get_feature_flags', {}).get('error')
            if admin_error:
                print(f"❌ AdminService.get_feature_flags() error: {admin_error}")
                print("   This is likely the root cause of the 500 error!")
        
        return self.results

async def main():
    """Main diagnostic execution"""
    print("🚀 Auth0 Feature Flags 500 Error Diagnostic Tool")
    print("=" * 60)
    print("Investigating why Auth0 tokens cause 500 errors on Feature Flags endpoint")
    print()
    
    debugger = Auth0TokenDebugger()
    
    try:
        # Setup database
        if not await debugger.setup_database():
            print("❌ Cannot continue without database connection")
            return
        
        # Run diagnostic tests in order
        await debugger.test_database_connectivity()
        await debugger.test_auth0_verification_function()
        
        # Create test user and organization
        test_user = await debugger.create_test_user_and_org()
        if not test_user:
            print("❌ Cannot continue without test user")
            return
        
        # Test authentication flow
        authenticated_user = await debugger.test_get_current_user_auth_flow(test_user)
        if not authenticated_user:
            print("❌ Authentication flow failed")
            return
        
        # Test admin authorization
        admin_user = await debugger.test_require_admin_function(authenticated_user)
        if not admin_user:
            print("❌ Admin authorization failed")
            return
        
        # Create test data
        await debugger.create_test_feature_flags()
        
        # Test services
        await debugger.test_audit_service_functionality(admin_user)
        await debugger.test_admin_service_get_feature_flags(admin_user)
        
        # Test full endpoint
        await debugger.test_full_endpoint_simulation(admin_user)
        
        # Test HTTP simulation
        await debugger.test_http_request_simulation()
        
    except Exception as e:
        print(f"❌ Diagnostic execution failed: {e}")
        traceback.print_exc()
    
    finally:
        # Generate report
        results = debugger.generate_report()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/Users/matt/Sites/MarketEdge/auth0_feature_flags_diagnostic_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Full results saved to: {results_file}")
        
        # Cleanup
        await debugger.cleanup()

if __name__ == "__main__":
    asyncio.run(main())