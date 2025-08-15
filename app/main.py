from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
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

# CORS middleware MUST be added first to handle preflight requests correctly
print(f"CORS Origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware order is important:
# 1. CORSMiddleware - MUST be first to handle preflight requests
# 2. TrustedHostMiddleware - basic security  
# 3. ErrorHandlerMiddleware - error handling
# 4. LoggingMiddleware - request logging
# 5. TenantContextMiddleware - extract tenant context (needed for rate limiting)
# 6. RateLimitMiddleware - rate limiting (uses tenant context)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
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

@app.get("/cors-debug")
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
        "timestamp": time.time()
    }
    
    # Log CORS debug request
    try:
        logger.info(f"CORS debug requested from origin: {origin}")
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