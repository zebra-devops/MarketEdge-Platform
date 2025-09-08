"""
Lazy Initialization Architecture for MarketEdge Platform
Replaces emergency mode with intelligent service bootstrapping
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Import startup metrics for performance tracking
try:
    from .startup_metrics import startup_monitor, track_startup_metric
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("Startup metrics not available")
    METRICS_AVAILABLE = False
    def track_startup_metric(name: str, metadata=None):
        def decorator(func):
            return func
        return decorator


class ServiceStatus(Enum):
    """Service initialization status"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing" 
    INITIALIZED = "initialized"
    FAILED = "failed"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceMetrics:
    """Service initialization metrics"""
    name: str
    status: ServiceStatus = ServiceStatus.NOT_INITIALIZED
    initialization_start: Optional[float] = None
    initialization_duration: Optional[float] = None
    failure_count: int = 0
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    health_check_count: int = 0
    last_health_check: Optional[float] = None
    dependencies: list = field(default_factory=list)
    # Circuit breaker fields
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: float = 300.0  # 5 minutes
    circuit_breaker_last_failure: Optional[float] = None
    circuit_breaker_consecutive_failures: int = 0


class LazyStartupManager:
    """
    Manages lazy initialization of platform services
    Ensures <5 second cold start with graceful degradation
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceMetrics] = {}
        self._initializers: Dict[str, Callable] = {}
        self._health_checkers: Dict[str, Callable] = {}
        self._initialization_lock = threading.Lock()
        self._startup_start_time = time.time()
        self._cold_start_threshold = 5.0  # seconds
        self._initialized_services = set()
        
    def register_service(
        self,
        name: str,
        initializer: Callable,
        health_checker: Optional[Callable] = None,
        dependencies: Optional[list] = None,
        max_retries: int = 3
    ):
        """Register a service for lazy initialization"""
        with self._initialization_lock:
            self._services[name] = ServiceMetrics(
                name=name,
                max_retries=max_retries,
                dependencies=dependencies or []
            )
            self._initializers[name] = initializer
            if health_checker:
                self._health_checkers[name] = health_checker
                
        logger.info(f"Registered service '{name}' for lazy initialization")
    
    async def initialize_service(self, service_name: str) -> bool:
        """Initialize a specific service lazily with performance tracking and circuit breaker"""
        if service_name in self._initialized_services:
            return True
            
        if service_name not in self._services:
            logger.error(f"Service '{service_name}' not registered")
            return False
            
        service = self._services[service_name]
        
        # Circuit breaker check
        if service.status == ServiceStatus.CIRCUIT_OPEN:
            current_time = time.time()
            if (service.circuit_breaker_last_failure and 
                current_time - service.circuit_breaker_last_failure < service.circuit_breaker_timeout):
                logger.warning(f"Service '{service_name}' circuit breaker is open. Waiting {service.circuit_breaker_timeout - (current_time - service.circuit_breaker_last_failure):.1f}s before retry")
                return False
            else:
                # Reset circuit breaker after timeout
                logger.info(f"Circuit breaker timeout expired for '{service_name}'. Resetting to allow retry.")
                service.status = ServiceStatus.NOT_INITIALIZED
                service.circuit_breaker_consecutive_failures = 0
        
        # Check if already being initialized
        if service.status == ServiceStatus.INITIALIZING:
            # Wait for initialization to complete
            while service.status == ServiceStatus.INITIALIZING:
                await asyncio.sleep(0.1)
            return service.status == ServiceStatus.INITIALIZED
            
        # Check dependencies first
        for dep in service.dependencies:
            if not await self.initialize_service(dep):
                logger.warning(f"Failed to initialize dependency '{dep}' for '{service_name}'")
                service.status = ServiceStatus.DEGRADED
                return False
        
        # Start performance tracking
        if METRICS_AVAILABLE:
            startup_monitor.start_metric(f"service_init_{service_name}", {
                "service": service_name,
                "dependencies": service.dependencies,
                "retry_count": service.retry_count
            })
        
        service.status = ServiceStatus.INITIALIZING
        service.initialization_start = time.time()
        
        try:
            initializer = self._initializers[service_name]
            
            # Handle both sync and async initializers
            if asyncio.iscoroutinefunction(initializer):
                await initializer()
            else:
                # Run sync initializer in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, initializer)
                
            service.status = ServiceStatus.INITIALIZED
            service.initialization_duration = time.time() - service.initialization_start
            service.circuit_breaker_consecutive_failures = 0  # Reset circuit breaker on success
            self._initialized_services.add(service_name)
            
            # End performance tracking on success
            if METRICS_AVAILABLE:
                startup_monitor.end_metric(f"service_init_{service_name}", success=True)
            
            logger.info(f"Service '{service_name}' initialized in {service.initialization_duration:.3f}s")
            return True
            
        except Exception as e:
            service.status = ServiceStatus.FAILED
            service.last_error = str(e)
            service.failure_count += 1
            service.initialization_duration = time.time() - service.initialization_start
            service.circuit_breaker_consecutive_failures += 1
            service.circuit_breaker_last_failure = time.time()
            
            # End performance tracking on failure
            if METRICS_AVAILABLE:
                startup_monitor.end_metric(f"service_init_{service_name}", success=False, error_message=str(e))
            
            logger.error(f"Failed to initialize service '{service_name}': {e}")
            
            # Circuit breaker logic - open circuit if failure threshold exceeded
            if service.circuit_breaker_consecutive_failures >= service.circuit_breaker_failure_threshold:
                service.status = ServiceStatus.CIRCUIT_OPEN
                logger.error(f"Circuit breaker opened for service '{service_name}' after {service.circuit_breaker_consecutive_failures} consecutive failures. Service will be unavailable for {service.circuit_breaker_timeout}s")
                return False
            
            # Retry logic (only if circuit is not open)
            if service.retry_count < service.max_retries:
                service.retry_count += 1
                logger.info(f"Retrying initialization of '{service_name}' ({service.retry_count}/{service.max_retries})")
                await asyncio.sleep(1)  # Brief delay before retry
                return await self.initialize_service(service_name)
            
            return False
    
    async def health_check_service(self, service_name: str) -> bool:
        """Check health of a service"""
        if service_name not in self._services:
            return False
            
        service = self._services[service_name]
        
        if service_name not in self._health_checkers:
            # No health checker defined, assume healthy if initialized
            return service.status == ServiceStatus.INITIALIZED
        
        try:
            health_checker = self._health_checkers[service_name]
            
            if asyncio.iscoroutinefunction(health_checker):
                is_healthy = await health_checker()
            else:
                loop = asyncio.get_event_loop()
                is_healthy = await loop.run_in_executor(None, health_checker)
                
            service.health_check_count += 1
            service.last_health_check = time.time()
            
            if not is_healthy and service.status == ServiceStatus.INITIALIZED:
                service.status = ServiceStatus.DEGRADED
                logger.warning(f"Service '{service_name}' health check failed - marked as degraded")
                
            return is_healthy
            
        except Exception as e:
            service.last_error = str(e)
            service.status = ServiceStatus.DEGRADED
            logger.error(f"Health check failed for service '{service_name}': {e}")
            return False
    
    @asynccontextmanager
    async def ensure_service(self, service_name: str):
        """Context manager to ensure service is available before use"""
        success = await self.initialize_service(service_name)
        if not success:
            logger.warning(f"Service '{service_name}' not available - entering degraded mode")
            
        try:
            yield success
        finally:
            # Could add cleanup logic here if needed
            pass
    
    def get_service_status(self, service_name: str) -> Optional[ServiceMetrics]:
        """Get detailed status of a service"""
        return self._services.get(service_name)
    
    def get_startup_metrics(self) -> Dict[str, Any]:
        """Get comprehensive startup metrics with performance monitoring"""
        current_time = time.time()
        total_startup_time = current_time - self._startup_start_time
        
        initialized_count = sum(1 for s in self._services.values() 
                              if s.status == ServiceStatus.INITIALIZED)
        failed_count = sum(1 for s in self._services.values() 
                         if s.status == ServiceStatus.FAILED)
        degraded_count = sum(1 for s in self._services.values() 
                           if s.status == ServiceStatus.DEGRADED)
        circuit_open_count = sum(1 for s in self._services.values() 
                               if s.status == ServiceStatus.CIRCUIT_OPEN)
        
        cold_start_success = total_startup_time < self._cold_start_threshold
        
        base_metrics = {
            "total_startup_time": round(total_startup_time, 3),
            "cold_start_threshold": self._cold_start_threshold,
            "cold_start_success": cold_start_success,
            "total_services": len(self._services),
            "initialized_services": initialized_count,
            "failed_services": failed_count,
            "degraded_services": degraded_count,
            "circuit_open_services": circuit_open_count,
            "service_details": {
                name: {
                    "status": service.status.value,
                    "initialization_duration": service.initialization_duration,
                    "failure_count": service.failure_count,
                    "retry_count": service.retry_count,
                    "last_error": service.last_error,
                    "health_check_count": service.health_check_count,
                    "dependencies": service.dependencies,
                    "circuit_breaker_consecutive_failures": service.circuit_breaker_consecutive_failures,
                    "circuit_breaker_last_failure": service.circuit_breaker_last_failure
                }
                for name, service in self._services.items()
            },
            "startup_timestamp": self._startup_start_time,
            "current_timestamp": current_time
        }
        
        # Add comprehensive performance monitoring if available
        if METRICS_AVAILABLE:
            try:
                performance_summary = startup_monitor.get_startup_summary()
                base_metrics.update({
                    "performance_monitoring": performance_summary,
                    "render_metrics": startup_monitor.get_render_specific_metrics()
                })
            except Exception as e:
                logger.error(f"Failed to get performance monitoring data: {e}")
                base_metrics["performance_monitoring_error"] = str(e)
        
        return base_metrics
    
    async def graceful_shutdown(self):
        """Gracefully shutdown all services"""
        logger.info("Starting graceful shutdown of lazy services...")
        
        # Could add service-specific shutdown logic here
        for service_name in self._initialized_services:
            try:
                # Services would register shutdown handlers if needed
                logger.info(f"Shutting down service: {service_name}")
            except Exception as e:
                logger.error(f"Error shutting down service '{service_name}': {e}")
                
        self._initialized_services.clear()
        logger.info("Graceful shutdown completed")


# Global lazy startup manager instance
lazy_startup_manager = LazyStartupManager()


# Service initialization functions with performance tracking
@track_startup_metric("database_initialization", {"service_type": "database", "priority": "critical"})
def _initialize_database():
    """Initialize database connections with performance tracking"""
    try:
        from .database import engine
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            conn.commit()
        logger.info("Database service initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def _check_database_health():
    """Check database health"""
    try:
        from .database import engine
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except Exception:
        return False


@track_startup_metric("redis_initialization", {"service_type": "cache", "priority": "high"})
def _initialize_redis():
    """Initialize Redis connection with performance tracking"""
    try:
        from .database import redis_client
        redis_client.ping()
        logger.info("Redis service initialized successfully")
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        raise


def _check_redis_health():
    """Check Redis health"""
    try:
        from .database import redis_client
        redis_client.ping()
        return True
    except Exception:
        return False


# Register core services
lazy_startup_manager.register_service(
    "database",
    _initialize_database,
    _check_database_health,
    max_retries=2
)

lazy_startup_manager.register_service(
    "redis", 
    _initialize_redis,
    _check_redis_health,
    max_retries=2
)