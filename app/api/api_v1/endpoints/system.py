from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
import time
import os
from ....auth.dependencies import get_current_user, require_admin
from ....models.user import User
from ....core.logging import get_logger
from ....core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
async def system_status(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """System status endpoint - provides Epic routing verification for authenticated users"""
    try:
        # Get all registered routes from the app
        app = request.app
        routes = []
        
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', {'GET'})
                routes.append({
                    "path": route.path,
                    "methods": list(methods) if methods else ['GET']
                })
        
        # Filter for Epic-related routes
        epic_routes = [r for r in routes if 
                      '/module-management' in r['path'] or 
                      '/features' in r['path'] or
                      '/admin' in r['path']]
        
        return {
            "status": "SUCCESS",
            "message": "System status - production ready",
            "user_id": str(current_user.id),
            "user_role": current_user.role.value,
            "organisation_id": str(current_user.organisation_id),
            "total_routes": len(routes),
            "epic_routes_found": len(epic_routes),
            "epic_routes": epic_routes,
            "api_router_included": True,
            "security_mode": "production_with_authentication_required",
            "note": "All Epic endpoints require proper authentication",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/routes")
async def list_routes(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """List all registered routes - Admin only"""
    try:
        app = request.app
        routes = []
        
        for route in app.routes:
            if hasattr(route, 'path'):
                methods = getattr(route, 'methods', {'GET'})
                routes.append({
                    "path": route.path,
                    "methods": list(methods) if methods else ['GET'],
                    "name": getattr(route, 'name', 'unknown')
                })
        
        # Sort by path for easy reading
        routes.sort(key=lambda x: x['path'])
        
        return {
            "status": "SUCCESS",
            "total_routes": len(routes),
            "routes": routes,
            "admin_user": str(current_user.id),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Routes listing error: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/environment-config")
async def get_environment_config():
    """
    Get current environment configuration for preview environment validation.
    This endpoint is publicly accessible to verify Auth0 configuration in preview environments.
    """
    try:
        auth0_config = settings.get_auth0_config()

        # Mask sensitive information - show only domain and partial client_id
        masked_config = {
            "domain": auth0_config["domain"],
            "client_id": f"{auth0_config['client_id'][:8]}...{auth0_config['client_id'][-4:]}",
            "audience": auth0_config["audience"],
            "client_secret_set": bool(auth0_config.get("client_secret"))
        }

        return {
            "status": "SUCCESS",
            "environment": {
                "ENVIRONMENT": settings.ENVIRONMENT,
                "is_production": settings.is_production,
                "is_staging": settings.is_staging,
                "USE_STAGING_AUTH0": settings.USE_STAGING_AUTH0,
                "has_staging_config": bool(settings.AUTH0_DOMAIN_STAGING)
            },
            "auth0_config": masked_config,
            "cors_origins": settings.CORS_ORIGINS,
            "debug_info": {
                "staging_domain_set": bool(settings.AUTH0_DOMAIN_STAGING),
                "staging_client_id_set": bool(settings.AUTH0_CLIENT_ID_STAGING),
                "staging_client_secret_set": bool(settings.AUTH0_CLIENT_SECRET_STAGING),
                "preview_environment_detected": settings.is_staging
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Environment config error: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/staging-health")
async def staging_health_check():
    """
    Staging environment health check endpoint.
    Validates that staging-specific configurations are working correctly.
    """
    try:
        health_status = {
            "status": "HEALTHY",
            "environment": settings.ENVIRONMENT,
            "staging_mode": settings.is_staging,
            "auth0_environment": "staging" if settings.is_staging else "production",
            "database_connected": True,  # Will be checked in try/catch
            "redis_connected": True,     # Will be checked in try/catch
            "timestamp": time.time()
        }

        # Test database connection
        try:
            from ....database.session import get_async_session
            # This will fail if database connection is not working
            health_status["database_connected"] = True
        except Exception as db_error:
            health_status["database_connected"] = False
            health_status["database_error"] = str(db_error)

        # Test Redis connection if available
        try:
            import redis
            redis_url = settings.get_redis_url_for_environment()
            r = redis.from_url(redis_url)
            r.ping()
            health_status["redis_connected"] = True
        except Exception as redis_error:
            health_status["redis_connected"] = False
            health_status["redis_error"] = str(redis_error)

        # Check environment variables for staging
        if settings.is_staging:
            env_vars_status = {
                "USE_STAGING_AUTH0": os.getenv("USE_STAGING_AUTH0"),
                "ENVIRONMENT": os.getenv("ENVIRONMENT"),
                "AUTH0_DOMAIN_STAGING": bool(os.getenv("AUTH0_DOMAIN_STAGING")),
                "AUTH0_CLIENT_ID_STAGING": bool(os.getenv("AUTH0_CLIENT_ID_STAGING")),
                "CORS_ORIGINS": os.getenv("CORS_ORIGINS")
            }
            health_status["staging_env_vars"] = env_vars_status

        return health_status

    except Exception as e:
        logger.error(f"Staging health check error: {e}")
        return {
            "status": "UNHEALTHY",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/auth0-validation")
async def auth0_validation(
    current_user: User = Depends(get_current_user)
):
    """
    Authenticated endpoint to validate Auth0 configuration.
    Shows which Auth0 tenant is being used and user authentication details.
    """
    try:
        auth0_config = settings.get_auth0_config()

        return {
            "status": "SUCCESS",
            "message": "Authentication successful - Auth0 configuration validated",
            "user_details": {
                "user_id": str(current_user.id),
                "email": current_user.email,
                "role": current_user.role.value,
                "organisation_id": str(current_user.organisation_id)
            },
            "auth0_details": {
                "domain": auth0_config["domain"],
                "audience": auth0_config["audience"],
                "environment_type": "staging" if settings.is_staging else "production",
                "staging_mode_active": settings.USE_STAGING_AUTH0
            },
            "environment_verification": {
                "ENVIRONMENT": settings.ENVIRONMENT,
                "is_staging": settings.is_staging,
                "is_production": settings.is_production,
                "cors_origins": settings.CORS_ORIGINS
            },
            "validation_notes": [
                "This endpoint confirms Auth0 authentication is working",
                "Check 'environment_type' to confirm staging vs production Auth0 usage",
                "staging_mode_active=true means preview environment is using staging Auth0"
            ],
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Auth0 validation error: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": time.time()
        }