"""
Enhanced Authentication Test Suite

Tests for the enhanced Auth0 integration with multi-tenant authentication,
JWT improvements, secure token refresh, and session management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.auth0 import Auth0Client, auth0_client
from app.auth.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token,
    get_user_permissions,
    should_refresh_token,
    extract_tenant_context_from_token
)
from app.auth.dependencies import get_current_user, require_permission, require_role
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan


class TestAuth0Client:
    """Test enhanced Auth0 client functionality"""

    def setup_method(self):
        self.auth0_client = Auth0Client()

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval"""
        mock_user_info = {
            "sub": "auth0|user123",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_user_info
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.auth0_client.get_user_info("test_token")
            
            assert result == mock_user_info

    @pytest.mark.asyncio
    async def test_get_user_info_retry_on_timeout(self):
        """Test retry logic on timeout"""
        import httpx
        
        with patch('httpx.AsyncClient') as mock_client:
            # First call times out, second succeeds
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                httpx.TimeoutException("Request timeout"),
                Mock(json=lambda: {"sub": "test"}, raise_for_status=lambda: None)
            ]
            
            with patch.object(self.auth0_client, '_exponential_backoff', return_value=None):
                result = await self.auth0_client.get_user_info("test_token")
                
            assert result == {"sub": "test"}

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_with_state(self):
        """Test token exchange with CSRF state parameter"""
        mock_token_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_token_response
            mock_response.raise_for_status.return_value = None
            mock_response.is_success = True
            mock_response.status_code = 200
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await self.auth0_client.exchange_code_for_token(
                code="test_code",
                redirect_uri="https://example.com/callback",
                state="secure_state_token"
            )
            
            assert result == mock_token_response
            
            # Verify state was included in the request
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            assert call_args[1]["data"]["state"] == "secure_state_token"

    def test_get_authorization_url_security_features(self):
        """Test authorization URL with enhanced security features"""
        redirect_uri = "https://example.com/callback"
        
        auth_url = self.auth0_client.get_authorization_url(redirect_uri)
        
        # Check that security parameters are included
        assert "prompt=select_account" in auth_url
        assert "max_age=3600" in auth_url
        assert "state=" in auth_url
        assert "scope=openid%20profile%20email" in auth_url

    def test_validate_redirect_uri_security(self):
        """Test redirect URI validation"""
        # Valid URIs
        assert self.auth0_client._validate_redirect_uri("https://example.com/callback")
        assert self.auth0_client._validate_redirect_uri("http://localhost:3000/callback")
        
        # Invalid URIs
        assert not self.auth0_client._validate_redirect_uri("")
        assert not self.auth0_client._validate_redirect_uri("javascript:alert('xss')")
        assert not self.auth0_client._validate_redirect_uri("ftp://example.com")

    @pytest.mark.asyncio
    async def test_revoke_token(self):
        """Test token revocation"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await self.auth0_client.revoke_token("refresh_token", "refresh_token")
            
            assert result is True


class TestJWTEnhancements:
    """Test enhanced JWT functionality"""

    def test_create_access_token_with_tenant_context(self):
        """Test access token creation with tenant context"""
        user_data = {"sub": "user123", "email": "test@example.com"}
        tenant_id = "org456"
        user_role = "admin"
        permissions = ["read:users", "write:users"]
        
        token = create_access_token(
            data=user_data,
            tenant_id=tenant_id,
            user_role=user_role,
            permissions=permissions
        )
        
        # Verify token can be decoded and contains expected claims
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["tenant_id"] == tenant_id
        assert payload["role"] == user_role
        assert payload["permissions"] == permissions
        assert "jti" in payload  # Unique token ID
        assert "iat" in payload  # Issued at
        assert "exp" in payload  # Expiration

    def test_create_refresh_token_with_family(self):
        """Test refresh token creation with token family"""
        user_data = {"sub": "user123"}
        tenant_id = "org456"
        token_family = "family789"
        
        token = create_refresh_token(
            data=user_data,
            tenant_id=tenant_id,
            token_family=token_family
        )
        
        payload = verify_token(token, expected_type="refresh")
        
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["tenant_id"] == tenant_id
        assert payload["family"] == token_family

    def test_verify_token_with_type_validation(self):
        """Test token verification with type validation"""
        # Create access token
        access_token = create_access_token({"sub": "user123"})
        
        # Should succeed when expecting access token
        payload = verify_token(access_token, expected_type="access")
        assert payload is not None
        
        # Should fail when expecting refresh token
        payload = verify_token(access_token, expected_type="refresh")
        assert payload is None

    def test_get_user_permissions(self):
        """Test permission generation based on role and tenant"""
        # Admin permissions
        admin_perms = get_user_permissions("admin")
        assert "read:users" in admin_perms
        assert "write:users" in admin_perms
        assert "manage:feature_flags" in admin_perms
        
        # Manager permissions
        manager_perms = get_user_permissions("manager")
        assert "read:users" in manager_perms
        assert "write:users" in manager_perms
        assert "manage:feature_flags" not in manager_perms
        
        # Viewer permissions
        viewer_perms = get_user_permissions("viewer")
        assert "read:organizations" in viewer_perms
        assert "write:users" not in viewer_perms

    def test_get_user_permissions_with_industry(self):
        """Test industry-specific permissions"""
        tenant_context = {"industry": "cinema"}
        
        perms = get_user_permissions("viewer", tenant_context)
        
        assert "read:organizations" in perms
        assert "read:cinema_data" in perms
        assert "analyze:cinema_metrics" in perms

    def test_should_refresh_token(self):
        """Test token refresh threshold logic"""
        # Create token that expires in 2 hours (more buffer)
        token_data = {"sub": "user123"}
        token = create_access_token(token_data, expires_delta=timedelta(hours=2))
        payload = verify_token(token)
        
        # Should not need refresh (expires in 2 hours, threshold is 15 minutes)
        assert not should_refresh_token(payload, threshold_minutes=15)
        
        # Should need refresh with very high threshold (200 minutes > remaining time)
        assert should_refresh_token(payload, threshold_minutes=200)

    def test_extract_tenant_context_from_token(self):
        """Test tenant context extraction"""
        token_data = {"sub": "user123", "email": "test@example.com"}
        tenant_id = "org456"
        user_role = "admin"
        permissions = ["read:users"]
        
        token = create_access_token(
            data=token_data,
            tenant_id=tenant_id,
            user_role=user_role,
            permissions=permissions
        )
        
        payload = verify_token(token)
        context = extract_tenant_context_from_token(payload)
        
        assert context["tenant_id"] == tenant_id
        assert context["user_role"] == user_role
        assert context["user_id"] == "user123"
        assert context["permissions"] == permissions


class TestAuthenticationDependencies:
    """Test enhanced authentication dependencies"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_tenant_validation(self):
        """Test user authentication with tenant context validation"""
        # Mock user and organization
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.email = "test@example.com"
        mock_user.organisation_id = "org456"
        mock_user.role = UserRole.admin
        mock_user.is_active = True
        mock_user.organisation = Mock()
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        mock_request.state = Mock()
        
        # Mock credentials
        mock_credentials = Mock()
        token = create_access_token(
            data={"sub": "user123", "email": "test@example.com"},
            tenant_id="org456",
            user_role="admin"
        )
        mock_credentials.credentials = token
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Import here to avoid circular imports
        from app.auth.dependencies import get_current_user
        
        # Test successful authentication
        result = await get_current_user(mock_request, mock_credentials, mock_db)
        
        assert result == mock_user
        assert hasattr(mock_request.state, 'tenant_context')

    @pytest.mark.asyncio
    async def test_get_current_user_tenant_mismatch(self):
        """Test authentication failure on tenant mismatch"""
        # Mock user with different tenant ID
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.organisation_id = "org999"  # Different from token
        mock_user.is_active = True
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        
        # Mock credentials with different tenant
        mock_credentials = Mock()
        token = create_access_token(
            data={"sub": "user123"},
            tenant_id="org456"  # Different from user
        )
        mock_credentials.credentials = token
        
        # Mock database
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        from app.auth.dependencies import get_current_user
        
        # Should raise HTTPException for tenant mismatch
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_credentials, mock_db)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Tenant context mismatch" in str(exc_info.value.detail)

    def test_require_permission_decorator(self):
        """Test permission-based access control"""
        required_perms = ["read:users", "write:users"]
        
        # Create permission dependency
        permission_dep = require_permission(required_perms)
        
        # Mock request with tenant context
        mock_request = Mock()
        mock_request.url.path = "/api/users"
        mock_request.state.tenant_context = {
            "permissions": ["read:users", "manage:system"]  # Has read:users
        }
        
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        
        # Should succeed (has read:users permission)
        result = permission_dep(mock_request, mock_user)
        assert result == mock_user

    def test_require_permission_insufficient(self):
        """Test permission denial"""
        required_perms = ["manage:system"]
        
        permission_dep = require_permission(required_perms)
        
        # Mock request without required permission
        mock_request = Mock()
        mock_request.url.path = "/api/admin"
        mock_request.state.tenant_context = {
            "permissions": ["read:users"]  # Missing manage:system
        }
        
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            permission_dep(mock_request, mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_require_role_decorator(self):
        """Test role-based access control"""
        required_roles = [UserRole.admin, UserRole.analyst]
        
        role_dep = require_role(required_roles)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/admin"
        
        # Mock admin user
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.role = UserRole.admin
        
        # Should succeed
        result = role_dep(mock_request, mock_user)
        assert result == mock_user
        
        # Mock viewer user
        mock_user.role = UserRole.viewer
        
        # Should fail
        with pytest.raises(HTTPException) as exc_info:
            role_dep(mock_request, mock_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestSecurityFeatures:
    """Test security enhancements"""

    def test_token_unique_identifiers(self):
        """Test that tokens have unique identifiers"""
        token1 = create_access_token({"sub": "user123"})
        token2 = create_access_token({"sub": "user123"})
        
        payload1 = verify_token(token1)
        payload2 = verify_token(token2)
        
        # JTI (JWT ID) should be different
        assert payload1["jti"] != payload2["jti"]

    def test_token_family_rotation(self):
        """Test refresh token family for rotation detection"""
        user_data = {"sub": "user123"}
        family_id = "family123"
        
        # Create two refresh tokens with same family
        token1 = create_refresh_token(user_data, token_family=family_id)
        token2 = create_refresh_token(user_data, token_family=family_id)
        
        payload1 = verify_token(token1, expected_type="refresh")
        payload2 = verify_token(token2, expected_type="refresh")
        
        # Should have same family but different JTI
        assert payload1["family"] == payload2["family"] == family_id
        assert payload1["jti"] != payload2["jti"]

    def test_secure_state_generation(self):
        """Test secure state parameter generation"""
        client = Auth0Client()
        
        # Generate multiple states
        state1 = client._generate_secure_state()
        state2 = client._generate_secure_state()
        
        # Should be different and sufficiently long
        assert state1 != state2
        assert len(state1) >= 32  # URL-safe base64 encoding
        assert len(state2) >= 32

    def test_token_expiry_validation(self):
        """Test token expiry enforcement"""
        # Create token with very short expiry
        short_expiry = timedelta(seconds=1)
        token = create_access_token(
            {"sub": "user123"}, 
            expires_delta=short_expiry
        )
        
        # Should be valid immediately
        payload = verify_token(token)
        assert payload is not None
        
        # Wait for expiry (in real tests, we'd mock time)
        import time
        time.sleep(2)
        
        # Should be expired now
        payload = verify_token(token)
        assert payload is None


@pytest.fixture
def mock_user():
    """Fixture for mock user"""
    user = Mock(spec=User)
    user.id = "user123"
    user.email = "test@example.com"
    user.organisation_id = "org456"
    user.role = UserRole.admin
    user.is_active = True
    user.organisation = Mock()
    user.organisation.name = "Test Org"
    user.organisation.industry = "Technology"
    user.organisation.subscription_plan = SubscriptionPlan.basic
    return user


@pytest.fixture
def mock_db():
    """Fixture for mock database session"""
    db = Mock(spec=Session)
    return db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])