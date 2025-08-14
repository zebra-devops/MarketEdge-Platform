"""
Health check utilities for Railway deployment validation.
Tests database and Redis connectivity over private network.
"""

import asyncio
import logging
from typing import Dict, Any
import asyncpg
import redis.asyncio as redis
from datetime import datetime
import time
from .config import settings

logger = logging.getLogger(__name__)

class HealthChecker:
    """Railway-specific health checker for database and Redis connectivity."""
    
    def __init__(self):
        self._db_pool = None
        self._redis_client = None
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """
        Test PostgreSQL connection over Railway's private network.
        Returns connection status, latency, and error details if any.
        """
        start_time = time.time()
        try:
            # Parse database URL to extract host info for debugging
            db_url_parts = settings.DATABASE_URL.replace("postgresql://", "").split("@")
            host_info = db_url_parts[1].split("/")[0] if len(db_url_parts) > 1 and "@" in settings.DATABASE_URL else "unknown"
            
            # Test connection with timeout and better error handling
            conn = await asyncpg.connect(
                settings.DATABASE_URL,
                server_settings={
                    'application_name': 'health_check'
                },
                timeout=15.0,  # Increased timeout for Railway
                command_timeout=10.0
            )
            
            # Test basic query
            await conn.execute("SELECT 1")
            await conn.close()
            
            latency = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "connected",
                "latency_ms": latency,
                "connection_type": "railway_private_network",
                "database_url_host": host_info,
                "database_url_scheme": "postgresql" if settings.DATABASE_URL.startswith("postgresql://") else "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "error": "Connection timeout (>15s)",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "connection_type": "railway_private_network",
                "database_url_host": host_info if 'host_info' in locals() else "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "connection_type": "railway_private_network",
                "database_url_host": host_info if 'host_info' in locals() else "unknown",
                "database_url_scheme": "postgresql" if settings.DATABASE_URL.startswith("postgresql://") else "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def check_redis_connection(self) -> Dict[str, Any]:
        """
        Test Redis connection using environment-aware configuration.
        Tests main Redis and conditionally tests rate limiting Redis if enabled.
        """
        results = {
            "main_redis": await self._test_redis_url(settings.get_redis_url_for_environment(), "main")
        }
        
        # Only test rate limiting Redis if rate limiting is enabled
        if settings.RATE_LIMIT_ENABLED:
            results["rate_limit_redis"] = await self._test_redis_url(settings.get_rate_limit_redis_url_for_environment(), "rate_limit")
        else:
            results["rate_limit_redis"] = {
                "status": "skipped",
                "reason": "Rate limiting is disabled (RATE_LIMIT_ENABLED=false)",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Overall status - consider rate limiting Redis only if it's enabled
        required_connections = ["main_redis"]
        if settings.RATE_LIMIT_ENABLED:
            required_connections.append("rate_limit_redis")
        
        all_connected = all(results[conn]["status"] == "connected" for conn in required_connections)
        
        return {
            "status": "connected" if all_connected else "error",
            "connections": results,
            "connection_type": "private_network",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _test_redis_url(self, redis_url: str, connection_name: str) -> Dict[str, Any]:
        """Test individual Redis URL connection."""
        start_time = time.time()
        client = None
        
        try:
            # Create Redis client with environment-appropriate settings
            conn_config = settings.get_redis_connection_config()
            client = redis.from_url(
                redis_url,
                **conn_config
            )
            
            # Test basic operations
            await client.ping()
            test_key = f"health_check:{connection_name}:{int(time.time())}"
            await client.set(test_key, "test_value", ex=60)  # 60 second expiry
            value = await client.get(test_key)
            await client.delete(test_key)
            
            latency = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "connected",
                "latency_ms": latency,
                "redis_host": redis_url.split("@")[1].split("/")[0] if "@" in redis_url else "unknown",
                "test_operations": ["ping", "set", "get", "delete"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "error": "Connection timeout (>10s)",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            if client:
                try:
                    await client.close()
                except:
                    pass
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for Railway deployment.
        Tests all service connections and returns detailed status.
        """
        start_time = time.time()
        
        try:
            # Run all checks concurrently
            db_check, redis_check = await asyncio.gather(
                self.check_database_connection(),
                self.check_redis_connection(),
                return_exceptions=True
            )
            
            # Handle exceptions from gather
            if isinstance(db_check, Exception):
                db_check = {
                    "status": "error",
                    "error": str(db_check),
                    "error_type": type(db_check).__name__
                }
            
            if isinstance(redis_check, Exception):
                redis_check = {
                    "status": "error", 
                    "error": str(redis_check),
                    "error_type": type(redis_check).__name__
                }
            
            # Overall health status
            db_healthy = db_check.get("status") == "connected"
            redis_healthy = redis_check.get("status") == "connected"
            overall_healthy = db_healthy and redis_healthy
            
            total_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "services": {
                    "database": db_check,
                    "redis": redis_check
                },
                "summary": {
                    "database_connected": db_healthy,
                    "redis_connected": redis_healthy,
                    "all_services_healthy": overall_healthy,
                    "total_check_time_ms": total_time
                },
                "environment": {
                    "railway_environment": settings.ENVIRONMENT,
                    "debug_mode": settings.DEBUG,
                    "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED
                },
                "network_info": {
                    "connection_type": "railway_private_network",
                    "database_host_info": "Railway PostgreSQL (private)",
                    "redis_host_info": "Railway Redis (private)"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "total_check_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global health checker instance
health_checker = HealthChecker()