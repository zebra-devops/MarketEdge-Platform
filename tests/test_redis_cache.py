import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.data.cache.redis_cache import RedisCacheManager
from app.data.interfaces.base import DataResponse, DataSourceType


class TestRedisCacheManager:
    """Test suite for RedisCacheManager"""
    
    @pytest.fixture
    def cache_config(self) -> Dict[str, Any]:
        """Cache configuration for testing"""
        return {
            "redis_url": "redis://localhost:6379/1",
            "default_ttl": 3600,
            "key_prefix": "test_cache:"
        }
    
    @pytest.fixture
    def sample_data_response(self) -> DataResponse:
        """Sample data response for testing"""
        return DataResponse(
            data=[{"id": 1, "name": "test"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1,
            execution_time_ms=50.0
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, cache_config):
        """Test cache manager initialization"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            assert cache_manager.default_ttl == 3600
            assert cache_manager.key_prefix == "test_cache:"
            assert cache_manager.redis_client is not None
            # Check that create_cache_client was called with the correct config
            mock_create_client.assert_called_once_with(cache_config)
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, cache_config):
        """Test initialization failure"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client', side_effect=Exception("Redis connection failed")):
            cache_manager = RedisCacheManager(cache_config)
            
            with pytest.raises(Exception, match="Redis connection failed"):
                await cache_manager.initialize()
    
    @pytest.mark.asyncio
    async def test_generate_cache_key(self, cache_config):
        """Test cache key generation"""
        cache_manager = RedisCacheManager(cache_config)
        
        key = cache_manager.generate_cache_key("competitive_data", "get_competitive_data", org_id="test_org", market="manchester")
        
        # Key should include the source and method
        assert "competitive_data" in key
        assert "get_competitive_data" in key
        # Parameters are hashed, so we just verify the structure
        assert len(key.split(':')) == 3  # source:method:hash
    
    @pytest.mark.asyncio
    async def test_get_success(self, cache_config, sample_data_response):
        """Test successful cache get"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock successful get
            cached_data = {
                "data": sample_data_response.data,
                "source": sample_data_response.source.value,
                "cached": True,
                "total_count": sample_data_response.total_count,
                "execution_time_ms": sample_data_response.execution_time_ms,
                "metadata": sample_data_response.metadata
            }
            mock_client.get.return_value = json.dumps(cached_data)
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.get("test_key")
            
            assert result is not None
            assert isinstance(result, dict)
            assert result["data"] == sample_data_response.data
            assert result["source"] == sample_data_response.source.value
            assert result["cached"] is True
            assert result["total_count"] == sample_data_response.total_count
            
            # Verify Redis was called with correct key
            expected_key = "test_cache:test_key"
            mock_client.get.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_get_miss(self, cache_config):
        """Test cache miss"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock cache miss
            mock_client.get.return_value = None
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.get("test_key")
            
            assert result is None
            mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_invalid_json(self, cache_config):
        """Test get with invalid JSON in cache"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock invalid JSON
            mock_client.get.return_value = "invalid json"
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.get("test_key")
            
            # Invalid JSON should fall back to the string value
            assert result == "invalid json"
    
    @pytest.mark.asyncio
    async def test_set_success(self, cache_config, sample_data_response):
        """Test successful cache set"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.set("test_key", sample_data_response.data)
            
            # Verify Redis was called with correct parameters
            expected_key = "test_cache:test_key"
            # The cache uses setex for TTL-based sets
            mock_client.setex.assert_called_once()
            
            call_args = mock_client.setex.call_args
            assert call_args[0][0] == expected_key  # key
            assert call_args[0][1] == 3600  # default TTL
    
    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_config, sample_data_response):
        """Test cache set with custom TTL"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            from datetime import timedelta
            await cache_manager.set("test_key", sample_data_response.data, ttl=timedelta(seconds=1800))
            
            # Verify custom TTL was used with setex
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            assert call_args[0][1] == 1800  # TTL in seconds
    
    @pytest.mark.asyncio
    async def test_set_with_filters(self, cache_config, sample_data_response):
        """Test cache set with filters"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            # Test setting with a complex key that includes filters
            complex_key = "test_org:manchester:competitive_data:filter_hash"
            await cache_manager.set(complex_key, sample_data_response.data)
            
            # Verify setex was called with correct key pattern
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            key = call_args[0][0]
            assert key.startswith("test_cache:test_org:manchester:competitive_data:filter_hash")
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_config):
        """Test cache deletion"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.delete("test_key")
            
            expected_key = "test_cache:test_key"
            mock_client.delete.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_config):
        """Test clearing cache by pattern"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Create async iterator for scan_iter
            async def async_scan_iter(*args, **kwargs):
                keys = [
                    "test_cache:org1:market1:data1",
                    "test_cache:org1:market2:data2",
                    "test_cache:org2:market1:data1"
                ]
                for key in keys:
                    yield key
                    
            mock_client.scan_iter = async_scan_iter
            # Mock delete to return the number of deleted keys
            mock_client.delete.return_value = 2
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.clear_pattern("test_cache:org1:*")
            
            # Should delete 2 keys matching the pattern
            assert result == 2
            # Verify delete was called once with all matching keys
            mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_pattern_no_matches(self, cache_config):
        """Test clearing cache pattern with no matches"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Create empty async iterator for scan_iter
            async def async_scan_iter(*args, **kwargs):
                return
                yield  # Never reached, but makes this an async generator
                
            mock_client.scan_iter = async_scan_iter
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.clear_pattern("test_cache:nonexistent:*")
            
            assert result == 0
            mock_client.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_exists(self, cache_config):
        """Test checking if key exists"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock exists to return True
            mock_client.exists.return_value = 1
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.exists("test_key")
            
            assert result is True
            expected_key = "test_cache:test_key"
            mock_client.exists.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_exists_false(self, cache_config):
        """Test checking if key doesn't exist"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock exists to return False
            mock_client.exists.return_value = 0
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.exists("test_key")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache_config):
        """Test getting cache statistics"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock info command - Redis info returns flat dict
            mock_client.info.return_value = {
                "used_memory_human": "2.5M",
                "connected_clients": 5,
                "total_commands_processed": 1000,
                "keyspace_hits": 80,
                "keyspace_misses": 20
            }
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            stats = await cache_manager.get_cache_stats()
            
            assert "hit_rate" in stats
            assert "used_memory" in stats
            assert "connected_clients" in stats
            assert "total_commands_processed" in stats
            assert "keyspace_hits" in stats
            assert "keyspace_misses" in stats
            assert stats["hit_rate"] == 80.0  # 80/(80+20)*100
            assert stats["connected_clients"] == 5
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_no_keyspace(self, cache_config):
        """Test getting cache stats with no keyspace info"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Mock info command with no keyspace
            mock_client.info.return_value = {}
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            stats = await cache_manager.get_cache_stats()
            
            assert stats["hit_rate"] == 0.0
            assert stats.get("keyspace_hits", 0) == 0
            assert stats.get("keyspace_misses", 0) == 0
    
    @pytest.mark.asyncio
    async def test_invalidate_org_cache(self, cache_config):
        """Test invalidating cache for organization"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            # Create async iterator for scan_iter
            async def async_scan_iter(*args, **kwargs):
                keys = [
                    "test_cache:test_org:market1:data1",
                    "test_cache:test_org:market2:data2",
                    "test_cache:other_org:market1:data1"
                ]
                for key in keys:
                    yield key
                    
            mock_client.scan_iter = async_scan_iter
            # Mock delete to return the number of deleted keys
            mock_client.delete.return_value = 2
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.invalidate_org_cache("test_org")
            
            # Should delete 2 keys for the org
            assert result == 2
            # Verify delete was called once with all matching keys
            mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close(self, cache_config):
        """Test closing the cache manager"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.close()
            
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_json_serialization(self, cache_config):
        """Test JSON serialization and deserialization"""
        with patch('app.data.cache.redis_cache.redis_manager.create_cache_client') as mock_create_client:
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            # Test setting and getting JSON data
            test_data = {"test": "value", "number": 123}
            await cache_manager.set("test_key", test_data)
            
            # Verify the data was serialized to JSON using setex
            assert mock_client.setex.called, "Redis setex method should be called"
            call_args = mock_client.setex.call_args
            serialized_value = call_args[0][2]  # Value is 3rd argument in setex
            
            # Test getting the data back
            mock_client.get.return_value = serialized_value
            result = await cache_manager.get("test_key")
            assert result == test_data 