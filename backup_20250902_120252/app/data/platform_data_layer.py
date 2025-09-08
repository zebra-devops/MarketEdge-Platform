from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from .interfaces.base import DataSourceType, QueryParams, DataResponse
from .interfaces.router import IDataSourceRouter
from .interfaces.cache import ICacheManager
from .router import DataSourceRouter
from .cache import RedisCacheManager
from .sources import SupabaseDataSource
from ..core.logging import logger


class PlatformDataLayer:
    """Main unified interface for all data access in the platform"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.router: Optional[IDataSourceRouter] = None
        self.cache_manager: Optional[ICacheManager] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the platform data layer"""
        try:
            # Initialize cache manager if configured
            if self.config.get("cache", {}).get("enabled", True):
                cache_config = self.config.get("cache", {})
                self.cache_manager = RedisCacheManager(cache_config)
                await self.cache_manager.initialize()
            
            # Initialize router
            self.router = DataSourceRouter(self.cache_manager)
            
            # Initialize and register data sources
            await self._initialize_data_sources()
            
            self._initialized = True
            logger.info("Platform data layer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize platform data layer: {e}")
            raise
    
    async def _initialize_data_sources(self) -> None:
        """Initialize and register all configured data sources"""
        sources_config = self.config.get("sources", {})
        
        # Initialize Supabase source
        if "supabase" in sources_config:
            supabase_config = sources_config["supabase"]
            supabase_source = SupabaseDataSource(supabase_config)
            await supabase_source.initialize()
            self.router.register_source(DataSourceType.SUPABASE, supabase_source)
        
        # Add other data sources here as they're implemented
        # PostgreSQL, Databricks, etc.
    
    async def get_competitive_intelligence(
        self,
        org_id: str,
        market: str,
        competitors: Optional[List[str]] = None,
        date_range: Optional[Dict[str, Union[str, datetime]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> DataResponse:
        """Get competitive intelligence data for a market"""
        self._ensure_initialized()
        
        # Build query parameters
        filters = {}
        if competitors:
            filters["competitors"] = competitors
        if date_range:
            filters["date_range"] = date_range
        
        params = QueryParams(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=["-date", "competitor_name"]
        )
        
        return await self.router.route_competitive_data(org_id, market, params)
    
    async def get_market_data(
        self,
        org_id: str,
        market: str,
        metrics: Optional[List[str]] = None,
        date_range: Optional[Dict[str, Union[str, datetime]]] = None,
        aggregation: str = "daily"
    ) -> DataResponse:
        """Get market analytics data"""
        self._ensure_initialized()
        
        filters = {
            "market": market,
            "metrics": metrics,
            "aggregation": aggregation
        }
        if date_range:
            filters["date_range"] = date_range
        
        params = QueryParams(
            filters=filters,
            order_by=["-date"]
        )
        
        return await self.router.route_analytics_data(org_id, params)
    
    async def get_reference_data(
        self,
        dataset: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> DataResponse:
        """Get reference/lookup data"""
        self._ensure_initialized()
        
        params = None
        if filters or limit:
            params = QueryParams(
                filters=filters,
                limit=limit,
                order_by=["name"] if dataset in ["competitors", "markets"] else None
            )
        
        return await self.router.route_reference_data(dataset, params)
    
    async def get_uk_markets(self) -> DataResponse:
        """Get list of UK markets"""
        return await self.get_reference_data("uk_markets")
    
    async def get_competitors(
        self, 
        market: Optional[str] = None
    ) -> DataResponse:
        """Get list of competitors, optionally filtered by market"""
        filters = {"market": market} if market else None
        return await self.get_reference_data("competitors", filters)
    
    async def get_market_segments(self, market: str) -> DataResponse:
        """Get market segments for a specific market"""
        filters = {"market": market}
        return await self.get_reference_data("market_segments", filters)
    
    async def search_competitive_data(
        self,
        org_id: str,
        search_query: str,
        market: Optional[str] = None,
        limit: int = 50
    ) -> DataResponse:
        """Search competitive intelligence data"""
        self._ensure_initialized()
        
        filters = {
            "search": search_query
        }
        if market:
            filters["market"] = market
        
        params = QueryParams(
            filters=filters,
            limit=limit,
            order_by=["-relevance", "-date"]
        )
        
        return await self.router.route_competitive_data(org_id, "all", params)
    
    async def get_trending_data(
        self,
        org_id: str,
        market: str,
        period: str = "7d",
        limit: int = 20
    ) -> DataResponse:
        """Get trending competitive data for a market"""
        self._ensure_initialized()
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=7)
        
        filters = {
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "trending": True
        }
        
        params = QueryParams(
            filters=filters,
            limit=limit,
            order_by=["-trend_score", "-date"]
        )
        
        return await self.router.route_competitive_data(org_id, market, params)
    
    async def get_analytics_summary(
        self,
        org_id: str,
        date_range: Optional[Dict[str, Union[str, datetime]]] = None
    ) -> DataResponse:
        """Get analytics summary across all markets"""
        self._ensure_initialized()
        
        filters = {
            "summary": True
        }
        if date_range:
            filters["date_range"] = date_range
        
        params = QueryParams(
            filters=filters,
            aggregations={
                "total_records": "count",
                "markets_covered": "count_distinct",
                "competitors_tracked": "count_distinct"
            }
        )
        
        return await self.router.route_analytics_data(org_id, params)
    
    async def execute_custom_query(
        self,
        query_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> DataResponse:
        """Execute a custom predefined query"""
        self._ensure_initialized()
        
        return await self.router.route_custom_query(
            "custom", 
            query_name, 
            parameters
        )
    
    async def invalidate_cache(
        self,
        org_id: Optional[str] = None,
        market: Optional[str] = None,
        pattern: Optional[str] = None
    ) -> int:
        """Invalidate cached data"""
        self._ensure_initialized()
        
        if not self.cache_manager:
            return 0
        
        if org_id:
            return await self.router.invalidate_cache_for_org(org_id)
        elif market:
            return await self.router.invalidate_cache_for_market(market)
        elif pattern:
            return await self.cache_manager.clear_pattern(pattern)
        else:
            # Clear all cache
            return await self.cache_manager.clear_pattern("*")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all components"""
        self._ensure_initialized()
        
        # Get data source health
        source_health = await self.router.health_check_all()
        
        # Get cache health
        cache_health = False
        cache_stats = {}
        if self.cache_manager:
            try:
                cache_stats = await self.cache_manager.get_cache_stats()
                cache_health = True
            except Exception as e:
                logger.error(f"Cache health check failed: {e}")
        
        # Get router stats
        router_stats = await self.router.get_routing_stats()
        
        return {
            "platform_data_layer": {
                "initialized": self._initialized,
                "healthy": all(source_health.values()) and cache_health
            },
            "data_sources": source_health,
            "cache": {
                "healthy": cache_health,
                "stats": cache_stats
            },
            "router": router_stats
        }
    
    async def get_usage_metrics(
        self,
        org_id: str,
        date_range: Optional[Dict[str, Union[str, datetime]]] = None
    ) -> Dict[str, Any]:
        """Get usage metrics for an organization"""
        self._ensure_initialized()
        
        # This would typically be implemented by querying usage logs
        # For now, return basic metrics from cache stats
        metrics = {
            "queries_executed": 0,
            "data_retrieved_mb": 0.0,
            "cache_hit_rate": 0.0,
            "average_response_time_ms": 0.0
        }
        
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_cache_stats()
            metrics["cache_hit_rate"] = cache_stats.get("hit_rate", 0.0)
        
        return metrics
    
    def _ensure_initialized(self) -> None:
        """Ensure the data layer is initialized"""
        if not self._initialized:
            raise RuntimeError("Platform data layer not initialized. Call initialize() first.")
    
    async def close(self) -> None:
        """Close all connections and cleanup resources"""
        try:
            if self.router:
                # Close all registered data sources
                for source in self.router.sources.values():
                    await source.close()
            
            if self.cache_manager:
                await self.cache_manager.close()
            
            self._initialized = False
            logger.info("Platform data layer closed")
            
        except Exception as e:
            logger.error(f"Error closing platform data layer: {e}")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized