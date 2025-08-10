import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
from datetime import datetime, timedelta

from app.data.platform_data_layer import PlatformDataLayer
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse
from app.data.config.data_layer_config import create_test_config


class TestDataLayerIntegration:
    """Integration tests for the complete data abstraction layer"""
    
    @pytest.fixture
    def integration_config(self) -> Dict[str, Any]:
        """Configuration for integration testing"""
        config = create_test_config()
        # Enable cache for integration tests
        config["cache"]["enabled"] = True
        return config
    
    @pytest.fixture
    def mock_supabase_response(self) -> Dict[str, Any]:
        """Mock Supabase response for integration tests"""
        return {
            "data": [
                {
                    "id": 1,
                    "org_id": "test-org-123",
                    "market": "manchester",
                    "competitor_name": "vue",
                    "date": "2024-01-15",
                    "price": 12.50,
                    "availability": True,
                    "created_at": "2024-01-15T10:00:00Z"
                },
                {
                    "id": 2,
                    "org_id": "test-org-123",
                    "market": "manchester",
                    "competitor_name": "cineworld",
                    "date": "2024-01-15",
                    "price": 11.99,
                    "availability": True,
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ],
            "count": 2,
            "error": None
        }
    
    @pytest.mark.asyncio
    async def test_full_initialization_flow(self, integration_config):
        """Test complete initialization flow with all components"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock cache manager
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            # Mock router
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            # Mock Supabase source
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Initialize data layer
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Verify all components were initialized
            assert data_layer._initialized
            assert data_layer.cache_manager is not None
            assert data_layer.router is not None
            
            # Verify Supabase source was registered
            mock_router_instance.register_source.assert_called_once_with(
                DataSourceType.SUPABASE, mock_supabase_instance
            )
            
            # Verify cache manager was initialized
            mock_cache_instance.initialize.assert_called_once()
            
            # Verify Supabase source was initialized
            mock_supabase_instance.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_competitive_intelligence_workflow(self, integration_config, mock_supabase_response):
        """Test complete competitive intelligence workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss then hit
            mock_cache_instance.get.return_value = None
            
            # Mock router response
            expected_response = DataResponse(
                data=mock_supabase_response["data"],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=2,
                execution_time_ms=100.0
            )
            mock_router_instance.route_competitive_data.return_value = expected_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test competitive intelligence query
            result = await data_layer.get_competitive_intelligence(
                org_id="test-org-123",
                market="manchester",
                competitors=["vue", "cineworld"],
                limit=10
            )
            
            # Verify result
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["competitor_name"] == "vue"
            assert result.data[1]["competitor_name"] == "cineworld"
            
            # Verify router was called
            mock_router_instance.route_competitive_data.assert_called_once()
            
            # Verify cache was checked and set
            mock_cache_instance.get.assert_called_once()
            mock_cache_instance.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_caching_workflow(self, integration_config, mock_supabase_response):
        """Test caching workflow with cache hit and miss scenarios"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss for first call, hit for second call
            cached_response = DataResponse(
                data=mock_supabase_response["data"],
                source=DataSourceType.SUPABASE,
                cached=True,
                total_count=2,
                execution_time_ms=50.0
            )
            
            mock_cache_instance.get.side_effect = [None, cached_response]
            
            # Mock router response for cache miss
            fresh_response = DataResponse(
                data=mock_supabase_response["data"],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=2,
                execution_time_ms=100.0
            )
            mock_router_instance.route_competitive_data.return_value = fresh_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # First call - cache miss
            result1 = await data_layer.get_competitive_intelligence(
                org_id="test-org-123",
                market="manchester"
            )
            
            assert result1 == fresh_response
            assert result1.cached is False
            mock_router_instance.route_competitive_data.assert_called_once()
            
            # Second call - cache hit
            result2 = await data_layer.get_competitive_intelligence(
                org_id="test-org-123",
                market="manchester"
            )
            
            assert result2 == cached_response
            assert result2.cached is True
            # Router should not be called again
            assert mock_router_instance.route_competitive_data.call_count == 1
    
    @pytest.mark.asyncio
    async def test_reference_data_workflow(self, integration_config):
        """Test reference data workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss
            mock_cache_instance.get.return_value = None
            
            # Mock router response
            expected_response = DataResponse(
                data=[
                    {"id": 1, "name": "manchester", "region": "north-west"},
                    {"id": 2, "name": "london", "region": "south-east"}
                ],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=2
            )
            mock_router_instance.route_reference_data.return_value = expected_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test reference data query
            result = await data_layer.get_uk_markets()
            
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["name"] == "manchester"
            assert result.data[1]["name"] == "london"
            
            # Verify router was called
            mock_router_instance.route_reference_data.assert_called_once_with("uk_markets", None)
    
    @pytest.mark.asyncio
    async def test_search_workflow(self, integration_config):
        """Test search workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss
            mock_cache_instance.get.return_value = None
            
            # Mock router response
            expected_response = DataResponse(
                data=[
                    {"id": 1, "competitor": "vue", "relevance": 0.95},
                    {"id": 2, "competitor": "vue cinema", "relevance": 0.85}
                ],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=2
            )
            mock_router_instance.route_competitive_data.return_value = expected_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test search
            result = await data_layer.search_competitive_data(
                org_id="test-org-123",
                search_query="vue cinema",
                market="manchester",
                limit=50
            )
            
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["relevance"] == 0.95
            
            # Verify router was called with correct parameters
            mock_router_instance.route_competitive_data.assert_called_once()
            call_args = mock_router_instance.route_competitive_data.call_args
            assert call_args[0][0] == "test-org-123"  # org_id
            assert call_args[0][1] == "all"  # market (all for search)
            
            # Verify search parameters
            params = call_args[0][2]
            assert params.filters["search"] == "vue cinema"
            assert params.filters["market"] == "manchester"
            assert params.limit == 50
            assert params.order_by == ["-relevance", "-date"]
    
    @pytest.mark.asyncio
    async def test_trending_data_workflow(self, integration_config):
        """Test trending data workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss
            mock_cache_instance.get.return_value = None
            
            # Mock router response
            expected_response = DataResponse(
                data=[
                    {"id": 1, "trend_score": 0.95, "competitor": "vue"},
                    {"id": 2, "trend_score": 0.85, "competitor": "cineworld"}
                ],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=2
            )
            mock_router_instance.route_competitive_data.return_value = expected_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test trending data
            result = await data_layer.get_trending_data(
                org_id="test-org-123",
                market="manchester",
                period="7d",
                limit=20
            )
            
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["trend_score"] == 0.95
            
            # Verify router was called with correct parameters
            mock_router_instance.route_competitive_data.assert_called_once()
            call_args = mock_router_instance.route_competitive_data.call_args
            
            # Verify trending parameters
            params = call_args[0][2]
            assert params.filters["trending"] is True
            assert "date_range" in params.filters
            assert params.limit == 20
            assert params.order_by == ["-trend_score", "-date"]
    
    @pytest.mark.asyncio
    async def test_health_check_workflow(self, integration_config):
        """Test health check workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock health check responses
            mock_router_instance.health_check_all.return_value = {
                "supabase": True,
                "redis": True
            }
            mock_router_instance.get_routing_stats.return_value = {
                "total_queries": 100,
                "cache_hits": 80,
                "cache_misses": 20,
                "average_response_time_ms": 150.0,
                "sources_used": {"supabase": 100}
            }
            mock_cache_instance.get_cache_stats.return_value = {
                "hit_rate": 0.8,
                "total_keys": 50,
                "avg_ttl": 1800
            }
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test health check
            health_status = await data_layer.get_health_status()
            
            assert health_status["platform_data_layer"]["initialized"] is True
            assert health_status["platform_data_layer"]["healthy"] is True
            assert health_status["data_sources"]["supabase"] is True
            assert health_status["cache"]["healthy"] is True
            assert health_status["cache"]["stats"]["hit_rate"] == 0.8
            assert health_status["router"]["total_queries"] == 100
            assert health_status["router"]["cache_hits"] == 80
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_workflow(self, integration_config):
        """Test cache invalidation workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock invalidation responses
            mock_router_instance.invalidate_cache_for_org.return_value = 5
            mock_router_instance.invalidate_cache_for_market.return_value = 3
            mock_cache_instance.clear_pattern.return_value = 10
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test org invalidation
            result1 = await data_layer.invalidate_cache(org_id="test-org")
            assert result1 == 5
            mock_router_instance.invalidate_cache_for_org.assert_called_once_with("test-org")
            
            # Test market invalidation
            result2 = await data_layer.invalidate_cache(market="manchester")
            assert result2 == 3
            mock_router_instance.invalidate_cache_for_market.assert_called_once_with("manchester")
            
            # Test pattern invalidation
            result3 = await data_layer.invalidate_cache(pattern="test:*")
            assert result3 == 10
            mock_cache_instance.clear_pattern.assert_called_once_with("test:*")
            
            # Test full invalidation
            result4 = await data_layer.invalidate_cache()
            assert result4 == 10
            mock_cache_instance.clear_pattern.assert_called_with("*")
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, integration_config):
        """Test error handling workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache miss
            mock_cache_instance.get.return_value = None
            
            # Mock router to raise exception
            mock_router_instance.route_competitive_data.side_effect = Exception("Database connection failed")
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test error handling
            with pytest.raises(Exception, match="Database connection failed"):
                await data_layer.get_competitive_intelligence(
                    org_id="test-org-123",
                    market="manchester"
                )
            
            # Verify cache was checked but not set due to error
            mock_cache_instance.get.assert_called_once()
            mock_cache_instance.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_usage_metrics_workflow(self, integration_config):
        """Test usage metrics workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock cache stats
            mock_cache_instance.get_cache_stats.return_value = {
                "hit_rate": 0.75,
                "total_keys": 100,
                "avg_ttl": 1800
            }
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test usage metrics
            metrics = await data_layer.get_usage_metrics("test-org-123")
            
            assert "queries_executed" in metrics
            assert "data_retrieved_mb" in metrics
            assert "cache_hit_rate" in metrics
            assert "average_response_time_ms" in metrics
            assert metrics["cache_hit_rate"] == 0.75
    
    @pytest.mark.asyncio
    async def test_cleanup_workflow(self, integration_config):
        """Test cleanup workflow"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock sources in router
            mock_router_instance.sources = {"supabase": mock_supabase_instance}
            
            # Initialize and test
            data_layer = PlatformDataLayer(integration_config)
            await data_layer.initialize()
            
            # Test cleanup
            await data_layer.close()
            
            # Verify all components were closed
            assert not data_layer._initialized
            mock_supabase_instance.close.assert_called_once()
            mock_cache_instance.close.assert_called_once() 