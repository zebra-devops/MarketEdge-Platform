"""
Tests for the Module Routing System

Comprehensive tests covering module registration, routing, authentication,
conflict detection, and performance monitoring.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.module_routing import (
    ModuleRoutingManager, RouteConflictDetector, RouteVersion,
    AuthLevel, ModuleRouteConfig, RegisteredRoute, RouteMetrics,
    IModuleRouter, initialize_module_routing
)
from app.core.module_registry import (
    ModuleRegistry, BaseModuleRouter, ModuleMetadata,
    ModuleValidator, ModuleDiscovery, RegistrationResult,
    ModuleLifecycleState
)
from app.models.modules import ModuleType, ModuleStatus
from app.models.user import User, UserRole
from app.services.feature_flag_service import FeatureFlagService
from app.services.module_service import ModuleService


class TestModuleRouter(BaseModuleRouter):
    """Test module router for testing purposes"""
    
    def __init__(self):
        metadata = ModuleMetadata(
            module_id="test_module",
            name="Test Module",
            version="1.0.0",
            description="Test module for unit tests",
            author="Test Suite",
            module_type=ModuleType.ANALYTICS,
            dependencies=[],
            permissions=["test_permission"],
            feature_flags=["test_feature"],
            entry_point="test_module"
        )
        super().__init__(metadata)
    
    def register_routes(self, router: APIRouter) -> None:
        """Register test routes"""
        
        @router.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @router.get("/test/{item_id}")
        async def test_parameterized(item_id: str):
            return {"item_id": item_id}
        
        @router.post("/test/create")
        async def test_create():
            return {"created": True}


class ConflictingTestModuleRouter(BaseModuleRouter):
    """Test module router that creates conflicts"""
    
    def __init__(self):
        metadata = ModuleMetadata(
            module_id="conflict_module",
            name="Conflict Module",
            version="1.0.0",
            description="Module that creates route conflicts",
            author="Test Suite",
            module_type=ModuleType.ANALYTICS,
            entry_point="conflict_module"
        )
        super().__init__(metadata)
    
    def register_routes(self, router: APIRouter) -> None:
        """Register conflicting routes"""
        
        @router.get("/test")  # Same as TestModuleRouter
        async def conflicting_endpoint():
            return {"message": "conflict"}


@pytest.fixture
async def mock_db():
    """Mock database session"""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
async def mock_feature_service():
    """Mock feature flag service"""
    service = AsyncMock(spec=FeatureFlagService)
    service.is_feature_enabled = AsyncMock(return_value=True)
    return service


@pytest.fixture
async def mock_module_service():
    """Mock module service"""
    service = AsyncMock(spec=ModuleService)
    service.get_available_modules = AsyncMock(return_value=[
        {"id": "test_module", "name": "Test Module"}
    ])
    service.log_module_usage = AsyncMock()
    return service


@pytest.fixture
async def routing_manager(mock_feature_service, mock_module_service):
    """Module routing manager fixture"""
    manager = ModuleRoutingManager(mock_feature_service, mock_module_service)
    return manager


@pytest.fixture
async def module_registry(mock_db):
    """Module registry fixture"""
    registry = ModuleRegistry(mock_db)
    return registry


@pytest.fixture
def test_user():
    """Test user fixture"""
    user = Mock(spec=User)
    user.id = "test_user_id"
    user.organisation_id = "test_org_id"
    user.role = UserRole.USER
    user.is_active = True
    return user


class TestRouteConflictDetector:
    """Test route conflict detection"""
    
    def test_no_conflict_different_paths(self):
        """Test that different paths don't create conflicts"""
        detector = RouteConflictDetector()
        
        # First route
        conflict = detector.check_conflict("/test1", ["GET"], "module1", "ns1")
        assert conflict is None
        
        # Different path should not conflict
        conflict = detector.check_conflict("/test2", ["GET"], "module2", "ns2")
        assert conflict is None
    
    def test_conflict_same_path_same_method(self):
        """Test that same path and method creates conflict"""
        detector = RouteConflictDetector()
        
        # Register first route
        detector.registered_patterns["/test:GET"] = RegisteredRoute(
            route=Mock(),
            module_id="module1",
            config=Mock(),
            path_pattern="/test",
            methods=["GET"]
        )
        
        # Same path and method should conflict
        conflict = detector.check_conflict("/test", ["GET"], "module2", "ns2")
        assert conflict is not None
        assert "already registered by module 'module1'" in conflict
    
    def test_no_conflict_same_path_different_method(self):
        """Test that same path with different methods don't conflict"""
        detector = RouteConflictDetector()
        
        # Register GET route
        detector.registered_patterns["/test:GET"] = RegisteredRoute(
            route=Mock(),
            module_id="module1", 
            config=Mock(),
            path_pattern="/test",
            methods=["GET"]
        )
        
        # POST to same path should not conflict
        conflict = detector.check_conflict("/test", ["POST"], "module2", "ns2")
        assert conflict is None
    
    def test_same_module_no_conflict(self):
        """Test that same module can register multiple routes"""
        detector = RouteConflictDetector()
        
        # Register first route
        detector.registered_patterns["/test1:GET"] = RegisteredRoute(
            route=Mock(),
            module_id="module1",
            config=Mock(),
            path_pattern="/test1",
            methods=["GET"]
        )
        
        # Same module should be able to register different routes
        conflict = detector.check_conflict("/test2", ["GET"], "module1", "ns1")
        assert conflict is None


