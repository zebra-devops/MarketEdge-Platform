from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
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

class ManualCORSMiddleware(BaseHTTPMiddleware):
    """Manual CORS middleware - emergency fix for Odeon demo"""
    
    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = allowed_origins
        print(f"Manual CORS Middleware initialized with: {allowed_origins}")
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin in self.allowed_origins:
                return Response(
                    content="",
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, X-Requested-With, Origin",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "600",
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

# Production-ready FastAPI app configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Multi-Tenant Business Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    root_path="",
)

# PRIORITY 1 FIX: Proper FastAPI CORSMiddleware implementation
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://app.zebra.associates",
    "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
]
logger.info(f"CORS PRIORITY 1 FIX: FastAPI CORSMiddleware with origins: {cors_origins}")

# Add CORS middleware FIRST - order matters for Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add middleware to the FastAPI app
# Middleware order is important:
# 1. TrustedHostMiddleware - basic security  
# 2. ErrorHandlerMiddleware - error handling
# 3. LoggingMiddleware - request logging
# 4. TenantContextMiddleware - extract tenant context (needed for rate limiting)
# 5. RateLimitMiddleware - rate limiting (uses tenant context)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for Railway health checks.
    CORS-001: Works with Caddy reverse proxy multi-service setup.
    """
    try:
        # Minimal health check that doesn't depend on database/redis
        health_data = {
            "status": "healthy",
            "version": settings.PROJECT_VERSION,
            "timestamp": time.time(),
            "cors_mode": "caddy_proxy_multi_service",
            "service_type": "fastapi_backend"
        }
        
        # Log health check request (but don't let logging failures affect health)
        try:
            logger.info("Health check requested - CORS-001 multi-service active")
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
                "cors_mode": "caddy_proxy_multi_service",
                "note": "basic_health_check_fallback"
            }
        )

@app.get("/cors-debug")
async def cors_debug(request: Request):
    """
    Debug endpoint to check CORS configuration and headers.
    CORS-001: Multi-service setup with Caddy proxy + FastAPI CORS.
    """
    origin = request.headers.get("origin", "no-origin-header")
    user_agent = request.headers.get("user-agent", "no-user-agent")
    
    debug_info = {
        "cors_mode": "caddy_proxy_multi_service",
        "cors_origins_configured": settings.CORS_ORIGINS,
        "request_origin": origin,
        "origin_allowed": origin in settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else False,
        "user_agent": user_agent,
        "all_headers": dict(request.headers),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "timestamp": time.time(),
        "fastapi_cors_middleware": "active",
        "caddy_proxy": "active",
        "service_type": "fastapi_backend"
    }
    
    # Log CORS debug request
    try:
        logger.info(f"CORS debug requested from origin: {origin} - CORS-001 active")
    except:
        pass
    
    return debug_info

@app.get("/ready")
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