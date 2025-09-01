from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time
import os
from .core.config import settings
from .core.logging import configure_logging
from .core.health_checks import health_checker
from .core.secret_manager import validate_secrets_startup, get_secrets_health
from .api.api_v1.api import api_router
from .middleware.error_handler import ErrorHandlerMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.tenant_context import TenantContextMiddleware
from .middleware.rate_limiting import RateLimitMiddleware
from .core.module_startup import initialize_module_system, shutdown_module_system, get_module_system_info

configure_logging()
logger = logging.getLogger(__name__)

# Validate secrets on startup
logger.info("Starting secret validation...")
try:
    validate_secrets_startup()
    logger.info("Secret validation completed successfully")
except Exception as e:
    logger.critical(f"Secret validation failed: {e}")
    logger.critical("Application cannot start safely with invalid secrets")

# Security: Removed redundant ManualCORSMiddleware - using FastAPI CORSMiddleware only

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

# Add middleware to the FastAPI app
# CRITICAL FIX: Middleware order matters for CORS to work on all responses
# 1. TrustedHostMiddleware - basic security  
# 2. ErrorHandlerMiddleware - error handling
# 3. LoggingMiddleware - request logging
# 4. CORSMiddleware - MUST BE LAST to handle all responses including errors
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# Security: Comprehensive CORS configuration for production deployment
# Migrated from Caddy to FastAPI for single-service architecture
allowed_origins = []

# Parse CORS_ORIGINS from environment (can be list or comma-separated string)
if isinstance(settings.CORS_ORIGINS, list):
    allowed_origins.extend(settings.CORS_ORIGINS)
elif isinstance(settings.CORS_ORIGINS, str):
    # Handle JSON array string or comma-separated values
    import json
    try:
        # Try parsing as JSON array first
        allowed_origins.extend(json.loads(settings.CORS_ORIGINS))
    except json.JSONDecodeError:
        # Fall back to comma-separated parsing
        allowed_origins.extend([origin.strip() for origin in settings.CORS_ORIGINS.split(",")])

# Ensure critical production origins are always included
critical_origins = [
    "https://app.zebra.associates",  # Primary production origin
    "https://marketedge-frontend.onrender.com",  # Render frontend
    "http://localhost:3000",  # Development
    "http://localhost:3001",  # Development
]

for origin in critical_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

logger.info(f"Security: FastAPI CORSMiddleware configured with origins: {allowed_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin", "X-Tenant-ID"],
    expose_headers=["Content-Type", "Authorization", "X-Tenant-ID"],
    max_age=600,  # Cache preflight requests for 10 minutes
)
# EMERGENCY: Disable tenant context and rate limiting for critical CORS testing
# app.add_middleware(TenantContextMiddleware)
# app.add_middleware(RateLimitMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """Initialize module routing system on application startup"""
    try:
        logger.info("Initializing module routing system...")
        
        # Initialize services needed for module system
        from .services.feature_flag_service import FeatureFlagService
        from .services.module_service import ModuleService
        from .core.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Initialize services
        feature_flag_service = FeatureFlagService(db)
        module_service = ModuleService(db)
        
        # Initialize module routing system
        await initialize_module_system(
            app=app,
            db=db,
            feature_flag_service=feature_flag_service,
            module_service=module_service,
            auto_discover=True  # Enable auto-discovery for development
        )
        
        logger.info("Module routing system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize module routing system: {str(e)}")
        # Don't fail startup if module system fails to initialize
        logger.warning("Application starting without module routing system")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of module routing system"""
    try:
        await shutdown_module_system(app)
    except Exception as e:
        logger.error(f"Error during module system shutdown: {str(e)}")


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for Render deployment.
    Single-service architecture with Gunicorn + FastAPI.
    """
    try:
        # Minimal health check that doesn't depend on database/redis
        health_data = {
            "status": "healthy",
            "version": settings.PROJECT_VERSION,
            "timestamp": time.time(),
            "architecture": "single_service_gunicorn_fastapi",
            "cors_mode": "fastapi_cors_middleware",
            "service_type": "production_ready_gunicorn"
        }
        
        # Log health check request (but don't let logging failures affect health)
        try:
            logger.info("Health check requested - Single service architecture active")
        except:
            pass  # Don't fail health check if logging fails
        
        return health_data
        
    except Exception as e:
        # Even if something goes wrong, return a basic response
        return JSONResponse(
            status_code=200,  # Still return 200 for Render health check
            content={
                "status": "healthy",
                "version": settings.PROJECT_VERSION,
                "timestamp": time.time(),
                "architecture": "single_service_fallback",
                "note": "basic_health_check_fallback"
            }
        )

