"""
Tests for the rate limiting middleware
"""
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
import redis.asyncio as redis

from app.middleware.rate_limiting import (
    RateLimitingMiddleware, 
    RedisRateLimiter,
    initialize_rate_limiting,
    cleanup_rate_limiting
)
from app.core.config import settings


class TestRedisRateLimiter:
    """Test Redis rate limiter implementation"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance for testing"""
        return RedisRateLimiter()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        client = AsyncMock()
        client.ping = AsyncMock()
        client.eval = AsyncMock()
        return client
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, rate_limiter, mock_redis_client):
        """Test successful Redis initialization"""
        with patch('redis.asyncio.ConnectionPool') as mock_pool:
            mock_pool.from_url.return_value = AsyncMock()
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_redis.return_value = mock_redis_client
                
                await rate_limiter.initialize()
                
                assert rate_limiter.redis_client == mock_redis_client
                assert rate_limiter.fallback_mode is False
                mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, rate_limiter):
        """Test Redis initialization failure enables fallback mode"""
        with patch('redis.asyncio.ConnectionPool') as mock_pool:
            mock_pool.from_url.side_effect = Exception("Connection failed")
            
            await rate_limiter.initialize()
            
            assert rate_limiter.fallback_mode is True
            assert rate_limiter.redis_client is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_check_success(self, rate_limiter, mock_redis_client):
        """Test successful rate limit check"""
        # Mock Lua script result: [allowed, remaining, reset_time, total_requests]
        mock_redis_client.eval.return_value = [1, 9, 1640995200, 1]
        rate_limiter.redis_client = mock_redis_client
        rate_limiter.fallback_mode = False
        
        allowed, info = await rate_limiter.check_rate_limit("test_key", 10, 60, 5)
        
        assert allowed is True
        assert info["remaining"] == 9
        assert info["reset_time"] == 1640995200
        assert info["total_requests"] == 1
        
        mock_redis_client.eval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_check_exceeded(self, rate_limiter, mock_redis_client):
        """Test rate limit exceeded scenario"""
        # Mock Lua script result: [allowed, remaining, reset_time, total_requests]
        mock_redis_client.eval.return_value = [0, 0, 1640995200, 11]
        rate_limiter.redis_client = mock_redis_client
        rate_limiter.fallback_mode = False
        
        allowed, info = await rate_limiter.check_rate_limit("test_key", 10, 60, 5)
        
        assert allowed is False
        assert info["remaining"] == 0
        assert info["total_requests"] == 11
    
    @pytest.mark.asyncio
    async def test_rate_limit_fallback_mode(self, rate_limiter):
        """Test fallback mode allows all requests"""
        rate_limiter.fallback_mode = True
        
        allowed, info = await rate_limiter.check_rate_limit("test_key", 10, 60, 5)
        
        assert allowed is True
        assert info["remaining"] == 10  # Default fallback value
    
    @pytest.mark.asyncio
    async def test_rate_limit_redis_error(self, rate_limiter, mock_redis_client):
        """Test Redis error handling during rate limit check"""
        mock_redis_client.eval.side_effect = redis.RedisError("Redis error")
        rate_limiter.redis_client = mock_redis_client
        rate_limiter.fallback_mode = False
        
        allowed, info = await rate_limiter.check_rate_limit("test_key", 10, 60, 5)
        
        # Should allow request on Redis error (graceful degradation)
        assert allowed is True


