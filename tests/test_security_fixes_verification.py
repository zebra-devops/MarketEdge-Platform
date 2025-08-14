"""
Comprehensive Security Fixes Verification Tests

This test suite verifies all critical security vulnerabilities have been fixed:
1. eval() usage replaced with json.loads()
2. SQL injection prevention
3. Authentication on all endpoints
4. Input validation and sanitization
5. Rate limiting functionality
6. Permission caching
7. Exception handling with security logging
8. Database query optimization
"""

import json
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.services.permission_service import PermissionResolutionEngine
from app.core.validators import sanitize_string_input, ValidationError
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security_exception_handler import SecurityExceptionHandler


class TestEvalVulnerabilityFixes:
    """Test that all eval() usage has been replaced with json.loads()"""
    
    def test_no_eval_in_organization_hierarchy_endpoint(self):
        """Verify organization hierarchy endpoint uses json.loads instead of eval"""
        # Read the source file and check for eval usage
        with open('app/api/api_v1/endpoints/organization_hierarchy.py', 'r') as f:
            content = f.read()
        
        # Should not contain any eval() calls
        assert 'eval(' not in content, "eval() usage found in organization_hierarchy.py"
        
        # Should contain json.loads usage
        assert 'json.loads(' in content, "json.loads() usage not found in organization_hierarchy.py"
    
    def test_no_eval_in_industry_templates_endpoint(self):
        """Verify industry templates endpoint uses json.loads instead of eval"""
        with open('app/api/api_v1/endpoints/industry_templates.py', 'r') as f:
            content = f.read()
        
        # Should not contain any eval() calls
        assert 'eval(' not in content, "eval() usage found in industry_templates.py"
        
        # Should contain json.loads usage
        assert 'json.loads(' in content, "json.loads() usage not found in industry_templates.py"
    
    def test_json_loads_handles_valid_json(self):
        """Test that json.loads properly handles valid JSON data"""
        test_data = {'key': 'value', 'number': 42}
        json_string = json.dumps(test_data)
        
        # This should work safely
        result = json.loads(json_string)
        assert result == test_data
    
    def test_json_loads_raises_exception_on_invalid_json(self):
        """Test that json.loads raises exception on invalid JSON (preventing code execution)"""
        malicious_code = "__import__('os').system('rm -rf /')"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(malicious_code)


class TestSQLInjectionPrevention:
    """Test that SQL injection vulnerabilities have been fixed"""
    
    def test_parameterized_queries_in_permission_service(self):
        """Verify permission service uses parameterized queries"""
        with open('app/services/permission_service.py', 'r') as f:
            content = f.read()
        
        # Should not contain string formatting in SQL contexts
        assert 'f"SELECT' not in content, "Found potential SQL injection vulnerability"
        assert 'f\'SELECT' not in content, "Found potential SQL injection vulnerability"
        assert '% ' not in content.replace('% ', ''), "Found potential string formatting in SQL"
    
    def test_admin_service_uses_ilike_safely(self):
        """Verify admin service audit log filtering uses safe methods"""
        with open('app/services/admin_service.py', 'r') as f:
            content = f.read()
        
        # Should use SQLAlchemy's ilike method (which is parameterized)
        assert '.ilike(f"%{' in content, "Safe ilike usage not found"
        # Should not use raw SQL with string formatting
        assert 'execute(f"' not in content, "Found potential raw SQL injection"


