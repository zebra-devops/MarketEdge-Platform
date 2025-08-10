"""
Rate Limiting Configuration System

Industry-specific rate limiting configuration for multi-tenant platform.
Supports different industries with tailored rate limits based on business requirements.
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import timedelta


class Industry(Enum):
    """Supported industry types with specific rate limiting requirements."""
    CINEMA = "cinema"
    HOTEL = "hotel"  
    GYM = "gym"
    B2B = "b2b"
    RETAIL = "retail"
    DEFAULT = "default"


class RateLimitType(Enum):
    """Different types of rate limits that can be applied."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    CONCURRENT_REQUESTS = "concurrent_requests"
    BANDWIDTH_LIMIT = "bandwidth_limit"


@dataclass
class RateLimitRule:
    """Individual rate limit rule configuration."""
    limit_type: RateLimitType
    limit: int
    window: timedelta
    burst_limit: Optional[int] = None  # Allow burst traffic up to this limit
    recovery_rate: Optional[float] = None  # Rate at which limits recover (tokens per second)
    
    def __post_init__(self):
        """Validate rule configuration."""
        if self.limit <= 0:
            raise ValueError("Rate limit must be positive")
        if self.burst_limit and self.burst_limit < self.limit:
            raise ValueError("Burst limit cannot be less than base limit")


@dataclass
class EndpointLimits:
    """Rate limits for specific endpoint patterns."""
    pattern: str  # URL pattern (supports wildcards)
    rules: List[RateLimitRule]
    priority: int = 0  # Higher priority rules are checked first
    tenant_specific: bool = True  # Whether limits apply per tenant
    user_specific: bool = False  # Whether limits apply per user


