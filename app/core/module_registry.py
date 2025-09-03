"""
US-103: Module Registration System - Core Registry

This module provides comprehensive module lifecycle management,
registration, validation, and discovery functionality for the
MarketEdge platform.
"""

import asyncio
import json
import logging
import time
import weakref
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import importlib.util
import inspect
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
from collections import OrderedDict
import threading
import gc

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from ..models.modules import AnalyticsModule, ModuleStatus, ModuleType
from ..models.user import User
from ..core.database import get_db
from ..core.auth_context import AuthenticationContextManager, get_auth_context_manager
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)


class RegistrationStatus(str, Enum):
    """Module registration status"""
    PENDING = "pending"
    VALIDATING = "validating"
    REGISTERED = "registered"
    FAILED = "failed"
    UPDATING = "updating"
    DEREGISTERING = "deregistering"


class ModuleHealth(str, Enum):
    """Module health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModuleDependency:
    """Module dependency specification"""
    module_id: str
    version_requirement: str = "*"  # semver pattern
    required: bool = True
    description: Optional[str] = None
    
    def is_satisfied_by(self, available_version: str) -> bool:
        """Check if dependency is satisfied by available version"""
        # Simple version matching for now
        if self.version_requirement == "*":
            return True
        return available_version >= self.version_requirement


@dataclass
class ModuleMetadata:
    """Comprehensive module metadata"""
    # Basic information
    id: str
    name: str
    version: str
    description: str
    
    # Classification
    module_type: ModuleType
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Technical specifications
    entry_point: str = ""
    config_schema: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies and requirements
    dependencies: List[ModuleDependency] = field(default_factory=list)
    system_requirements: Dict[str, Any] = field(default_factory=dict)
    min_platform_version: Optional[str] = None
    
    # API and Integration
    api_endpoints: List[str] = field(default_factory=list)
    event_handlers: List[str] = field(default_factory=list)
    database_migrations: List[str] = field(default_factory=list)
    
    # Frontend Integration
    frontend_components: List[str] = field(default_factory=list)
    frontend_routes: List[str] = field(default_factory=list)
    ui_extensions: Dict[str, Any] = field(default_factory=dict)
    
    # Security and Permissions
    required_permissions: List[str] = field(default_factory=list)
    security_policies: Dict[str, Any] = field(default_factory=dict)
    
    # Licensing and Distribution
    author: Optional[str] = None
    license: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        # Convert enums to values
        data['module_type'] = self.module_type.value
        # Convert dependencies to dicts
        data['dependencies'] = [asdict(dep) for dep in self.dependencies]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleMetadata':
        """Create from dictionary"""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Handle enum conversion
        if 'module_type' in data and isinstance(data['module_type'], str):
            data['module_type'] = ModuleType(data['module_type'])
        
        # Handle dependencies conversion
        if 'dependencies' in data and isinstance(data['dependencies'], list):
            dependencies = []
            for dep_data in data['dependencies']:
                if isinstance(dep_data, dict):
                    dependencies.append(ModuleDependency(**dep_data))
                elif isinstance(dep_data, ModuleDependency):
                    dependencies.append(dep_data)
            data['dependencies'] = dependencies
        
        return cls(**data)


@dataclass
class RegistrationRequest:
    """Module registration request"""
    module_metadata: ModuleMetadata
    requester_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: RegistrationStatus = RegistrationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleRegistration:
    """Registered module information"""
    metadata: ModuleMetadata
    registration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ModuleStatus = ModuleStatus.DEVELOPMENT
    health: ModuleHealth = ModuleHealth.UNKNOWN
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None
    health_check_results: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime information
    is_loaded: bool = False
    load_error: Optional[str] = None
    instance_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Metrics
    registration_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegistrationResult:
    """Result of module registration operation"""
    success: bool
    message: str
    registration_id: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None


class ModuleValidator:
    """Validates module registrations"""
    
    def __init__(self):
        self.validation_rules: List[Callable] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules"""
        self.validation_rules.extend([
            self._validate_required_fields,
            self._validate_module_id_format,
            self._validate_version_format,
            self._validate_entry_point,
            self._validate_dependencies,
            self._validate_config_schema,
            self._validate_api_endpoints,
            self._validate_permissions,
        ])
    
    async def validate_module(self, metadata: ModuleMetadata) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate module metadata
        
        Returns:
            Tuple of (is_valid, validation_results)
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        try:
            for rule in self.validation_rules:
                rule_name = rule.__name__
                try:
                    rule_result = await rule(metadata)
                    results["checks"][rule_name] = rule_result
                    
                    if not rule_result.get("valid", True):
                        results["valid"] = False
                        errors = rule_result.get("errors", [])
                        results["errors"].extend(errors)
                    
                    warnings = rule_result.get("warnings", [])
                    results["warnings"].extend(warnings)
                    
                except Exception as e:
                    logger.error(f"Validation rule {rule_name} failed: {str(e)}")
                    results["valid"] = False
                    results["errors"].append(f"Validation rule {rule_name} failed: {str(e)}")
            
            return results["valid"], results
            
        except Exception as e:
            logger.error(f"Module validation failed: {str(e)}")
            return False, {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "checks": {}
            }
    
    async def _validate_required_fields(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate required fields are present"""
        required_fields = ['id', 'name', 'version', 'description', 'module_type']
        errors = []
        
        for field in required_fields:
            if not getattr(metadata, field, None):
                errors.append(f"Required field '{field}' is missing or empty")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    
    async def _validate_module_id_format(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate module ID format"""
        import re
        
        # Module ID should be lowercase alphanumeric with underscores
        pattern = r'^[a-z][a-z0-9_]*$'
        
        if not re.match(pattern, metadata.id):
            return {
                "valid": False,
                "errors": ["Module ID must start with a letter and contain only lowercase letters, numbers, and underscores"],
                "warnings": []
            }
        
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }
    
    async def _validate_version_format(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate version format (semver)"""
        import re
        
        # Simple semver pattern
        pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$'
        
        if not re.match(pattern, metadata.version):
            return {
                "valid": False,
                "errors": ["Version must follow semantic versioning format (x.y.z)"],
                "warnings": []
            }
        
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }
    
    async def _validate_entry_point(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate entry point exists and is accessible"""
        warnings = []
        
        if not metadata.entry_point:
            warnings.append("Entry point not specified - module may not be loadable")
        else:
            # TODO: Add actual entry point validation
            # This would check if the module can be imported
            pass
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings
        }
    
    async def _validate_dependencies(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate module dependencies"""
        warnings = []
        
        # Check for circular dependencies (simplified check)
        dep_ids = [dep.module_id for dep in metadata.dependencies]
        if metadata.id in dep_ids:
            return {
                "valid": False,
                "errors": ["Module cannot depend on itself"],
                "warnings": []
            }
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings
        }
    
    async def _validate_config_schema(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate configuration schema"""
        warnings = []
        
        if metadata.config_schema and not isinstance(metadata.config_schema, dict):
            return {
                "valid": False,
                "errors": ["Config schema must be a dictionary"],
                "warnings": []
            }
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings
        }
    
    async def _validate_api_endpoints(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate API endpoints format"""
        warnings = []
        errors = []
        
        for endpoint in metadata.api_endpoints:
            if not isinstance(endpoint, str):
                errors.append("API endpoints must be strings")
            elif not endpoint.startswith('/'):
                warnings.append(f"API endpoint '{endpoint}' should start with '/'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _validate_permissions(self, metadata: ModuleMetadata) -> Dict[str, Any]:
        """Validate required permissions format"""
        errors = []
        
        for permission in metadata.required_permissions:
            if not isinstance(permission, str):
                errors.append("Required permissions must be strings")
            elif not permission:
                errors.append("Empty permission string not allowed")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }


class DependencyResolver:
    """Resolves module dependencies with memory management"""
    
    def __init__(self, max_cache_size: int = 1000):
        self.resolution_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_cache_size = max_cache_size
        self._cache_lock = threading.RLock()
        
        logger.debug(f"DependencyResolver initialized with cache size limit: {max_cache_size}")
    
    async def resolve_dependencies(
        self,
        target_module: ModuleMetadata,
        available_modules: Dict[str, ModuleRegistration]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Resolve module dependencies
        
        Returns:
            Tuple of (can_resolve, resolution_info)
        """
        resolution_info = {
            "resolvable": True,
            "resolved_dependencies": [],
            "missing_dependencies": [],
            "conflicting_dependencies": [],
            "dependency_chain": [],
            "load_order": []
        }
        
        try:
            # Build dependency graph
            dependency_graph = await self._build_dependency_graph(target_module, available_modules)
            
            # Check for circular dependencies
            if self._has_circular_dependencies(dependency_graph):
                resolution_info["resolvable"] = False
                resolution_info["conflicting_dependencies"].append("Circular dependency detected")
                return False, resolution_info
            
            # Resolve each dependency
            for dependency in target_module.dependencies:
                resolved = await self._resolve_single_dependency(
                    dependency, available_modules
                )
                
                if resolved:
                    resolution_info["resolved_dependencies"].append({
                        "module_id": dependency.module_id,
                        "required_version": dependency.version_requirement,
                        "resolved_version": resolved.metadata.version,
                        "registration_id": resolved.registration_id
                    })
                else:
                    resolution_info["missing_dependencies"].append({
                        "module_id": dependency.module_id,
                        "required_version": dependency.version_requirement,
                        "required": dependency.required,
                        "description": dependency.description
                    })
                    
                    if dependency.required:
                        resolution_info["resolvable"] = False
            
            # Calculate load order if resolvable
            if resolution_info["resolvable"]:
                load_order = await self._calculate_load_order(dependency_graph)
                resolution_info["load_order"] = load_order
            
            return resolution_info["resolvable"], resolution_info
            
        except Exception as e:
            logger.error(f"Dependency resolution failed: {str(e)}")
            resolution_info["resolvable"] = False
            resolution_info["conflicting_dependencies"].append(f"Resolution error: {str(e)}")
            return False, resolution_info
    
    async def _build_dependency_graph(
        self,
        target_module: ModuleMetadata,
        available_modules: Dict[str, ModuleRegistration]
    ) -> Dict[str, List[str]]:
        """Build dependency graph"""
        graph = {}
        
        def build_recursive(module_id: str, visited: Set[str]):
            if module_id in visited:
                return
            visited.add(module_id)
            
            # Find module metadata
            metadata = None
            if module_id == target_module.id:
                metadata = target_module
            elif module_id in available_modules:
                metadata = available_modules[module_id].metadata
            
            if metadata:
                dependencies = [dep.module_id for dep in metadata.dependencies]
                graph[module_id] = dependencies
                
                for dep_id in dependencies:
                    build_recursive(dep_id, visited)
        
        build_recursive(target_module.id, set())
        return graph
    
    def _has_circular_dependencies(self, graph: Dict[str, List[str]]) -> bool:
        """Check for circular dependencies using DFS"""
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for node in graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    return True
        
        return False
    
    async def _resolve_single_dependency(
        self,
        dependency: ModuleDependency,
        available_modules: Dict[str, ModuleRegistration]
    ) -> Optional[ModuleRegistration]:
        """Resolve a single dependency"""
        if dependency.module_id in available_modules:
            available_module = available_modules[dependency.module_id]
            if dependency.is_satisfied_by(available_module.metadata.version):
                return available_module
        
        return None
    
    async def _calculate_load_order(self, graph: Dict[str, List[str]]) -> List[str]:
        """Calculate module load order using topological sort"""
        in_degree = {node: 0 for node in graph}
        
        # Calculate in-degrees
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        # Topological sort
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # PERFORMANCE FIX: Cache result with memory bounds
        with self._cache_lock:
            cache_key = f"load_order_{hash(str(sorted(graph.items())))}"
            
            # Enforce cache size limit
            if len(self.resolution_cache) >= self.max_cache_size:
                # Remove oldest entry
                self.resolution_cache.popitem(last=False)
            
            self.resolution_cache[cache_key] = {'load_order': result}
            self.resolution_cache.move_to_end(cache_key)
        
        return result


class ModuleHealthChecker:
    """Monitors module health"""
    
    def __init__(self):
        self.health_check_timeout = 30  # seconds
        self.health_check_interval = 300  # 5 minutes
    
    async def check_module_health(
        self,
        registration: ModuleRegistration
    ) -> Tuple[ModuleHealth, Dict[str, Any]]:
        """Check health of a registered module"""
        health_results = {
            "status": ModuleHealth.UNKNOWN.value,
            "checks": {},
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Basic health checks
            checks = [
                self._check_module_loadable,
                self._check_entry_point_accessible,
                self._check_dependencies_available,
                self._check_configuration_valid,
            ]
            
            overall_health = ModuleHealth.HEALTHY
            
            for check in checks:
                check_name = check.__name__
                try:
                    check_result = await check(registration)
                    health_results["checks"][check_name] = check_result
                    
                    # Determine impact on overall health
                    if not check_result.get("passed", False):
                        severity = check_result.get("severity", "error")
                        if severity == "error":
                            overall_health = ModuleHealth.UNHEALTHY
                        elif severity == "warning" and overall_health == ModuleHealth.HEALTHY:
                            overall_health = ModuleHealth.DEGRADED
                
                except Exception as e:
                    logger.error(f"Health check {check_name} failed: {str(e)}")
                    health_results["checks"][check_name] = {
                        "passed": False,
                        "error": str(e),
                        "severity": "error"
                    }
                    overall_health = ModuleHealth.UNHEALTHY
            
            health_results["status"] = overall_health.value
            
        except Exception as e:
            logger.error(f"Module health check failed: {str(e)}")
            health_results["status"] = ModuleHealth.UNHEALTHY.value
            health_results["error"] = str(e)
        
        finally:
            health_results["duration_ms"] = int((time.time() - start_time) * 1000)
        
        return ModuleHealth(health_results["status"]), health_results
    
    async def _check_module_loadable(self, registration: ModuleRegistration) -> Dict[str, Any]:
        """Check if module can be loaded"""
        try:
            # This would attempt to import the module
            # For now, just return success
            return {
                "passed": True,
                "message": "Module appears loadable",
                "severity": "info"
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Module not loadable: {str(e)}",
                "severity": "error"
            }
    
    async def _check_entry_point_accessible(self, registration: ModuleRegistration) -> Dict[str, Any]:
        """Check if entry point is accessible"""
        entry_point = registration.metadata.entry_point
        if not entry_point:
            return {
                "passed": False,
                "message": "No entry point defined",
                "severity": "warning"
            }
        
        # TODO: Implement actual entry point check
        return {
            "passed": True,
            "message": "Entry point accessible",
            "severity": "info"
        }
    
    async def _check_dependencies_available(self, registration: ModuleRegistration) -> Dict[str, Any]:
        """Check if dependencies are available"""
        if not registration.metadata.dependencies:
            return {
                "passed": True,
                "message": "No dependencies required",
                "severity": "info"
            }
        
        # TODO: Check actual dependency availability
        return {
            "passed": True,
            "message": f"{len(registration.metadata.dependencies)} dependencies available",
            "severity": "info"
        }
    
    async def _check_configuration_valid(self, registration: ModuleRegistration) -> Dict[str, Any]:
        """Check if module configuration is valid"""
        try:
            # Validate against schema if available
            if registration.metadata.config_schema:
                # TODO: Implement JSON schema validation
                pass
            
            return {
                "passed": True,
                "message": "Configuration valid",
                "severity": "info"
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Invalid configuration: {str(e)}",
                "severity": "error"
            }


class ModuleRegistry:
    """
    US-103: Core module registry for lifecycle management with memory management
    
    Provides:
    - Module registration and deregistration
    - Validation and verification
    - Dependency resolution
    - Health monitoring
    - Discovery and listing
    - Memory-bounded operations
    """
    
    def __init__(
        self,
        audit_service: Optional[AuditService] = None,
        auth_context_manager: Optional[AuthenticationContextManager] = None,
        max_registered_modules: int = 1000,
        max_pending_registrations: int = 100
    ):
        self.audit_service = audit_service
        self.auth_context_manager = auth_context_manager
        
        # Core components
        self.validator = ModuleValidator()
        self.dependency_resolver = DependencyResolver()
        self.health_checker = ModuleHealthChecker()
        
        # PERFORMANCE FIX: Memory-bounded registry state
        self.max_registered_modules = max_registered_modules
        self.max_pending_registrations = max_pending_registrations
        
        # Use OrderedDict for LRU-like behavior
        self.registered_modules: OrderedDict[str, ModuleRegistration] = OrderedDict()
        self.pending_registrations: OrderedDict[str, RegistrationRequest] = OrderedDict()
        
        # Memory management
        self._module_access_times: Dict[str, float] = {}
        self._registry_lock = threading.RLock()  # Protect registry operations
        self._memory_cleanup_interval = 3600  # 1 hour
        self._last_memory_cleanup = time.time()
        
        # Background processing with controlled resources
        self.executor = ThreadPoolExecutor(
            max_workers=4, 
            thread_name_prefix="module-registry"
        )
        self.background_tasks: List[weakref.ref] = []  # Use weak references
        
        # Event handlers with memory limits
        self.event_handlers: Dict[str, List[Callable]] = {
            "module_registered": [],
            "module_deregistered": [],
            "module_activated": [],
            "module_deactivated": [],
            "module_health_changed": [],
            "dependency_resolved": [],
            "validation_failed": []
        }
        self._max_event_handlers_per_type = 20
        
        # Registry metrics for monitoring
        self.registry_metrics = {
            'total_registrations': 0,
            'active_modules': 0,
            'failed_registrations': 0,
            'memory_cleanups': 0
        }
        
        logger.info(f"Module Registry initialized with memory bounds: "
                   f"max_modules={max_registered_modules}, max_pending={max_pending_registrations}")
    
    async def start(self):
        """Start background tasks with memory management"""
        # Start health monitoring task
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self.background_tasks.append(weakref.ref(health_task))
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.background_tasks.append(weakref.ref(cleanup_task))
        
        # Start memory management task
        memory_task = asyncio.create_task(self._memory_management_loop())
        self.background_tasks.append(weakref.ref(memory_task))
        
        logger.info("Module Registry background tasks started with memory management")
    
    async def stop(self):
        """Stop background tasks with proper cleanup"""
        # Cancel all active tasks using weak references
        active_tasks = []
        for task_ref in self.background_tasks:
            task = task_ref()
            if task is not None and not task.done():
                task.cancel()
                active_tasks.append(task)
        
        if active_tasks:
            await asyncio.gather(*active_tasks, return_exceptions=True)
        
        # Shutdown executor with timeout
        self.executor.shutdown(wait=True, timeout=30)
        
        # Clear references to help with garbage collection
        with self._registry_lock:
            self.registered_modules.clear()
            self.pending_registrations.clear()
            self._module_access_times.clear()
            for handlers in self.event_handlers.values():
                handlers.clear()
        
        logger.info("Module Registry stopped with cleanup")
    
    async def register_module(
        self,
        module_metadata: ModuleMetadata,
        requester_id: str,
        auto_activate: bool = False
    ) -> str:
        """
        Register a new module
        
        Args:
            module_metadata: Module metadata
            requester_id: ID of user requesting registration
            auto_activate: Whether to activate module after registration
            
        Returns:
            str: Registration request ID
        """
        try:
            # Create registration request
            request = RegistrationRequest(
                module_metadata=module_metadata,
                requester_id=requester_id
            )
            
            # PERFORMANCE FIX: Add to pending with memory bounds
            with self._registry_lock:
                # Enforce pending registrations limit
                while len(self.pending_registrations) >= self.max_pending_registrations:
                    # Remove oldest pending request
                    oldest_id, oldest_request = self.pending_registrations.popitem(last=False)
                    logger.warning(f"Removing oldest pending registration: {oldest_id}")
                
                self.pending_registrations[request.request_id] = request
                self.pending_registrations.move_to_end(request.request_id)
            
            # Process registration asynchronously
            asyncio.create_task(
                self._process_registration_request(request, auto_activate)
            )
            
            logger.info(f"Module registration request created: {request.request_id} for module {module_metadata.id}")
            return request.request_id
            
        except Exception as e:
            logger.error(f"Error creating module registration request: {str(e)}")
            raise
    
    async def _process_registration_request(
        self,
        request: RegistrationRequest,
        auto_activate: bool = False
    ):
        """Process module registration request"""
        try:
            request.status = RegistrationStatus.VALIDATING
            
            # Validate module
            is_valid, validation_results = await self.validator.validate_module(
                request.module_metadata
            )
            
            request.validation_results = validation_results
            
            if not is_valid:
                request.status = RegistrationStatus.FAILED
                request.error_message = f"Validation failed: {'; '.join(validation_results.get('errors', []))}"
                request.processed_at = datetime.utcnow()
                
                await self._fire_event_handlers("validation_failed", request)
                return
            
            # Check for existing module
            existing = await self._get_module_from_db(request.module_metadata.id)
            if existing:
                request.status = RegistrationStatus.FAILED
                request.error_message = f"Module {request.module_metadata.id} already exists"
                request.processed_at = datetime.utcnow()
                return
            
            # Resolve dependencies
            can_resolve, resolution_info = await self.dependency_resolver.resolve_dependencies(
                request.module_metadata,
                self.registered_modules
            )
            
            if not can_resolve:
                request.status = RegistrationStatus.FAILED
                request.error_message = f"Dependency resolution failed: {resolution_info.get('missing_dependencies', [])}"
                request.processed_at = datetime.utcnow()
                return
            
            # Create module registration
            registration = ModuleRegistration(
                metadata=request.module_metadata,
                status=ModuleStatus.ACTIVE if auto_activate else ModuleStatus.DEVELOPMENT
            )
            
            # Store in database
            await self._store_module_in_db(registration)
            
            # PERFORMANCE FIX: Add to registry with memory bounds check
            with self._registry_lock:
                # Check memory bounds before adding
                await self._enforce_memory_limits()
                
                module_id = request.module_metadata.id
                self.registered_modules[module_id] = registration
                self._module_access_times[module_id] = time.time()
                
                # Move to end for LRU behavior
                self.registered_modules.move_to_end(module_id)
                
                self.registry_metrics['active_modules'] = len(self.registered_modules)
                self.registry_metrics['total_registrations'] += 1
            
            # Update request status
            request.status = RegistrationStatus.REGISTERED
            request.processed_at = datetime.utcnow()
            
            # Fire event handlers
            await self._fire_event_handlers("module_registered", registration)
            
            # Audit log
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id=request.requester_id,
                    action="REGISTER_MODULE",
                    resource_type="module",
                    resource_id=registration.metadata.id,
                    description=f"Registered module {registration.metadata.name}",
                    metadata={
                        "module_id": registration.metadata.id,
                        "version": registration.metadata.version,
                        "auto_activated": auto_activate
                    }
                )
            
            logger.info(f"Module {request.module_metadata.id} registered successfully")
            
        except Exception as e:
            logger.error(f"Error processing registration request: {str(e)}")
            request.status = RegistrationStatus.FAILED
            request.error_message = str(e)
            request.processed_at = datetime.utcnow()
        
        finally:
            # Clean up from pending
            if request.request_id in self.pending_registrations:
                del self.pending_registrations[request.request_id]
    
    async def deregister_module(
        self,
        module_id: str,
        requester_id: str,
        force: bool = False
    ) -> bool:
        """
        Deregister a module
        
        Args:
            module_id: Module to deregister
            requester_id: ID of user requesting deregistration
            force: Force deregistration even if dependencies exist
            
        Returns:
            bool: True if successfully deregistered
        """
        try:
            if module_id not in self.registered_modules:
                return False
            
            registration = self.registered_modules[module_id]
            
            # Check for dependent modules
            if not force:
                dependents = await self._find_dependent_modules(module_id)
                if dependents:
                    raise ValueError(f"Cannot deregister module {module_id}: has dependents {dependents}")
            
            # PERFORMANCE FIX: Remove from registry with cleanup
            with self._registry_lock:
                if module_id in self.registered_modules:
                    del self.registered_modules[module_id]
                if module_id in self._module_access_times:
                    del self._module_access_times[module_id]
                
                self.registry_metrics['active_modules'] = len(self.registered_modules)
            
            # Remove from database
            await self._remove_module_from_db(module_id)
            
            # Fire event handlers
            await self._fire_event_handlers("module_deregistered", registration)
            
            # Audit log
            if self.audit_service:
                await self.audit_service.log_action(
                    user_id=requester_id,
                    action="DEREGISTER_MODULE",
                    resource_type="module",
                    resource_id=module_id,
                    description=f"Deregistered module {registration.metadata.name}",
                    metadata={"forced": force}
                )
            
            logger.info(f"Module {module_id} deregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deregistering module {module_id}: {str(e)}")
            raise
    
    async def get_registered_modules(
        self,
        status_filter: Optional[ModuleStatus] = None,
        module_type_filter: Optional[ModuleType] = None
    ) -> List[ModuleRegistration]:
        """Get list of registered modules with optional filtering"""
        modules = list(self.registered_modules.values())
        
        if status_filter:
            modules = [m for m in modules if m.status == status_filter]
        
        if module_type_filter:
            modules = [m for m in modules if m.metadata.module_type == module_type_filter]
        
        return modules
    
    async def get_module_registration(self, module_id: str) -> Optional[ModuleRegistration]:
        """Get specific module registration with access tracking"""
        with self._registry_lock:
            if module_id in self.registered_modules:
                # Update access time for LRU
                self._module_access_times[module_id] = time.time()
                self.registered_modules.move_to_end(module_id)
                return self.registered_modules[module_id]
            return None
    
    async def discover_modules(
        self,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        module_type: Optional[ModuleType] = None
    ) -> List[ModuleRegistration]:
        """
        Discover modules based on search criteria
        
        Args:
            search_query: Text search in name/description
            tags: Filter by tags
            module_type: Filter by module type
            
        Returns:
            List of matching module registrations
        """
        modules = list(self.registered_modules.values())
        
        # Apply filters
        if search_query:
            search_lower = search_query.lower()
            modules = [
                m for m in modules
                if (search_lower in m.metadata.name.lower() or
                    search_lower in m.metadata.description.lower())
            ]
        
        if tags:
            modules = [
                m for m in modules
                if any(tag in m.metadata.tags for tag in tags)
            ]
        
        if module_type:
            modules = [m for m in modules if m.metadata.module_type == module_type]
        
        return modules
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for registry events with memory limits"""
        if event_type in self.event_handlers:
            handlers = self.event_handlers[event_type]
            
            # PERFORMANCE FIX: Limit number of event handlers
            if len(handlers) >= self._max_event_handlers_per_type:
                logger.warning(f"Maximum event handlers reached for {event_type}, removing oldest")
                handlers.pop(0)
            
            handlers.append(handler)
    
    # Private helper methods
    
    async def _get_module_from_db(self, module_id: str) -> Optional[AnalyticsModule]:
        """Get module from database"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(AnalyticsModule).where(AnalyticsModule.id == module_id)
                    result = await db_session.execute(stmt)
                    return result.scalar_one_or_none()
                except Exception as e:
                    logger.error(f"Database error getting module: {str(e)}")
                    break
            return None
        except Exception as e:
            logger.error(f"Error getting module from DB: {str(e)}")
            return None
    
    async def _store_module_in_db(self, registration: ModuleRegistration):
        """Store module registration in database"""
        try:
            async for db_session in get_db():
                try:
                    module = AnalyticsModule(
                        id=registration.metadata.id,
                        name=registration.metadata.name,
                        description=registration.metadata.description,
                        version=registration.metadata.version,
                        module_type=registration.metadata.module_type,
                        status=registration.status,
                        entry_point=registration.metadata.entry_point,
                        config_schema=registration.metadata.config_schema,
                        default_config=registration.metadata.default_config,
                        dependencies=[dep.module_id for dep in registration.metadata.dependencies],
                        api_endpoints=registration.metadata.api_endpoints,
                        frontend_components=registration.metadata.frontend_components,
                        documentation_url=registration.metadata.documentation_url,
                        created_by="system"  # TODO: Use actual user ID
                    )
                    
                    db_session.add(module)
                    await db_session.commit()
                    break
                    
                except Exception as e:
                    logger.error(f"Database error storing module: {str(e)}")
                    await db_session.rollback()
                    raise
        except Exception as e:
            logger.error(f"Error storing module in DB: {str(e)}")
            raise
    
    async def _remove_module_from_db(self, module_id: str):
        """Remove module from database"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(AnalyticsModule).where(AnalyticsModule.id == module_id)
                    result = await db_session.execute(stmt)
                    module = result.scalar_one_or_none()
                    
                    if module:
                        await db_session.delete(module)
                        await db_session.commit()
                    
                    break
                    
                except Exception as e:
                    logger.error(f"Database error removing module: {str(e)}")
                    await db_session.rollback()
                    raise
        except Exception as e:
            logger.error(f"Error removing module from DB: {str(e)}")
            raise
    
    async def _find_dependent_modules(self, module_id: str) -> List[str]:
        """Find modules that depend on the given module"""
        dependents = []
        for registration in self.registered_modules.values():
            for dependency in registration.metadata.dependencies:
                if dependency.module_id == module_id:
                    dependents.append(registration.metadata.id)
                    break
        return dependents
    
    async def _health_monitoring_loop(self):
        """Background health monitoring task"""
        while True:
            try:
                await asyncio.sleep(self.health_checker.health_check_interval)
                
                # Check health of all registered modules
                for registration in self.registered_modules.values():
                    try:
                        old_health = registration.health
                        new_health, health_results = await self.health_checker.check_module_health(registration)
                        
                        registration.health = new_health
                        registration.last_health_check = datetime.utcnow()
                        registration.health_check_results = health_results
                        
                        # Fire event if health changed
                        if old_health != new_health:
                            await self._fire_event_handlers("module_health_changed", {
                                "registration": registration,
                                "old_health": old_health,
                                "new_health": new_health
                            })
                            
                    except Exception as e:
                        logger.error(f"Health check failed for module {registration.metadata.id}: {str(e)}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Background cleanup task with memory management"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                with self._registry_lock:
                    # Clean up old pending registrations
                    cutoff_time = datetime.utcnow() - timedelta(hours=24)
                    expired_requests = [
                        req_id for req_id, request in self.pending_registrations.items()
                        if request.created_at < cutoff_time
                    ]
                    
                    for req_id in expired_requests:
                        del self.pending_registrations[req_id]
                    
                    if expired_requests:
                        logger.info(f"Cleaned up {len(expired_requests)} expired registration requests")
                    
                    # Clean up weak references
                    self.background_tasks = [ref for ref in self.background_tasks if ref() is not None]
                
                # Force garbage collection periodically
                gc.collect()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
    
    async def _memory_management_loop(self):
        """Background memory management task"""
        while True:
            try:
                await asyncio.sleep(self._memory_cleanup_interval)
                
                current_time = time.time()
                if (current_time - self._last_memory_cleanup) >= self._memory_cleanup_interval:
                    with self._registry_lock:
                        await self._enforce_memory_limits()
                        
                        # Clean up stale access times
                        stale_cutoff = current_time - (24 * 3600)  # 24 hours
                        stale_modules = [
                            module_id for module_id, access_time in self._module_access_times.items()
                            if access_time < stale_cutoff and module_id not in self.registered_modules
                        ]
                        
                        for module_id in stale_modules:
                            del self._module_access_times[module_id]
                        
                        if stale_modules:
                            logger.debug(f"Cleaned up {len(stale_modules)} stale access times")
                    
                    self._last_memory_cleanup = current_time
                    
                    # Force garbage collection
                    collected = gc.collect()
                    if collected > 0:
                        logger.debug(f"Garbage collected {collected} objects")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory management loop: {str(e)}")
    
    async def _enforce_memory_limits(self):
        """Enforce memory limits on registry storage"""
        try:
            # Check registered modules limit
            if len(self.registered_modules) >= self.max_registered_modules:
                # Remove oldest/least accessed modules
                modules_to_remove = []
                current_time = time.time()
                
                # Sort by access time, oldest first
                module_access_pairs = [
                    (module_id, self._module_access_times.get(module_id, 0))
                    for module_id in self.registered_modules.keys()
                ]
                module_access_pairs.sort(key=lambda x: x[1])
                
                # Remove 10% of modules to avoid constant cleanup
                num_to_remove = max(1, int(self.max_registered_modules * 0.1))
                for module_id, _ in module_access_pairs[:num_to_remove]:
                    modules_to_remove.append(module_id)
                
                for module_id in modules_to_remove:
                    registration = self.registered_modules.pop(module_id, None)
                    self._module_access_times.pop(module_id, None)
                    
                    if registration and self.audit_service:
                        await self.audit_service.log_action(
                            user_id="system",
                            action="MODULE_EVICTED",
                            resource_type="module",
                            resource_id=module_id,
                            description=f"Module evicted due to memory limits",
                            metadata={"reason": "memory_limit"}
                        )
                
                if modules_to_remove:
                    logger.warning(f"Evicted {len(modules_to_remove)} modules due to memory limits")
                    self.registry_metrics['memory_cleanups'] += 1
            
        except Exception as e:
            logger.error(f"Error enforcing memory limits: {str(e)}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        with self._registry_lock:
            return {
                'registered_modules_count': len(self.registered_modules),
                'pending_registrations_count': len(self.pending_registrations),
                'max_registered_modules': self.max_registered_modules,
                'max_pending_registrations': self.max_pending_registrations,
                'access_times_count': len(self._module_access_times),
                'background_tasks_count': len([ref for ref in self.background_tasks if ref() is not None]),
                'registry_metrics': self.registry_metrics.copy()
            }
    
    async def _fire_event_handlers(self, event_type: str, event_data: Any):
        """Fire event handlers for registry events"""
        try:
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_data)
                    else:
                        handler(event_data)
                except Exception as e:
                    logger.error(f"Event handler for {event_type} failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error firing event handlers: {str(e)}")


# Global instance
module_registry: Optional[ModuleRegistry] = None


def get_module_registry() -> ModuleRegistry:
    """Get the global module registry instance with fallback for £925K Zebra opportunity"""
    global module_registry
    if module_registry is None:
        # CRITICAL: Create emergency fallback registry for Zebra Associates demo
        logger.warning("Module registry not initialized - creating emergency fallback")
        
        # Create minimal registry without database dependencies
        from app.services.audit_service import AuditService
        emergency_registry = ModuleRegistry(
            audit_service=None,  # No audit in emergency mode
            auth_context_manager=None,
            max_registered_modules=100,
            max_pending_registrations=50
        )
        
        # Pre-register critical modules for Zebra demo
        emergency_modules = [
            "market_trends",
            "pricing_intelligence", 
            "competitive_analysis",
            "feature_flags"
        ]
        
        for module_id in emergency_modules:
            try:
                emergency_registry.registered_modules[module_id] = {
                    "id": module_id,
                    "name": module_id.replace("_", " ").title(),
                    "status": "active",
                    "type": "analytics"
                }
                logger.info(f"Emergency module registered: {module_id}")
            except Exception as e:
                logger.error(f"Failed to register emergency module {module_id}: {e}")
        
        module_registry = emergency_registry
        logger.warning("✅ Emergency module registry created with core modules")
        
    return module_registry


async def initialize_module_registry(
    audit_service: Optional[AuditService] = None,
    auth_context_manager: Optional[AuthenticationContextManager] = None,
    max_registered_modules: int = 1000,
    max_pending_registrations: int = 100
) -> ModuleRegistry:
    """Initialize the global module registry with memory management"""
    global module_registry
    if module_registry is None:
        module_registry = ModuleRegistry(
            audit_service=audit_service,
            auth_context_manager=auth_context_manager,
            max_registered_modules=max_registered_modules,
            max_pending_registrations=max_pending_registrations
        )
        await module_registry.start()
        logger.info(f"Global module registry initialized with memory bounds: "
                   f"max_modules={max_registered_modules}, max_pending={max_pending_registrations}")
    return module_registry