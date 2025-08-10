import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from app.data.platform_data_layer import PlatformDataLayer
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse
from app.data.config.data_layer_config import create_test_config


class TestPlatformDataLayer:
    """Test suite for PlatformDataLayer"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialization(self, test_config):
        """Test data layer initialization"""
        layer = PlatformDataLayer(test_config)
        
        assert layer.config == test_config
        assert layer.router is None
        assert layer.cache_manager is None
        assert not layer._initialized
        assert not layer.is_initialized
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_success(self, test_config):
        """Test successful initialization"""
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
            
            layer = PlatformDataLayer(test_config)
            await layer.initialize()
            
            assert layer._initialized
            assert layer.is_initialized
            assert layer.cache_manager is not None
            assert layer.router is not None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_without_cache(self, test_config):
        """Test initialization without cache enabled"""
        test_config["cache"]["enabled"] = False
        
        with patch('app.data.platform_data_layer.DataSourceRouter') as mock_router, \
             patch('app.data.platform_data_layer.SupabaseDataSource') as mock_supabase:
            
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            
            mock_supabase_instance = AsyncMock()
            mock_supabase.return_value = mock_supabase_instance
            
            layer = PlatformDataLayer(test_config)
            await layer.initialize()
            
            assert layer._initialized
            assert layer.cache_manager is None
            assert layer.router is not None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_initialize_failure(self, test_config):
        """Test initialization failure"""
        with patch('app.data.platform_data_layer.RedisCacheManager', side_effect=Exception("Cache error")):
            layer = PlatformDataLayer(test_config)
            
            with pytest.raises(Exception, match="Cache error"):
                await layer.initialize()
            
            assert not layer._initialized
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_competitive_intelligence(self, data_layer):
        """Test getting competitive intelligence data"""
        # Mock the router to return expected data
        mock_response = DataResponse(
            data=[{"id": 1, "competitor": "vue"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_competitive_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_competitive_intelligence(
            org_id="test-org",
            market="manchester",
            competitors=["vue", "cineworld"],
            limit=10
        )
        
        assert result == mock_response
        data_layer.router.route_competitive_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_competitive_data.call_args
        assert call_args[0][0] == "test-org"  # org_id
        assert call_args[0][1] == "manchester"  # market
        
        # Verify QueryParams
        params = call_args[0][2]
        assert params.filters["competitors"] == ["vue", "cineworld"]
        assert params.limit == 10
        assert params.order_by == ["-date", "competitor_name"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_market_data(self, data_layer):
        """Test getting market analytics data"""
        mock_response = DataResponse(
            data=[{"market": "manchester", "revenue": 1000}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_analytics_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_market_data(
            org_id="test-org",
            market="manchester",
            metrics=["revenue", "transactions"],
            aggregation="daily"
        )
        
        assert result == mock_response
        data_layer.router.route_analytics_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_analytics_data.call_args
        assert call_args[0][0] == "test-org"  # org_id
        
        # Verify QueryParams
        params = call_args[0][1]
        assert params.filters["market"] == "manchester"
        assert params.filters["metrics"] == ["revenue", "transactions"]
        assert params.filters["aggregation"] == "daily"
        assert params.order_by == ["-date"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_reference_data(self, data_layer):
        """Test getting reference data"""
        mock_response = DataResponse(
            data=[{"id": 1, "name": "manchester"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_reference_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_reference_data(
            dataset="uk_markets",
            filters={"active": True},
            limit=5
        )
        
        assert result == mock_response
        data_layer.router.route_reference_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_reference_data.call_args
        assert call_args[0][0] == "uk_markets"  # dataset
        
        # Verify QueryParams
        params = call_args[0][1]
        assert params.filters["active"] is True
        assert params.limit == 5
        assert params.order_by == ["name"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_uk_markets(self, data_layer):
        """Test getting UK markets"""
        mock_response = DataResponse(
            data=[{"id": 1, "name": "manchester"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_reference_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_uk_markets()
        
        assert result == mock_response
        data_layer.router.route_reference_data.assert_called_once_with("uk_markets", None)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_competitors(self, data_layer):
        """Test getting competitors"""
        mock_response = DataResponse(
            data=[{"id": 1, "name": "vue"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_reference_data.return_value = mock_response
        data_layer._initialized = True
        
        # Test with market filter
        result = await data_layer.get_competitors(market="manchester")
        
        assert result == mock_response
        data_layer.router.route_reference_data.assert_called_once()
        
        # Verify QueryParams
        call_args = data_layer.router.route_reference_data.call_args
        params = call_args[0][1]
        assert params.filters["market"] == "manchester"
        assert params.order_by == ["name"]
        
        # Test without market filter
        data_layer.router.reset_mock()
        result = await data_layer.get_competitors()
        
        call_args = data_layer.router.route_reference_data.call_args
        params = call_args[0][1]
        assert params.filters is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_competitive_data(self, data_layer):
        """Test searching competitive data"""
        mock_response = DataResponse(
            data=[{"id": 1, "competitor": "vue"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_competitive_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.search_competitive_data(
            org_id="test-org",
            search_query="vue cinema",
            market="manchester",
            limit=50
        )
        
        assert result == mock_response
        data_layer.router.route_competitive_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_competitive_data.call_args
        assert call_args[0][0] == "test-org"  # org_id
        assert call_args[0][1] == "all"  # market (all for search)
        
        # Verify QueryParams
        params = call_args[0][2]
        assert params.filters["search"] == "vue cinema"
        assert params.filters["market"] == "manchester"
        assert params.limit == 50
        assert params.order_by == ["-relevance", "-date"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_trending_data(self, data_layer):
        """Test getting trending data"""
        mock_response = DataResponse(
            data=[{"id": 1, "trend_score": 0.95}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_competitive_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_trending_data(
            org_id="test-org",
            market="manchester",
            period="7d",
            limit=20
        )
        
        assert result == mock_response
        data_layer.router.route_competitive_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_competitive_data.call_args
        assert call_args[0][0] == "test-org"  # org_id
        assert call_args[0][1] == "manchester"  # market
        
        # Verify QueryParams with date range
        params = call_args[0][2]
        assert params.filters["trending"] is True
        assert "date_range" in params.filters
        assert params.limit == 20
        assert params.order_by == ["-trend_score", "-date"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_analytics_summary(self, data_layer):
        """Test getting analytics summary"""
        mock_response = DataResponse(
            data={"total_records": 1000, "markets_covered": 5},
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_analytics_data.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.get_analytics_summary(
            org_id="test-org",
            date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"}
        )
        
        assert result == mock_response
        data_layer.router.route_analytics_data.assert_called_once()
        
        # Verify the call parameters
        call_args = data_layer.router.route_analytics_data.call_args
        assert call_args[0][0] == "test-org"  # org_id
        
        # Verify QueryParams
        params = call_args[0][1]
        assert params.filters["summary"] is True
        assert params.filters["date_range"]["start_date"] == "2024-01-01"
        assert params.filters["date_range"]["end_date"] == "2024-01-31"
        assert "aggregations" in params.__dict__
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_execute_custom_query(self, data_layer):
        """Test executing custom query"""
        mock_response = DataResponse(
            data=[{"result": "custom_data"}],
            source=DataSourceType.SUPABASE,
            cached=False,
            total_count=1
        )
        
        data_layer.router = AsyncMock()
        data_layer.router.route_custom_query.return_value = mock_response
        data_layer._initialized = True
        
        result = await data_layer.execute_custom_query(
            query_name="top_competitors",
            parameters={"market": "manchester", "limit": 5}
        )
        
        assert result == mock_response
        data_layer.router.route_custom_query.assert_called_once_with(
            "custom", "top_competitors", {"market": "manchester", "limit": 5}
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalidate_cache(self, data_layer):
        """Test cache invalidation"""
        data_layer.cache_manager = AsyncMock()
        data_layer.router = AsyncMock()
        data_layer.router.invalidate_cache_for_org.return_value = 5
        data_layer.router.invalidate_cache_for_market.return_value = 3
        data_layer.cache_manager.clear_pattern.return_value = 10
        data_layer._initialized = True
        
        # Test invalidate by org_id
        result = await data_layer.invalidate_cache(org_id="test-org")
        assert result == 5
        data_layer.router.invalidate_cache_for_org.assert_called_once_with("test-org")
        
        # Test invalidate by market
        data_layer.router.reset_mock()
        result = await data_layer.invalidate_cache(market="manchester")
        assert result == 3
        data_layer.router.invalidate_cache_for_market.assert_called_once_with("manchester")
        
        # Test invalidate by pattern
        data_layer.router.reset_mock()
        result = await data_layer.invalidate_cache(pattern="test:*")
        assert result == 10
        data_layer.cache_manager.clear_pattern.assert_called_once_with("test:*")
        
        # Test invalidate all
        data_layer.router.reset_mock()
        data_layer.cache_manager.reset_mock()
        result = await data_layer.invalidate_cache()
        assert result == 10
        data_layer.cache_manager.clear_pattern.assert_called_once_with("*")
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_no_cache_manager(self, data_layer):
        """Test cache invalidation when no cache manager"""
        data_layer.cache_manager = None
        data_layer._initialized = True
        
        result = await data_layer.invalidate_cache(org_id="test-org")
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, data_layer):
        """Test getting health status"""
        data_layer.cache_manager = AsyncMock()
        data_layer.router = AsyncMock()
        data_layer._initialized = True
        
        # Mock health check responses
        data_layer.router.health_check_all.return_value = {
            "supabase": True,
            "redis": True
        }
        data_layer.router.get_routing_stats.return_value = {
            "total_queries": 100,
            "cache_hits": 80
        }
        data_layer.cache_manager.get_cache_stats.return_value = {
            "hit_rate": 0.8,
            "total_keys": 50
        }
        
        result = await data_layer.get_health_status()
        
        assert result["platform_data_layer"]["initialized"] is True
        assert result["platform_data_layer"]["healthy"] is True
        assert result["data_sources"]["supabase"] is True
        assert result["cache"]["healthy"] is True
        assert result["cache"]["stats"]["hit_rate"] == 0.8
        assert result["router"]["total_queries"] == 100
    
    @pytest.mark.asyncio
    async def test_get_usage_metrics(self, data_layer):
        """Test getting usage metrics"""
        data_layer.cache_manager = AsyncMock()
        data_layer._initialized = True
        
        data_layer.cache_manager.get_cache_stats.return_value = {
            "hit_rate": 0.75,
            "total_keys": 100
        }
        
        result = await data_layer.get_usage_metrics("test-org")
        
        assert "queries_executed" in result
        assert "data_retrieved_mb" in result
        assert "cache_hit_rate" in result
        assert "average_response_time_ms" in result
        assert result["cache_hit_rate"] == 0.75
    
    @pytest.mark.asyncio
    async def test_get_usage_metrics_no_cache(self, data_layer):
        """Test getting usage metrics without cache manager"""
        data_layer.cache_manager = None
        data_layer._initialized = True
        
        result = await data_layer.get_usage_metrics("test-org")
        
        assert result["cache_hit_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_ensure_initialized_error(self, data_layer):
        """Test error when methods called before initialization"""
        data_layer._initialized = False
        
        with pytest.raises(RuntimeError, match="Platform data layer not initialized"):
            await data_layer.get_competitive_intelligence("test-org", "manchester")
    
    @pytest.mark.asyncio
    async def test_close(self, data_layer):
        """Test closing the data layer"""
        data_layer.router = AsyncMock()
        data_layer.cache_manager = AsyncMock()
        data_layer._initialized = True
        
        # Mock data sources
        mock_source = AsyncMock()
        data_layer.router.sources = {"supabase": mock_source}
        
        await data_layer.close()
        
        assert not data_layer._initialized
        mock_source.close.assert_called_once()
        data_layer.cache_manager.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self, data_layer):
        """Test closing with exception handling"""
        data_layer.router = AsyncMock()
        data_layer.cache_manager = AsyncMock()
        data_layer._initialized = True
        
        # Mock data sources that raise exception
        mock_source = AsyncMock()
        mock_source.close.side_effect = Exception("Close error")
        data_layer.router.sources = {"supabase": mock_source}
        
        # Should not raise exception
        await data_layer.close()
        
        assert not data_layer._initialized 