class RateLimitConfig:
    """
    Centralized rate limiting configuration for all industries.
    
    Provides industry-specific rate limits optimized for different business models:
    - Cinema: High burst for ticket booking, moderate sustained load
    - Hotel: Steady booking patterns with peak periods
    - Gym: Regular check-ins with peak hours
    - B2B: Professional usage with higher limits
    - Retail: High transaction volume with burst support
    """
    
    def __init__(self):
        self._industry_configs = self._initialize_industry_configs()
        self._endpoint_configs = self._initialize_endpoint_configs()
        self._global_limits = self._initialize_global_limits()
    
    def _initialize_industry_configs(self) -> Dict[Industry, Dict[str, RateLimitRule]]:
        """Initialize industry-specific rate limiting configurations."""
        
        return {
            Industry.CINEMA: {
                # Cinema-specific: High burst for ticket releases, moderate sustained
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=300,  # High limit for ticket booking rushes
                    window=timedelta(minutes=1),
                    burst_limit=500,  # Allow bursts during movie releases
                    recovery_rate=5.0  # 5 requests per second recovery
                ),
                "booking_requests": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=1000,
                    window=timedelta(hours=1),
                    burst_limit=1500
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=50,
                    window=timedelta(seconds=1)
                )
            },
            
            Industry.HOTEL: {
                # Hotel-specific: Steady booking with seasonal peaks
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=200,
                    window=timedelta(minutes=1),
                    burst_limit=300,
                    recovery_rate=3.3  # ~200 per minute recovery
                ),
                "booking_requests": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=800,
                    window=timedelta(hours=1),
                    burst_limit=1200
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=30,
                    window=timedelta(seconds=1)
                )
            },
            
            Industry.GYM: {
                # Gym-specific: Regular check-ins with peak hours
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=150,
                    window=timedelta(minutes=1),
                    burst_limit=250,  # Peak hour bursts
                    recovery_rate=2.5
                ),
                "checkin_requests": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=600,
                    window=timedelta(hours=1),
                    burst_limit=900
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=25,
                    window=timedelta(seconds=1)
                )
            },
            
            Industry.B2B: {
                # B2B-specific: Professional usage, higher sustained limits
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=500,  # Higher limits for business operations
                    window=timedelta(minutes=1),
                    burst_limit=750,
                    recovery_rate=8.3  # ~500 per minute recovery
                ),
                "business_operations": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=2000,
                    window=timedelta(hours=1),
                    burst_limit=3000
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=100,
                    window=timedelta(seconds=1)
                )
            },
            
            Industry.RETAIL: {
                # Retail-specific: High transaction volume
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=400,
                    window=timedelta(minutes=1),
                    burst_limit=600,  # Shopping season bursts
                    recovery_rate=6.7
                ),
                "transaction_requests": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=1500,
                    window=timedelta(hours=1),
                    burst_limit=2250
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=75,
                    window=timedelta(seconds=1)
                )
            },
            
            Industry.DEFAULT: {
                # Conservative defaults for unknown industries
                "api_calls": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=100,
                    window=timedelta(minutes=1),
                    burst_limit=150,
                    recovery_rate=1.7
                ),
                "general_requests": RateLimitRule(
                    limit_type=RateLimitType.REQUESTS_PER_HOUR,
                    limit=400,
                    window=timedelta(hours=1),
                    burst_limit=600
                ),
                "concurrent": RateLimitRule(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=20,
                    window=timedelta(seconds=1)
                )
            }
        }
    
    def _initialize_endpoint_configs(self) -> List[EndpointLimits]:
        """Initialize endpoint-specific rate limiting configurations."""
        
        return [
            # Authentication endpoints - more restrictive
            EndpointLimits(
                pattern="/api/v1/auth/*",
                rules=[
                    RateLimitRule(
                        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                        limit=20,
                        window=timedelta(minutes=1),
                        burst_limit=30
                    )
                ],
                priority=100,
                tenant_specific=False,
                user_specific=True
            ),
            
            # Admin endpoints - higher limits for operational needs
            EndpointLimits(
                pattern="/api/v1/admin/*",
                rules=[
                    RateLimitRule(
                        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                        limit=200,
                        window=timedelta(minutes=1),
                        burst_limit=300
                    )
                ],
                priority=90,
                tenant_specific=False,
                user_specific=True
            ),
            
            # Market Edge API - high volume for real-time data
            EndpointLimits(
                pattern="/api/v1/market-edge/*",
                rules=[
                    RateLimitRule(
                        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                        limit=300,
                        window=timedelta(minutes=1),
                        burst_limit=450
                    )
                ],
                priority=80,
                tenant_specific=True,
                user_specific=False
            ),
            
            # File upload endpoints - bandwidth considerations
            EndpointLimits(
                pattern="*/upload*",
                rules=[
                    RateLimitRule(
                        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                        limit=10,
                        window=timedelta(minutes=1),
                        burst_limit=20
                    ),
                    RateLimitRule(
                        limit_type=RateLimitType.BANDWIDTH_LIMIT,
                        limit=50 * 1024 * 1024,  # 50MB per minute
                        window=timedelta(minutes=1)
                    )
                ],
                priority=70,
                tenant_specific=True,
                user_specific=True
            ),
            
            # Health check - very permissive
            EndpointLimits(
                pattern="/health",
                rules=[
                    RateLimitRule(
                        limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                        limit=1000,
                        window=timedelta(minutes=1)
                    )
                ],
                priority=50,
                tenant_specific=False,
                user_specific=False
            )
        ]
    
    def _initialize_global_limits(self) -> Dict[str, RateLimitRule]:
        """Initialize global rate limits that apply to all requests."""
        
        return {
            # Global per-IP limits to prevent abuse
            "global_ip_limit": RateLimitRule(
                limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                limit=1000,
                window=timedelta(minutes=1),
                burst_limit=1500
            ),
            
            # Global concurrent connections limit
            "global_concurrent": RateLimitRule(
                limit_type=RateLimitType.CONCURRENT_REQUESTS,
                limit=500,
                window=timedelta(seconds=1)
            )
        }
    
    def get_industry_limits(self, industry: Industry) -> Dict[str, RateLimitRule]:
        """Get rate limits for a specific industry."""
        return self._industry_configs.get(industry, self._industry_configs[Industry.DEFAULT])
    
    def get_endpoint_limits(self, path: str) -> List[EndpointLimits]:
        """Get endpoint-specific limits that match the given path."""
        matching_limits = []
        
        for endpoint_config in self._endpoint_configs:
            if self._path_matches_pattern(path, endpoint_config.pattern):
                matching_limits.append(endpoint_config)
        
        # Sort by priority (higher priority first)
        return sorted(matching_limits, key=lambda x: x.priority, reverse=True)
    
    def get_global_limits(self) -> Dict[str, RateLimitRule]:
        """Get global rate limits."""
        return self._global_limits
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a pattern (supports basic wildcards)."""
        # Simple wildcard matching - can be enhanced with regex if needed
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return path.endswith(pattern[1:])
        elif "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                return path.startswith(parts[0]) and path.endswith(parts[1])
        
        return path == pattern
    
    def get_applicable_limits(
        self, 
        path: str, 
        industry: Industry, 
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Tuple[str, RateLimitRule, Dict[str, str]]]:
        """
        Get all applicable rate limits for a request.
        
        Returns a list of tuples containing:
        - Limit identifier
        - Rate limit rule
        - Context for key generation
        """
        applicable_limits = []
        
        # Add industry-specific limits
        industry_limits = self.get_industry_limits(industry)
        for limit_name, rule in industry_limits.items():
            context = {
                "type": "industry",
                "industry": industry.value,
                "limit_name": limit_name
            }
            if tenant_id:
                context["tenant_id"] = tenant_id
            
            applicable_limits.append((f"industry_{industry.value}_{limit_name}", rule, context))
        
        # Add endpoint-specific limits
        endpoint_limits = self.get_endpoint_limits(path)
        for endpoint_config in endpoint_limits:
            for i, rule in enumerate(endpoint_config.rules):
                context = {
                    "type": "endpoint",
                    "pattern": endpoint_config.pattern,
                    "rule_index": str(i)
                }
                
                if endpoint_config.tenant_specific and tenant_id:
                    context["tenant_id"] = tenant_id
                if endpoint_config.user_specific and user_id:
                    context["user_id"] = user_id
                
                limit_key = f"endpoint_{endpoint_config.pattern.replace('/', '_').replace('*', 'wildcard')}_{i}"
                applicable_limits.append((limit_key, rule, context))
        
        # Add global limits
        global_limits = self.get_global_limits()
        for limit_name, rule in global_limits.items():
            context = {
                "type": "global",
                "limit_name": limit_name
            }
            applicable_limits.append((f"global_{limit_name}", rule, context))
        
        return applicable_limits


# Global rate limit configuration instance
rate_limit_config = RateLimitConfig()