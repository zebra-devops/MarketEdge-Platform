"""
Industry Context Middleware

Provides industry-specific context and feature flag routing for requests.
Integrates with the tenant context to provide industry-aware routing and validation.
"""
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import uuid

from ..core.rate_limit_config import Industry
from ..core.industry_config import industry_config_manager
from ..models.organisation import Organisation
from ..models.user import User
from ..core.database import get_db
from ..core.logging import logger


class IndustryContextMiddleware:
    """
    Middleware to inject industry-specific context into requests.
    
    Sets industry context based on the authenticated user's organisation,
    enabling industry-specific routing, feature flags, and validation.
    """
    
    def __init__(self, app):
        self.app = app
        self.industry_config = industry_config_manager
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract industry context
            industry_context = await self._extract_industry_context(request)
            
            # Add industry context to request state
            if industry_context:
                scope["state"] = getattr(scope, "state", {})
                scope["state"]["industry_context"] = industry_context
            
            # Check industry-specific access permissions
            if not await self._validate_industry_access(request, industry_context):
                response = Response(
                    content="Industry-specific access denied",
                    status_code=status.HTTP_403_FORBIDDEN
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    async def _extract_industry_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract industry context from the request."""
        try:
            # Try to get user from request state (set by auth middleware)
            user = getattr(request.state, "user", None)
            if not user:
                return None
            
            # Get database session
            db_session = next(get_db())
            try:
                # Get organisation for the user - use parameterized query to prevent SQL injection
                from sqlalchemy import text
                organisation = db_session.query(Organisation).filter(
                    Organisation.id == user.organisation_id
                ).first()
                
                if not organisation:
                    return None
                
                industry_type = organisation.industry_type
                
                # Get industry-specific configuration
                context = {
                    "industry_type": industry_type,
                    "organisation_id": str(organisation.id),
                    "rate_limits": self.industry_config.get_rate_limit_config(industry_type),
                    "security_config": self.industry_config.get_security_config(industry_type),
                    "performance_config": self.industry_config.get_performance_config(industry_type),
                    "feature_flags": self.industry_config.get_feature_flags_config(industry_type),
                    "compliance_requirements": self.industry_config.get_compliance_requirements(industry_type),
                    "profile": self.industry_config.industry_mapper.get_industry_profile(industry_type)
                }
                
                return context
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.warning(f"Failed to extract industry context: {str(e)}")
            return None
    
    async def _validate_industry_access(
        self, 
        request: Request, 
        industry_context: Optional[Dict[str, Any]]
    ) -> bool:
        """Validate industry-specific access permissions."""
        try:
            # If no industry context, allow access (guest or system routes)
            if not industry_context:
                return True
            
            path = request.url.path
            method = request.method
            
            # Extract industry-specific validation rules
            industry_type = industry_context["industry_type"]
            feature_flags = industry_context["feature_flags"]
            
            # Apply industry-specific route restrictions
            restrictions = self._get_industry_route_restrictions(industry_type, feature_flags)
            
            for restriction in restrictions:
                if self._path_matches_restriction(path, method, restriction):
                    logger.warning(
                        f"Industry access denied: {industry_type.value} to {method} {path}"
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating industry access: {str(e)}")
            # Allow access on validation errors to prevent service disruption
            return True
    
    def _get_industry_route_restrictions(
        self, 
        industry_type: Industry, 
        feature_flags: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get industry-specific route restrictions."""
        restrictions = []
        
        # API access restrictions
        if not feature_flags.get("api_access", True):
            restrictions.append({
                "pattern": "/api/v1/external/*",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "reason": "External API access not available for this industry"
            })
        
        # Advanced analytics restrictions
        if not feature_flags.get("advanced_analytics", True):
            restrictions.append({
                "pattern": "/api/v1/analytics/advanced/*",
                "methods": ["GET", "POST"],
                "reason": "Advanced analytics not available for this industry"
            })
        
        # Integration marketplace restrictions
        if not feature_flags.get("integration_marketplace", False):
            restrictions.append({
                "pattern": "/api/v1/integrations/*",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "reason": "Integration marketplace not available for this industry"
            })
        
        # Multi-location support restrictions
        if not feature_flags.get("multi_location_support", True):
            restrictions.append({
                "pattern": "/api/v1/locations/*",
                "methods": ["POST", "PUT"],
                "reason": "Multi-location support not available for this industry"
            })
        
        # Industry-specific restrictions
        if industry_type == Industry.GYM:
            # Gyms might not have access to certain retail features
            restrictions.append({
                "pattern": "/api/v1/inventory/*",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "reason": "Inventory management not applicable for gym industry"
            })
        
        elif industry_type == Industry.CINEMA:
            # Cinemas might not have access to certain hotel features
            restrictions.append({
                "pattern": "/api/v1/room-management/*",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "reason": "Room management not applicable for cinema industry"
            })
        
        return restrictions
    
    def _path_matches_restriction(
        self, 
        path: str, 
        method: str, 
        restriction: Dict[str, Any]
    ) -> bool:
        """Check if a path and method match a restriction."""
        pattern = restriction["pattern"]
        methods = restriction["methods"]
        
        # Check method match
        if method not in methods:
            return False
        
        # Simple wildcard matching
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return path.endswith(pattern[1:])
        elif "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                return path.startswith(parts[0]) and path.endswith(parts[1])
        
        return path == pattern


def get_industry_context(request: Request) -> Optional[Dict[str, Any]]:
    """Get industry context from request state."""
    return getattr(request.state, "industry_context", None)


def require_industry_feature(feature_name: str):
    """Decorator to require a specific industry feature flag."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            industry_context = get_industry_context(request)
            
            if not industry_context:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Industry context required"
                )
            
            feature_flags = industry_context.get("feature_flags", {})
            if not feature_flags.get(feature_name, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature_name}' not available for this industry"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_industry_rate_limits(request: Request) -> Optional[Dict[str, Any]]:
    """Get industry-specific rate limits from request context."""
    industry_context = get_industry_context(request)
    if industry_context:
        return industry_context.get("rate_limits")
    return None


def get_industry_compliance_requirements(request: Request) -> List[str]:
    """Get industry-specific compliance requirements from request context."""
    industry_context = get_industry_context(request)
    if industry_context:
        return industry_context.get("compliance_requirements", [])
    return []