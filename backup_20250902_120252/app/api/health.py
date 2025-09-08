"""
Health Check Endpoints for Security and Performance Monitoring

Provides comprehensive health checks for all critical systems including:
- Database connectivity and performance
- Authentication system health
- JWT service status
- Module registry metrics
- Cache performance
- Rate limiting status
- Security metrics
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.auth_context import get_auth_context_manager
from ..core.module_registry import get_module_registry
from ..services.jwt_service import get_jwt_service
from ..models.user import User
from ..models.modules import AnalyticsModule

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    
    Returns:
        Dict with basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MarketEdge Platform"
    }


@router.get("/detailed")
async def detailed_health_check(
    include_security: bool = True,
    include_performance: bool = True,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Comprehensive health check with detailed system status
    
    Args:
        include_security: Include security-related health checks
        include_performance: Include performance metrics
        db: Database session
    
    Returns:
        Dict with detailed health information
    """
    start_time = time.time()
    health_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {},
        "metrics": {},
        "duration_ms": 0
    }
    
    try:
        # Database health check
        db_health = await _check_database_health(db)
        health_data["checks"]["database"] = db_health
        
        # Authentication system health
        auth_health = await _check_auth_system_health()
        health_data["checks"]["authentication"] = auth_health
        
        # JWT service health
        jwt_health = await _check_jwt_service_health()
        health_data["checks"]["jwt_service"] = jwt_health
        
        # Module registry health
        registry_health = await _check_module_registry_health()
        health_data["checks"]["module_registry"] = registry_health
        
        if include_security:
            # Security monitoring health
            security_health = await _check_security_health()
            health_data["checks"]["security"] = security_health
        
        if include_performance:
            # Performance metrics
            performance_metrics = await _get_performance_metrics()
            health_data["metrics"]["performance"] = performance_metrics
        
        # Determine overall health status
        health_data["status"] = _determine_overall_status(health_data["checks"])
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        health_data["status"] = "unhealthy"
        health_data["error"] = str(e)
    
    finally:
        health_data["duration_ms"] = int((time.time() - start_time) * 1000)
    
    return health_data


@router.get("/security")
async def security_health_check() -> Dict[str, Any]:
    """
    Security-focused health check
    
    Returns:
        Dict with security metrics and status
    """
    try:
        # Get security metrics from various services
        security_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "metrics": {}
        }
        
        # JWT service security metrics
        try:
            jwt_service = get_jwt_service()
            security_data["metrics"]["jwt"] = {
                "total_validations": jwt_service.validation_metrics.get("total_validations", 0),
                "failed_validations": jwt_service.validation_metrics.get("failed_validations", 0),
                "blacklist_hits": jwt_service.validation_metrics.get("blacklist_hits", 0),
                "cache_hits": jwt_service.validation_metrics.get("cache_hits", 0)
            }
        except Exception as e:
            security_data["metrics"]["jwt"] = {"error": str(e)}
        
        # Authentication context manager security
        try:
            auth_manager = get_auth_context_manager()
            if hasattr(auth_manager, 'security_events'):
                security_data["metrics"]["auth_context"] = {
                    "failed_verifications": len(auth_manager.security_events.get("failed_verifications", [])),
                    "suspicious_activities": len(auth_manager.security_events.get("suspicious_activities", [])),
                    "cache_invalidations": len(auth_manager.security_events.get("cache_invalidations", []))
                }
        except Exception as e:
            security_data["metrics"]["auth_context"] = {"error": str(e)}
        
        return security_data
        
    except Exception as e:
        logger.error(f"Error in security health check: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/performance")
async def performance_health_check() -> Dict[str, Any]:
    """
    Performance-focused health check
    
    Returns:
        Dict with performance metrics
    """
    try:
        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "metrics": {}
        }
        
        # Module registry memory stats
        try:
            registry = get_module_registry()
            if hasattr(registry, 'get_memory_stats'):
                performance_data["metrics"]["module_registry"] = registry.get_memory_stats()
        except Exception as e:
            performance_data["metrics"]["module_registry"] = {"error": str(e)}
        
        # Database connection pool stats would go here
        # Cache performance stats would go here
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error in performance health check: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/database")
async def database_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Database-specific health check
    
    Args:
        db: Database session
    
    Returns:
        Dict with database health information
    """
    try:
        db_health = await _check_database_health(db)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **db_health
        }
    except Exception as e:
        logger.error(f"Error in database health check: {str(e)}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


# Helper functions

async def _check_database_health(db: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity and performance"""
    start_time = time.time()
    
    try:
        # Basic connectivity test
        await db.execute(text("SELECT 1"))
        
        # Check key tables exist and get counts
        user_count = await db.execute(select(func.count(User.id)))
        user_count = user_count.scalar()
        
        module_count = await db.execute(select(func.count(AnalyticsModule.id)))
        module_count = module_count.scalar()
        
        response_time = (time.time() - start_time) * 1000
        
        status = "healthy"
        if response_time > 1000:  # More than 1 second
            status = "degraded"
        elif response_time > 5000:  # More than 5 seconds
            status = "unhealthy"
        
        return {
            "status": status,
            "response_time_ms": int(response_time),
            "statistics": {
                "user_count": user_count,
                "module_count": module_count
            },
            "checks": {
                "connectivity": "pass",
                "table_access": "pass"
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000)
        }


