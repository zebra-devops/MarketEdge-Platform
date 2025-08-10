import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from postgrest.exceptions import APIError

from ..interfaces.base import AbstractDataSource, DataSourceType, QueryParams, DataResponse
from ...core.logging import logger


class SupabaseDataSource(AbstractDataSource):
    """Supabase data source implementation with competitive intelligence focus"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(DataSourceType.SUPABASE, config)
        self.client: Optional[Client] = None
        self.url = config.get("url")
        self.key = config.get("key")
        self.schema = config.get("schema", "public")
        
    async def initialize(self) -> None:
        """Initialize Supabase client connection"""
        try:
            if not self.url or not self.key:
                raise ValueError("Supabase URL and key are required")
            
            self.client = create_client(self.url, self.key)
            
            # Test connection with a simple query
            await self.health_check()
            self._initialized = True
            
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check Supabase connection health"""
        try:
            if not self.client:
                return False
            
            # Simple health check query
            result = self.client.table("information_schema.tables").select("table_name").limit(1).execute()
            return len(result.data) >= 0
            
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    async def get_competitive_data(
        self,
        org_id: str,
        market: str,
        params: QueryParams
    ) -> DataResponse:
        """Get competitive intelligence data from Supabase"""
        start_time = time.time()
        
        try:
            # Build base query for competitive data
            query = self.client.table("competitive_intelligence").select("*")
            
            # Apply market filter
            query = query.eq("market", market)
            
            # Apply organization filter if RLS doesn't handle it
            query = query.eq("org_id", org_id)
            
            # Apply additional filters
            if params.filters:
                for key, value in params.filters.items():
                    if key == "competitors" and isinstance(value, list):
                        query = query.in_("competitor_name", value)
                    elif key == "date_range" and isinstance(value, dict):
                        if "start_date" in value:
                            query = query.gte("date", value["start_date"])
                        if "end_date" in value:
                            query = query.lte("date", value["end_date"])
                    else:
                        query = query.eq(key, value)
            
            # Apply ordering
            if params.order_by:
                for order_field in params.order_by:
                    if order_field.startswith("-"):
                        query = query.order(order_field[1:], desc=True)
                    else:
                        query = query.order(order_field)
            else:
                query = query.order("date", desc=True)
            
            # Apply pagination
            if params.limit:
                query = query.limit(params.limit)
            if params.offset:
                query = query.offset(params.offset)
            
            # Execute query
            result = await asyncio.to_thread(lambda: query.execute())
            
            execution_time = (time.time() - start_time) * 1000
            
            return DataResponse(
                data=result.data,
                source=DataSourceType.SUPABASE,
                total_count=len(result.data) if result.data else 0,
                execution_time_ms=execution_time,
                metadata={
                    "market": market,
                    "org_id": org_id,
                    "query_params": params.dict()
                }
            )
            
        except APIError as e:
            logger.error(f"Supabase API error in get_competitive_data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting competitive data: {e}")
            raise
    
    async def get_reference_data(
        self,
        dataset: str,
        params: Optional[QueryParams] = None
    ) -> DataResponse:
        """Get reference/lookup data from Supabase"""
        start_time = time.time()
        
        try:
            # Map dataset names to table names
            table_mapping = {
                "uk_markets": "uk_markets",
                "competitors": "competitors",
                "market_segments": "market_segments",
                "data_sources": "data_sources"
            }
            
            table_name = table_mapping.get(dataset)
            if not table_name:
                raise ValueError(f"Unknown reference dataset: {dataset}")
            
            query = self.client.table(table_name).select("*")
            
            # Apply filters if provided
            if params and params.filters:
                for key, value in params.filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    else:
                        query = query.eq(key, value)
            
            # Apply ordering
            if params and params.order_by:
                for order_field in params.order_by:
                    if order_field.startswith("-"):
                        query = query.order(order_field[1:], desc=True)
                    else:
                        query = query.order(order_field)
            
            # Apply pagination
            if params and params.limit:
                query = query.limit(params.limit)
            if params and params.offset:
                query = query.offset(params.offset)
            
            result = await asyncio.to_thread(lambda: query.execute())
            
            execution_time = (time.time() - start_time) * 1000
            
            return DataResponse(
                data=result.data,
                source=DataSourceType.SUPABASE,
                total_count=len(result.data) if result.data else 0,
                execution_time_ms=execution_time,
                metadata={
                    "dataset": dataset,
                    "table": table_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting reference data: {e}")
            raise
    
    async def get_analytics_data(
        self,
        org_id: str,
        params: QueryParams
    ) -> DataResponse:
        """Get analytics data from Supabase"""
        start_time = time.time()
        
        try:
            # This could route to different tables based on params
            # For now, using a general analytics table
            query = self.client.table("analytics_data").select("*")
            
            # Apply organization filter
            query = query.eq("org_id", org_id)
            
            # Apply filters
            if params.filters:
                for key, value in params.filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    elif key == "date_range" and isinstance(value, dict):
                        if "start_date" in value:
                            query = query.gte("date", value["start_date"])
                        if "end_date" in value:
                            query = query.lte("date", value["end_date"])
                    else:
                        query = query.eq(key, value)
            
            # Apply aggregations if specified
            if params.aggregations:
                # This would need custom logic based on your analytics requirements
                pass
            
            # Apply grouping
            if params.group_by:
                # Supabase doesn't have direct GROUP BY, might need RPC calls
                pass
            
            result = await asyncio.to_thread(lambda: query.execute())
            
            execution_time = (time.time() - start_time) * 1000
            
            return DataResponse(
                data=result.data,
                source=DataSourceType.SUPABASE,
                total_count=len(result.data) if result.data else 0,
                execution_time_ms=execution_time,
                metadata={
                    "org_id": org_id,
                    "analytics_type": "general"
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            raise
    
    async def execute_custom_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> DataResponse:
        """Execute a custom RPC function or query"""
        start_time = time.time()
        
        try:
            # Execute RPC function
            if params:
                result = await asyncio.to_thread(
                    lambda: self.client.rpc(query, params).execute()
                )
            else:
                result = await asyncio.to_thread(
                    lambda: self.client.rpc(query).execute()
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            return DataResponse(
                data=result.data,
                source=DataSourceType.SUPABASE,
                total_count=len(result.data) if result.data else 0,
                execution_time_ms=execution_time,
                metadata={
                    "query": query,
                    "custom": True
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            raise
    
    async def subscribe_to_changes(
        self,
        table: str,
        callback: callable,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """Subscribe to real-time changes in Supabase"""
        try:
            # Set up real-time subscription
            subscription = self.client.table(table).on("*", callback)
            
            if filters:
                for key, value in filters.items():
                    subscription = subscription.filter(key, "eq", value)
            
            subscription.subscribe()
            
            logger.info(f"Subscribed to changes on table: {table}")
            
        except Exception as e:
            logger.error(f"Error setting up subscription: {e}")
            raise
    
    async def close(self) -> None:
        """Close Supabase connection"""
        try:
            if self.client:
                # Supabase client doesn't need explicit closing
                # but we can clean up subscriptions if needed
                pass
            
            self._initialized = False
            logger.info("Supabase client closed")
            
        except Exception as e:
            logger.error(f"Error closing Supabase client: {e}")