from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .base import AbstractDataSource, DataSourceType, QueryParams, DataResponse


class IDataSourceRouter(ABC):
    """Interface for routing queries to appropriate data sources"""
    
    @abstractmethod
    async def route_competitive_data(
        self,
        org_id: str,
        market: str,
        params: QueryParams
    ) -> DataResponse:
        """Route competitive data query to appropriate source"""
        pass
    
    @abstractmethod
    async def route_reference_data(
        self,
        dataset: str,
        params: Optional[QueryParams] = None
    ) -> DataResponse:
        """Route reference data query to appropriate source"""
        pass
    
    @abstractmethod
    async def route_analytics_data(
        self,
        org_id: str,
        params: QueryParams
    ) -> DataResponse:
        """Route analytics query to appropriate source"""
        pass
    
    @abstractmethod
    async def route_custom_query(
        self,
        query_type: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> DataResponse:
        """Route custom query to appropriate source"""
        pass
    
    @abstractmethod
    def register_source(
        self,
        source_type: DataSourceType,
        source: AbstractDataSource
    ) -> None:
        """Register a new data source"""
        pass
    
    @abstractmethod
    def get_source(self, source_type: DataSourceType) -> Optional[AbstractDataSource]:
        """Get a specific data source"""
        pass
    
    @abstractmethod
    async def health_check_all(self) -> Dict[DataSourceType, bool]:
        """Check health of all registered sources"""
        pass