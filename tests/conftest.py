import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from app.data.config.data_layer_config import create_test_config
from app.data.platform_data_layer import PlatformDataLayer
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration for data layer"""
    return create_test_config()


@pytest.fixture
def mock_supabase_response() -> Dict[str, Any]:
    """Mock Supabase response data"""
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


@pytest.fixture
def mock_reference_data() -> Dict[str, Any]:
    """Mock reference data"""
    return {
        "data": [
            {"id": 1, "name": "manchester", "region": "north-west", "active": True},
            {"id": 2, "name": "london", "region": "south-east", "active": True},
            {"id": 3, "name": "birmingham", "region": "west-midlands", "active": True}
        ],
        "count": 3,
        "error": None
    }


@pytest.fixture
def sample_query_params() -> QueryParams:
    """Sample query parameters for testing"""
    return QueryParams(
        filters={"competitors": ["vue", "cineworld"]},
        limit=10,
        offset=0,
        order_by=["-date", "competitor_name"]
    )


@pytest.fixture
def sample_data_response() -> DataResponse:
    """Sample data response for testing"""
    return DataResponse(
        data=[{"id": 1, "name": "test"}],
        source=DataSourceType.SUPABASE,
        cached=False,
        total_count=1,
        execution_time_ms=50.0
    )


@pytest.fixture
async def data_layer(test_config) -> PlatformDataLayer:
    """Platform data layer instance for testing"""
    layer = PlatformDataLayer(test_config)
    # Don't initialize automatically - let tests control initialization
    yield layer
    if layer.is_initialized:
        await layer.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0
    return mock_redis


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    return mock_client, mock_table


# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 