"""
Redis Connection Manager

Provides centralized Redis connection management with environment-aware
configuration, fallback mechanisms, and connection pooling.
"""

import asyncio
import redis.asyncio as redis
from redis.exceptions import RedisError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .config import settings
from .logging import logger


class RedisConnectionManager:
    """
    Centralized Redis connection manager with environment-aware configuration
    and fallback mechanisms for development environments.
    """
    
    def __init__(self):
        self._main_client: Optional[redis.Redis] = None
        self._rate_limit_client: Optional[redis.Redis] = None
        self._initialized = False
        self._fallback_mode = False
        self._connection_cache = {}
        
    async def initialize(self) -> None:
        """Initialize Redis connections with fallback handling"""
        try:
            # Try to initialize main Redis connection
            await self._initialize_main_redis()
            
            # Try to initialize rate limiting Redis connection
            await self._initialize_rate_limit_redis()
            
            self._initialized = True
            logger.info("Redis connection manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connections: {e}")
            if settings.ENVIRONMENT == "development":
                logger.warning("Activating fallback mode for development environment")
                self._fallback_mode = True
                self._initialized = True
            else:
                raise
    
    async def _initialize_main_redis(self) -> None:
        """Initialize main Redis connection with retry logic"""
        redis_url = settings.get_redis_url_for_environment()
        conn_config = settings.get_redis_connection_config()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._main_client = redis.from_url(redis_url, **conn_config)
                await self._main_client.ping()
                logger.info(f"Main Redis connection established on attempt {attempt + 1}")
                return
                
            except (RedisError, ConnectionError) as e:
                if attempt == max_retries - 1:
                    if settings.ENVIRONMENT == "development":
                        logger.warning(f"Main Redis connection failed, will use fallback: {e}")
                        self._main_client = None
                        return
                    raise
                logger.warning(f"Main Redis connection attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
    
    async def _initialize_rate_limit_redis(self) -> None:
        """Initialize rate limiting Redis connection with retry logic"""
        redis_url = settings.get_rate_limit_redis_url_for_environment()
        conn_config = settings.get_redis_connection_config()
        
        # Rate limiter needs decode_responses=False for compatibility
        conn_config = conn_config.copy()
        conn_config["decode_responses"] = False
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._rate_limit_client = redis.from_url(redis_url, **conn_config)
                await self._rate_limit_client.ping()
                logger.info(f"Rate limit Redis connection established on attempt {attempt + 1}")
                return
                
            except (RedisError, ConnectionError) as e:
                if attempt == max_retries - 1:
                    if settings.ENVIRONMENT == "development":
                        logger.warning(f"Rate limit Redis connection failed, will use fallback: {e}")
                        self._rate_limit_client = None
                        return
                    raise
                logger.warning(f"Rate limit Redis connection attempt {attempt + 1} failed, retrying: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
    
    async def get_main_client(self) -> Optional[redis.Redis]:
        """Get main Redis client with connection health check"""
        if not self._initialized:
            await self.initialize()
            
        if self._main_client and not self._fallback_mode:
            try:
                # Health check
                await self._main_client.ping()
                return self._main_client
            except Exception as e:
                logger.warning(f"Main Redis health check failed: {e}")
                if settings.ENVIRONMENT == "development":
                    self._fallback_mode = True
                    return None
                
                # Try to reconnect in production
                await self._initialize_main_redis()
                return self._main_client
        
        return None
    
    async def get_rate_limit_client(self) -> Optional[redis.Redis]:
        """Get rate limiting Redis client with connection health check"""
        if not self._initialized:
            await self.initialize()
            
        if self._rate_limit_client and not self._fallback_mode:
            try:
                # Health check
                await self._rate_limit_client.ping()
                return self._rate_limit_client
            except Exception as e:
                logger.warning(f"Rate limit Redis health check failed: {e}")
                if settings.ENVIRONMENT == "development":
                    self._fallback_mode = True
                    return None
                
                # Try to reconnect in production
                await self._initialize_rate_limit_redis()
                return self._rate_limit_client
        
        return None
    
    async def create_cache_client(self, config: Dict[str, Any]) -> Optional[redis.Redis]:
        """Create a cache-specific Redis client"""
        if not self._initialized:
            await self.initialize()
            
        if self._fallback_mode:
            return None
            
        try:
            # Use provided redis_url or fall back to environment-aware URL
            redis_url = config.get("redis_url", settings.get_redis_url_for_environment())
            conn_config = settings.get_redis_connection_config()
            
            client = redis.from_url(redis_url, **conn_config)
            await client.ping()
            return client
            
        except Exception as e:
            logger.warning(f"Failed to create cache Redis client: {e}")
            if settings.ENVIRONMENT == "development":
                return None
            raise
    
    def is_connected(self) -> bool:
        """Check if any Redis connections are available"""
        return self._initialized and not self._fallback_mode
    
    def is_fallback_mode(self) -> bool:
        """Check if running in fallback mode"""
        return self._fallback_mode
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status for monitoring"""
        status = {
            "initialized": self._initialized,
            "fallback_mode": self._fallback_mode,
            "environment": settings.ENVIRONMENT,
            "connections": {}
        }
        
        # Check main Redis
        if self._main_client:
            try:
                await self._main_client.ping()
                status["connections"]["main"] = "connected"
            except Exception:
                status["connections"]["main"] = "disconnected"
        else:
            status["connections"]["main"] = "not_configured"
        
        # Check rate limit Redis
        if self._rate_limit_client:
            try:
                await self._rate_limit_client.ping()
                status["connections"]["rate_limit"] = "connected"
            except Exception:
                status["connections"]["rate_limit"] = "disconnected"
        else:
            status["connections"]["rate_limit"] = "not_configured"
        
        return status
    
    async def close(self) -> None:
        """Close all Redis connections"""
        if self._main_client:
            try:
                await self._main_client.close()
                logger.info("Main Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing main Redis connection: {e}")
        
        if self._rate_limit_client:
            try:
                await self._rate_limit_client.close()
                logger.info("Rate limit Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing rate limit Redis connection: {e}")
        
        self._main_client = None
        self._rate_limit_client = None
        self._initialized = False
        self._fallback_mode = False


# Global Redis connection manager instance
redis_manager = RedisConnectionManager()