class TestModuleRouteConfig:
    """Test module route configuration"""
    
    def test_valid_basic_config(self):
        """Test creating valid basic configuration"""
        config = ModuleRouteConfig(
            module_id="test_module",
            version=RouteVersion.V1,
            namespace="test",
            auth_level=AuthLevel.BASIC
        )
        assert config.module_id == "test_module"
        assert config.auth_level == AuthLevel.BASIC
        assert config.required_permissions == []
    
    def test_permission_auth_requires_permissions(self):
        """Test that PERMISSION auth level requires permissions"""
        with pytest.raises(ValueError, match="PERMISSION auth level requires"):
            ModuleRouteConfig(
                module_id="test",
                version=RouteVersion.V1,
                namespace="test",
                auth_level=AuthLevel.PERMISSION
                # Missing required_permissions
            )
    
    def test_role_auth_requires_roles(self):
        """Test that ROLE auth level requires roles"""
        with pytest.raises(ValueError, match="ROLE auth level requires"):
            ModuleRouteConfig(
                module_id="test",
                version=RouteVersion.V1,
                namespace="test",
                auth_level=AuthLevel.ROLE
                # Missing required_roles
            )


class TestRouteMetrics:
    """Test route performance metrics"""
    
    def test_initial_metrics(self):
        """Test initial metrics state"""
        metrics = RouteMetrics()
        assert metrics.call_count == 0
        assert metrics.total_duration_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.last_called is None
        assert metrics.avg_duration_ms == 0.0
    
    def test_record_successful_call(self):
        """Test recording successful call"""
        metrics = RouteMetrics()
        metrics.record_call(100.0, success=True)
        
        assert metrics.call_count == 1
        assert metrics.total_duration_ms == 100.0
        assert metrics.error_count == 0
        assert metrics.last_called is not None
        assert metrics.avg_duration_ms == 100.0
    
    def test_record_failed_call(self):
        """Test recording failed call"""
        metrics = RouteMetrics()
        metrics.record_call(150.0, success=False)
        
        assert metrics.call_count == 1
        assert metrics.error_count == 1
        assert metrics.avg_duration_ms == 150.0
    
    def test_multiple_calls_average(self):
        """Test average calculation with multiple calls"""
        metrics = RouteMetrics()
        metrics.record_call(100.0)
        metrics.record_call(200.0)
        metrics.record_call(300.0)
        
        assert metrics.call_count == 3
        assert metrics.total_duration_ms == 600.0
        assert metrics.avg_duration_ms == 200.0


