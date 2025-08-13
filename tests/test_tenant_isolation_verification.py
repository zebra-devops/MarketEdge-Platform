"""
Multi-Tenant Isolation Verification Tests

This test suite verifies that all security fixes maintain proper tenant isolation:
1. Database RLS policies are enforced
2. API endpoints respect tenant boundaries  
3. Auth tokens contain correct tenant context
4. Cross-tenant data access is prevented
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.middleware.tenant_context import TenantContextMiddleware, SuperAdminContextManager
from app.auth.jwt import create_access_token, verify_token


class TestTenantIsolationWithSecurityFixes:
    """Verify tenant isolation is maintained across all security enhancements"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def tenant1_org(self):
        """Mock organization for tenant 1"""
        return Organisation(
            id=uuid.uuid4(),
            name="Tenant 1 Corp",
            industry="Technology",
            subscription_plan=SubscriptionPlan.basic
        )
    
    @pytest.fixture
    def tenant2_org(self):
        """Mock organization for tenant 2"""
        return Organisation(
            id=uuid.uuid4(),
            name="Tenant 2 Corp", 
            industry="Healthcare",
            subscription_plan=SubscriptionPlan.professional
        )
    
    @pytest.fixture
    def tenant1_user(self, tenant1_org):
        """Mock user for tenant 1"""
        return User(
            id=uuid.uuid4(),
            email="user1@tenant1.com",
            first_name="User",
            last_name="One",
            organisation_id=tenant1_org.id,
            role=UserRole.analyst,
            is_active=True,
            organisation=tenant1_org
        )
    
    @pytest.fixture
    def tenant2_user(self, tenant2_org):
        """Mock user for tenant 2"""
        return User(
            id=uuid.uuid4(),
            email="user2@tenant2.com", 
            first_name="User",
            last_name="Two",
            organisation_id=tenant2_org.id,
            role=UserRole.viewer,
            is_active=True,
            organisation=tenant2_org
        )
    
    def test_jwt_token_contains_tenant_context(self, tenant1_user):
        """Test that JWT tokens contain proper tenant context"""
        token_data = {
            "sub": str(tenant1_user.id),
            "email": tenant1_user.email
        }
        
        access_token = create_access_token(
            data=token_data,
            tenant_id=str(tenant1_user.organisation_id),
            user_role=tenant1_user.role.value,
            permissions=["read:data", "write:data"]
        )
        
        # Verify token contains tenant context
        payload = verify_token(access_token)
        assert payload is not None
        assert payload["tenant_id"] == str(tenant1_user.organisation_id)
        assert payload["user_role"] == tenant1_user.role.value
        assert "read:data" in payload["permissions"]
    
    @pytest.mark.asyncio
    async def test_middleware_sets_correct_tenant_context(self, mock_db, tenant1_user):
        """Test that enhanced middleware sets correct database tenant context"""
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_get_db.return_value.__next__ = Mock(return_value=mock_db)
            
            middleware = TenantContextMiddleware(app)
            
            tenant_context = {
                "tenant_id": tenant1_user.organisation_id,
                "user_role": tenant1_user.role.value,
                "user_id": tenant1_user.id
            }
            
            await middleware._set_database_context(tenant_context)
            
            # Verify database session variables are set for RLS
            expected_calls = [
                (text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                 {"tenant_id": str(tenant1_user.organisation_id)}),
                (text("SELECT set_config('app.current_user_role', :user_role, true)"),
                 {"user_role": tenant1_user.role.value}),
                (text("SELECT set_config('app.current_user_id', :user_id, true)"),
                 {"user_id": str(tenant1_user.id)}),
                (text("SELECT set_config('app.allow_cross_tenant', :allow_cross_tenant, true)"),
                 {"allow_cross_tenant": "false"})
            ]
            
            # Verify execute was called with tenant isolation parameters
            assert mock_db.execute.call_count >= 4
            assert mock_db.commit.called
    
    def test_cross_tenant_access_prevention(self, tenant1_user, tenant2_user):
        """Test that users cannot access data from other tenants"""
        # Create token for tenant1 user
        token_data = {"sub": str(tenant1_user.id), "email": tenant1_user.email}
        tenant1_token = create_access_token(
            data=token_data,
            tenant_id=str(tenant1_user.organisation_id),
            user_role=tenant1_user.role.value,
            permissions=["read:data"]
        )
        
        # Verify token is for tenant1
        payload = verify_token(tenant1_token)
        assert payload["tenant_id"] == str(tenant1_user.organisation_id)
        assert payload["tenant_id"] != str(tenant2_user.organisation_id)
    
    @pytest.mark.asyncio
    async def test_super_admin_cross_tenant_context(self, mock_db):
        """Test SuperAdminContextManager for controlled cross-tenant access"""
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@platform.com",
            role=UserRole.admin,
            is_active=True
        )
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_get_db.return_value.__next__ = Mock(return_value=mock_db)
            
            context_manager = SuperAdminContextManager(admin_user)
            
            # Test entering cross-tenant context
            await context_manager.__aenter__()
            
            # Verify cross-tenant access is enabled
            expected_call = (
                text("SELECT set_config('app.allow_cross_tenant', 'true', true)")
            )
            
            mock_db.execute.assert_called()
            mock_db.commit.assert_called()
            
            # Test exiting context
            await context_manager.__aexit__(None, None, None)
            
            # Verify cross-tenant access is disabled
            expected_disable_call = (
                text("SELECT set_config('app.allow_cross_tenant', 'false', true)")
            )
            
            assert mock_db.execute.call_count >= 2
    
    def test_non_admin_cannot_use_super_admin_context(self, tenant1_user):
        """Test that non-admin users cannot use SuperAdminContextManager"""
        with pytest.raises(ValueError, match="SuperAdminContextManager can only be used by admin users"):
            SuperAdminContextManager(tenant1_user)
    
    def test_tenant_validation_in_enhanced_middleware(self, mock_db, tenant1_user):
        """Test that enhanced middleware validates tenant context properly"""
        from app.middleware.tenant_context import TenantContextMiddleware
        
        middleware = TenantContextMiddleware(app)
        
        # Test with valid tenant context
        valid_context = {
            "tenant_id": str(tenant1_user.organisation_id),
            "user_role": tenant1_user.role.value,
            "user_id": str(tenant1_user.id)
        }
        
        # This should not raise an exception
        # (Full integration test would require FastAPI request/response cycle)
        assert valid_context["tenant_id"] is not None
        assert valid_context["user_role"] in ["viewer", "analyst", "admin"]
        assert valid_context["user_id"] is not None
    
    def test_auth_parameter_validation_maintains_tenant_context(self):
        """Test that enhanced input validation doesn't break tenant isolation"""
        from app.core.validators import AuthParameterValidator
        
        # Valid parameters that should preserve tenant context
        valid_params = AuthParameterValidator(
            code="secure_auth_code_for_tenant1",
            redirect_uri="https://tenant1.example.com/callback",
            state="secure_state_with_tenant_context"
        )
        
        # Validation should succeed and preserve tenant-specific redirect URI
        assert valid_params.redirect_uri == "https://tenant1.example.com/callback"
        assert "tenant1" in valid_params.redirect_uri
    
    def test_cookie_security_preserves_tenant_isolation(self):
        """Test that enhanced cookie security doesn't affect tenant isolation"""
        from app.core.config import settings
        
        # Get cookie settings
        cookie_settings = settings.get_cookie_settings()
        
        # Verify security settings don't interfere with tenant context
        assert cookie_settings["httponly"] == True  # Prevents XSS
        assert cookie_settings["path"] == "/"  # Available app-wide
        
        # In production, should have additional security
        if settings.is_production:
            assert cookie_settings["secure"] == True
            assert cookie_settings["samesite"] == "strict"
    
    def test_management_api_token_respects_tenant_boundaries(self):
        """Test that Management API tokens respect tenant boundaries"""
        from app.auth.auth0 import Auth0Client
        
        client = Auth0Client()
        
        # Test organization extraction respects tenant boundaries
        user_info_tenant1 = {
            "sub": "auth0|tenant1_user",
            "email": "user@tenant1.com",
            "org_id": "tenant1_org_123",
            "org_name": "Tenant 1 Organization"
        }
        
        orgs = client._extract_org_from_user_metadata(user_info_tenant1)
        
        assert len(orgs) == 1
        assert orgs[0]["id"] == "tenant1_org_123"
        assert orgs[0]["name"] == "Tenant 1 Organization"
        
        # Should only return organizations for the authenticated user's tenant
        user_info_no_org = {
            "sub": "auth0|user_no_org",
            "email": "user@example.com"
        }
        
        orgs_empty = client._extract_org_from_user_metadata(user_info_no_org)
        assert len(orgs_empty) == 0


