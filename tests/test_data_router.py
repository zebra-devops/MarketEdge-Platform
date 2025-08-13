import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.data.router.data_router import DataSourceRouter
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse
from app.data.interfaces.router import IDataSourceRouter


class TestDataSourceRouter:
    """Test suite for DataSourceRouter"""
    
    @pytest.fixture
    def router_config(self) -> Dict[str, Any]:
        """Router configuration for testing"""
        return {
            "default_source": "supabase",
            "enable_fallback": True,
            "health_check_interval": 60
        }
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_supabase_source(self):
        """Mock Supabase data source"""
        mock_source = AsyncMock()
        mock_source.source_type = DataSourceType.SUPABASE
        mock_source.is_initialized = True
        return mock_source
    
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
    async def test_initialization(self, router_config, mock_cache_manager):
        """Test router initialization"""
        router = DataSourceRouter(mock_cache_manager)
        
        assert router.cache_manager == mock_cache_manager
        assert router.sources == {}
        assert router.default_source == "supabase"
        assert router.enable_fallback is True
        assert router.health_check_interval == 60
    
    @pytest.mark.asyncio
    async def test_register_source(self, router_config, mock_cache_manager, mock_supabase_source):
        """Test registering a data source"""
        router = DataSourceRouter(mock_cache_manager)
        
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        assert DataSourceType.SUPABASE in router.sources
        assert router.sources[DataSourceType.SUPABASE] == mock_supabase_source
    
    @pytest.mark.asyncio
    async def test_register_multiple_sources(self, router_config, mock_cache_manager):
        """Test registering multiple data sources"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock different sources
        supabase_source = AsyncMock()
        supabase_source.source_type = DataSourceType.SUPABASE
        
        postgres_source = AsyncMock()
        postgres_source.source_type = DataSourceType.POSTGRESQL
        
        router.register_source(DataSourceType.SUPABASE, supabase_source)
        router.register_source(DataSourceType.POSTGRESQL, postgres_source)
        
        assert len(router.sources) == 2
        assert DataSourceType.SUPABASE in router.sources
        assert DataSourceType.POSTGRESQL in router.sources
    
    @pytest.mark.asyncio
    async def test_get_source(self, router_config, mock_cache_manager, mock_supabase_source):
        """Test getting a registered source"""
        router = DataSourceRouter(mock_cache_manager)
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        source = router.get_source(DataSourceType.SUPABASE)
        assert source == mock_supabase_source
        
        # Test getting non-existent source
        source = router.get_source(DataSourceType.POSTGRESQL)
        assert source is None
    
    @pytest.mark.asyncio
    async def test_route_competitive_data_success(self, router_config, mock_cache_manager, mock_supabase_source, sample_data_response):
        """Test successful routing of competitive data query"""
        router = DataSourceRouter(mock_cache_manager)
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock source response
        mock_supabase_source.get_competitive_data.return_value = sample_data_response
        
        params = QueryParams(filters={"competitors": ["vue"]})
        result = await router.route_competitive_data("test-org", "manchester", params)
        
        assert result == sample_data_response
        mock_supabase_source.get_competitive_data.assert_called_once_with(org_id="test-org", market="manchester", params=params)
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_competitive_data_cache_hit(self, router_config, mock_cache_manager, sample_data_response):
        """Test competitive data routing with cache hit"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache hit
        mock_cache_manager.get.return_value = sample_data_response
        
        params = QueryParams()
        result = await router.route_competitive_data("test-org", "manchester", params)
        
        assert result == sample_data_response
        assert result.cached is True
        # Should not call data source
        assert not hasattr(router, 'sources') or not router.sources
    
    @pytest.mark.asyncio
    async def test_route_competitive_data_fallback(self, router_config, mock_cache_manager):
        """Test competitive data routing with fallback"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock primary source failure
        supabase_source = AsyncMock()
        supabase_source.get_competitive_data.side_effect = Exception("Supabase error")
        router.register_source(DataSourceType.SUPABASE, supabase_source)
        
        # Mock fallback source success
        postgres_source = AsyncMock()
        postgres_source.get_competitive_data.return_value = DataResponse(
            data=[{"id": 1, "fallback": True}],
            source=DataSourceType.POSTGRESQL,
            cached=False
        )
        router.register_source(DataSourceType.POSTGRESQL, postgres_source)
        
        params = QueryParams()
        result = await router.route_competitive_data("test-org", "manchester", params)
        
        assert result.source == DataSourceType.POSTGRESQL
        assert result.data[0]["fallback"] is True
        postgres_source.get_competitive_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_competitive_data_no_sources(self, router_config, mock_cache_manager):
        """Test competitive data routing with no available sources"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        params = QueryParams()
        
        with pytest.raises(RuntimeError, match="No data sources available"):
            await router.route_competitive_data("test-org", "manchester", params)
    
    @pytest.mark.asyncio
    async def test_route_reference_data_success(self, router_config, mock_cache_manager, mock_supabase_source, sample_data_response):
        """Test successful routing of reference data query"""
        router = DataSourceRouter(mock_cache_manager)
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock source response
        mock_supabase_source.get_reference_data.return_value = sample_data_response
        
        params = QueryParams(filters={"active": True})
        result = await router.route_reference_data("uk_markets", params)
        
        assert result == sample_data_response
        mock_supabase_source.get_reference_data.assert_called_once_with("uk_markets", params)
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_analytics_data_success(self, router_config, mock_cache_manager, mock_supabase_source, sample_data_response):
        """Test successful routing of analytics data query"""
        router = DataSourceRouter(mock_cache_manager)
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock source response
        mock_supabase_source.get_analytics_data.return_value = sample_data_response
        
        params = QueryParams(filters={"market": "manchester"})
        result = await router.route_analytics_data("test-org", params)
        
        assert result == sample_data_response
        mock_supabase_source.get_analytics_data.assert_called_once_with("test-org", params)
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_custom_query_success(self, router_config, mock_cache_manager, mock_supabase_source, sample_data_response):
        """Test successful routing of custom query"""
        router = DataSourceRouter(mock_cache_manager)
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock source response
        mock_supabase_source.execute_custom_query.return_value = sample_data_response
        
        result = await router.route_custom_query("custom", "top_competitors", {"market": "manchester"})
        
        assert result == sample_data_response
        mock_supabase_source.execute_custom_query.assert_called_once_with("top_competitors", {"market": "manchester"})
        mock_cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, router_config, mock_cache_manager):
        """Test health check for all sources"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock sources with different health states
        healthy_source = AsyncMock()
        healthy_source.health_check.return_value = True
        
        unhealthy_source = AsyncMock()
        unhealthy_source.health_check.return_value = False
        
        router.register_source(DataSourceType.SUPABASE, healthy_source)
        router.register_source(DataSourceType.POSTGRESQL, unhealthy_source)
        
        health_status = await router.health_check_all()
        
        assert health_status[DataSourceType.SUPABASE] is True
        assert health_status[DataSourceType.POSTGRESQL] is False
        assert len(health_status) == 2
    
    @pytest.mark.asyncio
    async def test_health_check_all_with_exception(self, router_config, mock_cache_manager):
        """Test health check with source exception"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock source that raises exception
        failing_source = AsyncMock()
        failing_source.health_check.side_effect = Exception("Health check failed")
        
        router.register_source(DataSourceType.SUPABASE, failing_source)
        
        health_status = await router.health_check_all()
        
        assert health_status[DataSourceType.SUPABASE] is False
    
    @pytest.mark.asyncio
    async def test_get_routing_stats(self, router_config, mock_cache_manager):
        """Test getting routing statistics"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache stats
        mock_cache_manager.get_cache_stats.return_value = {
            "hit_rate": 0.75,
            "total_keys": 100
        }
        
        stats = await router.get_routing_stats()
        
        assert "total_queries" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "average_response_time_ms" in stats
        assert "sources_used" in stats
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_for_org(self, router_config, mock_cache_manager):
        """Test cache invalidation for organization"""
        router = DataSourceRouter(mock_cache_manager)
        
        mock_cache_manager.invalidate_for_org.return_value = 5
        
        result = await router.invalidate_cache_for_org("test-org")
        
        assert result == 5
        mock_cache_manager.invalidate_for_org.assert_called_once_with("test-org")
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_for_market(self, router_config, mock_cache_manager):
        """Test cache invalidation for market"""
        router = DataSourceRouter(mock_cache_manager)
        
        mock_cache_manager.invalidate_for_market.return_value = 3
        
        result = await router.invalidate_cache_for_market("manchester")
        
        assert result == 3
        mock_cache_manager.invalidate_for_market.assert_called_once_with("manchester")
    
    @pytest.mark.asyncio
    async def test_route_with_cache_disabled(self, router_config, mock_supabase_source, sample_data_response):
        """Test routing with cache disabled"""
        router = DataSourceRouter(None)  # No cache manager
        router.register_source(DataSourceType.SUPABASE, mock_supabase_source)
        
        # Mock source response
        mock_supabase_source.get_competitive_data.return_value = sample_data_response
        
        params = QueryParams()
        result = await router.route_competitive_data("test-org", "manchester", params)
        
        assert result == sample_data_response
        mock_supabase_source.get_competitive_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_with_source_not_initialized(self, router_config, mock_cache_manager):
        """Test routing with uninitialized source"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock uninitialized source
        uninitialized_source = AsyncMock()
        uninitialized_source.is_initialized = False
        
        router.register_source(DataSourceType.SUPABASE, uninitialized_source)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        params = QueryParams()
        
        with pytest.raises(RuntimeError, match="No data sources available"):
            await router.route_competitive_data("test-org", "manchester", params)
    
    @pytest.mark.asyncio
    async def test_route_with_multiple_failures(self, router_config, mock_cache_manager):
        """Test routing when all sources fail"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock sources that all fail
        failing_source1 = AsyncMock()
        failing_source1.get_competitive_data.side_effect = Exception("Source 1 error")
        failing_source1.is_initialized = True
        
        failing_source2 = AsyncMock()
        failing_source2.get_competitive_data.side_effect = Exception("Source 2 error")
        failing_source2.is_initialized = True
        
        router.register_source(DataSourceType.SUPABASE, failing_source1)
        router.register_source(DataSourceType.POSTGRESQL, failing_source2)
        
        params = QueryParams()
        
        with pytest.raises(Exception, match="Source 2 error"):
            await router.route_competitive_data("test-org", "manchester", params)
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, router_config, mock_cache_manager):
        """Test cache key generation for different query types"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Test competitive data cache key
        competitive_key = router._get_cache_key("competitive_data", "test-org", "manchester", QueryParams())
        assert "competitive_data" in competitive_key
        assert "test-org" in competitive_key
        assert "manchester" in competitive_key
        
        # Test reference data cache key
        reference_key = router._get_cache_key("reference_data", "uk_markets", None, QueryParams(filters={"active": True}))
        assert "reference_data" in reference_key
        assert "uk_markets" in reference_key
        
        # Test analytics data cache key
        analytics_key = router._get_cache_key("analytics_data", "test-org", None, QueryParams(filters={"market": "manchester"}))
        assert "analytics_data" in analytics_key
        assert "test-org" in analytics_key
    
    @pytest.mark.asyncio
    async def test_source_priority_routing(self, router_config, mock_cache_manager):
        """Test routing with source priority"""
        router = DataSourceRouter(mock_cache_manager)
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Create sources with different priorities
        primary_source = AsyncMock()
        primary_source.source_type = DataSourceType.SUPABASE
        primary_source.is_initialized = True
        primary_source.get_competitive_data.return_value = DataResponse(
            data=[{"id": 1, "source": "primary"}],
            source=DataSourceType.SUPABASE,
            cached=False
        )
        
        secondary_source = AsyncMock()
        secondary_source.source_type = DataSourceType.POSTGRESQL
        secondary_source.is_initialized = True
        secondary_source.get_competitive_data.return_value = DataResponse(
            data=[{"id": 2, "source": "secondary"}],
            source=DataSourceType.POSTGRESQL,
            cached=False
        )
        
        router.register_source(DataSourceType.SUPABASE, primary_source)
        router.register_source(DataSourceType.POSTGRESQL, secondary_source)
        
        params = QueryParams()
        result = await router.route_competitive_data("test-org", "manchester", params)
        
        # Should use primary source
        assert result.source == DataSourceType.SUPABASE
        assert result.data[0]["source"] == "primary"
        primary_source.get_competitive_data.assert_called_once()
        secondary_source.get_competitive_data.assert_not_called() 