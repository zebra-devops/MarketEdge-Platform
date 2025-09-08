"""
Module System Startup

Handles initialization of the module routing system during application startup.
"""

import logging
from typing import Optional

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .module_routing import initialize_module_routing, get_module_routing_manager
from .module_registry import initialize_module_registry, get_module_registry
from ..services.feature_flag_service import FeatureFlagService
from ..services.module_service import ModuleService
from ..middleware.module_auth import ModuleAuthMiddleware

logger = logging.getLogger(__name__)


async def initialize_module_system(
    app: FastAPI,
    db: AsyncSession,
    feature_flag_service: FeatureFlagService,
    module_service: ModuleService,
    auto_discover: bool = True
) -> None:
    """
    Initialize the complete module routing system
    
    Args:
        app: FastAPI application instance
        db: Database session
        feature_flag_service: Feature flag service instance
        module_service: Module service instance
        auto_discover: Whether to automatically discover and register modules
    """
    try:
        logger.info("Initializing module routing system...")
        
        # Initialize module routing manager
        routing_manager = await initialize_module_routing(feature_flag_service, module_service)
        
        # Initialize module registry
        registry = await initialize_module_registry(db)
        
        # Add module authentication middleware
        app.add_middleware(ModuleAuthMiddleware, feature_flag_service=feature_flag_service, module_service=module_service)
        
        # Include module routes in the main application
        module_router = routing_manager.get_router()
        app.include_router(module_router, prefix="/api/v1")
        
        # Auto-discover and register modules if enabled
        if auto_discover:
            logger.info("Starting auto-discovery of modules...")
            results = await registry.auto_discover_and_register()
            
            successful_registrations = [r for r in results if r.success]
            failed_registrations = [r for r in results if not r.success]
            
            logger.info(f"Module auto-discovery completed: {len(successful_registrations)} successful, {len(failed_registrations)} failed")
            
            if successful_registrations:
                logger.info("Successfully registered modules: " + 
                           ", ".join([r.module_id for r in successful_registrations]))
            
            if failed_registrations:
                logger.warning("Failed to register modules: " + 
                              ", ".join([f"{r.module_id} ({r.message})" for r in failed_registrations]))
        
        logger.info("Module routing system initialization completed successfully")
        
        # Store references in app state for access during runtime
        app.state.module_routing_manager = routing_manager
        app.state.module_registry = registry
        
    except Exception as e:
        logger.error(f"Failed to initialize module routing system: {str(e)}")
        raise


async def shutdown_module_system(app: FastAPI) -> None:
    """
    Clean shutdown of the module system
    
    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Shutting down module routing system...")
        
        # Clean up any resources if needed
        if hasattr(app.state, 'module_registry'):
            registry = app.state.module_registry
            registered_modules = registry.get_registered_modules()
            
            logger.info(f"Cleaning up {len(registered_modules)} registered modules")
            
            # Could implement module-specific cleanup here
            for module_id in registered_modules:
                try:
                    await registry.unregister_module(module_id)
                except Exception as e:
                    logger.warning(f"Error during cleanup of module {module_id}: {str(e)}")
        
        logger.info("Module routing system shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during module system shutdown: {str(e)}")


def get_module_system_info() -> dict:
    """
    Get information about the current state of the module system
    
    Returns:
        Dictionary with module system status information
    """
    try:
        routing_manager = get_module_routing_manager()
        registry = get_module_registry()
        
        registered_modules = registry.get_registered_modules()
        route_metrics = routing_manager.get_route_metrics()
        
        return {
            "initialized": True,
            "registered_modules": len(registered_modules),
            "total_routes": len(route_metrics),
            "modules": registered_modules,
            "system_status": "healthy"
        }
        
    except RuntimeError:
        return {
            "initialized": False,
            "error": "Module system not initialized"
        }
    except Exception as e:
        return {
            "initialized": True,
            "error": str(e),
            "system_status": "error"
        }