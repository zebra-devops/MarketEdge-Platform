from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel


class DataSourceType(str, Enum):
    """Types of data sources supported by the platform"""
    SUPABASE = "supabase"
    DATABRICKS = "databricks"
    REST_API = "rest_api"
    POSTGRESQL = "postgresql"
    REDIS = "redis"


class QueryParams(BaseModel):
    """Standardized query parameters for data requests"""
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, Union[str, datetime]]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[List[str]] = None
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    group_by: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None


class DataResponse(BaseModel):
    """Standardized response format for all data sources"""
    data: Any
    source: DataSourceType
    cached: bool = False
    cache_ttl: Optional[int] = None
    total_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AbstractDataSource(ABC):
    """Base class for all data source implementations"""
    
    def __init__(self, source_type: DataSourceType, config: Dict[str, Any]):
        self.source_type = source_type
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the data source connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is healthy and accessible"""
        pass
    
    @abstractmethod
    async def get_competitive_data(
        self,
        org_id: str,
        market: str,
        params: QueryParams
    ) -> DataResponse:
        """Get competitive intelligence data"""
        pass
    
    @abstractmethod
    async def get_reference_data(
        self,
        dataset: str,
        params: Optional[QueryParams] = None
    ) -> DataResponse:
        """Get reference/lookup data"""
        pass
    
    @abstractmethod
    async def get_analytics_data(
        self,
        org_id: str,
        params: QueryParams
    ) -> DataResponse:
        """Get analytics data"""
        pass
    
    @abstractmethod
    async def execute_custom_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> DataResponse:
        """Execute a custom query (SQL, REST endpoint, etc.)"""
        pass
    
    async def close(self) -> None:
        """Close connections and cleanup resources"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized