import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
from datetime import datetime, timedelta

from app.data.platform_data_layer import PlatformDataLayer
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse
from app.data.config.data_layer_config import create_test_config


class TestCoreFunctionality:
    """Simplified test suite focusing on core functionality"""
    
    @pytest.fixture
    def test_config(self) -> Dict[str, Any]:
        """Test configuration for data layer"""
        config = create_test_config()
        # Disable cache for simpler testing
        config["cache"]["enabled"] = False
        return config
    
    @pytest.fixture
    def sample_data_response(self) -> DataResponse:
        """Sample data response for testing"""
        return DataResponse(
            data=[
                {
                    "id": 1,
                    "org_id": "test-org-123",
                    "market": "manchester",
                    "competitor_name": "vue",
                    "date": "2024-01-15",
                    "price": 12.50,
                    "availability": True
                }
            ],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1,
            execution_time_ms=50.0
        )
    
    @pytest.mark.asyncio
    async def test_platform_data_layer_initialization(self, test_config):
        """Test that the platform data layer can be initialized"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Test initialization
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Verify initialization
            assert data_layer._initialized is True
            assert data_layer.is_initialized is True
            assert data_layer.router is not None
            assert data_layer.cache_manager is None  # Cache disabled
    
    @pytest.mark.asyncio
    async def test_platform_data_layer_with_cache(self, test_config):
        """Test that the platform data layer works with cache enabled"""
        # Enable cache
        test_config["cache"]["enabled"] = True
        
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Test initialization
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Verify initialization
            assert data_layer._initialized is True
            assert data_layer.cache_manager is not None
    
    @pytest.mark.asyncio
    async def test_competitive_intelligence_query(self, test_config, sample_data_response):
        """Test competitive intelligence data query"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock router response
            mock_router_instance.route_competitive_data.return_value = sample_data_response
            
            # Initialize and test
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test query
            result = await data_layer.get_competitive_intelligence(
                org_id="test-org-123",
                market="manchester",
                competitors=["vue", "cineworld"],
                limit=10
            )
            
            # Verify result
            assert result == sample_data_response
            assert len(result.data) == 1
            assert result.data[0]["competitor_name"] == "vue"
            assert result.data[0]["market"] == "manchester"
            
            # Verify router was called
            mock_router_instance.route_competitive_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reference_data_query(self, test_config):
        """Test reference data query"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
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
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test query
            result = await data_layer.get_uk_markets()
            
            # Verify result
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["name"] == "manchester"
            assert result.data[1]["name"] == "london"
            
            # Verify router was called
            mock_router_instance.route_reference_data.assert_called_once_with("uk_markets", None)
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, test_config):
        """Test search functionality"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
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
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test search
            result = await data_layer.search_competitive_data(
                org_id="test-org-123",
                search_query="vue cinema",
                market="manchester",
                limit=50
            )
            
            # Verify result
            assert result == expected_response
            assert len(result.data) == 2
            assert result.data[0]["relevance"] == 0.95
            
            # Verify router was called with correct parameters
            mock_router_instance.route_competitive_data.assert_called_once()
            call_args = mock_router_instance.route_competitive_data.call_args
            assert call_args[0][0] == "test-org-123"  # org_id
            assert call_args[0][1] == "all"  # market (all for search)
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_config):
        """Test health check functionality"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
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
                "total_keys": 50
            }
            
            # Initialize and test
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test health check
            health_status = await data_layer.get_health_status()
            
            # Verify health status
            assert health_status["platform_data_layer"]["initialized"] is True
            # Note: health check might fail if cache manager is not properly mocked
            # We'll just verify the basic structure
            assert "platform_data_layer" in health_status
            assert "data_sources" in health_status
            assert "router" in health_status
            assert health_status["data_sources"]["supabase"] is True
            assert health_status["router"]["total_queries"] == 100
            assert health_status["router"]["cache_hits"] == 80
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_config):
        """Test error handling when data source fails"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock router to raise exception
            mock_router_instance.route_competitive_data.side_effect = Exception("Database connection failed")
            
            # Initialize and test
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test error handling
            with pytest.raises(Exception, match="Database connection failed"):
                await data_layer.get_competitive_intelligence(
                    org_id="test-org-123",
                    market="manchester"
                )
    
    @pytest.mark.asyncio
    async def test_cleanup(self, test_config):
        """Test cleanup functionality"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock sources in router
            mock_router_instance.sources = {"supabase": mock_supabase_instance}
            
            # Initialize and test
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test cleanup
            await data_layer.close()
            
            # Verify cleanup
            assert not data_layer._initialized
            mock_supabase_instance.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_without_cache(self, test_config):
        """Test initialization without cache"""
        # Ensure cache is disabled
        test_config["cache"]["enabled"] = False
        
        with patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Test initialization
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Verify initialization without cache
            assert data_layer._initialized is True
            assert data_layer.cache_manager is None
            assert data_layer.router is not None
    
    @pytest.mark.asyncio
    async def test_multiple_queries(self, test_config, sample_data_response):
        """Test multiple queries work correctly"""
        with patch('app.data.platform_data_layer.RedisCacheManager') as mock_cache, \
             patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            # Mock components
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            mock_router_instance = AsyncMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            # Mock router responses
            mock_router_instance.route_competitive_data.return_value = sample_data_response
            mock_router_instance.route_reference_data.return_value = DataResponse(
                data=[{"id": 1, "name": "test"}],
                source=DataSourceType.SUPABASE,
                cached=False,
                total_count=1
            )
            
            # Initialize and test
            data_layer = PlatformDataLayer(test_config)
            await data_layer.initialize()
            
            # Test multiple queries
            result1 = await data_layer.get_competitive_intelligence(
                org_id="test-org-123",
                market="manchester"
            )
            
            result2 = await data_layer.get_uk_markets()
            
            # Verify both queries worked
            assert result1 == sample_data_response
            assert result2.data[0]["name"] == "test"
            assert mock_router_instance.route_competitive_data.call_count == 1
            assert mock_router_instance.route_reference_data.call_count == 1 