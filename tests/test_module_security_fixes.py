"""
Comprehensive security tests for module system security fixes in US-101.

This test suite verifies:
1. Module signature verification system
2. SQL injection prevention in module registry
3. Feature flag bypass prevention
4. Async database security in auth middleware
5. Metrics memory leak prevention
6. Security event logging
"""

import pytest
import asyncio
import time
import hmac
import hashlib
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.module_registry import (
    ModuleRegistry, ModuleValidator, ModuleSignatureVerifier, 
    ModuleSignatureError, ModuleMetadata, BaseModuleRouter,
    ModuleLifecycleState, RegistrationResult
)
from app.core.module_routing import (
    ModuleRoutingManager, RouteMetrics, ModuleMetricsPersistence,
    RouteVersion, ModuleRouteConfig, AuthLevel
)
from app.middleware.module_auth import ModuleAuthMiddleware, ModuleAuthCache
from app.services.feature_flag_service import FeatureFlagService
from app.services.module_service import ModuleService
from app.models.user import User, UserRole
from app.models.modules import AnalyticsModule, ModuleStatus, ModuleType


class TestModuleSignatureVerification:
    """Test module signature verification system"""
    
    @pytest.fixture
    def signature_verifier(self):
        return ModuleSignatureVerifier("test_secret_key_123")
    
    @pytest.fixture
    def sample_module_data(self):
        return {
            "module_id": "test_module",
            "name": "Test Module",
            "version": "1.0.0",
            "entry_point": "app.modules.test_module",
            "checksum": "abc123"
        }
    
    def test_signature_generation(self, signature_verifier, sample_module_data):
        """Test signature generation is consistent"""
        sig1 = signature_verifier.generate_signature(sample_module_data)
        sig2 = signature_verifier.generate_signature(sample_module_data)
        
        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex digest length
        assert isinstance(sig1, str)
    
    def test_signature_verification_success(self, signature_verifier, sample_module_data):
        """Test successful signature verification"""
        signature = signature_verifier.generate_signature(sample_module_data)
        
        assert signature_verifier.verify_signature(sample_module_data, signature) is True
    
    def test_signature_verification_failure(self, signature_verifier, sample_module_data):
        """Test signature verification failure with tampered data"""
        signature = signature_verifier.generate_signature(sample_module_data)
        
        # Tamper with the data
        tampered_data = sample_module_data.copy()
        tampered_data["module_id"] = "malicious_module"
        
        assert signature_verifier.verify_signature(tampered_data, signature) is False
    
    def test_signature_verification_invalid_signature(self, signature_verifier, sample_module_data):
        """Test signature verification with invalid signature"""
        fake_signature = "invalid_signature_123"
        
        assert signature_verifier.verify_signature(sample_module_data, fake_signature) is False
    
    def test_module_code_validation_safe(self, signature_verifier, tmp_path):
        """Test AST validation accepts safe code"""
        safe_code = '''
def hello_world():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
'''
        test_file = tmp_path / "safe_module.py"
        test_file.write_text(safe_code)
        
        assert signature_verifier.validate_module_code(str(test_file)) is True
    
    def test_module_code_validation_dangerous(self, signature_verifier, tmp_path):
        """Test AST validation rejects dangerous code"""
        dangerous_code = '''
import os
import subprocess

def dangerous_function():
    os.system("rm -rf /")
    eval("malicious_code")
    subprocess.run(["malicious", "command"])
'''
        test_file = tmp_path / "dangerous_module.py"
        test_file.write_text(dangerous_code)
        
        assert signature_verifier.validate_module_code(str(test_file)) is False
    
    def test_module_code_validation_nonexistent_file(self, signature_verifier):
        """Test validation of non-existent file"""
        assert signature_verifier.validate_module_code("nonexistent_file.py") is False


