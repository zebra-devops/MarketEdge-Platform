import time
from typing import Dict, List, Optional, Any
from datetime import timedelta

from ..interfaces.base import AbstractDataSource, DataSourceType, QueryParams, DataResponse
from ..interfaces.router import IDataSourceRouter
from ..interfaces.cache import ICacheManager
from ...core.logging import logger


class DataSourceRouter(IDataSourceRouter):
    """Routes queries to appropriate data sources with caching and failover"""
    
    def __init__(self, cache_manager: Optional[ICacheManager] = None, config: Optional[Dict[str, Any]] = None):
        self.sources: Dict[DataSourceType, AbstractDataSource] = {}
        self.cache_manager = cache_manager
        self.fallback_order: Dict[str, List[DataSourceType]] = {}
        self.query_routing_rules: Dict[str, DataSourceType] = {}
        
        # Configuration attributes
        if config:
            self.default_source = config.get('default_source', 'supabase')
            self.enable_fallback = config.get('enable_fallback', True)
            self.health_check_interval = config.get('health_check_interval', 60)
        else:
            self.default_source = 'supabase'
            self.enable_fallback = True
            self.health_check_interval = 60
        
        # Default routing rules
        self._setup_default_routing()
    
    def _setup_default_routing(self) -> None:
        """Setup default routing rules for different query types"""
        # Competitive data routing
        self.query_routing_rules.update({
            "competitive_data": DataSourceType.SUPABASE,
            "reference_data": DataSourceType.SUPABASE,
            "analytics_data": DataSourceType.SUPABASE,
            "custom_query": DataSourceType.SUPABASE
        })
        
        # Fallback order if primary source fails
        self.fallback_order = {
            "competitive_data": [DataSourceType.SUPABASE, DataSourceType.POSTGRESQL],
            "reference_data": [DataSourceType.SUPABASE, DataSourceType.POSTGRESQL],
            "analytics_data": [DataSourceType.SUPABASE, DataSourceType.DATABRICKS, DataSourceType.POSTGRESQL],
            "custom_query": [DataSourceType.SUPABASE, DataSourceType.POSTGRESQL]
        }
    
    def register_source(
        self, 
        source_type: DataSourceType, 
        source: AbstractDataSource
    ) -> None:
        """Register a new data source"""
        self.sources[source_type] = source
        logger.info(f"Registered data source: {source_type}")
    
    def get_source(self, source_type: DataSourceType) -> Optional[AbstractDataSource]:
        """Get a specific data source"""
        return self.sources.get(source_type)
    
    async def route_competitive_data(
        self,
        org_id: str,
        market: str,
        params: QueryParams
    ) -> DataResponse:
        """Route competitive data query to appropriate source"""
        query_type = "competitive_data"
        
        # Generate cache key
        cache_key = None
        if self.cache_manager:
            cache_key = self.cache_manager.generate_cache_key(
                source=query_type,
                method="get_competitive_data",
                org_id=org_id,
                market=market,
                **(params.model_dump(exclude_none=True) if hasattr(params, 'model_dump') else params.dict(exclude_none=True))
            )
            
            # Try to get from cache first
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for competitive data query: {cache_key}")
                cached_result["cached"] = True
                return DataResponse(**cached_result)
        
        # Get data from source with fallback
        result = await self._execute_with_fallback(
            query_type=query_type,
            method_name="get_competitive_data",
            org_id=org_id,
            market=market,
            params=params
        )
        
        # Cache the result
        if self.cache_manager and cache_key and result:
            cache_ttl = timedelta(minutes=30)  # Cache competitive data for 30 minutes
            await self.cache_manager.set(
                cache_key, 
                (result.model_dump() if hasattr(result, 'model_dump') else result.dict()), 
                ttl=cache_ttl
            )
            result.cache_ttl = int(cache_ttl.total_seconds())
        
        return result
    
    async def route_reference_data(
        self,
        dataset: str,
        params: Optional[QueryParams] = None
    ) -> DataResponse:
        """Route reference data query to appropriate source"""
        query_type = "reference_data"
        
        # Generate cache key
        cache_key = None
        if self.cache_manager:
            cache_params = (params.model_dump(exclude_none=True) if hasattr(params, 'model_dump') else params.dict(exclude_none=True)) if params else {}
            cache_key = self.cache_manager.generate_cache_key(
                source=query_type,
                method="get_reference_data",
                dataset=dataset,
                **cache_params
            )
            
            # Try to get from cache first
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for reference data query: {cache_key}")
                cached_result["cached"] = True
                return DataResponse(**cached_result)
        
        # Get data from source with fallback
        result = await self._execute_with_fallback(
            query_type=query_type,
            method_name="get_reference_data",
            dataset=dataset,
            params=params
        )
        
        # Cache the result (reference data can be cached longer)
        if self.cache_manager and cache_key and result:
            cache_ttl = timedelta(hours=4)  # Cache reference data for 4 hours
            await self.cache_manager.set(
                cache_key, 
                (result.model_dump() if hasattr(result, 'model_dump') else result.dict()), 
                ttl=cache_ttl
            )
            result.cache_ttl = int(cache_ttl.total_seconds())
        
        return result
    
    async def route_analytics_data(
        self,
        org_id: str,
        params: QueryParams
    ) -> DataResponse:
        """Route analytics query to appropriate source"""
        query_type = "analytics_data"
        
        # Generate cache key
        cache_key = None
        if self.cache_manager:
            cache_key = self.cache_manager.generate_cache_key(
                source=query_type,
                method="get_analytics_data",
                org_id=org_id,
                **(params.model_dump(exclude_none=True) if hasattr(params, 'model_dump') else params.dict(exclude_none=True))
            )
            
            # Try to get from cache first
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for analytics data query: {cache_key}")
                cached_result["cached"] = True
                return DataResponse(**cached_result)
        
        # Get data from source with fallback
        result = await self._execute_with_fallback(
            query_type=query_type,
            method_name="get_analytics_data",
            org_id=org_id,
            params=params
        )
        
        # Cache the result
        if self.cache_manager and cache_key and result:
            cache_ttl = timedelta(minutes=15)  # Cache analytics data for 15 minutes
            await self.cache_manager.set(
                cache_key, 
                (result.model_dump() if hasattr(result, 'model_dump') else result.dict()), 
                ttl=cache_ttl
            )
            result.cache_ttl = int(cache_ttl.total_seconds())
        
        return result
    
    async def route_custom_query(
        self,
        query_type: str,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> DataResponse:
        """Route custom query to appropriate source"""
        # Custom queries are typically not cached due to their dynamic nature
        return await self._execute_with_fallback(
            query_type="custom_query",
            method_name="execute_custom_query",
            query=query,
            params=params
        )
    
    async def _execute_with_fallback(
        self,
        query_type: str,
        method_name: str,
        **kwargs
    ) -> DataResponse:
        """Execute query with fallback to alternative sources"""
        # Get primary source for this query type
        primary_source_type = self.query_routing_rules.get(query_type)
        if not primary_source_type:
            raise ValueError(f"No routing rule found for query type: {query_type}")
        
        # Get fallback order
        fallback_sources = self.fallback_order.get(query_type, [primary_source_type])
        
        last_error = None
        
        for source_type in fallback_sources:
            source = self.sources.get(source_type)
            if not source:
                logger.warning(f"Data source {source_type} not registered")
                continue
            
            if not source.is_initialized:
                logger.warning(f"Data source {source_type} not initialized")
                continue
            
            try:
                # Check source health before using
                if not await source.health_check():
                    logger.warning(f"Data source {source_type} failed health check")
                    continue
                
                # Execute the method
                method = getattr(source, method_name)
                result = await method(**kwargs)
                
                if source_type != primary_source_type:
                    logger.info(f"Used fallback source {source_type} for {query_type}")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.error(f"Error with source {source_type} for {query_type}: {e}")
                continue
        
        # All sources failed
        error_msg = f"All data sources failed for {query_type}"
        if last_error:
            error_msg += f". Last error: {last_error}"
        
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def health_check_all(self) -> Dict[DataSourceType, bool]:
        """Check health of all registered sources"""
        health_status = {}
        
        for source_type, source in self.sources.items():
            try:
                if source.is_initialized:
                    health_status[source_type] = await source.health_check()
                else:
                    health_status[source_type] = False
            except Exception as e:
                logger.error(f"Health check failed for {source_type}: {e}")
                health_status[source_type] = False
        
        return health_status
    
    def update_routing_rule(
        self, 
        query_type: str, 
        primary_source: DataSourceType
    ) -> None:
        """Update routing rule for a specific query type"""
        self.query_routing_rules[query_type] = primary_source
        logger.info(f"Updated routing rule: {query_type} -> {primary_source}")
    
    def update_fallback_order(
        self, 
        query_type: str, 
        sources: List[DataSourceType]
    ) -> None:
        """Update fallback order for a specific query type"""
        self.fallback_order[query_type] = sources
        logger.info(f"Updated fallback order for {query_type}: {sources}")
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = {
            "registered_sources": list(self.sources.keys()),
            "routing_rules": self.query_routing_rules.copy(),
            "fallback_orders": self.fallback_order.copy(),
            "health_status": await self.health_check_all()
        }
        
        if self.cache_manager:
            stats["cache_stats"] = await self.cache_manager.get_cache_stats()
        
        return stats
    
    async def invalidate_cache_for_org(self, org_id: str) -> int:
        """Invalidate all cached data for an organization"""
        if not self.cache_manager:
            return 0
        
        return await self.cache_manager.invalidate_org_cache(org_id)
    
    async def invalidate_cache_for_market(self, market: str) -> int:
        """Invalidate all cached data for a specific market"""
        if not self.cache_manager:
            return 0
        
        pattern = f"*:*:*{market}*"
        return await self.cache_manager.clear_pattern(pattern)
    
    def _get_cache_key(self, query_type: str, org_id: str, market: str, params: QueryParams) -> str:
        """Generate cache key for data queries"""
        if not self.cache_manager:
            return ""
        
        # Generate cache key manually since the cache manager method might be async
        params_dict = params.model_dump(exclude_none=True) if hasattr(params, 'model_dump') else params.dict(exclude_none=True)
        key_parts = [query_type, "query", org_id or "none", market or "none"]
        for key, value in params_dict.items():
            key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)