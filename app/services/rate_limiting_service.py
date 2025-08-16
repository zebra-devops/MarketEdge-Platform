"""
Rate Limiting Service

Provides Redis-based rate limiting with tenant-aware quotas and industry-specific limits.
Supports sliding window rate limiting with <5ms overhead requirement.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
from redis.exceptions import RedisError

from ..core.logging import logger


class IndustryType(str, Enum):
    """Industry types with specific rate limiting requirements"""
    HOTEL = "hotel"
    CINEMA = "cinema"
    GYM = "gym"
    B2B = "b2b"
    RETAIL = "retail"
    GENERAL = "general"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different request types"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 0  # Additional burst capacity
    
    def __post_init__(self):
        if self.burst_limit == 0:
            self.burst_limit = min(self.requests_per_minute * 2, 100)


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    limit_type: str = "minute"


class RateLimitingService:
    """
    Redis-based rate limiting service with tenant isolation and industry-specific limits.
    
    Features:
    - Sliding window rate limiting
    - Tenant-aware quotas
    - Industry-specific rate limits
    - Performance optimized (<5ms overhead)
    - Comprehensive logging and monitoring
    """
    
    # Industry-specific rate limit configurations
    INDUSTRY_LIMITS = {
        IndustryType.CINEMA: RateLimitConfig(
            requests_per_minute=200,  # Higher limits for cinema ticketing systems
            requests_per_hour=10000,
            requests_per_day=200000,
            burst_limit=300
        ),
        IndustryType.HOTEL: RateLimitConfig(
            requests_per_minute=150,  # High for real-time pricing updates
            requests_per_hour=7500,
            requests_per_day=150000,
            burst_limit=200
        ),
        IndustryType.GYM: RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=5000,
            requests_per_day=100000,
            burst_limit=150
        ),
        IndustryType.B2B: RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=6000,
            requests_per_day=120000,
            burst_limit=180
        ),
        IndustryType.RETAIL: RateLimitConfig(
            requests_per_minute=80,
            requests_per_hour=4000,
            requests_per_day=80000,
            burst_limit=120
        ),
        IndustryType.GENERAL: RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=3000,
            requests_per_day=60000,
            burst_limit=100
        )
    }
    
    def __init__(self, redis_url: str):
        """Initialize rate limiting service with Redis connection"""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.key_prefix = "rate_limit:"
        self.sliding_window_size = 60  # seconds for minute window
        
    async def initialize(self) -> None:
        """Initialize Redis connection with optimized settings"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20,  # Connection pooling for performance
                connection_pool=None
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiting service initialized successfully")
            
        except RedisError as e:
            logger.error(f"Failed to initialize rate limiting service: {e}")
            raise
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        user_id: str,
        industry_type: IndustryType,
        endpoint: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check rate limit for a request with <5ms performance target.
        
        Uses sliding window algorithm for accurate rate limiting.
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized, allowing request")
            return RateLimitResult(allowed=True, remaining=999, reset_time=int(time.time()) + 60)
        
        start_time = time.perf_counter()
        
        try:
            # Get rate limit configuration for industry
            config = self.INDUSTRY_LIMITS.get(industry_type, self.INDUSTRY_LIMITS[IndustryType.GENERAL])
            
            # Create rate limit key (tenant isolated)
            key_base = f"{self.key_prefix}{tenant_id}:{user_id}"
            if endpoint:
                key_base += f":{endpoint}"
            
            # Check minute limit (most restrictive, checked first)
            minute_result = await self._check_sliding_window(
                f"{key_base}:minute",
                config.requests_per_minute + config.burst_limit,
                60
            )
            
            if not minute_result.allowed:
                processing_time = (time.perf_counter() - start_time) * 1000
                await self._log_rate_limit_event(
                    tenant_id, user_id, industry_type, "blocked_minute", processing_time
                )
                return minute_result
            
            # Check hour limit
            hour_result = await self._check_sliding_window(
                f"{key_base}:hour",
                config.requests_per_hour,
                3600
            )
            
            if not hour_result.allowed:
                processing_time = (time.perf_counter() - start_time) * 1000
                await self._log_rate_limit_event(
                    tenant_id, user_id, industry_type, "blocked_hour", processing_time
                )
                return hour_result
            
            # Check daily limit
            daily_result = await self._check_sliding_window(
                f"{key_base}:day",
                config.requests_per_day,
                86400
            )
            
            if not daily_result.allowed:
                processing_time = (time.perf_counter() - start_time) * 1000
                await self._log_rate_limit_event(
                    tenant_id, user_id, industry_type, "blocked_day", processing_time
                )
                return daily_result
            
            # All checks passed, record the request
            await self._record_request(key_base)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Log performance if over threshold
            if processing_time > 5.0:
                logger.warning(
                    f"Rate limiting check exceeded 5ms threshold: {processing_time:.2f}ms",
                    extra={
                        "event": "rate_limit_performance_warning",
                        "processing_time": processing_time,
                        "tenant_id": tenant_id,
                        "industry_type": industry_type
                    }
                )
            
            await self._log_rate_limit_event(
                tenant_id, user_id, industry_type, "allowed", processing_time
            )
            
            return RateLimitResult(
                allowed=True,
                remaining=minute_result.remaining,
                reset_time=minute_result.reset_time,
                limit_type="minute"
            )
            
        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Error in rate limiting check: {e}",
                extra={
                    "event": "rate_limit_error",
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "industry_type": industry_type,
                    "processing_time": processing_time
                },
                exc_info=True
            )
            # Fail open for availability
            return RateLimitResult(allowed=True, remaining=999, reset_time=int(time.time()) + 60)
    
    async def _check_sliding_window(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """
        Check sliding window rate limit using Redis sorted sets.
        Optimized for performance with pipelined operations.
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Use pipeline for atomic operations
        pipeline = self.redis_client.pipeline()
        
        # Remove old entries and count current requests in one atomic operation
        pipeline.zremrangebyscore(key, 0, window_start)
        pipeline.zcard(key)
        pipeline.expire(key, window_seconds + 60)  # Add buffer to TTL
        
        results = await pipeline.execute()
        current_count = results[1]
        
        if current_count >= limit:
            # Calculate when window will have space
            pipeline = self.redis_client.pipeline()
            pipeline.zrange(key, 0, 0, withscores=True)
            oldest_request = await pipeline.execute()
            
            if oldest_request[0]:
                reset_time = int(oldest_request[0][0][1] + window_seconds)
                retry_after = max(1, reset_time - int(now))
            else:
                reset_time = int(now + window_seconds)
                retry_after = window_seconds
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after,
                limit_type=f"{window_seconds}s"
            )
        
        return RateLimitResult(
            allowed=True,
            remaining=limit - current_count - 1,  # -1 for current request
            reset_time=int(now + window_seconds),
            limit_type=f"{window_seconds}s"
        )
    
    async def _record_request(self, key_base: str) -> None:
        """Record a request across all time windows using pipelined operations"""
        now = time.time()
        request_id = f"{now}:{id(asyncio.current_task())}"
        
        # Use pipeline for performance
        pipeline = self.redis_client.pipeline()
        
        # Add to all time windows
        pipeline.zadd(f"{key_base}:minute", {request_id: now})
        pipeline.zadd(f"{key_base}:hour", {request_id: now})
        pipeline.zadd(f"{key_base}:day", {request_id: now})
        
        # Set TTLs
        pipeline.expire(f"{key_base}:minute", 120)  # 2 minutes
        pipeline.expire(f"{key_base}:hour", 7200)   # 2 hours
        pipeline.expire(f"{key_base}:day", 172800)  # 2 days
        
        await pipeline.execute()
    
    async def _log_rate_limit_event(
        self, 
        tenant_id: str, 
        user_id: str, 
        industry_type: IndustryType,
        result: str,
        processing_time: float
    ) -> None:
        """Log rate limiting events for monitoring and analysis"""
        logger.info(
            "Rate limit check completed",
            extra={
                "event": "rate_limit_check",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "industry_type": industry_type.value,
                "result": result,
                "processing_time_ms": round(processing_time, 2)
            }
        )
    
    async def get_rate_limit_status(
        self,
        tenant_id: str,
        user_id: str,
        industry_type: IndustryType
    ) -> Dict[str, Any]:
        """Get current rate limit status for monitoring"""
        if not self.redis_client:
            return {"error": "Redis client not initialized"}
        
        try:
            config = self.INDUSTRY_LIMITS.get(industry_type, self.INDUSTRY_LIMITS[IndustryType.GENERAL])
            key_base = f"{self.key_prefix}{tenant_id}:{user_id}"
            
            # Get current counts for all windows
            pipeline = self.redis_client.pipeline()
            pipeline.zcard(f"{key_base}:minute")
            pipeline.zcard(f"{key_base}:hour")
            pipeline.zcard(f"{key_base}:day")
            
            results = await pipeline.execute()
            
            return {
                "industry_type": industry_type.value,
                "limits": {
                    "minute": config.requests_per_minute + config.burst_limit,
                    "hour": config.requests_per_hour,
                    "day": config.requests_per_day
                },
                "current": {
                    "minute": results[0],
                    "hour": results[1],
                    "day": results[2]
                },
                "remaining": {
                    "minute": max(0, (config.requests_per_minute + config.burst_limit) - results[0]),
                    "hour": max(0, config.requests_per_hour - results[1]),
                    "day": max(0, config.requests_per_day - results[2])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def reset_rate_limit(
        self,
        tenant_id: str,
        user_id: str,
        window: Optional[str] = None
    ) -> bool:
        """Reset rate limits for a user (admin function)"""
        if not self.redis_client:
            return False
        
        try:
            key_base = f"{self.key_prefix}{tenant_id}:{user_id}"
            
            if window:
                # Reset specific window
                await self.redis_client.delete(f"{key_base}:{window}")
                logger.info(
                    f"Rate limit reset for {window} window",
                    extra={
                        "event": "rate_limit_reset",
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "window": window
                    }
                )
            else:
                # Reset all windows
                pipeline = self.redis_client.pipeline()
                pipeline.delete(f"{key_base}:minute")
                pipeline.delete(f"{key_base}:hour")
                pipeline.delete(f"{key_base}:day")
                await pipeline.execute()
                
                logger.info(
                    "All rate limits reset",
                    extra={
                        "event": "rate_limit_reset_all",
                        "tenant_id": tenant_id,
                        "user_id": user_id
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}", exc_info=True)
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics for monitoring"""
        if not self.redis_client:
            return {"error": "Redis client not initialized"}
        
        try:
            # Get all rate limiting keys
            keys = []
            async for key in self.redis_client.scan_iter(match=f"{self.key_prefix}*"):
                keys.append(key)
            
            total_keys = len(keys)
            active_limits = 0
            
            # Sample some keys to check activity
            sample_size = min(100, total_keys)
            if keys:
                sample_keys = keys[:sample_size]
                pipeline = self.redis_client.pipeline()
                
                for key in sample_keys:
                    pipeline.zcard(key)
                
                results = await pipeline.execute()
                active_limits = sum(1 for count in results if count > 0)
            
            return {
                "total_rate_limit_keys": total_keys,
                "active_limits": active_limits,
                "sample_size": sample_size,
                "memory_usage": await self._get_memory_usage()
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limiting statistics: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _get_memory_usage(self) -> Dict[str, Any]:
        """Get Redis memory usage statistics"""
        try:
            info = await self.redis_client.info("memory")
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "used_memory_rss": info.get("used_memory_rss_human", "N/A"),
                "used_memory_peak": info.get("used_memory_peak_human", "N/A")
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"error": str(e)}
    
    async def close(self) -> None:
        """Close Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Rate limiting service closed")
        except Exception as e:
            logger.error(f"Error closing rate limiting service: {e}")