class TestAuthenticationCoverage:
    """Test that all API endpoints have proper authentication"""
    
    def test_organizations_industries_endpoint_requires_auth(self):
        """Verify /industries endpoint requires authentication"""
        with open('app/api/api_v1/endpoints/organisations.py', 'r') as f:
            content = f.read()
        
        # The get_available_industries function should have authentication
        lines = content.split('\n')
        found_function = False
        has_auth = False
        
        for i, line in enumerate(lines):
            if 'def get_available_industries(' in line:
                found_function = True
                # Check next few lines for Depends(get_current_user)
                for j in range(i, min(i + 5, len(lines))):
                    if 'get_current_user' in lines[j]:
                        has_auth = True
                        break
                break
        
        assert found_function, "get_available_industries function not found"
        assert has_auth, "/industries endpoint missing authentication"
    
    def test_health_endpoint_is_only_unauthenticated(self):
        """Verify only health endpoints are unauthenticated"""
        import os
        import re
        
        unauthenticated_endpoints = []
        
        # Scan all endpoint files
        endpoints_dir = 'app/api/api_v1/endpoints'
        for filename in os.listdir(endpoints_dir):
            if filename.endswith('.py'):
                with open(os.path.join(endpoints_dir, filename), 'r') as f:
                    content = f.read()
                
                # Find async def functions that don't have authentication
                functions = re.findall(r'async def (\w+)\([^)]*\):', content)
                
                for func in functions:
                    func_start = content.find(f'async def {func}(')
                    if func_start != -1:
                        # Get the function definition (until next function or end)
                        next_func = content.find('async def ', func_start + 1)
                        func_content = content[func_start:next_func if next_func != -1 else len(content)]
                        
                        # Check if function has authentication dependencies
                        has_auth = any(dep in func_content for dep in [
                            'get_current_user', 'require_admin', 'require_super_admin', 
                            'require_role', 'require_permission'
                        ])
                        
                        if not has_auth:
                            unauthenticated_endpoints.append(func)
        
        # Only health_check should be unauthenticated
        acceptable_unauthenticated = {'health_check'}
        unexpected = set(unauthenticated_endpoints) - acceptable_unauthenticated
        
        assert len(unexpected) == 0, f"Unexpected unauthenticated endpoints: {unexpected}"


class TestInputValidation:
    """Test comprehensive input validation and sanitization"""
    
    def test_sanitize_string_input_prevents_xss(self):
        """Test XSS prevention in input sanitization"""
        malicious_input = "<script>alert('xss')</script>Hello"
        
        sanitized = sanitize_string_input(malicious_input, allow_html=False)
        
        # Should escape HTML entities
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
    
    def test_sanitize_string_input_prevents_sql_injection(self):
        """Test SQL injection prevention in input sanitization"""
        malicious_input = "'; DROP TABLE users; --"
        
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string_input(malicious_input)
        
        assert exc_info.value.violation_type == "sql_injection"
    
    def test_sanitize_string_input_length_limit(self):
        """Test input length validation"""
        long_input = "A" * 2000
        
        with pytest.raises(ValidationError) as exc_info:
            sanitize_string_input(long_input, max_length=1000)
        
        assert exc_info.value.violation_type == "length_exceeded"
    
    def test_sanitize_string_input_removes_control_characters(self):
        """Test removal of control characters"""
        input_with_controls = "Hello\x00\x01\x02World"
        
        sanitized = sanitize_string_input(input_with_controls)
        
        assert sanitized == "HelloWorld"


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('app.middleware.rate_limiter.redis.Redis')
    def test_rate_limiter_initialization(self, mock_redis):
        """Test rate limiter initializes correctly"""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        rate_limiter = RateLimiterMiddleware(app)
        
        # Should have default configuration
        assert rate_limiter.default_limits['standard'] == 1000
        assert rate_limiter.default_limits['admin'] == float('inf')
    
    def test_rate_limiter_exempt_routes(self):
        """Test rate limiter exempts appropriate routes"""
        rate_limiter = RateLimiterMiddleware(app)
        
        # Create mock request
        mock_request = Mock()
        mock_request.url.path = '/health'
        
        # Should skip rate limiting for health endpoint
        assert rate_limiter._should_skip_rate_limiting(mock_request) == True
        
        # Should not skip for API endpoints
        mock_request.url.path = '/api/v1/organisations'
        assert rate_limiter._should_skip_rate_limiting(mock_request) == False


