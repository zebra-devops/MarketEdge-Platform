import asyncio
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError

from ..interfaces.cache import ICacheManager
from ...core.logging import logger
from ...core.config import settings
from ...core.redis_manager import redis_manager


class RedisCacheManager(ICacheManager):
    """Redis-based cache manager for the data abstraction layer"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = config.get("default_ttl", 3600)  # 1 hour default
        self.key_prefix = config.get("key_prefix", "data_layer:")
        
    async def initialize(self) -> None:
        """Initialize Redis connection using centralized connection manager"""
        try:
            # Use centralized Redis connection manager
            self.redis_client = await redis_manager.create_cache_client(self.config)
            
            if self.redis_client:
                logger.info("Redis cache manager initialized successfully")
            else:
                if redis_manager.is_fallback_mode():
                    logger.warning("Redis cache manager initialized in fallback mode (no Redis connection)")
                else:
                    logger.error("Failed to get Redis client from connection manager")
                    raise ConnectionError("Could not establish Redis connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback support"""
        try:
            if not self.redis_client:
                if redis_manager.is_fallback_mode():
                    return None  # Cache miss in fallback mode
                logger.warning("Redis client not initialized")
                return None
            
            full_key = f"{self.key_prefix}{key}"
            cached_value = await self.redis_client.get(full_key)
            
            if cached_value is None:
                return None
            
            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(cached_value)
            except (json.JSONDecodeError, TypeError):
                return cached_value
                
        except RedisError as e:
            logger.error(f"Redis error getting key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set value in cache with optional TTL and fallback support"""
        try:
            if not self.redis_client:
                if redis_manager.is_fallback_mode():
                    return True  # Pretend success in fallback mode
                logger.warning("Redis client not initialized")
                return False
            
            full_key = f"{self.key_prefix}{key}"
            
            # Serialize value to JSON if it's not a string
            if isinstance(value, str):
                serialized_value = value
            else:
                try:
                    serialized_value = json.dumps(value, default=str)
                except (TypeError, ValueError) as e:
                    logger.error(f"Failed to serialize value for key {key}: {e}")
                    return False
            
            # Set TTL
            ttl_seconds = None
            if ttl:
                ttl_seconds = int(ttl.total_seconds())
            elif self.default_ttl:
                ttl_seconds = self.default_ttl
            
            if ttl_seconds:
                await self.redis_client.setex(full_key, ttl_seconds, serialized_value)
            else:
                await self.redis_client.set(full_key, serialized_value)
            
            return True
            
        except RedisError as e:
            logger.error(f"Redis error setting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache with fallback support"""
        try:
            if not self.redis_client:
                if redis_manager.is_fallback_mode():
                    return True  # Pretend success in fallback mode
                return False
            
            full_key = f"{self.key_prefix}{key}"
            result = await self.redis_client.delete(full_key)
            return result > 0
            
        except RedisError as e:
            logger.error(f"Redis error deleting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self.redis_client:
                return False
            
            full_key = f"{self.key_prefix}{key}"
            result = await self.redis_client.exists(full_key)
            return result > 0
            
        except RedisError as e:
            logger.error(f"Redis error checking key existence {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking key existence {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            if not self.redis_client:
                return 0
            
            full_pattern = f"{self.key_prefix}{pattern}"
            keys = []
            
            # Use SCAN to find keys matching pattern
            async for key in self.redis_client.scan_iter(match=full_pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except RedisError as e:
            logger.error(f"Redis error clearing pattern {pattern}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error clearing pattern {pattern}: {e}")
            return 0
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for a key in seconds"""
        try:
            if not self.redis_client:
                return None
            
            full_key = f"{self.key_prefix}{key}"
            ttl = await self.redis_client.ttl(full_key)
            
            # Redis returns -1 if key exists but has no TTL, -2 if key doesn't exist
            if ttl == -2:
                return None  # Key doesn't exist
            elif ttl == -1:
                return -1  # Key exists but no TTL
            else:
                return ttl
                
        except RedisError as e:
            logger.error(f"Redis error getting TTL for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting TTL for key {key}: {e}")
            return None
    
    def generate_cache_key(
        self, 
        source: str, 
        method: str, 
        **kwargs
    ) -> str:
        """Generate standardized cache key"""
        # Create a deterministic key based on source, method, and parameters
        key_parts = [source, method]
        
        # Sort kwargs for consistent key generation
        if kwargs:
            sorted_params = sorted(kwargs.items())
            params_str = json.dumps(sorted_params, sort_keys=True, default=str)
            # Hash parameters to keep key length manageable
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
            key_parts.append(params_hash)
        
        return ":".join(key_parts)
    
    async def invalidate_source_cache(self, source: str) -> int:
        """Invalidate all cache entries for a specific data source"""
        pattern = f"{source}:*"
        return await self.clear_pattern(pattern)
    
    async def invalidate_org_cache(self, org_id: str) -> int:
        """Invalidate all cache entries for a specific organization"""
        pattern = f"*:*:*{org_id}*"
        return await self.clear_pattern(pattern)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if not self.redis_client:
                return {}
            
            info = await self.redis_client.info()
            
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except RedisError as e:
            logger.error(f"Redis error getting cache stats: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def close(self) -> None:
        """Close Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis cache manager closed")
        except Exception as e:
            logger.error(f"Error closing Redis cache manager: {e}")