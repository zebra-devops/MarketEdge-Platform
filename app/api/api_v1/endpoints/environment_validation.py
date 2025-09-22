from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import redis
from ....core.database import get_db
from ....core.logging import get_logger
from ....auth.auth0 import auth0_client
from sqlalchemy import text

logger = get_logger(__name__)
router = APIRouter()

@router.get("/environment")
async def get_environment_info(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Environment validation endpoint for preview environments.
    Returns non-sensitive environment configuration for validation.
    """
    try:
        env_info = {
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "use_staging_auth0": os.getenv("USE_STAGING_AUTH0", "false").lower() == "true",
            "node_env": os.getenv("NODE_ENV", "unknown"),
            "render_service_type": os.getenv("RENDER_SERVICE_TYPE", "unknown"),
            "render_service_name": os.getenv("RENDER_SERVICE_NAME", "unknown"),
            "render_git_branch": os.getenv("RENDER_GIT_BRANCH", "unknown"),
            "render_git_commit": os.getenv("RENDER_GIT_COMMIT", "unknown")[:8] if os.getenv("RENDER_GIT_COMMIT") else "unknown",
        }

        # Auth0 configuration (non-sensitive)
        auth0_info = {
            "domain": auth0_client.domain if hasattr(auth0_client, 'domain') else "not_configured",
            "client_id": auth0_client.client_id[:8] + "..." if hasattr(auth0_client, 'client_id') and auth0_client.client_id else "not_configured",
            "audience": auth0_client.audience if hasattr(auth0_client, 'audience') else "not_configured"
        }

        # Database connectivity test
        database_status = {
            "connected": False,
            "error": None
        }
        try:
            result = db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            database_status["connected"] = row[0] == 1 if row else False
        except Exception as e:
            database_status["error"] = str(e)[:100]  # Truncate error message

        # Redis connectivity test
        redis_status = {
            "connected": False,
            "error": None
        }
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                redis_status["connected"] = True
            else:
                redis_status["error"] = "REDIS_URL not configured"
        except Exception as e:
            redis_status["error"] = str(e)[:100]  # Truncate error message

        # Health metrics
        health_metrics = {
            "timestamp": "2025-09-22T00:00:00Z",  # This will be dynamic in real implementation
            "uptime_seconds": 0,  # Would calculate actual uptime
            "memory_usage_mb": 0,  # Would get actual memory usage
            "cpu_usage_percent": 0  # Would get actual CPU usage
        }

        return {
            "status": "success",
            "environment": env_info,
            "auth0": auth0_info,
            "database": database_status,
            "redis": redis_status,
            "health": health_metrics,
            "preview_validation": {
                "is_preview": env_info["render_service_type"] == "preview",
                "branch_name": env_info["render_git_branch"],
                "staging_auth0": env_info["use_staging_auth0"],
                "environment_type": env_info["environment"]
            }
        }

    except Exception as e:
        logger.error(f"Environment validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Environment validation failed: {str(e)}"
        )

@router.get("/health-detailed")
async def get_detailed_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check for preview environment validation.
    """
    try:
        checks = {}

        # Database health
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            checks["database"] = {"status": "unhealthy", "message": f"Database error: {str(e)[:100]}"}

        # Auth0 configuration health
        try:
            if hasattr(auth0_client, 'domain') and auth0_client.domain:
                checks["auth0"] = {"status": "healthy", "message": "Auth0 client configured"}
            else:
                checks["auth0"] = {"status": "unhealthy", "message": "Auth0 client not properly configured"}
        except Exception as e:
            checks["auth0"] = {"status": "unhealthy", "message": f"Auth0 error: {str(e)[:100]}"}

        # Redis health
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                r = redis.from_url(redis_url)
                r.ping()
                checks["redis"] = {"status": "healthy", "message": "Redis connection successful"}
            else:
                checks["redis"] = {"status": "warning", "message": "Redis URL not configured"}
        except Exception as e:
            checks["redis"] = {"status": "unhealthy", "message": f"Redis error: {str(e)[:100]}"}

        # Overall health
        overall_status = "healthy"
        if any(check["status"] == "unhealthy" for check in checks.values()):
            overall_status = "unhealthy"
        elif any(check["status"] == "warning" for check in checks.values()):
            overall_status = "warning"

        return {
            "status": overall_status,
            "timestamp": "2025-09-22T00:00:00Z",
            "checks": checks,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "preview_environment": os.getenv("RENDER_SERVICE_TYPE") == "preview"
        }

    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": "2025-09-22T00:00:00Z",
            "error": f"Health check failed: {str(e)[:100]}",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "preview_environment": os.getenv("RENDER_SERVICE_TYPE") == "preview"
        }

@router.get("/cors-test")
async def cors_test():
    """
    Simple endpoint to test CORS configuration in preview environments.
    """
    return {
        "message": "CORS test successful",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "timestamp": "2025-09-22T00:00:00Z",
        "preview": os.getenv("RENDER_SERVICE_TYPE") == "preview"
    }