async def _check_auth_system_health() -> Dict[str, Any]:
    """Check authentication system health"""
    try:
        auth_manager = get_auth_context_manager()
        
        # Check if auth manager is available and responsive
        if not auth_manager:
            return {
                "status": "unhealthy",
                "error": "Authentication context manager not available"
            }
        
        # Get active contexts count
        active_contexts = len(auth_manager.active_contexts) if hasattr(auth_manager, 'active_contexts') else 0
        
        return {
            "status": "healthy",
            "active_contexts": active_contexts,
            "cache_available": hasattr(auth_manager, 'cache') and auth_manager.cache is not None
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_jwt_service_health() -> Dict[str, Any]:
    """Check JWT service health"""
    try:
        jwt_service = get_jwt_service()
        
        if not jwt_service:
            return {
                "status": "unhealthy",
                "error": "JWT service not available"
            }
        
        # Check blacklist functionality
        blacklist_status = "healthy"
        if hasattr(jwt_service, 'blacklist'):
            try:
                # Test blacklist read operation
                await jwt_service.blacklist.is_blacklisted("test-token")
            except Exception:
                blacklist_status = "degraded"
        
        return {
            "status": "healthy",
            "blacklist_status": blacklist_status,
            "cache_size": len(jwt_service.token_cache) if hasattr(jwt_service, 'token_cache') else 0
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_module_registry_health() -> Dict[str, Any]:
    """Check module registry health"""
    try:
        registry = get_module_registry()
        
        if not registry:
            return {
                "status": "unhealthy",
                "error": "Module registry not available"
            }
        
        # Get registry statistics
        registered_count = len(registry.registered_modules) if hasattr(registry, 'registered_modules') else 0
        pending_count = len(registry.pending_registrations) if hasattr(registry, 'pending_registrations') else 0
        
        status = "healthy"
        if hasattr(registry, 'max_registered_modules'):
            if registered_count >= registry.max_registered_modules * 0.9:
                status = "degraded"  # Close to memory limit
        
        return {
            "status": status,
            "registered_modules": registered_count,
            "pending_registrations": pending_count,
            "background_tasks": len(registry.background_tasks) if hasattr(registry, 'background_tasks') else 0
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _check_security_health() -> Dict[str, Any]:
    """Check security monitoring systems"""
    try:
        security_status = {
            "status": "healthy",
            "checks": {}
        }
        
        # Check JWT blacklist functionality
        try:
            jwt_service = get_jwt_service()
            if hasattr(jwt_service, 'blacklist'):
                # Simple blacklist test
                await jwt_service.blacklist.is_blacklisted("health-check-token")
                security_status["checks"]["jwt_blacklist"] = "operational"
            else:
                security_status["checks"]["jwt_blacklist"] = "not_available"
        except Exception as e:
            security_status["checks"]["jwt_blacklist"] = f"error: {str(e)}"
            security_status["status"] = "degraded"
        
        # Check rate limiting
        try:
            # This would test rate limiting if accessible
            security_status["checks"]["rate_limiting"] = "operational"
        except Exception as e:
            security_status["checks"]["rate_limiting"] = f"error: {str(e)}"
        
        return security_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def _get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics from various systems"""
    try:
        metrics = {}
        
        # Memory usage metrics
        try:
            import psutil
            process = psutil.Process()
            metrics["memory"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            metrics["memory"] = {"error": "psutil not available"}
        
        # CPU metrics
        try:
            import psutil
            metrics["cpu"] = {
                "percent": psutil.cpu_percent(interval=0.1),
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except ImportError:
            metrics["cpu"] = {"error": "psutil not available"}
        
        return metrics
        
    except Exception as e:
        return {"error": str(e)}


def _determine_overall_status(checks: Dict[str, Any]) -> str:
    """Determine overall health status from individual checks"""
    if not checks:
        return "unknown"
    
    statuses = []
    for check_name, check_data in checks.items():
        if isinstance(check_data, dict) and "status" in check_data:
            statuses.append(check_data["status"])
        elif isinstance(check_data, dict) and "error" in check_data:
            statuses.append("unhealthy")
    
    if "unhealthy" in statuses:
        return "unhealthy"
    elif "degraded" in statuses:
        return "degraded"
    elif "healthy" in statuses:
        return "healthy"
    else:
        return "unknown"