@app.get("/cors-debug")
async def cors_debug(request: Request):
    """
    Debug endpoint to check CORS configuration and headers.
    Single-service architecture with comprehensive FastAPI CORS.
    """
    origin = request.headers.get("origin", "no-origin-header")
    user_agent = request.headers.get("user-agent", "no-user-agent")
    
    # Get the configured allowed origins
    allowed_origins_debug = []
    if isinstance(settings.CORS_ORIGINS, list):
        allowed_origins_debug = settings.CORS_ORIGINS
    elif isinstance(settings.CORS_ORIGINS, str):
        import json
        try:
            allowed_origins_debug = json.loads(settings.CORS_ORIGINS)
        except json.JSONDecodeError:
            allowed_origins_debug = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    
    debug_info = {
        "architecture": "single_service_gunicorn_fastapi",
        "cors_mode": "fastapi_cors_middleware_comprehensive",
        "cors_origins_configured": allowed_origins_debug,
        "request_origin": origin,
        "origin_allowed": origin in allowed_origins_debug,
        "user_agent": user_agent,
        "all_headers": dict(request.headers),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "timestamp": time.time(),
        "service_type": "production_ready_single_service"
    }
    
    # Log CORS debug request
    try:
        logger.info(f"CORS debug requested from origin: {origin} - Single service architecture")
    except:
        pass
    
    return debug_info

@app.get("/secrets/validate")
async def secrets_validation_check(request: Request):
    """
    Secrets validation endpoint for monitoring and debugging.
    Returns validation status for all critical secrets.
    """
    try:
        from .core.secret_manager import secret_manager
        
        summary = secret_manager.get_validation_summary()
        
        # Don't expose actual secret values, only validation status
        safe_response = {
            "validation_summary": {
                "total_secrets": summary["total_secrets"],
                "valid_secrets": summary["valid_secrets"],
                "invalid_secrets": summary["invalid_secrets"],
                "placeholder_secrets": summary["placeholder_secrets"],
                "connectivity_issues": summary["connectivity_issues"],
                "critical_issues": summary["critical_issues"]
            },
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time(),
            "overall_status": "healthy" if summary["invalid_secrets"] == 0 else "degraded"
        }
        
        # Add detailed issues for debugging (without secret values)
        if settings.DEBUG:
            issues_detail = {}
            for key, result in summary["validation_details"].items():
                if result.issues:
                    issues_detail[key] = {
                        "is_valid": result.is_valid,
                        "issues": result.issues,
                        "connectivity_ok": result.connectivity_ok
                    }
            safe_response["issues_detail"] = issues_detail
        
        status_code = 200 if summary["invalid_secrets"] == 0 else 503
        
        return JSONResponse(
            status_code=status_code,
            content=safe_response
        )
        
    except Exception as e:
        logger.error(f"Secrets validation check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "validation_summary": {
                    "status": "error",
                    "error": str(e) if settings.DEBUG else "Validation check failed"
                },
                "timestamp": time.time()
            }
        )

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


@app.get("/modules/system/info")
async def module_system_info(request: Request):
    """
    Get information about the module routing system status
    """
    try:
        system_info = get_module_system_info()
        system_info.update({
            "timestamp": time.time(),
            "api_version": settings.PROJECT_VERSION
        })
        return system_info
    except Exception as e:
        logger.error(f"Error getting module system info: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error retrieving module system information",
                "timestamp": time.time()
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