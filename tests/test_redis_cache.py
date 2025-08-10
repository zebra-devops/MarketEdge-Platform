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
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            assert cache_manager.default_ttl == 3600
            assert cache_manager.key_prefix == "test_cache:"
            assert cache_manager.redis_client is not None
            # Check that redis.from_url was called with the correct URL and parameters
            mock_redis.assert_called_once()
            call_args = mock_redis.call_args
            assert call_args[0][0] == "redis://localhost:6379/1"  # URL
            assert call_args[1]["encoding"] == "utf-8"
            assert call_args[1]["decode_responses"] is True
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, cache_config):
        """Test initialization failure"""
        with patch('app.data.cache.redis_cache.redis.from_url', side_effect=Exception("Redis connection failed")):
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
        assert "test_org" in key
        assert "manchester" in key
    
    @pytest.mark.asyncio
    async def test_get_success(self, cache_config, sample_data_response):
        """Test successful cache get"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
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
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
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
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock invalid JSON
            mock_client.get.return_value = "invalid json"
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.get("test_key")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_set_success(self, cache_config, sample_data_response):
        """Test successful cache set"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.set("test_key", sample_data_response.data)
            
            # Verify Redis was called with correct parameters
            expected_key = "test_cache:test_key"
            mock_client.set.assert_called_once()
            
            call_args = mock_client.set.call_args
            assert call_args[0][0] == expected_key  # key
            # TTL is optional, so we don't assert it
    
    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_config, sample_data_response):
        """Test cache set with custom TTL"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            from datetime import timedelta
            await cache_manager.set("test_key", sample_data_response.data, ttl=timedelta(seconds=1800))
            
            # Verify custom TTL was used
            call_args = mock_client.set.call_args
            # TTL is passed as ex parameter
            assert "ex" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_set_with_filters(self, cache_config, sample_data_response):
        """Test cache set with filters"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            # Test setting with a complex key that includes filters
            complex_key = "test_org:manchester:competitive_data:filter_hash"
            await cache_manager.set(complex_key, sample_data_response.data)
            
            # Verify key was used correctly
            call_args = mock_client.set.call_args
            key = call_args[0][0]
            assert "test_cache:test_org:manchester:competitive_data:filter_hash" in key
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_config):
        """Test cache deletion"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.delete("test_key")
            
            expected_key = "test_cache:test_key"
            mock_client.delete.assert_called_once_with(expected_key)
    
    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_config):
        """Test clearing cache by pattern"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock scan_iter to return some keys
            mock_client.scan_iter.return_value = [
                "test_cache:org1:market1:data1",
                "test_cache:org1:market2:data2",
                "test_cache:org2:market1:data1"
            ]
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.clear_pattern("test_cache:org1:*")
            
            # Should delete 2 keys matching the pattern
            assert result == 2
            assert mock_client.delete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_clear_pattern_no_matches(self, cache_config):
        """Test clearing cache pattern with no matches"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock scan_iter to return no keys
            mock_client.scan_iter.return_value = []
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.clear_pattern("test_cache:nonexistent:*")
            
            assert result == 0
            mock_client.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_exists(self, cache_config):
        """Test checking if key exists"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
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
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock exists to return False
            mock_client.exists.return_value = 0
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.exists("test_key")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache_config):
        """Test getting cache statistics"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock info command
            mock_client.info.return_value = {
                "keyspace": {
                    "db1": {
                        "keys": 100,
                        "expires": 50,
                        "avg_ttl": 1800
                    }
                },
                "stats": {
                    "keyspace_hits": 80,
                    "keyspace_misses": 20
                }
            }
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            stats = await cache_manager.get_cache_stats()
            
            assert "hit_rate" in stats
            assert "total_keys" in stats
            assert "expired_keys" in stats
            assert "avg_ttl" in stats
            assert stats["total_keys"] == 100
            assert stats["expired_keys"] == 50
            assert stats["avg_ttl"] == 1800
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_no_keyspace(self, cache_config):
        """Test getting cache stats with no keyspace info"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock info command with no keyspace
            mock_client.info.return_value = {}
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            stats = await cache_manager.get_cache_stats()
            
            assert stats["total_keys"] == 0
            assert stats["expired_keys"] == 0
            assert stats["avg_ttl"] == 0
    
    @pytest.mark.asyncio
    async def test_invalidate_org_cache(self, cache_config):
        """Test invalidating cache for organization"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Mock scan_iter to return keys for the org
            mock_client.scan_iter.return_value = [
                "test_cache:test_org:market1:data1",
                "test_cache:test_org:market2:data2",
                "test_cache:other_org:market1:data1"
            ]
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            result = await cache_manager.invalidate_org_cache("test_org")
            
            # Should delete 2 keys for the org
            assert result == 2
            assert mock_client.delete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_close(self, cache_config):
        """Test closing the cache manager"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            await cache_manager.close()
            
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_json_serialization(self, cache_config):
        """Test JSON serialization and deserialization"""
        with patch('app.data.cache.redis_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache_manager = RedisCacheManager(cache_config)
            await cache_manager.initialize()
            
            # Test setting and getting JSON data
            test_data = {"test": "value", "number": 123}
            await cache_manager.set("test_key", test_data)
            
            # Verify the data was serialized to JSON
            call_args = mock_client.set.call_args
            serialized_value = call_args[0][1]
            assert isinstance(serialized_value, str)
            
            # Test getting the data back
            mock_client.get.return_value = serialized_value
            result = await cache_manager.get("test_key")
            assert result == test_data 