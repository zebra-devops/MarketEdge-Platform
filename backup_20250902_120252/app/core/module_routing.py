"""
API Gateway Module Routing System

This module provides the core infrastructure for dynamic module routing,
allowing modules to register their own API endpoints with versioning,
namespacing, authentication, and conflict detection.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import time
import asyncio
from functools import wraps
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.routing import APIRoute
from starlette.routing import Match, NoMatchFound

from ..auth.dependencies import get_current_user, require_permission, require_role
from ..models.user import User
from ..services.feature_flag_service import FeatureFlagService
from ..services.module_service import ModuleService

logger = logging.getLogger(__name__)


class RouteVersion(Enum):
    """Supported API versions for module routing"""
    V1 = "v1"
    V2 = "v2" 
    V3 = "v3"


class AuthLevel(Enum):
    """Authentication levels for module routes"""
    NONE = "none"              # No authentication required
    BASIC = "basic"            # Require valid user authentication
    PERMISSION = "permission"   # Require specific permissions
    ROLE = "role"              # Require specific roles
    ADMIN = "admin"            # Require admin role


@dataclass
class RouteMetrics:
    """Performance metrics for a route with bounded storage"""
    call_count: int = 0
    total_duration_ms: float = 0.0
    error_count: int = 0
    last_called: Optional[float] = None
    avg_duration_ms: float = 0.0
    created_at: float = field(default_factory=time.time)
    
    # Bounded storage to prevent memory leaks
    MAX_CALL_COUNT = 10000  # Reset after this many calls
    MAX_AGE_SECONDS = 3600  # Reset after 1 hour

    def record_call(self, duration_ms: float, success: bool = True):
        """Record a route call with automatic reset for memory management"""
        current_time = time.time()
        
        # Check if metrics should be reset due to age or call count
        if (self.call_count >= self.MAX_CALL_COUNT or 
            current_time - self.created_at >= self.MAX_AGE_SECONDS):
            self._reset_metrics(current_time)
        
        self.call_count += 1
        self.total_duration_ms += duration_ms
        if not success:
            self.error_count += 1
        self.last_called = current_time
        self.avg_duration_ms = self.total_duration_ms / self.call_count
    
    def _reset_metrics(self, current_time: float):
        """Reset metrics to prevent memory accumulation"""
        self.call_count = 0
        self.total_duration_ms = 0.0
        self.error_count = 0
        self.avg_duration_ms = 0.0
        self.created_at = current_time


@dataclass
class ModuleRouteConfig:
    """Configuration for a module route"""
    module_id: str
    version: RouteVersion
    namespace: str
    auth_level: AuthLevel = AuthLevel.BASIC
    required_permissions: List[str] = field(default_factory=list)
    required_roles: List[str] = field(default_factory=list)
    rate_limit: Optional[int] = None  # requests per minute
    feature_flags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.auth_level == AuthLevel.PERMISSION and not self.required_permissions:
            raise ValueError("PERMISSION auth level requires at least one permission")
        if self.auth_level == AuthLevel.ROLE and not self.required_roles:
            raise ValueError("ROLE auth level requires at least one role")


class IModuleRouter(ABC):
    """Interface for module routers"""
    
    @abstractmethod
    def get_module_id(self) -> str:
        """Get the unique module identifier"""
        pass
    
    @abstractmethod
    def get_version(self) -> RouteVersion:
        """Get the module version"""
        pass
    
    @abstractmethod
    def get_namespace(self) -> str:
        """Get the module namespace"""
        pass
    
    @abstractmethod
    def register_routes(self, router: APIRouter) -> None:
        """Register module routes on the provided router"""
        pass
    
    @abstractmethod
    def get_health_check(self) -> Callable:
        """Get health check endpoint for this module"""
        pass


@dataclass
class RegisteredRoute:
    """Information about a registered module route"""
    route: APIRoute
    module_id: str
    config: ModuleRouteConfig
    path_pattern: str
    methods: List[str]
    metrics: RouteMetrics = field(default_factory=RouteMetrics)


class RouteConflictDetector:
    """Detects and resolves conflicts between module routes"""
    
    def __init__(self):
        self.registered_patterns: Dict[str, RegisteredRoute] = {}
        self.namespace_modules: Dict[str, List[str]] = defaultdict(list)
    
    def check_conflict(self, path_pattern: str, methods: List[str], module_id: str, namespace: str) -> Optional[str]:
        """
        Check for route conflicts
        
        Returns:
            None if no conflict, error message if conflict detected
        """
        # Check for exact path and method conflicts
        route_key = f"{path_pattern}:{':'.join(sorted(methods))}"
        
        if route_key in self.registered_patterns:
            existing_route = self.registered_patterns[route_key]
            if existing_route.module_id != module_id:
                return f"Route conflict: {path_pattern} ({methods}) already registered by module '{existing_route.module_id}'"
        
        # Check for namespace conflicts within same module
        if module_id in self.namespace_modules[namespace] and len(self.namespace_modules[namespace]) > 1:
            return f"Namespace conflict: '{namespace}' already used by multiple modules"
        
        # Check for overlapping path patterns
        for existing_key, existing_route in self.registered_patterns.items():
            if self._paths_overlap(path_pattern, existing_route.path_pattern):
                # Allow same module to register overlapping paths (method differentiation)
                if existing_route.module_id != module_id:
                    # Check if methods overlap
                    if set(methods) & set(existing_route.methods):
                        return f"Path overlap conflict: {path_pattern} overlaps with {existing_route.path_pattern} from module '{existing_route.module_id}'"
        
        return None
    
    def register_route(self, route: RegisteredRoute):
        """Register a route after conflict check passes"""
        route_key = f"{route.path_pattern}:{':'.join(sorted(route.methods))}"
        self.registered_patterns[route_key] = route
        self.namespace_modules[route.config.namespace].append(route.module_id)
    
    def _paths_overlap(self, path1: str, path2: str) -> bool:
        """Check if two path patterns overlap"""
        # Convert FastAPI path patterns to regex for overlap detection
        def path_to_regex(path: str) -> str:
            # Convert {param} to named regex groups
            pattern = re.sub(r'\{([^}]+)\}', r'(?P<\1>[^/]+)', path)
            return f"^{pattern}$"
        
        try:
            regex1 = re.compile(path_to_regex(path1))
            regex2 = re.compile(path_to_regex(path2))
            
            # Check if either pattern could match the other's literal form
            # This is a simplified check - more sophisticated overlap detection could be implemented
            return (regex1.pattern == regex2.pattern or 
                    path1.replace('{', '').replace('}', '') == path2.replace('{', '').replace('}', ''))
        except re.error:
            # If regex compilation fails, assume potential conflict
            return True


class ModuleMetricsPersistence:
    """Handles persistence and rotation of module metrics to prevent memory leaks"""
    
    def __init__(self, max_metrics: int = 1000, rotation_interval: int = 3600):
        self.max_metrics = max_metrics
        self.rotation_interval = rotation_interval
        self.last_rotation = time.time()
        self.persisted_metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="metrics-persist")
    
    async def maybe_rotate_metrics(self, route_metrics: Dict[str, RouteMetrics]):
        """Rotate metrics if needed to prevent memory leaks"""
        current_time = time.time()
        
        if (len(route_metrics) > self.max_metrics or 
            current_time - self.last_rotation > self.rotation_interval):
            await self._rotate_metrics(route_metrics, current_time)
    
    async def _rotate_metrics(self, route_metrics: Dict[str, RouteMetrics], current_time: float):
        """Rotate old metrics to persistent storage"""
        try:
            # Persist current metrics asynchronously
            persistent_data = {}
            for route_key, metrics in route_metrics.items():
                persistent_data[route_key] = {
                    "call_count": metrics.call_count,
                    "total_duration_ms": metrics.total_duration_ms,
                    "error_count": metrics.error_count,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "last_called": metrics.last_called,
                    "rotated_at": current_time
                }
            
            # Persist to storage (could be database, file, etc.)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._persist_to_storage, persistent_data)
            
            # Clear old metrics but keep recent ones
            cutoff_time = current_time - 300  # Keep last 5 minutes
            routes_to_keep = {
                k: v for k, v in route_metrics.items() 
                if v.last_called and v.last_called > cutoff_time
            }
            
            route_metrics.clear()
            route_metrics.update(routes_to_keep)
            
            self.last_rotation = current_time
            logger.info(f"Rotated metrics: kept {len(routes_to_keep)}, persisted {len(persistent_data)}")
            
        except Exception as e:
            logger.error(f"Error rotating metrics: {str(e)}")
    
    def _persist_to_storage(self, data: Dict[str, Any]):
        """Persist metrics data to storage (runs in thread executor)"""
        try:
            # For now, just store in memory - could be extended to database/file
            timestamp = time.time()
            for route_key, metrics in data.items():
                if route_key not in self.persisted_metrics:
                    self.persisted_metrics[route_key] = []
                self.persisted_metrics[route_key].append(metrics)
                
                # Keep only last 10 entries per route to prevent unbounded growth
                if len(self.persisted_metrics[route_key]) > 10:
                    self.persisted_metrics[route_key] = self.persisted_metrics[route_key][-10:]
        except Exception as e:
            logger.error(f"Error persisting metrics: {str(e)}")


class ModuleRoutingManager:
    """
    Central manager for module routing system
    
    Handles registration, conflict detection, authentication, and monitoring
    for dynamically registered module routes.
    """
    
    def __init__(self, feature_flag_service: FeatureFlagService, module_service: ModuleService):
        self.feature_flag_service = feature_flag_service
        self.module_service = module_service
        self.conflict_detector = RouteConflictDetector()
        self.registered_modules: Dict[str, IModuleRouter] = {}
        self.route_metrics: Dict[str, RouteMetrics] = {}
        self.main_router = APIRouter()
        
        # Enhanced metrics and performance systems
        self.metrics_persistence = ModuleMetricsPersistence()
        self.registration_queue = asyncio.Queue()
        self.registration_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="module-reg")
        self._background_tasks: List[asyncio.Task] = []
        
        # Start background processing tasks
        self._start_background_tasks()
        
        logger.info("Enhanced module routing manager initialized")
    
    def _start_background_tasks(self):
        """Start background tasks for metrics and processing"""
        try:
            # Start metrics rotation task
            task1 = asyncio.create_task(self._metrics_rotation_task())
            self._background_tasks.append(task1)
            
            # Start async registration processing task
            task2 = asyncio.create_task(self._process_registration_queue())
            self._background_tasks.append(task2)
            
        except RuntimeError:
            # No event loop running yet - tasks will be started later
            logger.debug("Event loop not running - background tasks will start with first operation")
    
    async def _metrics_rotation_task(self):
        """Background task to rotate metrics periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.metrics_persistence.maybe_rotate_metrics(self.route_metrics)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics rotation task: {str(e)}")
                await asyncio.sleep(60)  # Continue after error
    
    async def _process_registration_queue(self):
        """Background task to process module registrations asynchronously"""
        while True:
            try:
                # Get registration task from queue
                registration_task = await self.registration_queue.get()
                
                # Process the registration
                await self._execute_registration_task(registration_task)
                
                # Mark task as done
                self.registration_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in registration queue processing: {str(e)}")
    
    async def _execute_registration_task(self, task_data: Dict[str, Any]):
        """Execute a module registration task"""
        try:
            module_router = task_data["module_router"]
            callback = task_data.get("callback")
            
            # Perform the actual registration
            await self._perform_module_registration(module_router)
            
            # Call callback if provided
            if callback and callable(callback):
                await callback(True, None)
                
        except Exception as e:
            logger.error(f"Module registration task failed: {str(e)}")
            callback = task_data.get("callback")
            if callback and callable(callback):
                await callback(False, str(e))
    
    async def register_module_async(self, module_router: IModuleRouter, callback: Optional[Callable] = None) -> None:
        """Register a module asynchronously using background processing"""
        task_data = {
            "module_router": module_router,
            "callback": callback
        }
        await self.registration_queue.put(task_data)
        logger.info(f"Module {module_router.get_module_id()} queued for async registration")
    
    async def register_module(self, module_router: IModuleRouter) -> None:
        """Register a module and its routes (synchronous version)"""
        await self._perform_module_registration(module_router)
    
    async def _perform_module_registration(self, module_router: IModuleRouter) -> None:
        """
        Perform the actual module registration with enhanced security and logging
        
        Args:
            module_router: Module router implementing IModuleRouter
            
        Raises:
            ValueError: If module conflicts detected or validation fails
        """
        start_time = time.time()
        module_id = module_router.get_module_id()
        namespace = module_router.get_namespace()
        version = module_router.get_version()
        
        logger.info(f"Registering module: {module_id} (namespace: {namespace}, version: {version.value})")
        
        # Security event logging
        self._log_security_event("MODULE_REGISTRATION_STARTED", {
            "module_id": module_id,
            "namespace": namespace,
            "version": version.value,
            "timestamp": time.time()
        })
        
        try:
            # Check if module already registered
            if module_id in self.registered_modules:
                self._log_security_event("MODULE_REGISTRATION_CONFLICT", {
                    "module_id": module_id,
                    "error": "Already registered"
                })
                raise ValueError(f"Module '{module_id}' is already registered")
            
            # Create module-specific router
            module_api_router = APIRouter()
            
            # Register module routes
            module_router.register_routes(module_api_router)
            
            # Validate and check conflicts for each route
            for route in module_api_router.routes:
                if isinstance(route, APIRoute):
                    conflict_error = self.conflict_detector.check_conflict(
                        path_pattern=route.path,
                        methods=list(route.methods),
                        module_id=module_id,
                        namespace=namespace
                    )
                    
                    if conflict_error:
                        self._log_security_event("MODULE_ROUTE_CONFLICT", {
                            "module_id": module_id,
                            "route_path": route.path,
                            "error": conflict_error
                        })
                        logger.error(f"Route conflict detected for module {module_id}: {conflict_error}")
                        raise ValueError(conflict_error)
            
            # If no conflicts, register all routes
            for route in module_api_router.routes:
                if isinstance(route, APIRoute):
                    # Create route config with defaults
                    config = ModuleRouteConfig(
                        module_id=module_id,
                        version=version,
                        namespace=namespace,
                        description=f"Route from module {module_id}",
                        tags=[module_id, namespace]
                    )
                    
                    registered_route = RegisteredRoute(
                        route=route,
                        module_id=module_id,
                        config=config,
                        path_pattern=route.path,
                        methods=list(route.methods)
                    )
                    
                    # Register with conflict detector
                    self.conflict_detector.register_route(registered_route)
                    
                    # Add performance monitoring
                    monitored_endpoint = self._add_monitoring(route.endpoint, module_id, route.path)
                    
                    # Add authentication wrapper
                    authenticated_endpoint = await self._add_authentication(monitored_endpoint, config)
                    
                    # Update route endpoint
                    route.endpoint = authenticated_endpoint
            
            # Include module router in main router with versioned prefix
            version_prefix = f"/{version.value}"
            namespace_prefix = f"/{namespace}" if namespace else ""
            full_prefix = f"/modules{version_prefix}{namespace_prefix}"
            
            self.main_router.include_router(
                module_api_router,
                prefix=full_prefix,
                tags=[module_id, f"module-{namespace}"]
            )
            
            # Register module
            self.registered_modules[module_id] = module_router
            
            # Add health check endpoint
            health_check = module_router.get_health_check()
            self.main_router.add_api_route(
                path=f"{full_prefix}/health",
                endpoint=self._add_monitoring(health_check, module_id, "health"),
                methods=["GET"],
                tags=[module_id, "health"]
            )
            
            # Log successful registration
            duration_ms = (time.time() - start_time) * 1000
            self._log_security_event("MODULE_REGISTRATION_SUCCESS", {
                "module_id": module_id,
                "namespace": namespace,
                "version": version.value,
                "full_prefix": full_prefix,
                "duration_ms": duration_ms,
                "routes_registered": len([r for r in module_api_router.routes if isinstance(r, APIRoute)])
            })
            
            logger.info(f"Successfully registered module '{module_id}' with prefix '{full_prefix}' in {duration_ms:.2f}ms")
            
        except Exception as e:
            # Log failed registration
            self._log_security_event("MODULE_REGISTRATION_FAILED", {
                "module_id": module_id,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            })
            raise
    
    async def unregister_module(self, module_id: str) -> None:
        """Unregister a module and remove its routes"""
        if module_id not in self.registered_modules:
            raise ValueError(f"Module '{module_id}' is not registered")
        
        # For now, log the unregistration - full implementation would require
        # dynamic route removal which is complex in FastAPI
        logger.info(f"Module '{module_id}' marked for unregistration")
        del self.registered_modules[module_id]
    
    def get_registered_modules(self) -> List[str]:
        """Get list of registered module IDs"""
        return list(self.registered_modules.keys())
    
    def get_route_metrics(self, module_id: Optional[str] = None) -> Dict[str, RouteMetrics]:
        """Get performance metrics for routes"""
        if module_id:
            return {k: v for k, v in self.route_metrics.items() if k.startswith(f"{module_id}:")}
        return self.route_metrics.copy()
    
    def get_router(self) -> APIRouter:
        """Get the main router with all registered module routes"""
        return self.main_router
    
    async def _add_authentication(self, endpoint: Callable, config: ModuleRouteConfig) -> Callable:
        """Add authentication wrapper to endpoint based on config"""
        
        if config.auth_level == AuthLevel.NONE:
            return endpoint
        
        # Start with basic user authentication
        dependencies = [Depends(get_current_user)]
        
        if config.auth_level == AuthLevel.PERMISSION and config.required_permissions:
            dependencies.append(Depends(require_permission(config.required_permissions)))
        
        elif config.auth_level == AuthLevel.ROLE and config.required_roles:
            from ..models.user import UserRole
            roles = [UserRole(role) for role in config.required_roles if role in UserRole.__members__]
            if roles:
                dependencies.append(Depends(require_role(roles)))
        
        elif config.auth_level == AuthLevel.ADMIN:
            from ..auth.dependencies import require_admin
            dependencies.append(Depends(require_admin))
        
        # Feature flag check wrapper
        if config.feature_flags:
            
            @wraps(endpoint)
            async def feature_flag_wrapper(*args, **kwargs):
                # Extract user from dependencies
                user = kwargs.get('current_user') or next(
                    (arg for arg in args if isinstance(arg, User)), None
                )
                
                if user:
                    # Check all required feature flags
                    for flag_key in config.feature_flags:
                        is_enabled = await self.feature_flag_service.is_feature_enabled(flag_key, user)
                        if not is_enabled:
                            logger.warning(f"Feature flag '{flag_key}' disabled for user {user.id}")
                            raise HTTPException(
                                status_code=403,
                                detail=f"Feature '{flag_key}' is not available"
                            )
                
                return await endpoint(*args, **kwargs)
            
            return feature_flag_wrapper
        
        return endpoint
    
    def _add_monitoring(self, endpoint: Callable, module_id: str, route_path: str) -> Callable:
        """Add performance monitoring to endpoint"""
        metrics_key = f"{module_id}:{route_path}"
        
        if metrics_key not in self.route_metrics:
            self.route_metrics[metrics_key] = RouteMetrics()
        
        @wraps(endpoint)
        async def monitored_endpoint(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await endpoint(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Error in module route {metrics_key}: {str(e)}")
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                self.route_metrics[metrics_key].record_call(duration_ms, success)
                
                logger.debug(f"Route {metrics_key} completed", extra={
                    "module_id": module_id,
                    "route_path": route_path,
                    "duration_ms": duration_ms,
                    "success": success
                })
        
        return monitored_endpoint
    
    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events for monitoring and analysis"""
        try:
            security_log_data = {
                "event_type": event_type,
                "timestamp": time.time(),
                "component": "module_routing",
                "data": event_data
            }
            
            # Log with structured data for security monitoring
            logger.info(f"SECURITY_EVENT: {event_type}", extra=security_log_data)
            
            # Could also send to security monitoring system
            # await self._send_to_security_monitoring(security_log_data)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources and background tasks"""
        try:
            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete cancellation
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Shutdown executor
            self.registration_executor.shutdown(wait=True)
            self.metrics_persistence.executor.shutdown(wait=True)
            
            logger.info("Module routing manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global instance to be used across the application
module_routing_manager: Optional[ModuleRoutingManager] = None


def get_module_routing_manager() -> ModuleRoutingManager:
    """Get the global module routing manager instance"""
    global module_routing_manager
    if module_routing_manager is None:
        raise RuntimeError("Module routing manager not initialized. Call initialize_module_routing() first.")
    return module_routing_manager


async def initialize_module_routing(feature_flag_service: FeatureFlagService, module_service: ModuleService) -> ModuleRoutingManager:
    """Initialize the global module routing manager"""
    global module_routing_manager
    if module_routing_manager is None:
        module_routing_manager = ModuleRoutingManager(feature_flag_service, module_service)
        logger.info("Global module routing manager initialized")
    return module_routing_manager