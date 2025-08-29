from fastapi import APIRouter
from .endpoints import (
    auth, users, organisations, tools, market_edge, admin, features, 
    rate_limits, rate_limit_observability, organization_hierarchy, industry_templates, user_management, user_import, database, debug_auth, module_management
)
from ..health import router as health_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(user_management.router, tags=["user-management"])
api_router.include_router(user_import.router, tags=["user-import"])
api_router.include_router(organisations.router, prefix="/organisations", tags=["organisations"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(market_edge.router, tags=["market-edge"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(features.router, tags=["features"])
api_router.include_router(rate_limits.router, prefix="/admin", tags=["rate-limiting"])
api_router.include_router(rate_limit_observability.router, prefix="/observability", tags=["rate-limit-observability"])

# New hierarchical organization management endpoints
api_router.include_router(organization_hierarchy.router, prefix="/v2", tags=["organization-hierarchy"])
api_router.include_router(industry_templates.router, prefix="/v2", tags=["industry-templates"])

# Database diagnostic and testing endpoints
api_router.include_router(database.router, prefix="/database", tags=["database-diagnostics"])

# Debug authentication endpoint for 500 error investigation
api_router.include_router(debug_auth.router, prefix="/debug", tags=["debug"])

# Module management endpoints for dynamic module routing
api_router.include_router(module_management.router, prefix="/module-management", tags=["module-management"])

# Health check endpoints for monitoring
api_router.include_router(health_router, tags=["health"])