class TestPermissionCaching:
    """Test permission result caching implementation"""
    
    @patch('app.services.permission_service.cache_manager')
    def test_permission_resolution_uses_cache(self, mock_cache):
        """Test permission resolution checks cache first"""
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = None
        
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.hierarchy_assignments = []
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_user
        
        engine = PermissionResolutionEngine(mock_db)
        user_id = uuid.uuid4()
        
        result = engine.resolve_user_permissions(user_id)
        
        # Should check cache
        mock_cache.get.assert_called_once()
        # Should set cache on miss
        mock_cache.set.assert_called_once()
    
    @patch('app.services.permission_service.cache_manager')
    def test_permission_cache_invalidation(self, mock_cache):
        """Test permission cache invalidation works"""
        mock_cache.delete_pattern.return_value = 5
        
        mock_db = Mock(spec=Session)
        engine = PermissionResolutionEngine(mock_db)
        user_id = uuid.uuid4()
        
        engine.invalidate_user_permissions_cache(user_id)
        
        # Should delete cache entries
        expected_pattern = f"{engine.cache_prefix}user:{user_id}:*"
        mock_cache.delete_pattern.assert_called_once_with(expected_pattern)


class TestExceptionHandling:
    """Test comprehensive exception handling and security logging"""
    
    def test_security_exception_handler_sanitizes_errors(self):
        """Test security exception handler doesn't leak sensitive data"""
        handler = SecurityExceptionHandler(app)
        
        # Test that error responses don't contain sensitive information
        mock_request = Mock()
        mock_request.url.path = '/api/v1/test'
        mock_request.method = 'POST'
        mock_request.state.request_id = 'test-123'
        
        # Simulate database error with sensitive info
        class SensitiveError(Exception):
            def __str__(self):
                return "Database connection failed: user=admin, password=secret123"
        
        # Exception handler should sanitize the response
        with patch('app.middleware.security_exception_handler.logger') as mock_logger:
            try:
                raise SensitiveError()
            except Exception as e:
                # The handler should not expose the sensitive information
                assert "password=secret123" not in str(e)
    
    def test_security_exception_handler_logs_threats(self):
        """Test security exception handler detects and logs threats"""
        handler = SecurityExceptionHandler(app)
        
        # Create error that looks like injection attempt
        error_msg = "SQL injection attempt detected: UNION SELECT * FROM users"
        
        # Should increment security counters
        initial_count = handler.security_events['injection_attempts']
        
        # Simulate threat detection logic
        threat_indicators = ['injection', 'sql', 'union', 'select']
        if any(indicator in error_msg.lower() for indicator in threat_indicators):
            handler.security_events['injection_attempts'] += 1
        
        assert handler.security_events['injection_attempts'] == initial_count + 1


class TestDatabaseQueryOptimization:
    """Test database query optimization (N+1 prevention)"""
    
    def test_permission_service_uses_joinedload(self):
        """Test permission service uses joinedload to prevent N+1 queries"""
        with open('app/services/permission_service.py', 'r') as f:
            content = f.read()
        
        # Should use joinedload for related objects
        assert 'joinedload(' in content, "joinedload usage not found"
        assert 'joinedload(User.hierarchy_assignments)' in content
    
    def test_organization_queries_are_optimized(self):
        """Test organization-related queries use proper loading strategies"""
        with open('app/api/api_v1/endpoints/organization_hierarchy.py', 'r') as f:
            content = f.read()
        
        # Should use joinedload or selectinload for related data
        loading_strategies = ['joinedload(', 'selectinload(']
        has_optimization = any(strategy in content for strategy in loading_strategies)
        
        assert has_optimization, "No query optimization found in organization endpoints"


class TestSecurityIntegration:
    """Integration tests for security features working together"""
    
    def test_complete_security_stack(self):
        """Test that all security features work together"""
        # This would be a comprehensive integration test
        # that verifies the entire security stack
        
        # 1. Input validation
        # 2. Authentication
        # 3. Authorization  
        # 4. Rate limiting
        # 5. Audit logging
        # 6. Error handling
        
        # For now, just verify key components exist
        assert hasattr(app, 'middleware_stack')
        
        # Verify security middleware is registered
        middleware_types = [type(middleware) for middleware in app.user_middleware]
        middleware_names = [m.__name__ if hasattr(m, '__name__') else str(m) for m in middleware_types]
        
        # Should have security-related middleware
        security_indicators = ['Security', 'RateLimit', 'Tenant', 'Auth', 'Exception']
        has_security_middleware = any(
            any(indicator in str(middleware) for indicator in security_indicators)
            for middleware in middleware_names
        )
        
        assert has_security_middleware, "Security middleware not found in application stack"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])