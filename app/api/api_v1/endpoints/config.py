"""Configuration endpoints for environment-aware frontend configuration."""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.core.config import settings

router = APIRouter()


@router.get("/auth0")
async def get_auth0_config() -> Dict[str, Any]:
    """
    Get Auth0 configuration for the current environment.

    Returns environment-appropriate Auth0 configuration for frontend use.
    Automatically selects production or staging configuration based on environment.
    """
    auth0_config = settings.get_auth0_config()

    # Return only frontend-safe configuration (no secrets)
    return {
        "domain": auth0_config["domain"],
        "clientId": auth0_config["client_id"],
        "audience": auth0_config["audience"],
        "environment": settings.ENVIRONMENT,
        "isStaging": settings.is_staging,
        "isProduction": settings.is_production,
    }


@router.get("/environment")
async def get_environment_config() -> Dict[str, Any]:
    """
    Get general environment configuration.

    Returns environment information and feature flags for frontend use.
    """
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "isProduction": settings.is_production,
        "isStaging": settings.is_staging,
        "corsOrigins": settings.CORS_ORIGINS,
        "apiVersion": settings.API_V1_STR,
        "projectName": settings.PROJECT_NAME,
        "projectVersion": settings.PROJECT_VERSION,
    }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for staging/preview environments.

    Returns basic health status and environment information.
    """
    auth0_config = settings.get_auth0_config()

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "auth0_domain": auth0_config["domain"],
        "auth0_configured": bool(auth0_config["client_id"]),
        "staging_auth0": settings.is_staging,
    }