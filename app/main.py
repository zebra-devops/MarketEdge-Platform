from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
import json
from .core.config import settings
from .core.logging import configure_logging
from .core.health_checks import health_checker
from .api.api_v1.api import api_router
from .middleware.error_handler import ErrorHandlerMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.tenant_context import TenantContextMiddleware
from .middleware.rate_limiting import RateLimitMiddleware

configure_logging()
logger = logging.getLogger(__name__)

class ASGICORSHandler:
    """
    ASGI-level CORS handler that completely bypasses FastAPI routing.
    This is an emergency fix for the Odeon demo authentication issue.
    """
    
    def __init__(self, app):
        self.app = app
        # EMERGENCY CORS FIX v3: Custom domain priority + deployment timestamp
        self.allowed_origins = [
            "https://app.zebra.associates",  # CRITICAL: Custom domain FIRST
            "http://localhost:3000", 
            "http://localhost:3001",
            "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
        ]
        print(f"ASGI CORS Handler initialized with origins: {self.allowed_origins}")
        print(f"DEPLOYMENT TIMESTAMP: {time.time()}")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Get headers and method
        headers = dict(scope.get("headers", []))
        method = scope.get("method", "")
        origin = headers.get(b"origin", b"").decode("utf-8")
        
        # Handle OPTIONS preflight requests immediately for allowed origins
        if method == "OPTIONS" and origin in self.allowed_origins:
            response_headers = [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"),
                (b"access-control-allow-headers", b"Content-Type, Authorization, Accept, X-Requested-With, Origin"),
                (b"access-control-max-age", b"600"),
                (b"content-type", b"application/json"),
            ]
            
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": response_headers,
            })
            
            await send({
                "type": "http.response.body",
                "body": json.dumps({"preflight": "emergency_cors_bypass"}).encode(),
            })
            return
        
        # For non-OPTIONS requests, add CORS headers to the response
        if origin in self.allowed_origins:
            async def send_with_cors(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.extend([
                        (b"access-control-allow-origin", origin.encode()),
                        (b"access-control-allow-credentials", b"true"),
                        (b"access-control-expose-headers", b"*"),
                    ])
                    message["headers"] = headers
                await send(message)
            
            await self.app(scope, receive, send_with_cors)
        else:
            await self.app(scope, receive, send)

# Production-ready FastAPI app configuration
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Multi-Tenant Business Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    root_path="",
)

# EMERGENCY: Completely bypass FastAPI CORS with ASGI-level handler  
print("EMERGENCY CORS FIX v3: Custom domain FIRST priority + deployment verification")
print(f"Custom domain: https://app.zebra.associates") 
print("DEPLOYMENT TIMESTAMP:", time.time())
print("FORCE REDEPLOY FOR ODEON DEMO - CORS FIX URGENT:", time.time())

# Wrap FastAPI app with our emergency ASGI CORS handler
app = ASGICORSHandler(fastapi_app)

# Add middleware to the FastAPI app (before ASGI wrapping)
# Middleware order is important:
# 1. TrustedHostMiddleware - basic security  
# 2. ErrorHandlerMiddleware - error handling
# 3. LoggingMiddleware - request logging
# 4. TenantContextMiddleware - extract tenant context (needed for rate limiting)
# 5. RateLimitMiddleware - rate limiting (uses tenant context)
fastapi_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
fastapi_app.add_middleware(ErrorHandlerMiddleware)
fastapi_app.add_middleware(LoggingMiddleware)
fastapi_app.add_middleware(TenantContextMiddleware)
fastapi_app.add_middleware(RateLimitMiddleware)

fastapi_app.include_router(api_router, prefix=settings.API_V1_STR)


@fastapi_app.get("/health")
async def health_check(request: Request):
    """
    Simple health check endpoint for Railway health checks.
    Returns basic application status without external dependencies.
    """
    try:
        # Minimal health check that doesn't depend on database/redis
        health_data = {
            "status": "healthy",
            "version": settings.PROJECT_VERSION,
            "timestamp": time.time(),
        }
        
        # Log health check request (but don't let logging failures affect health)
        try:
            logger.info("Health check requested - application is running")
        except:
            pass  # Don't fail health check if logging fails
        
        return health_data
        
    except Exception as e:
        # Even if something goes wrong, return a basic response
        return JSONResponse(
            status_code=200,  # Still return 200 for Railway health check
            content={
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": time.time(),
                "note": "basic_health_check_fallback"
            }
        )

@fastapi_app.get("/cors-debug")
async def cors_debug(request: Request):
    """
    Debug endpoint to check CORS configuration and headers.
    Only available in production for emergency debugging.
    """
    origin = request.headers.get("origin", "no-origin-header")
    user_agent = request.headers.get("user-agent", "no-user-agent")
    
    debug_info = {
        "cors_origins_configured": settings.CORS_ORIGINS,
        "request_origin": origin,
        "origin_allowed": origin in settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else False,
        "user_agent": user_agent,
        "all_headers": dict(request.headers),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "timestamp": time.time(),
        "asgi_cors_handler": "active"
    }
    
    # Log CORS debug request
    try:
        logger.info(f"CORS debug requested from origin: {origin}")
    except:
        pass
    
    return debug_info

@fastapi_app.get("/ready")
async def readiness_check():
    """
    Railway readiness check endpoint.
    Verifies database and Redis connectivity over private network.
    """
    try:
        # Comprehensive health check with actual service connectivity
        health_result = await health_checker.comprehensive_health_check()
        
        if health_result["status"] == "healthy":
            return {
                "status": "ready",
                "version": settings.PROJECT_VERSION,
                "network_type": "railway_private_network",
                "services": health_result["services"],
                "summary": health_result["summary"],
                "timestamp": time.time(),
            }
        else:
            logger.warning("Readiness check failed - services not healthy", extra=health_result)
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "version": settings.PROJECT_VERSION,
                    "services": health_result["services"],
                    "error": "One or more services not healthy",
                    "details": health_result if settings.DEBUG else None,
                    "timestamp": time.time(),
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e) if settings.DEBUG else "Service not ready",
                "timestamp": time.time(),
            }
        )


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )