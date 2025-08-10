import asyncio
import time
import json
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError

from ..core.config import settings
from ..core.logging import logger
from ..models.rate_limiting import RateLimitRule, RateLimitScope, RateLimitPeriod, SICRateLimitConfig
from ..models.organisation import Organisation, SubscriptionPlan
from ..models.sectors import SICCode
from ..data.cache.redis_cache import RedisCacheManager
from sqlalchemy.orm import Session


@dataclass
class RateLimitResult:
    """Result of rate limiting check"""
    allowed: bool
    current_usage: int
    limit: int
    reset_time: datetime
    retry_after: Optional[int] = None
    processing_time_ms: float = 0.0
    rule_applied: Optional[str] = None


@dataclass
class RateLimitWindow:
    """Sliding window configuration"""
    window_size_seconds: int
    max_requests: int
    bucket_size_seconds: int = 60  # Size of each bucket in the sliding window


class RateLimiterService:
    """
    High-performance Redis-based rate limiter with sliding window algorithm
    
    Features:
    - Sliding window rate limiting with configurable bucket sizes
    - Tenant-aware quotas with hierarchy: user > org > sic_code > plan > global
    - Industry-specific limits based on SIC codes
    - <5ms performance requirement
    - Burst request handling
    - Multi-level caching for rule resolution
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.rule_cache: Dict[str, RateLimitRule] = {}
        self.cache_ttl = 300  # 5 minutes cache for rules
        self.last_cache_refresh = 0
        
        # Performance optimization: Lua scripts for atomic operations
        self.sliding_window_script = """
        local key = KEYS[1]
        local window_size = tonumber(ARGV[1])
        local max_requests = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        local bucket_size = tonumber(ARGV[4])
        
        -- Calculate window start
        local window_start = current_time - window_size
        
        -- Remove expired buckets
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- Count current requests in window
        local current_count = redis.call('ZCARD', key)
        
        -- Check if limit exceeded
        if current_count >= max_requests then
            -- Get oldest entry to calculate retry time
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 0
            if #oldest > 0 then
                retry_after = math.ceil(oldest[2] + window_size - current_time)
            end
            return {0, current_count, max_requests, retry_after}
        end
        
        -- Add current request
        local bucket_time = math.floor(current_time / bucket_size) * bucket_size
        redis.call('ZADD', key, current_time, current_time .. ':' .. math.random())
        
        -- Set expiry
        redis.call('EXPIRE', key, window_size + bucket_size)
        
        return {1, current_count + 1, max_requests, 0}
        """

    async def initialize(self):
        """Initialize Redis connection and Lua scripts"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding manually for performance
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=50  # Connection pool for high performance
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Register Lua scripts
            self.sliding_window_sha = await self.redis_client.script_load(self.sliding_window_script)
            
            logger.info("Rate limiter service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter service: {e}")
            raise

    async def check_rate_limit(
        self, 
        endpoint: str, 
        method: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        db_session: Optional[Session] = None
    ) -> RateLimitResult:
        """
        Check if request should be rate limited
        
        Performance target: <5ms
        """
        start_time = time.time()
        
        try:
            # 1. Resolve applicable rate limit rule (cached)
            rule = await self._resolve_rate_limit_rule(
                endpoint, method, tenant_id, user_id, db_session
            )
            
            if not rule:
                # No rate limiting configured
                return RateLimitResult(
                    allowed=True,
                    current_usage=0,
                    limit=float('inf'),
                    reset_time=datetime.now() + timedelta(hours=1),
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # 2. Generate Redis key for this rate limit scope
            redis_key = self._generate_redis_key(rule, tenant_id, user_id, ip_address)
            
            # 3. Apply sliding window rate limiting
            window = RateLimitWindow(
                window_size_seconds=rule.period_seconds,
                max_requests=rule.requests_per_period,
                bucket_size_seconds=min(60, rule.period_seconds // 10)  # Optimize bucket size
            )
            
            # 4. Execute Lua script for atomic check and increment
            current_time = time.time()
            result = await self.redis_client.evalsha(
                self.sliding_window_sha,
                1,
                redis_key.encode(),
                str(window.window_size_seconds).encode(),
                str(window.max_requests).encode(),
                str(current_time).encode(),
                str(window.bucket_size_seconds).encode()
            )
            
            allowed, current_usage, limit, retry_after = result
            allowed = bool(allowed)
            
            # 5. Calculate reset time
            reset_time = datetime.fromtimestamp(
                current_time + window.window_size_seconds - (current_time % window.bucket_size_seconds)
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Log if processing took too long
            if processing_time > 5.0:
                logger.warning(
                    f"Rate limit check exceeded 5ms target: {processing_time:.2f}ms",
                    extra={
                        "endpoint": endpoint,
                        "tenant_id": tenant_id,
                        "processing_time_ms": processing_time
                    }
                )
            
            return RateLimitResult(
                allowed=allowed,
                current_usage=current_usage,
                limit=limit,
                reset_time=reset_time,
                retry_after=retry_after if retry_after > 0 else None,
                processing_time_ms=processing_time,
                rule_applied=rule.identifier
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(
                f"Error in rate limit check: {e}",
                extra={
                    "endpoint": endpoint,
                    "tenant_id": tenant_id,
                    "processing_time_ms": processing_time
                },
                exc_info=True
            )
            
            # Fail open for availability
            return RateLimitResult(
                allowed=True,
                current_usage=0,
                limit=float('inf'),
                reset_time=datetime.now() + timedelta(hours=1),
                processing_time_ms=processing_time
            )

    async def _resolve_rate_limit_rule(
        self,
        endpoint: str,
        method: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        db_session: Optional[Session] = None
    ) -> Optional[RateLimitRule]:
        """
        Resolve the applicable rate limit rule with caching
        
        Priority order:
        1. User-specific rule
        2. Organisation-specific rule  
        3. SIC code-specific rule
        4. Subscription plan rule
        5. Global default rule
        """
        
        # Check cache first
        cache_key = f"{endpoint}:{method}:{tenant_id}:{user_id or 'none'}"
        cached_rule = await self._get_cached_rule(cache_key)
        if cached_rule:
            return cached_rule

        if not db_session:
            # Return cached global default if available
            return await self._get_cached_rule("global_default")
        
        try:
            # Get organization details for rule resolution
            org = db_session.query(Organisation).filter(Organisation.id == tenant_id).first()
            if not org:
                return None
            
            # Build rule query with priority order
            rule_conditions = []
            
            # 1. User-specific rules
            if user_id:
                rule_conditions.append(
                    (RateLimitScope.user, user_id, 100)
                )
            
            # 2. Organisation-specific rules
            rule_conditions.append(
                (RateLimitScope.organisation, tenant_id, 80)
            )
            
            # 3. SIC code-specific rules
            if org.sic_code:
                rule_conditions.append(
                    (RateLimitScope.sic_code, org.sic_code, 60)
                )
            
            # 4. Subscription plan rules
            rule_conditions.append(
                (RateLimitScope.subscription_plan, org.subscription_plan.value, 40)
            )
            
            # 5. Global default rules
            rule_conditions.append(
                (RateLimitScope.global_default, None, 20)
            )
            
            # Find the highest priority matching rule
            best_rule = None
            best_priority = -1
            
            for scope, scope_value, base_priority in rule_conditions:
                rules = db_session.query(RateLimitRule).filter(
                    RateLimitRule.scope == scope,
                    RateLimitRule.scope_value == scope_value,
                    RateLimitRule.is_active == True,
                    RateLimitRule.endpoint_pattern == endpoint  # Exact match for now
                ).order_by(RateLimitRule.priority.desc()).all()
                
                for rule in rules:
                    total_priority = base_priority + rule.priority
                    if total_priority > best_priority:
                        best_rule = rule
                        best_priority = total_priority
            
            # If no exact endpoint match, try wildcard patterns
            if not best_rule:
                # This would be implemented with more sophisticated pattern matching
                # For now, return a sensible default based on subscription plan
                best_rule = self._get_default_rule_for_plan(org.subscription_plan, org.sic_code)
            
            # Cache the result
            await self._cache_rule(cache_key, best_rule)
            
            return best_rule
            
        except Exception as e:
            logger.error(f"Error resolving rate limit rule: {e}", exc_info=True)
            return None

    def _get_default_rule_for_plan(
        self, 
        plan: SubscriptionPlan, 
        sic_code: Optional[str] = None
    ) -> RateLimitRule:
        """Generate a default rule based on subscription plan and industry"""
        
        # Base limits by plan
        plan_limits = {
            SubscriptionPlan.basic: {"minute": 30, "hour": 500, "day": 5000},
            SubscriptionPlan.professional: {"minute": 100, "hour": 2000, "day": 20000},
            SubscriptionPlan.enterprise: {"minute": 300, "hour": 10000, "day": 100000}
        }
        
        base_limits = plan_limits.get(plan, plan_limits[SubscriptionPlan.basic])
        
        # Apply industry factors if SIC code is available
        industry_multiplier = 1.0
        if sic_code:
            # High-frequency industries get higher limits
            high_frequency_sics = ["55100", "59140", "62020"]  # Hotels, Cinema, Software
            if sic_code in high_frequency_sics:
                industry_multiplier = 1.5
        
        return RateLimitRule(
            id=f"default_{plan.value}_{sic_code or 'generic'}",
            rule_name=f"Default {plan.value} plan limits",
            scope=RateLimitScope.subscription_plan,
            scope_value=plan.value,
            endpoint_pattern="*",
            requests_per_period=int(base_limits["minute"] * industry_multiplier),
            period=RateLimitPeriod.minute,
            burst_requests=int(base_limits["minute"] * industry_multiplier * 2),
            burst_period_seconds=60,
            priority=0,
            is_active=True
        )

    async def _get_cached_rule(self, cache_key: str) -> Optional[RateLimitRule]:
        """Get cached rule if available and not expired"""
        try:
            if not self.redis_client:
                return None
                
            cached_data = await self.redis_client.get(f"rate_limit_rule:{cache_key}")
            if cached_data:
                rule_data = json.loads(cached_data.decode())
                # Reconstruct RateLimitRule object
                return RateLimitRule(**rule_data)
            return None
        except Exception:
            return None

    async def _cache_rule(self, cache_key: str, rule: Optional[RateLimitRule]):
        """Cache rule for performance"""
        try:
            if not self.redis_client or not rule:
                return
                
            rule_data = {
                "id": rule.id,
                "rule_name": rule.rule_name,
                "scope": rule.scope,
                "scope_value": rule.scope_value,
                "endpoint_pattern": rule.endpoint_pattern,
                "requests_per_period": rule.requests_per_period,
                "period": rule.period,
                "burst_requests": rule.burst_requests,
                "burst_period_seconds": rule.burst_period_seconds,
                "priority": rule.priority,
                "is_active": rule.is_active
            }
            
            await self.redis_client.setex(
                f"rate_limit_rule:{cache_key}",
                self.cache_ttl,
                json.dumps(rule_data)
            )
        except Exception as e:
            logger.warning(f"Failed to cache rate limit rule: {e}")

    def _generate_redis_key(
        self, 
        rule: RateLimitRule, 
        tenant_id: str, 
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Generate Redis key for rate limiting"""
        
        # Key structure: rate_limit:{scope}:{identifier}:{endpoint_hash}
        if rule.scope == RateLimitScope.user and user_id:
            identifier = f"user:{user_id}"
        elif rule.scope == RateLimitScope.organisation:
            identifier = f"org:{tenant_id}"
        elif rule.scope == RateLimitScope.sic_code:
            identifier = f"sic:{rule.scope_value}"
        elif rule.scope == RateLimitScope.subscription_plan:
            identifier = f"plan:{rule.scope_value}"
        else:
            identifier = "global"
        
        # Hash endpoint pattern to keep key length manageable
        import hashlib
        endpoint_hash = hashlib.md5(rule.endpoint_pattern.encode()).hexdigest()[:8]
        
        return f"rate_limit:{identifier}:{endpoint_hash}"

    async def get_current_usage(
        self, 
        tenant_id: str, 
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Dict[str, Dict[str, int]]:
        """Get current rate limit usage for monitoring"""
        try:
            if not self.redis_client:
                return {}
            
            # Pattern to match rate limit keys for this tenant/user
            if user_id:
                pattern = f"rate_limit:user:{user_id}:*"
            else:
                pattern = f"rate_limit:org:{tenant_id}:*"
            
            usage = {}
            async for key in self.redis_client.scan_iter(match=pattern):
                key_str = key.decode() if isinstance(key, bytes) else key
                current_count = await self.redis_client.zcard(key_str)
                usage[key_str] = current_count
            
            return usage
            
        except Exception as e:
            logger.error(f"Error getting rate limit usage: {e}")
            return {}

    async def reset_rate_limit(
        self, 
        tenant_id: str, 
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> bool:
        """Reset rate limit for emergency situations"""
        try:
            if not self.redis_client:
                return False
            
            # Pattern to match rate limit keys
            if user_id:
                pattern = f"rate_limit:user:{user_id}:*"
            else:
                pattern = f"rate_limit:org:{tenant_id}:*"
            
            if endpoint:
                import hashlib
                endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
                pattern = pattern.replace("*", endpoint_hash)
            
            # Delete matching keys
            keys_deleted = 0
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
                keys_deleted += 1
            
            logger.info(
                f"Reset rate limits for tenant {tenant_id}, deleted {keys_deleted} keys",
                extra={
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "keys_deleted": keys_deleted
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Rate limiter service closed")
        except Exception as e:
            logger.error(f"Error closing rate limiter service: {e}")


# Global instance
rate_limiter_service = RateLimiterService()