class TestModuleRoutingManager:
    """Test module routing manager functionality"""
    
    @pytest.mark.asyncio
    async def test_register_module_success(self, routing_manager):
        """Test successful module registration"""
        test_module = TestModuleRouter()
        
        await routing_manager.register_module(test_module)
        
        # Check module was registered
        registered_modules = routing_manager.get_registered_modules()
        assert "test_module" in registered_modules
        
        # Check router was created
        router = routing_manager.get_router()
        assert router is not None
    
    @pytest.mark.asyncio
    async def test_register_duplicate_module_fails(self, routing_manager):
        """Test that registering duplicate module fails"""
        test_module = TestModuleRouter()
        
        # Register first time
        await routing_manager.register_module(test_module)
        
        # Register again should fail
        with pytest.raises(ValueError, match="already registered"):
            await routing_manager.register_module(test_module)
    
    @pytest.mark.asyncio
    async def test_register_conflicting_routes_fails(self, routing_manager):
        """Test that conflicting routes cause registration to fail"""
        test_module = TestModuleRouter()
        conflict_module = ConflictingTestModuleRouter()
        
        # Register first module
        await routing_manager.register_module(test_module)
        
        # Register conflicting module should fail
        with pytest.raises(ValueError, match="Route conflict"):
            await routing_manager.register_module(conflict_module)
    
    @pytest.mark.asyncio
    async def test_unregister_module_success(self, routing_manager):
        """Test successful module unregistration"""
        test_module = TestModuleRouter()
        
        # Register module
        await routing_manager.register_module(test_module)
        assert "test_module" in routing_manager.get_registered_modules()
        
        # Unregister module
        await routing_manager.unregister_module("test_module")
        assert "test_module" not in routing_manager.get_registered_modules()
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_module_fails(self, routing_manager):
        """Test that unregistering nonexistent module fails"""
        with pytest.raises(ValueError, match="not registered"):
            await routing_manager.unregister_module("nonexistent_module")
    
    def test_get_route_metrics(self, routing_manager):
        """Test getting route metrics"""
        # Add some mock metrics
        routing_manager.route_metrics["test_module:/test"] = RouteMetrics()
        routing_manager.route_metrics["test_module:/test"].record_call(100.0)
        
        # Get all metrics
        all_metrics = routing_manager.get_route_metrics()
        assert "test_module:/test" in all_metrics
        
        # Get module-specific metrics
        module_metrics = routing_manager.get_route_metrics("test_module")
        assert "test_module:/test" in module_metrics
        assert len(module_metrics) == 1


