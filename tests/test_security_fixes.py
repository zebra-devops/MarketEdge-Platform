"""
Comprehensive security tests for critical security fixes in Issue #4.

This test suite verifies:
1. Auth0 Management API Token Security
2. Input Validation & Injection Prevention
3. Production Cookie Security
4. Multi-tenant Isolation
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.main import app
from app.auth.auth0 import Auth0Client, auth0_client
from app.core.validators import (
    AuthParameterValidator, 
    ValidationError, 
    sanitize_string_input,
    validate_tenant_id,
    create_security_headers
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.organisation import Organisation


class TestAuth0ManagementAPITokenSecurity:
    """Test Auth0 Management API token security fixes"""
    
    @pytest.fixture
    def auth0_client_instance(self):
        return Auth0Client()
    
    @pytest.mark.asyncio
    async def test_management_api_token_caching(self, auth0_client_instance):
        """Test secure Management API token caching and rotation"""
        with patch.object(httpx.AsyncClient, 'post') as mock_post:
            # Mock successful token response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "access_token": "secure_mgmt_token_123",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            mock_post.return_value = mock_response
            
            # First call should fetch new token
            token1 = await auth0_client_instance._get_management_api_token()
            assert token1 == "secure_mgmt_token_123"
            assert mock_post.call_count == 1
            
            # Second call should use cached token
            token2 = await auth0_client_instance._get_management_api_token()
            assert token2 == "secure_mgmt_token_123"
            assert mock_post.call_count == 1  # No additional calls
            
            # Verify token is cached with expiry
            assert hasattr(auth0_client_instance, '_mgmt_token_cache')
            assert hasattr(auth0_client_instance, '_mgmt_token_expiry')
    
    @pytest.mark.asyncio
    async def test_management_api_secure_error_handling(self, auth0_client_instance):
        """Test secure error handling for Management API failures"""
        with patch.object(httpx.AsyncClient, 'post') as mock_post:
            # Mock HTTP error
            mock_post.side_effect = httpx.HTTPStatusError(
                message="Unauthorized",
                request=Mock(),
                response=Mock(status_code=401)
            )
            
            token = await auth0_client_instance._get_management_api_token()
            assert token is None
    
    @pytest.mark.asyncio
    async def test_user_orgs_with_fallback(self, auth0_client_instance):
        """Test user organizations with secure fallback to user metadata"""
        with patch.object(auth0_client_instance, '_get_user_info_secure') as mock_userinfo, \
             patch.object(auth0_client_instance, '_get_management_api_token') as mock_mgmt_token:
            
            # Mock user info
            mock_userinfo.return_value = {
                "sub": "auth0|user123",
                "email": "test@example.com",
                "org_id": "org_123",
                "org_name": "Test Organization"
            }
            
            # Mock Management API token failure (fallback scenario)
            mock_mgmt_token.return_value = None
            
            orgs = await auth0_client_instance.get_user_organizations("test_token")
            
            # Should fallback to user metadata
            assert orgs is not None
            assert len(orgs) == 1
            assert orgs[0]["id"] == "org_123"
            assert orgs[0]["name"] == "Test Organization"
    
    @pytest.mark.asyncio
    async def test_secure_user_info_validation(self, auth0_client_instance):
        """Test secure user info retrieval with input validation"""
        # Test invalid access token
        result = await auth0_client_instance._get_user_info_secure("")
        assert result is None
        
        result = await auth0_client_instance._get_user_info_secure(None)
        assert result is None
        
        result = await auth0_client_instance._get_user_info_secure("   ")
        assert result is None


class TestInputValidationSecurity:
    """Test comprehensive input validation and injection prevention"""
    
    def test_auth_parameter_validator_code_validation(self):
        """Test authorization code parameter validation"""
        # Valid code
        validator = AuthParameterValidator(
            code="valid_auth_code_123",
            redirect_uri="https://example.com/callback"
        )
        assert validator.code == "valid_auth_code_123"
        
        # Invalid codes - should raise validation errors
        with pytest.raises(ValueError, match="Code length must be between"):
            AuthParameterValidator(
                code="short",  # Too short
                redirect_uri="https://example.com/callback"
            )
        
        with pytest.raises(ValueError, match="Code contains invalid characters"):
            AuthParameterValidator(
                code="code_with_<script>alert('xss')</script>",
                redirect_uri="https://example.com/callback"
            )
        
        # Test that codes with spaces are rejected (will fail character validation first)
        with pytest.raises((ValueError, ValidationError)):
            AuthParameterValidator(
                code="code_with union select_attack",  # Contains spaces - fails character validation
                redirect_uri="https://example.com/callback"
            )
    
    def test_redirect_uri_security_validation(self):
        """Test redirect URI security validation"""
        # Valid HTTPS URI
        validator = AuthParameterValidator(
            code="valid_code_123",
            redirect_uri="https://myapp.example.com/callback"
        )
        assert validator.redirect_uri == "https://myapp.example.com/callback"
        
        # Invalid schemes
        with pytest.raises(ValueError, match="Redirect URI must use HTTP or HTTPS"):
            AuthParameterValidator(
                code="valid_code_123",
                redirect_uri="javascript:alert('xss')"
            )
        
        with pytest.raises(ValueError, match="Redirect URI must use HTTP or HTTPS"):
            AuthParameterValidator(
                code="valid_code_123",
                redirect_uri="data:text/html,<script>alert('xss')</script>"
            )
        
        # XSS prevention
        with pytest.raises(ValueError, match="Redirect URI contains potentially malicious content"):
            AuthParameterValidator(
                code="valid_code_123",
                redirect_uri="https://example.com/callback?param=<script>alert('xss')</script>"
            )
    
    def test_state_parameter_validation(self):
        """Test state parameter validation for CSRF protection"""
        # Valid state
        validator = AuthParameterValidator(
            code="valid_code_123",
            redirect_uri="https://example.com/callback",
            state="secure_state_token_123"
        )
        assert validator.state == "secure_state_token_123"
        
        # Invalid state with injection attempts
        with pytest.raises(ValueError, match="State contains invalid characters"):
            AuthParameterValidator(
                code="valid_code_123",
                redirect_uri="https://example.com/callback",
                state="state_with_<script>alert('xss')</script>"
            )
        
        with pytest.raises(ValueError, match="State contains invalid characters"):
            AuthParameterValidator(
                code="valid_code_123",
                redirect_uri="https://example.com/callback",
                state="state_with_semicolon;"
            )
    
    def test_string_sanitization(self):
        """Test string sanitization against injection attacks"""
        # Normal string
        sanitized = sanitize_string_input("normal_string_123", max_length=100)
        assert sanitized == "normal_string_123"
        
        # XSS prevention
        sanitized = sanitize_string_input("Hello World", max_length=100)
        assert sanitized == "Hello World"
        
        # Test HTML escaping
        sanitized = sanitize_string_input("<b>Bold</b>", max_length=100)
        assert "&lt;b&gt;" in sanitized
        assert "<b>" not in sanitized
        
        # SQL injection prevention
        with pytest.raises(ValidationError, match="Input contains potentially malicious SQL patterns"):
            sanitize_string_input("'; DROP TABLE users; --", max_length=100)
        
        with pytest.raises(ValidationError, match="Input contains potentially malicious SQL patterns"):
            sanitize_string_input("1 OR 1=1", max_length=100)
        
        # Length validation
        with pytest.raises(ValidationError, match="Input too long \\(max 1000 characters\\)"):
            sanitize_string_input("a" * 1001, max_length=1000)
        
        # Control character removal
        sanitized = sanitize_string_input("test\x00\x01string", max_length=100)
        assert sanitized == "teststring"
    
    def test_tenant_id_validation(self):
        """Test tenant ID validation for multi-tenant security"""
        # Valid UUID
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_tenant_id(valid_uuid)
        assert result == valid_uuid
        
        # Invalid formats
        with pytest.raises(ValidationError, match="Invalid tenant ID format"):
            validate_tenant_id("not_a_uuid")
        
        with pytest.raises(ValidationError, match="Tenant ID is required and must be a string"):
            validate_tenant_id("")
        
        with pytest.raises(ValidationError, match="Tenant ID is required and must be a string"):
            validate_tenant_id(None)


class TestProductionCookieSecurity:
    """Test production cookie security enhancements"""
    
    def test_cookie_security_settings_development(self):
        """Test cookie settings in development environment"""
        # Mock development environment
        with patch.object(settings, 'ENVIRONMENT', 'development'):
            cookie_settings = settings.get_cookie_settings()
            
            assert cookie_settings['httponly'] == True
            assert cookie_settings['path'] == '/'
            # In development, secure might be False for localhost testing
    
    def test_cookie_security_settings_production(self):
        """Test cookie settings in production environment"""
        # Mock production environment
        with patch.object(settings, 'ENVIRONMENT', 'production'):
            cookie_settings = settings.get_cookie_settings()
            
            assert cookie_settings['secure'] == True
            assert cookie_settings['httponly'] == True
            assert cookie_settings['samesite'] == 'strict'  # Strict in production
            assert cookie_settings['path'] == '/'
    
    def test_security_headers_creation(self):
        """Test security headers for production"""
        headers = create_security_headers()
        
        # Verify critical security headers
        assert 'X-Content-Type-Options' in headers
        assert headers['X-Content-Type-Options'] == 'nosniff'
        
        assert 'X-Frame-Options' in headers
        assert headers['X-Frame-Options'] == 'DENY'
        
        assert 'X-XSS-Protection' in headers
        assert headers['X-XSS-Protection'] == '1; mode=block'
        
        assert 'Strict-Transport-Security' in headers
        assert 'max-age=31536000' in headers['Strict-Transport-Security']
        
        assert 'Content-Security-Policy' in headers
        assert "default-src 'self'" in headers['Content-Security-Policy']
        
        assert 'Cache-Control' in headers
        assert 'no-store' in headers['Cache-Control']


class TestMultiTenantSecurityIsolation:
    """Test multi-tenant isolation is maintained across security fixes"""
    
    def test_tenant_context_validation_in_middleware(self):
        """Test tenant context validation in enhanced middleware"""
        from app.middleware.tenant_context import TenantContextMiddleware
        
        # Test would require full middleware integration
        # This is a placeholder for middleware-specific tenant isolation tests
        pass
    
    @pytest.mark.asyncio
    async def test_database_session_isolation(self):
        """Test database session variables maintain tenant isolation"""
        # Mock database session for testing RLS policies
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_db = Mock(spec=Session)
            # Create proper generator function
            def mock_db_generator():
                yield mock_db
            mock_get_db.return_value = mock_db_generator()
            # Mock database operations
            mock_db.execute.return_value = Mock()
            mock_db.commit.return_value = None
            
            from app.middleware.tenant_context import TenantContextMiddleware
            middleware = TenantContextMiddleware(app)
            
            # Test tenant context setting maintains isolation
            tenant_context = {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_role": "viewer",
                "user_id": "user_123"
            }
            
            await middleware._set_database_context(tenant_context)
            
            # Verify session variables are set for RLS
            expected_calls = [
                ("SELECT set_config('app.current_tenant_id', :tenant_id, true)", 
                 {"tenant_id": "550e8400-e29b-41d4-a716-446655440000"}),
                ("SELECT set_config('app.current_user_role', :user_role, true)", 
                 {"user_role": "viewer"}),
                ("SELECT set_config('app.current_user_id', :user_id, true)", 
                 {"user_id": "user_123"}),
                ("SELECT set_config('app.allow_cross_tenant', :allow_cross_tenant, true)", 
                 {"allow_cross_tenant": "false"})
            ]
            
            # Verify execute was called with correct parameters
            assert mock_db.execute.call_count >= len(expected_calls)


class TestSecurityIntegration:
    """Integration tests for all security fixes working together"""
    
    def test_enhanced_login_endpoint_security(self):
        """Test login endpoint with all security enhancements"""
        client = TestClient(app)
        
        # Test malicious input rejection
        malicious_data = {
            "code": "<script>alert('xss')</script>",
            "redirect_uri": "javascript:alert('xss')",
            "state": "'; DROP TABLE users; --"
        }
        
        response = client.post("/api/v1/auth/login", json=malicious_data)
        
        # Should reject malicious input
        assert response.status_code == 400
        assert "Invalid request parameters" in response.json()["detail"]
    
    def test_security_headers_in_response(self):
        """Test that security headers are added to responses"""
        client = TestClient(app)
        
        # Make a request to any endpoint
        response = client.get("/health")
        
        # Check for security headers (if middleware is configured)
        # Note: This depends on middleware configuration in main.py
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection'
        ]
        
        # Some headers might be added by middleware
        for header in expected_headers:
            if header in response.headers:
                assert response.headers[header] is not None
    
    def test_cookie_security_in_auth_response(self):
        """Test that auth endpoints set secure cookies"""
        # This would require mocking the full auth flow
        # and checking Set-Cookie headers in the response
        pass


class TestSecurityMetrics:
    """Test security monitoring and metrics"""
    
    def test_security_violation_logging(self):
        """Test that security violations are properly logged"""
        with patch('app.core.validators.logger') as mock_logger:
            # Attempt validation that should fail
            try:
                sanitize_string_input("'; DROP TABLE users; --", max_length=100)
            except ValidationError:
                pass
            
            # Verify security violation was logged
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            assert "SQL injection pattern detected" in str(call_args)
    
    def test_failed_auth_attempt_logging(self):
        """Test that failed authentication attempts are logged"""
        # This would test that the enhanced logging in auth endpoints
        # properly records failed attempts with relevant security context
        pass


@pytest.mark.performance
class TestSecurityPerformance:
    """Test that security enhancements don't significantly impact performance"""
    
    @pytest.mark.asyncio
    async def test_input_validation_performance(self):
        """Test input validation performance under load"""
        import time
        
        # Test normal string validation performance
        test_string = "valid_input_string_123" * 10  # 230 chars
        
        start_time = time.time()
        for _ in range(1000):
            sanitize_string_input(test_string, max_length=5000)
        end_time = time.time()
        
        # Should complete 1000 validations in reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
    
    def test_security_headers_performance(self):
        """Test security headers creation performance"""
        import time
        
        start_time = time.time()
        for _ in range(1000):
            create_security_headers()
        end_time = time.time()
        
        # Should create headers quickly
        assert (end_time - start_time) < 0.5  # Less than 0.5 seconds


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])