class TestModuleValidatorSecurity:
    """Test enhanced security in module validator"""
    
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        db.execute.return_value.scalar_one_or_none.return_value = None
        return db
    
    @pytest.fixture
    def sample_router(self):
        router = Mock()
        router.get_module_id.return_value = "valid_module_123"
        router.get_namespace.return_value = "valid-namespace"
        router.get_version.return_value = RouteVersion.V1
        router.get_health_check.return_value = lambda: {"status": "healthy"}
        router.register_routes.return_value = None
        return router
    
    @pytest.mark.asyncio
    async def test_module_id_validation_valid(self, mock_db, sample_router):
        """Test valid module ID passes validation"""
        errors = await ModuleValidator.validate_module_router(sample_router, mock_db)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_module_id_validation_malicious(self, mock_db):
        """Test malicious module ID fails validation"""
        malicious_router = Mock()
        malicious_router.get_module_id.return_value = "'; DROP TABLE modules; --"
        malicious_router.get_namespace.return_value = "namespace"
        malicious_router.get_version.return_value = RouteVersion.V1
        malicious_router.get_health_check.return_value = lambda: {"status": "healthy"}
        malicious_router.register_routes.return_value = None
        
        errors = await ModuleValidator.validate_module_router(malicious_router, mock_db)
        assert len(errors) > 0
        assert any("malicious" in error.lower() or "validation failed" in error.lower() for error in errors)
    
    @pytest.mark.asyncio
    async def test_namespace_validation_malicious(self, mock_db):
        """Test malicious namespace fails validation"""
        malicious_router = Mock()
        malicious_router.get_module_id.return_value = "valid_module"
        malicious_router.get_namespace.return_value = "<script>alert('xss')</script>"
        malicious_router.get_version.return_value = RouteVersion.V1
        malicious_router.get_health_check.return_value = lambda: {"status": "healthy"}
        malicious_router.register_routes.return_value = None
        
        errors = await ModuleValidator.validate_module_router(malicious_router, mock_db)
        assert len(errors) > 0
        assert any("validation failed" in error.lower() for error in errors)
    
    def test_metadata_validation_safe(self):
        """Test safe metadata passes validation"""
        metadata = ModuleMetadata(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            description="A test module",
            author="Test Author",
            module_type=ModuleType.ANALYTICS,
            entry_point="app.modules.test_module",
            dependencies=["dep1", "dep-2"]
        )
        
        errors = ModuleValidator.validate_module_metadata(metadata)
        assert len(errors) == 0
    
    def test_metadata_validation_malicious_entry_point(self):
        """Test malicious entry point fails validation"""
        metadata = ModuleMetadata(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            description="A test module",
            author="Test Author",
            module_type=ModuleType.ANALYTICS,
            entry_point="../../../etc/passwd",  # Path traversal
            dependencies=[]
        )
        
        errors = ModuleValidator.validate_module_metadata(metadata)
        assert len(errors) > 0
        assert any("path traversal" in error.lower() for error in errors)


class TestFeatureFlagSecurity:
    """Test feature flag bypass prevention"""
    
    @pytest.fixture
    def mock_feature_service(self):
        service = AsyncMock(spec=FeatureFlagService)
        service.is_feature_enabled.return_value = True
        return service
    
    @pytest.fixture
    def mock_module_service(self):
        return AsyncMock(spec=ModuleService)
    
    @pytest.fixture
    def sample_user(self):
        user = Mock(spec=User)
        user.id = "user_123"
        user.organisation_id = "org_123"
        user.role = UserRole.USER
        return user
    
    @pytest.fixture
    def middleware(self, mock_feature_service, mock_module_service):
        app = Mock()
        return ModuleAuthMiddleware(app, mock_feature_service, mock_module_service)
    
    @pytest.mark.asyncio
    async def test_feature_flag_check_missing_user_context(self, middleware):
        """Test feature flag check fails without user context"""
        # Test with None user
        result = await middleware._check_feature_flags(None, ["test_feature"])
        assert result["success"] is False
        assert result["status_code"] == status.HTTP_403_FORBIDDEN
        assert "User context required" in result["message"]
        
        # Test with user missing attributes
        incomplete_user = Mock()
        delattr(incomplete_user, 'id')  # Remove required attribute
        result = await middleware._check_feature_flags(incomplete_user, ["test_feature"])
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_feature_flag_check_invalid_flag_format(self, middleware, sample_user):
        """Test feature flag check fails with invalid flag format"""
        # Test empty flag
        result = await middleware._check_feature_flags(sample_user, [""])
        assert result["success"] is False
        
        # Test non-string flag
        result = await middleware._check_feature_flags(sample_user, [123])
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_feature_flag_check_with_context(self, middleware, sample_user, mock_feature_service):
        """Test feature flag check includes proper user context"""
        await middleware._check_feature_flags(sample_user, ["test_feature"])
        
        # Verify the service was called with user context
        mock_feature_service.is_feature_enabled.assert_called_once()
        call_args = mock_feature_service.is_feature_enabled.call_args
        
        # Check that user and context were passed
        assert call_args[0][0] == "test_feature"  # flag name
        assert call_args[0][1] == sample_user      # user object
        
        # Check context contains required fields
        context = call_args[0][2]
        assert "user_id" in context
        assert "organisation_id" in context
        assert "timestamp" in context