class TestModuleValidator:
    """Test module validation"""
    
    @pytest.mark.asyncio
    async def test_valid_module_passes(self, mock_db):
        """Test that valid module passes validation"""
        test_module = TestModuleRouter()
        
        # Mock database to return no existing module
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        errors = await ModuleValidator.validate_module_router(test_module, mock_db)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_empty_module_id_fails(self, mock_db):
        """Test that empty module ID fails validation"""
        # Create module with invalid ID
        metadata = ModuleMetadata(
            module_id="",  # Empty ID
            name="Test",
            version="1.0.0",
            description="Test",
            author="Test",
            module_type=ModuleType.ANALYTICS
        )
        invalid_module = BaseModuleRouter(metadata)
        
        errors = await ModuleValidator.validate_module_router(invalid_module, mock_db)
        assert any("non-empty string" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_module_id_format_fails(self, mock_db):
        """Test that invalid module ID format fails validation"""
        # Create module with invalid ID format
        metadata = ModuleMetadata(
            module_id="invalid-module-id!",  # Contains invalid characters
            name="Test",
            version="1.0.0", 
            description="Test",
            author="Test",
            module_type=ModuleType.ANALYTICS
        )
        invalid_module = BaseModuleRouter(metadata)
        
        errors = await ModuleValidator.validate_module_router(invalid_module, mock_db)
        assert any("alphanumeric characters and underscores" in error for error in errors)


class TestModuleRegistry:
    """Test module registry functionality"""
    
    @pytest.mark.asyncio
    async def test_register_module_success(self, module_registry):
        """Test successful module registration through registry"""
        test_module = TestModuleRouter()
        
        # Mock the routing manager
        with patch('app.core.module_registry.get_module_routing_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            result = await module_registry.register_module(test_module)
            
            assert result.success is True
            assert result.module_id == "test_module"
            assert result.lifecycle_state == ModuleLifecycleState.ACTIVE
    
    @pytest.mark.asyncio
    async def test_register_invalid_module_fails(self, module_registry):
        """Test that invalid module registration fails"""
        # Create invalid module (empty ID)
        metadata = ModuleMetadata(
            module_id="",
            name="Invalid",
            version="1.0.0",
            description="Invalid module",
            author="Test",
            module_type=ModuleType.ANALYTICS
        )
        invalid_module = BaseModuleRouter(metadata)
        
        result = await module_registry.register_module(invalid_module)
        
        assert result.success is False
        assert result.lifecycle_state == ModuleLifecycleState.ERROR
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_unregister_module_success(self, module_registry):
        """Test successful module unregistration"""
        test_module = TestModuleRouter()
        
        # Mock successful registration and then unregistration
        with patch('app.core.module_registry.get_module_routing_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager
            
            # Register first
            await module_registry.register_module(test_module)
            
            # Then unregister
            result = await module_registry.unregister_module("test_module")
            
            assert result.success is True
            assert result.lifecycle_state == ModuleLifecycleState.UNREGISTERED
    
    def test_get_registered_modules(self, module_registry):
        """Test getting list of registered modules"""
        # Add a module to the registry
        test_module = TestModuleRouter()
        module_registry.registered_modules["test_module"] = test_module
        
        modules = module_registry.get_registered_modules()
        assert "test_module" in modules
    
    def test_get_registration_history(self, module_registry):
        """Test getting registration history"""
        # Add some history
        result = RegistrationResult(
            success=True,
            module_id="test_module",
            message="Test registration",
            lifecycle_state=ModuleLifecycleState.ACTIVE
        )
        module_registry.registration_history.append(result)
        
        history = module_registry.get_registration_history()
        assert len(history) == 1
        assert history[0].module_id == "test_module"


class TestModuleDiscovery:
    """Test module discovery functionality"""
    
    def test_discovery_initialization(self):
        """Test discovery service initialization"""
        discovery = ModuleDiscovery("test/modules")
        assert str(discovery.modules_path).endswith("test/modules")
        assert discovery.discovered_modules == {}
    
    @pytest.mark.asyncio
    async def test_discover_no_modules_directory(self):
        """Test discovery when modules directory doesn't exist"""
        discovery = ModuleDiscovery("nonexistent/path")
        
        modules = await discovery.discover_modules()
        assert modules == {}
    
    @pytest.mark.asyncio
    async def test_discover_modules_with_mock_filesystem(self):
        """Test module discovery with mocked filesystem"""
        discovery = ModuleDiscovery("test/modules")
        
        # Mock the discovery process
        with patch.object(discovery.modules_path, 'exists', return_value=True), \
             patch.object(discovery.modules_path, 'glob', return_value=[]):
            
            modules = await discovery.discover_modules()
            assert isinstance(modules, dict)


class TestIntegration:
    """Integration tests for the complete module system"""
    
    @pytest.mark.asyncio
    async def test_full_module_lifecycle(self, mock_feature_service, mock_module_service, mock_db):
        """Test complete module lifecycle: registration, usage, unregistration"""
        # Initialize managers
        routing_manager = ModuleRoutingManager(mock_feature_service, mock_module_service)
        registry = ModuleRegistry(mock_db)
        
        # Create test module
        test_module = TestModuleRouter()
        
        # Mock routing manager registration
        with patch('app.core.module_registry.get_module_routing_manager', return_value=routing_manager):
            # Register module
            result = await registry.register_module(test_module)
            assert result.success is True
            
            # Check module is registered
            assert "test_module" in registry.get_registered_modules()
            
            # Get module status
            status = await registry.get_module_status("test_module")
            assert status is not None
            assert status["module_id"] == "test_module"
            
            # Unregister module
            unregister_result = await registry.unregister_module("test_module")
            assert unregister_result.success is True
            
            # Check module is no longer registered
            assert "test_module" not in registry.get_registered_modules()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, routing_manager):
        """Test that metrics are collected properly"""
        # Register a module
        test_module = TestModuleRouter()
        await routing_manager.register_module(test_module)
        
        # Simulate route calls by directly updating metrics
        metrics_key = "test_module:/test"
        routing_manager.route_metrics[metrics_key] = RouteMetrics()
        routing_manager.route_metrics[metrics_key].record_call(100.0, success=True)
        routing_manager.route_metrics[metrics_key].record_call(200.0, success=False)
        
        # Check metrics
        all_metrics = routing_manager.get_route_metrics()
        assert metrics_key in all_metrics
        
        metrics = all_metrics[metrics_key]
        assert metrics.call_count == 2
        assert metrics.error_count == 1
        assert metrics.avg_duration_ms == 150.0


# Performance tests
class TestPerformance:
    """Performance tests for module routing system"""
    
    @pytest.mark.asyncio
    async def test_large_number_of_modules(self, routing_manager):
        """Test system performance with many modules"""
        # This would be a longer-running test for performance validation
        modules_to_create = 10  # Reduced for unit test speed
        
        for i in range(modules_to_create):
            # Create unique test modules
            metadata = ModuleMetadata(
                module_id=f"test_module_{i}",
                name=f"Test Module {i}",
                version="1.0.0",
                description=f"Test module {i}",
                author="Test Suite",
                module_type=ModuleType.ANALYTICS,
                entry_point=f"test_module_{i}"
            )
            
            class DynamicTestModule(BaseModuleRouter):
                def register_routes(self, router: APIRouter) -> None:
                    @router.get(f"/test_{i}")
                    async def dynamic_endpoint():
                        return {"module": i}
            
            module = DynamicTestModule(metadata)
            await routing_manager.register_module(module)
        
        # Check all modules registered
        registered = routing_manager.get_registered_modules()
        assert len(registered) == modules_to_create
        
        # Check no performance degradation (basic check)
        import time
        start_time = time.time()
        routing_manager.get_route_metrics()
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 1.0  # Less than 1 second


if __name__ == "__main__":
    pytest.main([__file__])