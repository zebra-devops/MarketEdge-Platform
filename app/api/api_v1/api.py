from fastapi import APIRouter
from .endpoints import auth, users, organisations, tools, market_edge, admin, features, rate_limits, rate_limit_observability

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organisations.router, prefix="/organisations", tags=["organisations"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(market_edge.router, tags=["market-edge"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(features.router, tags=["features"])
api_router.include_router(rate_limits.router, prefix="/admin", tags=["rate-limiting"])
api_router.include_router(rate_limit_observability.router, prefix="/observability", tags=["rate-limit-observability"])