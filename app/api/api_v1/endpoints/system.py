from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
import time
from ....auth.dependencies import get_current_user, require_admin
from ....models.user import User
from ....core.logging import get_logger

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