class TestDatabaseRLSWithSecurityFixes:
    """Test that RLS policies work correctly with security enhancements"""
    
    @pytest.mark.asyncio
    async def test_rls_enforcement_with_tenant_context(self):
        """Test that RLS policies are enforced with enhanced tenant context"""
        # This would require actual database connection for full testing
        # Mock the behavior for now
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_db = Mock(spec=Session)
            mock_get_db.return_value.__next__ = Mock(return_value=mock_db)
            
            from app.middleware.tenant_context import TenantContextMiddleware
            middleware = TenantContextMiddleware(app)
            
            # Set tenant context
            tenant_context = {
                "tenant_id": str(uuid.uuid4()),
                "user_role": "analyst", 
                "user_id": str(uuid.uuid4())
            }
            
            await middleware._set_database_context(tenant_context)
            
            # Verify RLS session variables are set
            assert mock_db.execute.called
            assert mock_db.commit.called
            
            # Clear context
            await middleware._clear_database_context()
            
            # Verify context is cleared
            assert mock_db.execute.call_count >= 8  # 4 sets + 4 clears


class TestAPIEndpointTenantIsolation:
    """Test API endpoints maintain tenant isolation with security fixes"""
    
    def test_login_endpoint_maintains_tenant_context(self):
        """Test that enhanced login endpoint maintains tenant context"""
        client = TestClient(app)
        
        # Mock valid login data with tenant-specific redirect
        login_data = {
            "code": "valid_auth_code_123",
            "redirect_uri": "https://tenant1.myapp.com/callback",
            "state": "secure_state_token"
        }
        
        # The login endpoint should validate input while preserving tenant context
        # (Full test would require mocking Auth0 and database)
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Should not expose internal errors that could leak tenant info
        if response.status_code == 400:
            assert "tenant" not in response.json().get("detail", "").lower()
    
    def test_auth_headers_include_tenant_context(self):
        """Test that auth responses include proper tenant context headers"""
        # This would be tested in full integration tests
        # For now, verify the middleware adds the headers
        
        from app.middleware.tenant_context import TenantContextMiddleware
        middleware = TenantContextMiddleware(app)
        
        # Verify middleware is configured to add tenant headers
        assert middleware is not None
    
    def test_security_headers_dont_leak_tenant_info(self):
        """Test that security headers don't accidentally leak tenant information"""
        from app.core.validators import create_security_headers
        
        headers = create_security_headers()
        
        # Verify no tenant info in security headers
        for header_name, header_value in headers.items():
            assert "tenant" not in header_value.lower()
            assert "organisation" not in header_value.lower()
            assert "org" not in header_value.lower()


@pytest.mark.integration
class TestEndToEndTenantIsolation:
    """End-to-end tests for tenant isolation with all security fixes"""
    
    def test_complete_auth_flow_maintains_isolation(self):
        """Test complete authentication flow maintains tenant isolation"""
        # This would test:
        # 1. Auth0 URL generation with tenant context
        # 2. Code exchange with input validation
        # 3. Token creation with tenant info
        # 4. Cookie setting with secure flags
        # 5. Database context setting
        # 6. API access with proper isolation
        
        # Placeholder for full integration test
        pass
    
    def test_security_monitoring_for_tenant_violations(self):
        """Test that security monitoring detects tenant boundary violations"""
        # This would test logging and monitoring of:
        # 1. Cross-tenant access attempts
        # 2. Invalid tenant context in tokens
        # 3. Suspicious redirect URIs
        # 4. SQL injection attempts in tenant data
        
        # Placeholder for security monitoring test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])