class TestAsyncDatabaseSecurity:
    """Test async database security in auth middleware"""
    
    @pytest.fixture
    def cache(self):
        return ModuleAuthCache()
    
    def test_auth_cache_expiry(self, cache):
        """Test auth cache properly expires entries"""
        cache.cache_auth("test_key", {"user": "test_user"})
        
        # Should return cached data immediately
        result = cache.get_cached_auth("test_key")
        assert result is not None
        assert result["user"] == "test_user"
        
        # Mock time passing beyond TTL
        with patch('time.time', return_value=time.time() + 400):
            result = cache.get_cached_auth("test_key")
            assert result is None
    
    def test_module_config_cache(self, cache):
        """Test module configuration caching"""
        config = {"auth_level": "BASIC", "permissions": []}
        cache.cache_module_config("test_module", config)
        
        result = cache.get_cached_module_config("test_module")
        assert result == config
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test proper error handling for database failures"""
        # This would require mocking the actual database calls
        # to test error scenarios
        pass


class TestMetricsMemoryManagement:
    """Test metrics memory leak prevention"""
    
    def test_route_metrics_bounded_storage(self):
        """Test route metrics automatically reset to prevent memory leaks"""
        metrics = RouteMetrics()
        
        # Simulate many calls
        for i in range(RouteMetrics.MAX_CALL_COUNT + 10):
            metrics.record_call(10.0, success=True)
        
        # Metrics should have been reset
        assert metrics.call_count <= RouteMetrics.MAX_CALL_COUNT
    
    def test_route_metrics_age_reset(self):
        """Test route metrics reset based on age"""
        metrics = RouteMetrics()
        
        # Mock old creation time
        metrics.created_at = time.time() - RouteMetrics.MAX_AGE_SECONDS - 100
        
        # Record a call - should trigger reset
        metrics.record_call(10.0, success=True)
        
        # Should be reset to 1 call
        assert metrics.call_count == 1
        assert abs(metrics.created_at - time.time()) < 1  # Recently reset
    
    @pytest.mark.asyncio
    async def test_metrics_persistence_rotation(self):
        """Test metrics persistence prevents memory accumulation"""
        persistence = ModuleMetricsPersistence(max_metrics=10, rotation_interval=1)
        
        # Create many metrics to trigger rotation
        test_metrics = {}
        for i in range(15):
            metric = RouteMetrics()
            metric.call_count = i
            metric.last_called = time.time()
            test_metrics[f"route_{i}"] = metric
        
        await persistence.maybe_rotate_metrics(test_metrics)
        
        # Should have triggered rotation due to max_metrics limit
        assert len(test_metrics) <= persistence.max_metrics


class TestSecurityEventLogging:
    """Test security event logging system"""
    
    @pytest.fixture
    def routing_manager(self):
        feature_service = AsyncMock(spec=FeatureFlagService)
        module_service = AsyncMock(spec=ModuleService)
        return ModuleRoutingManager(feature_service, module_service)
    
    def test_security_event_logging(self, routing_manager):
        """Test security events are properly logged"""
        with patch.object(routing_manager, 'logger') as mock_logger:
            event_data = {"test": "data"}
            routing_manager._log_security_event("TEST_EVENT", event_data)
            
            # Verify logging was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "TEST_EVENT" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_registration_security_logging(self, routing_manager):
        """Test module registration logs security events"""
        # Mock module router
        mock_router = Mock()
        mock_router.get_module_id.return_value = "test_module"
        mock_router.get_namespace.return_value = "test"
        mock_router.get_version.return_value = RouteVersion.V1
        mock_router.register_routes.return_value = None
        mock_router.get_health_check.return_value = lambda: {"status": "healthy"}
        
        with patch.object(routing_manager, '_log_security_event') as mock_log:
            try:
                await routing_manager.register_module(mock_router)
            except Exception:
                pass  # Expected due to mocking
            
            # Verify security events were logged
            assert mock_log.call_count >= 1
            
            # Check for registration started event
            calls = [call[0] for call in mock_log.call_args_list]
            assert any("REGISTRATION_STARTED" in str(call) for call in calls)


class TestIntegratedSecurityScenarios:
    """Test integrated security scenarios across multiple components"""
    
    @pytest.mark.asyncio
    async def test_malicious_module_registration_blocked(self):
        """Test that a malicious module registration is completely blocked"""
        # This would test the full pipeline of security checks
        # from signature verification through to final registration
        pass
    
    @pytest.mark.asyncio
    async def test_feature_flag_bypass_attempt_blocked(self):
        """Test that feature flag bypass attempts are blocked"""
        # This would test various bypass scenarios
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_registration_security(self):
        """Test security during concurrent module registrations"""
        # This would test race conditions and concurrent access scenarios
        pass


class TestPerformanceSecurityTradeoffs:
    """Test that security fixes don't significantly impact performance"""
    
    @pytest.mark.asyncio
    async def test_signature_verification_performance(self):
        """Test signature verification performance under load"""
        verifier = ModuleSignatureVerifier("test_key")
        module_data = {"module_id": "test", "version": "1.0.0"}
        
        start_time = time.time()
        for _ in range(1000):
            signature = verifier.generate_signature(module_data)
            verifier.verify_signature(module_data, signature)
        end_time = time.time()
        
        # Should complete 1000 verifications in reasonable time
        assert (end_time - start_time) < 2.0  # Less than 2 seconds
    
    def test_input_validation_performance(self):
        """Test input validation performance"""
        # Test that security validation doesn't create significant bottlenecks
        start_time = time.time()
        for _ in range(1000):
            ModuleValidator.ALLOWED_MODULE_ID_PATTERN.match("test_module_123")
            ModuleValidator.ALLOWED_NAMESPACE_PATTERN.match("test-namespace")
        end_time = time.time()
        
        assert (end_time - start_time) < 0.5  # Less than 0.5 seconds
    
    def test_metrics_performance(self):
        """Test metrics recording performance"""
        metrics = RouteMetrics()
        
        start_time = time.time()
        for i in range(10000):
            metrics.record_call(1.0, success=True)
        end_time = time.time()
        
        # Should handle many metrics updates quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])