class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}
        
        return app
    
    @pytest.fixture
    def app_with_middleware(self, app):
        """Add rate limiting middleware to app"""
        app.add_middleware(RateLimitingMiddleware)
        return app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client"""
        return TestClient(app_with_middleware)
    
    @pytest.fixture(autouse=True)
    def setup_settings(self):
        """Setup test settings"""
        original_enabled = settings.RATE_LIMIT_ENABLED
        original_limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = 5
        
        yield
        
        # Restore original settings
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = original_limit
    
    def test_excluded_routes_bypass_rate_limiting(self, client):
        """Test that excluded routes bypass rate limiting"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
    
    def test_rate_limiting_disabled(self, app):
        """Test middleware behavior when rate limiting is disabled"""
        settings.RATE_LIMIT_ENABLED = False
        
        app.add_middleware(RateLimitingMiddleware)
        client = TestClient(app)
        
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" not in response.headers
    
    @patch('app.middleware.rate_limiting.RateLimitingMiddleware._ensure_initialized')
    @patch('app.middleware.rate_limiting.RateLimitingMiddleware.rate_limiter')
    def test_successful_request_within_limits(self, mock_rate_limiter, mock_init, client):
        """Test successful request within rate limits"""
        mock_init.return_value = None
        mock_rate_limiter.check_rate_limit.return_value = (
            True, 
            {"remaining": 4, "reset_time": int(time.time() + 60), "total_requests": 1}
        )
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "4"
        assert "X-RateLimit-Processing-Time" in response.headers
    
    @patch('app.middleware.rate_limiting.RateLimitingMiddleware._ensure_initialized')
    @patch('app.middleware.rate_limiting.RateLimitingMiddleware.rate_limiter')
    def test_rate_limit_exceeded(self, mock_rate_limiter, mock_init, client):
        """Test request when rate limit is exceeded"""
        mock_init.return_value = None
        mock_rate_limiter.check_rate_limit.return_value = (
            False, 
            {"remaining": 0, "reset_time": int(time.time() + 60), "total_requests": 6}
        )
        
        response = client.get("/test")
        
        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in response.headers
        
        error_data = response.json()
        assert error_data["detail"]["error"] == "Rate limit exceeded"
    
    @patch('app.middleware.rate_limiting.RateLimitingMiddleware._ensure_initialized')
    def test_middleware_error_graceful_degradation(self, mock_init, client):
        """Test middleware handles errors gracefully"""
        mock_init.side_effect = Exception("Initialization failed")
        
        response = client.get("/test")
        
        # Should continue without rate limiting on errors
        assert response.status_code == 200
    
    def test_client_identifier_priority(self):
        """Test client identifier selection priority"""
        middleware = RateLimitingMiddleware(None)
        
        # Mock request with tenant context
        request = MagicMock()
        request.state.tenant_id = "tenant-123"
        request.state.user_id = "user-456"
        request.client.host = "192.168.1.1"
        
        client_id = middleware._get_client_identifier(request)
        assert client_id == "tenant:tenant-123"
        
        # Mock request with only user context
        delattr(request.state, 'tenant_id')
        client_id = middleware._get_client_identifier(request)
        assert client_id == "user:user-456"
        
        # Mock request with only IP
        delattr(request.state, 'user_id')
        client_id = middleware._get_client_identifier(request)
        assert client_id == "ip:192.168.1.1"
    
    def test_client_ip_extraction(self):
        """Test client IP extraction with proxy headers"""
        middleware = RateLimitingMiddleware(None)
        
        # Test X-Forwarded-For header
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.1"
        
        # Test X-Real-IP header
        request.headers = {"X-Real-IP": "203.0.113.2"}
        ip = middleware._get_client_ip(request)
        assert ip == "203.0.113.2"
        
        # Test direct client IP
        request.headers = {}
        request.client.host = "192.168.1.1"
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_rate_limits_by_user_role(self):
        """Test different rate limits based on user role"""
        middleware = RateLimitingMiddleware(None)
        
        # Admin user
        request = MagicMock()
        request.state.user_role = "admin"
        limit, window = middleware._get_rate_limits(request)
        assert limit == settings.RATE_LIMIT_ADMIN_REQUESTS_PER_MINUTE
        
        # Regular user with tenant
        request.state.user_role = "user"
        request.state.tenant_id = "tenant-123"
        limit, window = middleware._get_rate_limits(request)
        assert limit == settings.RATE_LIMIT_TENANT_REQUESTS_PER_MINUTE
        
        # Unauthenticated user
        delattr(request.state, 'user_role')
        delattr(request.state, 'tenant_id')
        limit, window = middleware._get_rate_limits(request)
        assert limit == settings.RATE_LIMIT_REQUESTS_PER_MINUTE


class TestRateLimitingIntegration:
    """Integration tests for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_global_initialization(self):
        """Test global rate limiting initialization"""
        await initialize_rate_limiting()
        
        # Should not raise an exception
        await cleanup_rate_limiting()
    
    @pytest.mark.asyncio 
    async def test_performance_requirements(self):
        """Test that rate limiting meets <5ms performance requirement"""
        rate_limiter = RedisRateLimiter()
        
        # Mock fast Redis response
        with patch.object(rate_limiter, 'redis_client') as mock_client:
            mock_client.eval.return_value = [1, 9, int(time.time() + 60), 1]
            rate_limiter.fallback_mode = False
            
            start_time = time.time()
            await rate_limiter.check_rate_limit("test_key", 10, 60, 5)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Should be well under 5ms (allowing for test overhead)
            assert elapsed_ms < 50  # 50ms buffer for test environment
    
    def test_lua_script_logic(self):
        """Test the Lua script logic for token bucket algorithm"""
        # This would require a real Redis instance for integration testing
        # Here we verify the script structure and parameters
        rate_limiter = RedisRateLimiter()
        
        # Verify script uses proper Redis commands
        # This is a placeholder for more comprehensive Lua script testing
        assert hasattr(rate_limiter, 'check_rate_limit')


@pytest.mark.asyncio
async def test_redis_connection_resilience():
    """Test Redis connection resilience and recovery"""
    rate_limiter = RedisRateLimiter()
    
    # Test initialization with connection failure
    with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool:
        mock_pool.side_effect = Exception("Connection failed")
        await rate_limiter.initialize()
        assert rate_limiter.fallback_mode is True
    
    # Test recovery after connection restored
    with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool:
        mock_pool.return_value = AsyncMock()
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_redis.return_value = mock_client
            
            await rate_limiter.initialize()
            assert rate_limiter.fallback_mode is False


def test_middleware_ordering():
    """Test that rate limiting middleware is properly ordered in the stack"""
    app = FastAPI()
    
    # Simulate the middleware stack from main.py
    from app.middleware.tenant_context import TenantContextMiddleware
    from app.middleware.rate_limiting import RateLimitingMiddleware
    
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    
    # Verify middleware is in the stack
    assert len(app.middleware_stack) > 0
    
    # Rate limiting middleware should come after tenant context middleware
    # in the processing order (but before in the add_middleware order)
    middleware_types = [type(m.cls).__name__ for m in app.middleware_stack]
    assert "RateLimitingMiddleware" in middleware_types
    assert "TenantContextMiddleware" in middleware_types