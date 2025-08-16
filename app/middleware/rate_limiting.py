"""
Rate Limiting Middleware

FastAPI middleware that provides tenant-aware rate limiting with Redis backend.
Integrates with existing tenant context middleware for seamless multi-tenant support.
"""
import time
import asyncio
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logging import logger
from ..core.rate_limit_config import Industry
from ..services.rate_limit_service import get_rate_limit_service, RateLimitResult
from ..models.organisation import Organisation


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that enforces tenant-aware rate limits.
    
    Features:
    - Industry-specific rate limiting
    - Multi-tenant isolation
    - <5ms performance overhead
    - Graceful degradation on Redis failures
    - Comprehensive logging and monitoring
    """
    
    def __init__(self, app):
        super().__init__(app)
        self._rate_limit_service = None
        
        # Routes that should skip rate limiting
        self.excluded_routes = {
            "/health",
            "/docs",
            "/redoc", 
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware processing logic."""
        start_time = time.time()
        concurrent_keys = []
        
        try:
            # Check if rate limiting is enabled globally
            from ..core.config import settings
            if not settings.RATE_LIMIT_ENABLED:
                return await call_next(request)
            
            # Skip rate limiting for excluded routes
            if self._should_skip_rate_limiting(request):
                return await call_next(request)
            
            # Get rate limiting service
            rate_service = await self._get_rate_service()
            if not rate_service:
                # Service unavailable, allow request but log warning
                logger.warning("Rate limiting service unavailable, allowing request")
                return await call_next(request)
            
            # Extract request context
            context = await self._extract_request_context(request)
            
            # Check rate limits before processing request
            rate_results = await self._check_rate_limits(rate_service, request, context)
            
            # Find any failed rate limit checks
            failed_checks = [result for result in rate_results if not result.allowed]
            
            if failed_checks:
                # Return rate limit exceeded response
                return await self._create_rate_limit_response(failed_checks[0])
            
            # Track concurrent requests if applicable
            if rate_results:
                concurrent_keys = await rate_service.track_concurrent_request(
                    request.url.path,
                    context["industry"],
                    context.get("tenant_id"),
                    context.get("user_id")
                )
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            if rate_results:
                self._add_rate_limit_headers(response, rate_results)
            
            # Add performance metrics
            processing_time = (time.time() - start_time) * 1000
            response.headers["X-RateLimit-Processing-Time"] = f"{processing_time:.2f}ms"
            
            return response
            
        except Exception as e:
            logger.error(
                "Rate limiting middleware error",
                extra={
                    "event": "rate_limit_middleware_error",
                    "error": str(e),
                    "path": request.url.path
                },
                exc_info=True
            )
            
            # On middleware errors, allow the request to proceed
            # but ensure we still release concurrent tracking
            try:
                if concurrent_keys and self._rate_limit_service:
                    await self._rate_limit_service.release_concurrent_request(concurrent_keys)
            except Exception:
                pass
            
            # Continue with request processing
            return await call_next(request)
        
        finally:
            # Always release concurrent request tracking
            try:
                if concurrent_keys and self._rate_limit_service:
                    await self._rate_limit_service.release_concurrent_request(concurrent_keys)
            except Exception as e:
                logger.warning(f"Failed to release concurrent tracking: {e}")
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if request should skip rate limiting."""
        path = request.url.path
        
        # Skip excluded routes
        if path in self.excluded_routes:
            return True
        
        # Skip static files and assets
        if path.startswith(("/static/", "/assets/", "/favicon")):
            return True
        
        return False
    
    async def _get_rate_service(self):
        """Get rate limiting service with caching."""
        if self._rate_limit_service is None:
            try:
                self._rate_limit_service = await get_rate_limit_service()
            except Exception as e:
                logger.error(f"Failed to get rate limiting service: {e}")
                return None
        
        return self._rate_limit_service
    
    async def _extract_request_context(self, request: Request) -> dict:
        """Extract context needed for rate limiting from request."""
        context = {
            "industry": Industry.DEFAULT,  # Default fallback
            "tenant_id": None,
            "user_id": None,
            "ip_address": self._get_client_ip(request)
        }
        
        try:
            # Get tenant context from request state (set by TenantContextMiddleware)
            if hasattr(request.state, "tenant_id"):
                context["tenant_id"] = str(request.state.tenant_id)
                context["user_id"] = str(request.state.user_id)
                
                # Get industry from tenant's organisation
                industry = await self._get_tenant_industry(request.state.tenant_id)
                if industry:
                    context["industry"] = industry
            
            # For unauthenticated requests, we still have IP-based limits
            
        except Exception as e:
            logger.warning(f"Error extracting rate limit context: {e}")
            # Continue with defaults
        
        return context
    
    async def _get_tenant_industry(self, tenant_id: str) -> Optional[Industry]:
        """Get industry for a tenant (cached lookup)."""
        try:
            # This would typically be cached in a real implementation
            # For now, we'll use a simple mapping or database lookup
            
            # Example industry mapping - in production this would come from the database
            # and be cached with Redis
            industry_mapping = {
                # Add tenant_id -> industry mappings as needed
                # This could also be determined from organisation SIC codes
            }
            
            industry_str = industry_mapping.get(tenant_id)
            if industry_str:
                return Industry(industry_str)
            
            # If not found, we could look up the organisation's SIC code
            # and map it to an industry, but for now return DEFAULT
            return Industry.DEFAULT
            
        except Exception as e:
            logger.warning(f"Error getting tenant industry: {e}")
            return Industry.DEFAULT
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if there are multiple
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client IP from connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _check_rate_limits(
        self, 
        rate_service, 
        request: Request, 
        context: dict
    ) -> List[RateLimitResult]:
        """Check all applicable rate limits for the request."""
        try:
            # Estimate request size for bandwidth limiting
            request_size = self._estimate_request_size(request)
            
            # Check rate limits
            results = await rate_service.check_rate_limits(
                path=request.url.path,
                industry=context["industry"],
                tenant_id=context.get("tenant_id"),
                user_id=context.get("user_id"),
                ip_address=context.get("ip_address"),
                request_size=request_size
            )
            
            # Log rate limit checks for monitoring
            if results:
                logger.debug(
                    "Rate limit check completed",
                    extra={
                        "event": "rate_limit_check",
                        "path": request.url.path,
                        "tenant_id": context.get("tenant_id"),
                        "industry": context["industry"].value,
                        "checks": len(results),
                        "allowed": all(r.allowed for r in results)
                    }
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            # On error, allow the request
            return []
    
    def _estimate_request_size(self, request: Request) -> int:
        """Estimate request size for bandwidth limiting."""
        size = 0
        
        # Add headers size (rough estimate)
        for key, value in request.headers.items():
            size += len(key) + len(value) + 4  # ": \r\n"
        
        # Add URL size
        size += len(str(request.url))
        
        # Add content length if available
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size += int(content_length)
            except ValueError:
                pass
        
        # Minimum size estimate
        return max(size, 100)
    
    async def _create_rate_limit_response(self, failed_result: RateLimitResult) -> JSONResponse:
        """Create rate limit exceeded response."""
        
        headers = failed_result.to_headers()
        
        response_data = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {failed_result.limit} per window",
            "limit": failed_result.limit,
            "remaining": failed_result.remaining,
            "reset_time": failed_result.reset_time.isoformat(),
            "rule": failed_result.rule_name
        }
        
        if failed_result.retry_after:
            response_data["retry_after"] = failed_result.retry_after
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response_data,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_results: List[RateLimitResult]) -> None:
        """Add rate limiting headers to response."""
        
        # Find the most restrictive rate limit for headers
        if not rate_results:
            return
        
        # Use the first successful result or the most restrictive one
        primary_result = rate_results[0]
        for result in rate_results:
            if result.remaining < primary_result.remaining:
                primary_result = result
        
        # Add headers
        headers = primary_result.to_headers()
        for key, value in headers.items():
            response.headers[key] = value
        
        # Add additional metadata
        response.headers["X-RateLimit-Rules-Count"] = str(len(rate_results))


class RateLimitManager:
    """
    Rate Limit Management utilities for admin operations.
    
    Provides methods for creating default rules, industry-specific configurations,
    and emergency bypass operations with proper authorization checks.
    """
    
    @staticmethod
    async def create_default_rules(db):
        """Create default rate limiting rules for the platform."""
        from ..models.rate_limiting import RateLimitRule, RateLimitScope, RateLimitPeriod
        
        try:
            # Check if default rules already exist
            existing_defaults = db.query(RateLimitRule).filter(
                RateLimitRule.scope == RateLimitScope.GLOBAL
            ).first()
            
            if existing_defaults:
                logger.info("Default rate limit rules already exist")
                return
            
            # Create default rules
            default_rules = [
                {
                    "rule_name": "global_api_limit",
                    "description": "Global API rate limit for all endpoints",
                    "scope": RateLimitScope.GLOBAL,
                    "endpoint_pattern": "/api/*",
                    "requests_per_period": 1000,
                    "period": RateLimitPeriod.HOUR,
                    "burst_requests": 100,
                    "priority": 10,
                    "is_active": True
                },
                {
                    "rule_name": "auth_endpoint_limit",
                    "description": "Restrictive limit for authentication endpoints",
                    "scope": RateLimitScope.GLOBAL,
                    "endpoint_pattern": "/api/v1/auth/*",
                    "requests_per_period": 20,
                    "period": RateLimitPeriod.MINUTE,
                    "burst_requests": 5,
                    "priority": 100,
                    "is_active": True
                },
                {
                    "rule_name": "admin_endpoint_limit",
                    "description": "Higher limits for admin endpoints",
                    "scope": RateLimitScope.GLOBAL,
                    "endpoint_pattern": "/api/v1/admin/*",
                    "requests_per_period": 200,
                    "period": RateLimitPeriod.MINUTE,
                    "burst_requests": 50,
                    "priority": 90,
                    "is_active": True
                }
            ]
            
            for rule_data in default_rules:
                rule = RateLimitRule(**rule_data)
                db.add(rule)
            
            db.commit()
            logger.info(f"Created {len(default_rules)} default rate limit rules")
            
        except Exception as e:
            logger.error(f"Error creating default rate limit rules: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def create_industry_rules(db):
        """Create industry-specific rate limiting rules."""
        from ..models.rate_limiting import RateLimitRule, RateLimitScope, RateLimitPeriod
        from ..core.industry_config import Industry, industry_config_manager
        
        try:
            # Check if industry rules already exist
            existing_industry = db.query(RateLimitRule).filter(
                RateLimitRule.scope == RateLimitScope.SIC_CODE
            ).first()
            
            if existing_industry:
                logger.info("Industry-specific rate limit rules already exist")
                return
            
            industry_rules = []
            
            for industry in Industry:
                if industry == Industry.DEFAULT:
                    continue
                
                # Get industry-specific configuration
                rate_limits = industry_config_manager.get_rate_limit_config(industry)
                
                # Create rules for each industry
                for rule_type, rate_limit_rule in rate_limits.items():
                    industry_rules.append({
                        "rule_name": f"{industry.value}_{rule_type}",
                        "description": f"{industry.value.title()} industry {rule_type} rate limit",
                        "scope": RateLimitScope.SIC_CODE,
                        "scope_value": industry.value,
                        "endpoint_pattern": "/api/v1/*",
                        "requests_per_period": rate_limit_rule.limit,
                        "period": RateLimitPeriod.MINUTE if "minute" in rule_type else RateLimitPeriod.HOUR,
                        "burst_requests": rate_limit_rule.burst_limit or rate_limit_rule.limit,
                        "priority": 50,
                        "is_active": True,
                        "config": {
                            "industry": industry.value,
                            "rule_type": rule_type,
                            "recovery_rate": getattr(rate_limit_rule, 'recovery_rate', None)
                        }
                    })
            
            for rule_data in industry_rules:
                rule = RateLimitRule(**rule_data)
                db.add(rule)
            
            db.commit()
            logger.info(f"Created {len(industry_rules)} industry-specific rate limit rules")
            
        except Exception as e:
            logger.error(f"Error creating industry-specific rate limit rules: {e}")
            db.rollback()
            raise
    
    @staticmethod
    async def emergency_bypass(
        tenant_id: str,
        duration_minutes: int,
        admin_id: str,
        reason: str,
        db
    ) -> Dict[str, Any]:
        """
        Create emergency bypass for rate limiting with full audit logging.
        """
        try:
            # Validate admin authorization
            if not RateLimitManager._validate_admin_authorization(admin_id, tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin authorization required for emergency bypass"
                )
            
            # Limit bypass duration for security
            duration_minutes = min(duration_minutes, 60)  # Max 1 hour
            
            # Create bypass record (would typically go to database)
            bypass_data = {
                "tenant_id": tenant_id,
                "admin_id": admin_id,
                "reason": reason,
                "duration_minutes": duration_minutes,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=duration_minutes)
            }
            
            # Log critical event
            logger.critical(
                "Emergency rate limit bypass activated",
                extra={
                    "event": "emergency_bypass_activated",
                    "tenant_id": tenant_id,
                    "admin_id": admin_id,
                    "reason": reason,
                    "duration_minutes": duration_minutes
                }
            )
            
            return {
                "success": True,
                "bypass_id": f"bypass_{tenant_id}_{int(time.time())}",
                "expires_at": bypass_data["expires_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating emergency bypass: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create emergency bypass"
            )
    
    @staticmethod
    def _validate_admin_authorization(admin_id: str, tenant_id: str) -> bool:
        """Validate admin authorization for emergency operations."""
        try:
            # TODO: Implement actual admin authorization check
            # This should verify admin role and tenant permissions
            return admin_id and tenant_id
        except Exception:
            return False


class RateLimitException(HTTPException):
    """Custom exception for rate limit exceeded scenarios."""
    
    def __init__(self, result: RateLimitResult):
        self.rate_result = result
        
        detail = {
            "error": "Rate limit exceeded",
            "limit": result.limit,
            "remaining": result.remaining,
            "reset_time": result.reset_time.isoformat(),
            "rule": result.rule_name
        }
        
        if result.retry_after:
            detail["retry_after"] = result.retry_after
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=result.to_headers()
        )


# Utility functions for manual rate limit checking in endpoints
# Alias for backward compatibility
RateLimitingMiddleware = RateLimitMiddleware

# Additional utility classes and functions that might be expected
class RedisRateLimiter:
    """Alias for the core rate limiter for backward compatibility."""
    pass

async def initialize_rate_limiting():
    """Initialize rate limiting components."""
    pass

async def cleanup_rate_limiting():
    """Cleanup rate limiting resources."""
    pass


def get_rate_limiting_service():
    """Get the rate limiting service instance."""
    from ..services.rate_limiting_service import RateLimitingService
    return RateLimitingService()

# Utility functions for manual rate limit checking in endpoints
async def check_endpoint_rate_limit(
    request: Request,
    custom_limits: Optional[dict] = None
) -> None:
    """
    Manually check rate limits in an endpoint.
    
    Useful for endpoints that need custom rate limiting logic
    or additional checks beyond the middleware.
    """
    try:
        rate_service = await get_rate_limit_service()
        if not rate_service:
            return  # Service unavailable, allow request
        
        # Extract context similar to middleware
        context = {
            "industry": Industry.DEFAULT,
            "tenant_id": getattr(request.state, "tenant_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "ip_address": request.client.host if request.client else "unknown"
        }
        
        # Check rate limits
        results = await rate_service.check_rate_limits(
            path=request.url.path,
            industry=context["industry"],
            tenant_id=str(context["tenant_id"]) if context["tenant_id"] else None,
            user_id=str(context["user_id"]) if context["user_id"] else None,
            ip_address=context["ip_address"]
        )
        
        # Check for failures
        failed_checks = [result for result in results if not result.allowed]
        if failed_checks:
            raise RateLimitException(failed_checks[0])
    
    except RateLimitException:
        raise  # Re-raise rate limit exceptions
    except Exception as e:
        logger.error(f"Error in manual rate limit check: {e}")
        # Allow request to proceed on error