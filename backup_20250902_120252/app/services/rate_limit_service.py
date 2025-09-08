"""
Redis-based Rate Limiting Service

Implements sliding window rate limiting with Redis backend for multi-tenant platform.
Provides high-performance rate limiting with <5ms overhead using efficient Redis operations.
"""
import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError
import json

from ..core.logging import logger
from ..core.rate_limit_config import RateLimitRule, RateLimitType, Industry, rate_limit_config


class RateLimitResult:
    """Result of a rate limit check."""
    
    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_time: datetime,
        retry_after: Optional[int] = None,
        rule_name: str = "unknown"
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after  # Seconds until retry allowed
        self.rule_name = rule_name
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for client information."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_time.timestamp())),
            "X-RateLimit-Rule": self.rule_name
        }
        
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        
        return headers


class SlidingWindowRateLimiter:
    """
    High-performance sliding window rate limiter using Redis.
    
    Uses Redis sorted sets to implement precise sliding window rate limiting
    with sub-5ms performance overhead.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.key_prefix = "rate_limit:"
    
    async def check_limit(
        self, 
        key: str, 
        rule: RateLimitRule,
        current_time: Optional[float] = None,
        request_cost: int = 1
    ) -> RateLimitResult:
        """
        Check if request is within rate limit using sliding window algorithm.
        
        Args:
            key: Unique identifier for the rate limit bucket
            rule: Rate limiting rule to apply
            current_time: Current timestamp (for testing)
            request_cost: Cost of this request (default 1)
        
        Returns:
            RateLimitResult with decision and metadata
        """
        if current_time is None:
            current_time = time.time()
        
        window_seconds = rule.window.total_seconds()
        window_start = current_time - window_seconds
        
        try:
            if rule.limit_type == RateLimitType.REQUESTS_PER_MINUTE or \
               rule.limit_type == RateLimitType.REQUESTS_PER_HOUR:
                return await self._check_requests_limit(
                    key, rule, current_time, window_start, request_cost
                )
            elif rule.limit_type == RateLimitType.CONCURRENT_REQUESTS:
                return await self._check_concurrent_limit(
                    key, rule, current_time, request_cost
                )
            elif rule.limit_type == RateLimitType.BANDWIDTH_LIMIT:
                return await self._check_bandwidth_limit(
                    key, rule, current_time, window_start, request_cost
                )
            else:
                logger.warning(f"Unsupported rate limit type: {rule.limit_type}")
                return RateLimitResult(True, rule.limit, rule.limit, datetime.fromtimestamp(current_time))
        
        except RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request but log the error
            return RateLimitResult(True, rule.limit, rule.limit, datetime.fromtimestamp(current_time))
        except Exception as e:
            logger.error(f"Unexpected error in rate limiting: {e}")
            # Fail open - allow request but log the error
            return RateLimitResult(True, rule.limit, rule.limit, datetime.fromtimestamp(current_time))
    
    async def _check_requests_limit(
        self, 
        key: str, 
        rule: RateLimitRule, 
        current_time: float, 
        window_start: float,
        request_cost: int
    ) -> RateLimitResult:
        """Check request-based rate limits using sliding window."""
        
        redis_key = f"{self.key_prefix}{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(redis_key)
        
        # Execute pipeline
        results = await pipe.execute()
        current_count = results[1]
        
        # Calculate remaining capacity
        effective_limit = rule.burst_limit if rule.burst_limit else rule.limit
        remaining = max(0, effective_limit - current_count)
        
        # Check if request would exceed limit
        if current_count + request_cost > effective_limit:
            # Calculate retry after time
            oldest_entry_score = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest_entry_score:
                oldest_time = oldest_entry_score[0][1]
                retry_after = int(oldest_time + rule.window.total_seconds() - current_time) + 1
            else:
                retry_after = int(rule.window.total_seconds())
            
            return RateLimitResult(
                allowed=False,
                limit=effective_limit,
                remaining=remaining,
                reset_time=datetime.fromtimestamp(current_time + rule.window.total_seconds()),
                retry_after=retry_after,
                rule_name=f"{rule.limit_type.value}_{rule.limit}"
            )
        
        # Add current request(s) to sliding window
        pipe = self.redis.pipeline()
        for i in range(request_cost):
            # Use microsecond precision to handle high-frequency requests
            request_time = current_time + (i * 0.000001)
            pipe.zadd(redis_key, {f"req_{request_time}_{i}": request_time})
        
        # Set expiration on the key
        pipe.expire(redis_key, int(rule.window.total_seconds()) + 60)
        
        await pipe.execute()
        
        return RateLimitResult(
            allowed=True,
            limit=effective_limit,
            remaining=remaining - request_cost,
            reset_time=datetime.fromtimestamp(current_time + rule.window.total_seconds()),
            rule_name=f"{rule.limit_type.value}_{rule.limit}"
        )
    
    async def _check_concurrent_limit(
        self, 
        key: str, 
        rule: RateLimitRule, 
        current_time: float,
        request_cost: int
    ) -> RateLimitResult:
        """Check concurrent request limits."""
        
        redis_key = f"{self.key_prefix}concurrent:{key}"
        
        # Get current concurrent requests
        current_concurrent = await self.redis.get(redis_key) or 0
        current_concurrent = int(current_concurrent)
        
        if current_concurrent + request_cost > rule.limit:
            return RateLimitResult(
                allowed=False,
                limit=rule.limit,
                remaining=max(0, rule.limit - current_concurrent),
                reset_time=datetime.fromtimestamp(current_time + 60),  # Arbitrary reset time
                retry_after=5,  # Try again in 5 seconds
                rule_name=f"concurrent_{rule.limit}"
            )
        
        # Note: Incrementing concurrent requests should be handled by the middleware
        # when the request starts and decremented when it completes
        
        return RateLimitResult(
            allowed=True,
            limit=rule.limit,
            remaining=rule.limit - current_concurrent - request_cost,
            reset_time=datetime.fromtimestamp(current_time + 60),
            rule_name=f"concurrent_{rule.limit}"
        )
    
    async def _check_bandwidth_limit(
        self, 
        key: str, 
        rule: RateLimitRule, 
        current_time: float, 
        window_start: float,
        request_cost: int  # In bytes
    ) -> RateLimitResult:
        """Check bandwidth-based rate limits."""
        
        redis_key = f"{self.key_prefix}bandwidth:{key}"
        
        # Remove expired bandwidth entries
        await self.redis.zremrangebyscore(redis_key, 0, window_start)
        
        # Sum current bandwidth usage
        bandwidth_entries = await self.redis.zrange(redis_key, 0, -1, withscores=True)
        current_usage = sum(int(entry[0].decode().split('_')[1]) for entry in bandwidth_entries)
        
        remaining_bandwidth = max(0, rule.limit - current_usage)
        
        if current_usage + request_cost > rule.limit:
            return RateLimitResult(
                allowed=False,
                limit=rule.limit,
                remaining=remaining_bandwidth,
                reset_time=datetime.fromtimestamp(current_time + rule.window.total_seconds()),
                retry_after=int(rule.window.total_seconds()),
                rule_name=f"bandwidth_{rule.limit}"
            )
        
        # Add current bandwidth usage
        await self.redis.zadd(
            redis_key, 
            {f"bw_{request_cost}_{current_time}": current_time}
        )
        await self.redis.expire(redis_key, int(rule.window.total_seconds()) + 60)
        
        return RateLimitResult(
            allowed=True,
            limit=rule.limit,
            remaining=remaining_bandwidth - request_cost,
            reset_time=datetime.fromtimestamp(current_time + rule.window.total_seconds()),
            rule_name=f"bandwidth_{rule.limit}"
        )
    
    async def increment_concurrent(self, key: str, amount: int = 1, ttl: int = 300) -> int:
        """Increment concurrent request counter."""
        redis_key = f"{self.key_prefix}concurrent:{key}"
        
        pipe = self.redis.pipeline()
        pipe.incrby(redis_key, amount)
        pipe.expire(redis_key, ttl)
        results = await pipe.execute()
        
        return results[0]
    
    async def decrement_concurrent(self, key: str, amount: int = 1) -> int:
        """Decrement concurrent request counter."""
        redis_key = f"{self.key_prefix}concurrent:{key}"
        
        current = await self.redis.get(redis_key)
        if current:
            new_value = max(0, int(current) - amount)
            if new_value == 0:
                await self.redis.delete(redis_key)
            else:
                await self.redis.set(redis_key, new_value)
            return new_value
        
        return 0


class RateLimitService:
    """
    High-level rate limiting service that orchestrates multiple rate limiters
    and integrates with the multi-tenant configuration system.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.limiter: Optional[SlidingWindowRateLimiter] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connection and rate limiter."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Keep binary for performance
                socket_connect_timeout=5,
                socket_timeout=2,  # Fast timeout for rate limiting
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self.limiter = SlidingWindowRateLimiter(self.redis_client)
            self._initialized = True
            
            logger.info("Rate limiting service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limiting service: {e}")
            raise
    
    async def check_rate_limits(
        self,
        path: str,
        industry: Industry,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_size: int = 1  # Size in bytes for bandwidth limiting
    ) -> List[RateLimitResult]:
        """
        Check all applicable rate limits for a request.
        
        Returns list of rate limit results - if any are denied, the request should be rejected.
        """
        if not self._initialized:
            logger.warning("Rate limiting service not initialized, allowing all requests")
            return []
        
        # Get all applicable limits for this request
        applicable_limits = rate_limit_config.get_applicable_limits(
            path, industry, tenant_id, user_id
        )
        
        results = []
        current_time = time.time()
        
        # Check each applicable limit
        for limit_name, rule, context in applicable_limits:
            # Generate cache key for this specific limit
            cache_key = self._generate_cache_key(limit_name, context, ip_address)
            
            # Determine request cost based on rule type
            request_cost = 1
            if rule.limit_type == RateLimitType.BANDWIDTH_LIMIT:
                request_cost = request_size
            
            # Check the rate limit
            result = await self.limiter.check_limit(
                cache_key, rule, current_time, request_cost
            )
            result.rule_name = limit_name
            results.append(result)
            
            # If this limit is exceeded, we can short-circuit (optional optimization)
            if not result.allowed:
                logger.info(
                    f"Rate limit exceeded: {limit_name}",
                    extra={
                        "event": "rate_limit_exceeded",
                        "rule": limit_name,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "path": path,
                        "remaining": result.remaining,
                        "limit": result.limit
                    }
                )
        
        return results
    
    async def track_concurrent_request(
        self, 
        path: str, 
        industry: Industry,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Track concurrent request start. Returns list of keys to decrement when request completes.
        """
        if not self._initialized:
            return []
        
        concurrent_keys = []
        applicable_limits = rate_limit_config.get_applicable_limits(
            path, industry, tenant_id, user_id
        )
        
        for limit_name, rule, context in applicable_limits:
            if rule.limit_type == RateLimitType.CONCURRENT_REQUESTS:
                cache_key = self._generate_cache_key(limit_name, context)
                await self.limiter.increment_concurrent(cache_key)
                concurrent_keys.append(cache_key)
        
        return concurrent_keys
    
    async def release_concurrent_request(self, concurrent_keys: List[str]) -> None:
        """Release concurrent request tracking."""
        if not self._initialized or not concurrent_keys:
            return
        
        for key in concurrent_keys:
            try:
                await self.limiter.decrement_concurrent(key)
            except Exception as e:
                logger.warning(f"Failed to decrement concurrent counter for {key}: {e}")
    
    def _generate_cache_key(
        self, 
        limit_name: str, 
        context: Dict[str, str], 
        ip_address: Optional[str] = None
    ) -> str:
        """Generate Redis cache key for rate limit bucket."""
        
        key_parts = [limit_name]
        
        # Add context components in consistent order
        for key in sorted(context.keys()):
            if key in context:
                key_parts.append(f"{key}:{context[key]}")
        
        # Add IP address for global limits
        if context.get("type") == "global" and ip_address:
            key_parts.append(f"ip:{ip_address}")
        
        # Create key and hash if too long
        key = ":".join(key_parts)
        if len(key) > 250:  # Redis key length limit
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
            key = f"{limit_name}:hash:{key_hash}"
        
        return key
    
    async def get_rate_limit_stats(
        self, 
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get rate limiting statistics for monitoring."""
        if not self._initialized:
            return {}
        
        try:
            # Get Redis stats
            info = await self.redis_client.info()
            
            # Count rate limit keys
            pattern = f"{self.limiter.key_prefix}*"
            if tenant_id:
                pattern = f"{self.limiter.key_prefix}*tenant_id:{tenant_id}*"
            
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            return {
                "redis_connected": True,
                "total_rate_limit_keys": len(keys),
                "redis_memory_usage": info.get("used_memory_human", "N/A"),
                "redis_keyspace_hits": info.get("keyspace_hits", 0),
                "redis_keyspace_misses": info.get("keyspace_misses", 0),
                "tenant_filter": tenant_id
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {"error": str(e)}
    
    async def reset_rate_limits(
        self, 
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """Reset rate limits for a tenant or user. Returns number of keys deleted."""
        if not self._initialized:
            return 0
        
        try:
            patterns = []
            
            if tenant_id:
                patterns.append(f"{self.limiter.key_prefix}*tenant_id:{tenant_id}*")
            
            if user_id:
                patterns.append(f"{self.limiter.key_prefix}*user_id:{user_id}*")
            
            if not patterns:
                patterns.append(f"{self.limiter.key_prefix}*")
            
            total_deleted = 0
            for pattern in patterns:
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_deleted += deleted
            
            logger.info(f"Reset {total_deleted} rate limit keys")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error resetting rate limits: {e}")
            return 0
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiting service closed")


# Global rate limiting service instance
rate_limit_service: Optional[RateLimitService] = None


async def get_rate_limit_service() -> RateLimitService:
    """Get the global rate limiting service instance."""
    global rate_limit_service
    
    if rate_limit_service is None:
        from ..core.config import settings
        rate_limit_service = RateLimitService(settings.REDIS_URL)
        await rate_limit_service.initialize()
    
    return rate_limit_service