import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
from typing import Dict, Any

from app.data.sources.supabase_client import SupabaseDataSource
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse


class TestSupabaseDataSource:
    """Test suite for SupabaseDataSource"""
    
    @pytest.fixture
    def supabase_config(self) -> Dict[str, Any]:
        """Supabase configuration for testing"""
        return {
            "url": "http://localhost:54321",
            "key": "test-anon-key",
            "schema": "public"
        }
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        with patch('app.data.sources.supabase_client.create_client') as mock_create:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_client.table.return_value = mock_table
            mock_create.return_value = mock_client
            yield mock_client, mock_table
    
    @pytest.mark.asyncio
    async def test_initialization(self, supabase_config):
        """Test Supabase data source initialization"""
        source = SupabaseDataSource(supabase_config)
        
        assert source.source_type == DataSourceType.SUPABASE
        assert source.config == supabase_config
        assert source.url == "http://localhost:54321"
        assert source.key == "test-anon-key"
        assert source.schema == "public"
        assert not source._initialized
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, supabase_config, mock_supabase_client):
        """Test successful initialization"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock health check response with proper .data attribute
        mock_health_response = Mock()
        mock_health_response.data = [{"table_name": "test"}]
        mock_health_response.count = 1
        mock_health_response.error = None
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_health_response
        
        source = SupabaseDataSource(supabase_config)
        await source.initialize()
        
        assert source._initialized
        assert source.is_initialized
        assert source.client is not None
    
    @pytest.mark.asyncio
    async def test_initialize_missing_config(self):
        """Test initialization with missing configuration"""
        source = SupabaseDataSource({})
        
        with pytest.raises(ValueError, match="Supabase URL and key are required"):
            await source.initialize()
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, supabase_config, mock_supabase_client):
        """Test successful health check"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock successful health check with proper .data attribute
        mock_health_response = Mock()
        mock_health_response.data = [{"table_name": "test"}]
        mock_health_response.count = 1
        mock_health_response.error = None
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_health_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        
        result = await source.health_check()
        
        assert result is True
        mock_table.select.assert_called_once_with("table_name")
        mock_table.select.return_value.limit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, supabase_config, mock_supabase_client):
        """Test health check failure"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock failed health check
        mock_table.select.return_value.limit.return_value.execute.side_effect = Exception("Connection error")
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        
        result = await source.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_no_client(self, supabase_config):
        """Test health check without client"""
        source = SupabaseDataSource(supabase_config)
        
        result = await source.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_competitive_data(self, supabase_config, mock_supabase_client):
        """Test getting competitive intelligence data"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        
        # Create a proper mock response object with .data attribute
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "org_id": "test-org",
                "market": "manchester",
                "competitor_name": "vue",
                "date": "2024-01-15",
                "price": 12.50,
                "availability": True
            }
        ]
        mock_response.count = 1
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        params = QueryParams(
            filters={
                "competitors": ["vue", "cineworld"],
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            },
            limit=10,
            offset=5,  # Use non-zero offset to test the functionality
            order_by=["-date", "competitor_name"]
        )
        
        result = await source.get_competitive_data("test-org", "manchester", params)
        
        assert isinstance(result, DataResponse)
        assert result.source == DataSourceType.SUPABASE
        assert result.cached is False
        assert len(result.data) == 1
        assert result.data[0]["competitor_name"] == "vue"
        assert result.total_count == 1
        
        # Verify query construction
        mock_table.select.assert_called_once_with("*")
        mock_query.eq.assert_any_call("market", "manchester")
        mock_query.eq.assert_any_call("org_id", "test-org")
        mock_query.in_.assert_called_once_with("competitor_name", ["vue", "cineworld"])
        mock_query.gte.assert_called_once_with("date", "2024-01-01")
        mock_query.lte.assert_called_once_with("date", "2024-01-31")
        mock_query.order.assert_any_call("date", desc=True)
        mock_query.order.assert_any_call("competitor_name")
        mock_query.limit.assert_called_once_with(10)
        mock_query.offset.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_get_competitive_data_with_error(self, supabase_config, mock_supabase_client):
        """Test getting competitive data with error"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.execute.side_effect = Exception("Database error")
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        params = QueryParams()
        
        with pytest.raises(Exception, match="Database error"):
            await source.get_competitive_data("test-org", "manchester", params)
    
    @pytest.mark.asyncio
    async def test_get_reference_data(self, supabase_config, mock_supabase_client):
        """Test getting reference data"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Create mock response with .data attribute
        mock_response = Mock()
        mock_response.data = [
            {"id": 1, "name": "manchester", "region": "north-west"},
            {"id": 2, "name": "london", "region": "south-east"}
        ]
        mock_response.count = 2
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        params = QueryParams(
            filters={"active": True},
            limit=5,
            order_by=["name"]
        )
        
        result = await source.get_reference_data("uk_markets", params)
        
        assert isinstance(result, DataResponse)
        assert result.source == DataSourceType.SUPABASE
        assert result.cached is False
        assert len(result.data) == 2
        assert result.total_count == 2
        
        # Verify query construction
        mock_table.select.assert_called_once_with("*")
        mock_query.eq.assert_called_once_with("active", True)
        mock_query.order.assert_called_once_with("name")
        mock_query.limit.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_get_reference_data_no_params(self, supabase_config, mock_supabase_client):
        """Test getting reference data without parameters"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.order.return_value = mock_query
        
        # Create mock response with .data attribute
        mock_response = Mock()
        mock_response.data = [{"id": 1, "name": "test"}]
        mock_response.count = 1
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        result = await source.get_reference_data("uk_markets")
        
        assert isinstance(result, DataResponse)
        assert len(result.data) == 1
        
        # Verify default ordering
        mock_query.order.assert_called_once_with("name")
    
    @pytest.mark.asyncio
    async def test_get_analytics_data(self, supabase_config, mock_supabase_client):
        """Test getting analytics data"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        
        # Create mock response with .data attribute
        mock_response = Mock()
        mock_response.data = [
            {
                "market": "manchester",
                "date": "2024-01-15",
                "revenue": 1000.50,
                "transactions": 150
            }
        ]
        mock_response.count = 1
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        params = QueryParams(
            filters={
                "market": "manchester",
                "metrics": ["revenue", "transactions"],
                "aggregation": "daily"
            },
            order_by=["-date"]
        )
        
        result = await source.get_analytics_data("test-org", params)
        
        assert isinstance(result, DataResponse)
        assert result.source == DataSourceType.SUPABASE
        assert result.cached is False
        assert len(result.data) == 1
        assert result.data[0]["revenue"] == 1000.50
        
        # Verify query construction
        mock_table.select.assert_called_once_with("*")
        mock_query.eq.assert_called_once_with("market", "manchester")
        mock_query.order.assert_called_once_with("date", desc=True)
    
    @pytest.mark.asyncio
    async def test_execute_custom_query(self, supabase_config, mock_supabase_client):
        """Test executing custom query"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        
        # Create mock response with .data attribute
        mock_response = Mock()
        mock_response.data = [{"custom_result": "test_data"}]
        mock_response.count = 1
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        result = await source.execute_custom_query(
            "SELECT * FROM custom_table WHERE id = $1",
            {"id": 123}
        )
        
        assert isinstance(result, DataResponse)
        assert result.source == DataSourceType.SUPABASE
        assert result.cached is False
        assert len(result.data) == 1
        assert result.data[0]["custom_result"] == "test_data"
    
    @pytest.mark.asyncio
    async def test_execute_custom_query_with_error(self, supabase_config, mock_supabase_client):
        """Test executing custom query with error"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.execute.side_effect = Exception("Query error")
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        with pytest.raises(Exception, match="Query error"):
            await source.execute_custom_query("SELECT * FROM invalid_table")
    
    @pytest.mark.asyncio
    async def test_subscribe_to_changes(self, supabase_config, mock_supabase_client):
        """Test subscribing to real-time changes"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock subscription
        mock_subscription = MagicMock()
        mock_table.on.return_value = mock_subscription
        mock_subscription.eq.return_value = mock_subscription
        mock_subscription.subscribe.return_value = mock_subscription
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        callback_called = False
        
        def test_callback(payload):
            nonlocal callback_called
            callback_called = True
        
        await source.subscribe_to_changes(
            table="competitive_intelligence",
            callback=test_callback,
            filters={"market": "manchester"}
        )
        
        # Verify subscription setup
        mock_table.on.assert_called_once_with("INSERT")
        mock_subscription.eq.assert_called_once_with("market", "manchester")
        mock_subscription.subscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close(self, supabase_config):
        """Test closing the data source"""
        source = SupabaseDataSource(supabase_config)
        source.client = MagicMock()
        source._initialized = True
        
        await source.close()
        
        # Verify client is set to None
        assert source.client is None
        assert not source._initialized
    
    @pytest.mark.asyncio
    async def test_query_parameter_handling(self, supabase_config, mock_supabase_client):
        """Test various query parameter combinations"""
        mock_client, mock_table = mock_supabase_client
        
        # Mock query chain
        mock_query = mock_table.select.return_value
        mock_query.eq.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        
        # Create mock response with .data attribute
        mock_response = Mock()
        mock_response.data = []
        mock_response.count = 0
        mock_response.error = None
        mock_query.execute.return_value = mock_response
        
        source = SupabaseDataSource(supabase_config)
        source.client = mock_client
        source._initialized = True
        
        # Test with complex filters
        params = QueryParams(
            filters={
                "competitors": ["vue", "cineworld"],
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                "availability": True,
                "price_min": 10.0
            },
            limit=50,
            offset=10,
            order_by=["-date", "competitor_name", "price"]
        )
        
        await source.get_competitive_data("test-org", "manchester", params)
        
        # Verify all filters were applied
        mock_query.eq.assert_any_call("market", "manchester")
        mock_query.eq.assert_any_call("org_id", "test-org")
        mock_query.eq.assert_any_call("availability", True)
        mock_query.eq.assert_any_call("price_min", 10.0)
        mock_query.in_.assert_called_once_with("competitor_name", ["vue", "cineworld"])
        mock_query.gte.assert_called_once_with("date", "2024-01-01")
        mock_query.lte.assert_called_once_with("date", "2024-01-31")
        mock_query.limit.assert_called_once_with(50)
        mock_query.offset.assert_called_once_with(10)
        
        # Verify ordering
        assert mock_query.order.call_count == 3  # Three order fields 