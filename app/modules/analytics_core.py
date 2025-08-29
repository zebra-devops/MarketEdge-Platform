"""
Analytics Core Module

Example module demonstrating the module routing system.
Provides core analytics functionality with proper versioning,
authentication, and feature flag integration.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.module_registry import BaseModuleRouter, ModuleMetadata
from ..core.module_routing import RouteVersion, AuthLevel
from ..middleware.module_auth import require_module_auth, create_module_auth_dependency
from ..models.modules import ModuleType
from ..models.user import User
from ..core.database import get_db
from ..auth.dependencies import get_current_user

logger = logging.getLogger(__name__)


class AnalyticsCoreModule(BaseModuleRouter):
    """
    Core analytics module providing fundamental analytics capabilities
    """
    
    @classmethod
    def create_instance(cls):
        """Factory method for creating module instance"""
        metadata = ModuleMetadata(
            module_id="analytics_core",
            name="Analytics Core",
            version="1.0.0",
            description="Core analytics module providing fundamental data analysis capabilities",
            author="MarketEdge Development Team",
            module_type=ModuleType.ANALYTICS,
            dependencies=[],
            permissions=["read_analytics", "view_dashboard"],
            feature_flags=["analytics_core_enabled"],
            config_schema={
                "type": "object",
                "properties": {
                    "max_query_limit": {"type": "integer", "default": 1000},
                    "cache_ttl_seconds": {"type": "integer", "default": 300},
                    "enable_advanced_features": {"type": "boolean", "default": False}
                }
            },
            default_config={
                "auth_level": "BASIC",
                "required_permissions": ["read_analytics"],
                "feature_flags": ["analytics_core_enabled"],
                "max_query_limit": 1000,
                "cache_ttl_seconds": 300,
                "enable_advanced_features": False
            },
            entry_point="app.modules.analytics_core.AnalyticsCoreModule",
            tags=["analytics", "core", "dashboard"]
        )
        return cls(metadata)
    
    def get_version(self) -> RouteVersion:
        return RouteVersion.V1
    
    def get_namespace(self) -> str:
        return "analytics-core"
    
    def register_routes(self, router: APIRouter) -> None:
        """Register all module routes"""
        
        # Dashboard overview endpoint
        @router.get("/dashboard/overview")
        @require_module_auth(auth_level="BASIC", permissions=["read_analytics"])
        async def get_dashboard_overview(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            time_period: str = Query("30d", description="Time period for data (7d, 30d, 90d)")
        ):
            """Get dashboard overview data"""
            try:
                # Calculate date range
                days = {"7d": 7, "30d": 30, "90d": 90}.get(time_period, 30)
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Mock analytics data - in real implementation, query actual data
                overview_data = {
                    "time_period": time_period,
                    "start_date": start_date.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "metrics": {
                        "total_users": 1250,
                        "active_users": 890,
                        "total_sessions": 3420,
                        "avg_session_duration": 24.5,
                        "conversion_rate": 12.8
                    },
                    "trends": {
                        "user_growth": 8.2,
                        "session_growth": 15.6,
                        "engagement_change": 4.3
                    },
                    "top_features": [
                        {"name": "Dashboard", "usage_count": 2100, "percentage": 61.4},
                        {"name": "Reports", "usage_count": 1850, "percentage": 54.1},
                        {"name": "Analytics", "usage_count": 1200, "percentage": 35.1}
                    ]
                }
                
                logger.info(f"Dashboard overview requested by user {current_user.id} for period {time_period}")
                return overview_data
                
            except Exception as e:
                logger.error(f"Error getting dashboard overview: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving dashboard data")
        
        # User analytics endpoint
        @router.get("/analytics/users")
        @require_module_auth(auth_level="BASIC", permissions=["read_analytics"])
        async def get_user_analytics(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            limit: int = Query(100, le=1000, description="Maximum number of records to return"),
            offset: int = Query(0, ge=0, description="Number of records to skip")
        ):
            """Get user analytics data"""
            try:
                # Mock user analytics data
                analytics_data = {
                    "total_count": 1250,
                    "limit": limit,
                    "offset": offset,
                    "users": [
                        {
                            "user_id": f"user_{i}",
                            "sessions": 15 + i,
                            "total_time_minutes": 450 + (i * 20),
                            "last_active": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                            "feature_usage": {
                                "dashboard": 12,
                                "reports": 8,
                                "analytics": 5
                            }
                        }
                        for i in range(offset, min(offset + limit, 50))  # Limit mock data
                    ]
                }
                
                logger.info(f"User analytics requested by user {current_user.id}")
                return analytics_data
                
            except Exception as e:
                logger.error(f"Error getting user analytics: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving user analytics")
        
        # Feature usage analytics endpoint
        @router.get("/analytics/features")
        @require_module_auth(auth_level="BASIC", permissions=["read_analytics"])
        async def get_feature_analytics(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            feature_name: Optional[str] = Query(None, description="Specific feature to analyze")
        ):
            """Get feature usage analytics"""
            try:
                if feature_name:
                    # Return specific feature analytics
                    feature_data = {
                        "feature_name": feature_name,
                        "total_usage": 2100,
                        "unique_users": 650,
                        "avg_usage_per_user": 3.2,
                        "usage_trend": [
                            {"date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), 
                             "count": 50 + i * 2}
                            for i in range(30, 0, -1)
                        ]
                    }
                    return feature_data
                else:
                    # Return overview of all features
                    features_data = {
                        "total_features": 15,
                        "features": [
                            {
                                "name": "Dashboard",
                                "usage_count": 2100,
                                "unique_users": 650,
                                "growth_rate": 12.5
                            },
                            {
                                "name": "Reports",
                                "usage_count": 1850,
                                "unique_users": 580,
                                "growth_rate": 8.2
                            },
                            {
                                "name": "Analytics",
                                "usage_count": 1200,
                                "unique_users": 420,
                                "growth_rate": 15.8
                            }
                        ]
                    }
                    return features_data
                
            except Exception as e:
                logger.error(f"Error getting feature analytics: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving feature analytics")
        
        # Advanced analytics (requires feature flag)
        @router.get("/analytics/advanced")
        @require_module_auth(
            auth_level="BASIC", 
            permissions=["read_analytics", "advanced_analytics"],
            feature_flags=["advanced_analytics_enabled"]
        )
        async def get_advanced_analytics(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            analysis_type: str = Query("cohort", description="Type of analysis (cohort, funnel, retention)")
        ):
            """Get advanced analytics (requires feature flag)"""
            try:
                if analysis_type == "cohort":
                    analytics_data = {
                        "analysis_type": "cohort",
                        "cohorts": [
                            {
                                "cohort_date": "2024-01",
                                "size": 150,
                                "retention_rates": [100, 85, 72, 65, 58, 52]
                            },
                            {
                                "cohort_date": "2024-02", 
                                "size": 180,
                                "retention_rates": [100, 88, 75, 68, 61]
                            }
                        ]
                    }
                elif analysis_type == "funnel":
                    analytics_data = {
                        "analysis_type": "funnel",
                        "steps": [
                            {"step": "Landing", "users": 10000, "conversion_rate": 100},
                            {"step": "Sign Up", "users": 2500, "conversion_rate": 25},
                            {"step": "Onboarding", "users": 2200, "conversion_rate": 88},
                            {"step": "First Use", "users": 1800, "conversion_rate": 81.8},
                            {"step": "Regular Use", "users": 1200, "conversion_rate": 66.7}
                        ]
                    }
                else:
                    analytics_data = {
                        "analysis_type": "retention",
                        "overall_retention": 68.5,
                        "retention_by_period": {
                            "day_1": 92.3,
                            "day_7": 78.5,
                            "day_30": 68.5,
                            "day_90": 45.2
                        }
                    }
                
                logger.info(f"Advanced analytics ({analysis_type}) requested by user {current_user.id}")
                return analytics_data
                
            except Exception as e:
                logger.error(f"Error getting advanced analytics: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving advanced analytics")
        
        # Configuration endpoint
        @router.get("/config")
        @require_module_auth(auth_level="BASIC")
        async def get_module_config(
            current_user: User = Depends(get_current_user)
        ):
            """Get module configuration"""
            return {
                "module_id": self.metadata.module_id,
                "version": self.metadata.version,
                "features": {
                    "dashboard": True,
                    "user_analytics": True,
                    "feature_analytics": True,
                    "advanced_analytics": False  # Depends on feature flag
                },
                "limits": {
                    "max_query_limit": 1000,
                    "cache_ttl_seconds": 300
                }
            }
    
    async def _check_health(self) -> Dict[str, Any]:
        """Custom health check implementation"""
        try:
            # Perform health checks specific to this module
            health_data = {
                "status": "healthy",
                "module_id": self.metadata.module_id,
                "version": self.metadata.version,
                "checks": {
                    "database_connection": "ok",
                    "analytics_service": "ok",
                    "cache_service": "ok"
                },
                "metrics": {
                    "queries_last_hour": 450,
                    "avg_response_time_ms": 125,
                    "error_rate": 0.02
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed for {self.metadata.module_id}: {str(e)}")
            self.set_health_status("unhealthy", str(e))
            
            return {
                "status": "unhealthy",
                "module_id": self.metadata.module_id,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }


# Export the module class for discovery
__all__ = ["AnalyticsCoreModule"]