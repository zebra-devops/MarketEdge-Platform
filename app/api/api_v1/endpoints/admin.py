from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from ....core.database import get_db, get_async_db
from ....auth.dependencies import get_current_user, require_admin
from ....models.user import User
from ....models.feature_flags import FeatureFlag, FeatureFlagOverride
from ....models.modules import AnalyticsModule, OrganisationModule, ModuleStatus
from ....models.audit_log import AuditLog, AdminAction
from ....models.sectors import SICCode
from ....services.feature_flag_service import FeatureFlagService
from ....services.module_service import ModuleService
from ....services.audit_service import AuditService
from ....services.admin_service import AdminService
from ....services.rate_limiting_service import RateLimitingService, IndustryType
from ....services.rate_limit_admin_service import RateLimitAdminService
from ....middleware.rate_limiting import get_rate_limiting_service

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models
class FeatureFlagCreate(BaseModel):
    flag_key: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_enabled: bool = False
    rollout_percentage: int = Field(0, ge=0, le=100)
    scope: str = "global"
    config: Dict[str, Any] = Field(default_factory=dict)
    allowed_sectors: List[str] = Field(default_factory=list)
    blocked_sectors: List[str] = Field(default_factory=list)
    module_id: Optional[str] = None


class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    config: Optional[Dict[str, Any]] = None
    allowed_sectors: Optional[List[str]] = None
    blocked_sectors: Optional[List[str]] = None


class FeatureFlagOverrideCreate(BaseModel):
    organisation_id: Optional[str] = None
    user_id: Optional[str] = None
    is_enabled: bool
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


class ModuleEnableRequest(BaseModel):
    organisation_id: str
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str]
    organisation_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: str
    severity: str
    success: bool


class RateLimitUpdateRequest(BaseModel):
    rate_limit_per_hour: Optional[int] = Field(None, ge=100, le=50000)
    burst_limit: Optional[int] = Field(None, ge=10, le=1000)
    rate_limit_enabled: Optional[bool] = None


class BulkRateLimitUpdateRequest(BaseModel):
    subscription_plan: str = Field(..., pattern="^(basic|professional|enterprise)$")
    rate_limit_per_hour: int = Field(..., ge=100, le=50000)
    burst_limit: int = Field(..., ge=10, le=1000)


# Feature Flag Management Endpoints

@router.get("/feature-flags")
async def list_feature_flags(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
    module_id: Optional[str] = Query(None),
    enabled_only: bool = Query(False)
):
    """List all feature flags with optional filtering"""
    admin_service = AdminService(db)
    
    try:
        feature_flags = await admin_service.get_feature_flags(
            admin_user=current_user,
            module_id=module_id,
            enabled_only=enabled_only
        )
        return {"feature_flags": feature_flags}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature flags"
        )


@router.post("/feature-flags")
async def create_feature_flag(
    flag_data: FeatureFlagCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new feature flag"""
    feature_flag_service = FeatureFlagService(db)
    
    try:
        feature_flag = await feature_flag_service.create_feature_flag(
            flag_data.dict(),
            current_user.id
        )
        
        return {
            "id": feature_flag.id,
            "flag_key": feature_flag.flag_key,
            "name": feature_flag.name,
            "message": "Feature flag created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create feature flag: {str(e)}"
        )


@router.put("/feature-flags/{flag_id}")
async def update_feature_flag(
    flag_id: str,
    updates: FeatureFlagUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Update an existing feature flag"""
    admin_service = AdminService(db)
    
    try:
        # Only include non-None values in updates
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        result = await admin_service.update_feature_flag(
            flag_id=flag_id,
            admin_user=current_user,
            updates=update_data
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature flag"
        )


@router.post("/feature-flags/{flag_id}/overrides")
async def create_feature_flag_override(
    flag_id: str,
    override_data: FeatureFlagOverrideCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a feature flag override"""
    feature_flag_service = FeatureFlagService(db)
    
    try:
        override = await feature_flag_service.create_override(
            flag_id,
            override_data.dict(exclude_none=True),
            current_user.id
        )
        
        return {
            "id": override.id,
            "message": "Feature flag override created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create override: {str(e)}"
        )


@router.get("/feature-flags/{flag_id}/analytics")
async def get_feature_flag_analytics(
    flag_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get usage analytics for a feature flag"""
    feature_flag_service = FeatureFlagService(db)
    
    try:
        analytics = await feature_flag_service.get_usage_analytics(flag_id, days)
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get analytics: {str(e)}"
        )


# Module Management Endpoints

@router.get("/modules")
async def list_modules(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False)
):
    """List all analytics modules"""
    module_service = ModuleService(db)
    
    # Get all modules (admin can see all)
    query = db.query(AnalyticsModule)
    if not include_inactive:
        query = query.filter(AnalyticsModule.status == ModuleStatus.ACTIVE)
    
    modules = query.order_by(AnalyticsModule.created_at.desc()).all()
    
    return {
        "modules": [
            {
                "id": module.id,
                "name": module.name,
                "description": module.description,
                "version": module.version,
                "module_type": module.module_type.value,
                "status": module.status.value,
                "is_core": module.is_core,
                "requires_license": module.requires_license,
                "pricing_tier": module.pricing_tier,
                "dependencies": module.dependencies,
                "created_at": module.created_at,
                "updated_at": module.updated_at
            }
            for module in modules
        ]
    }


@router.post("/modules/{module_id}/enable")
async def enable_module_for_organisation(
    module_id: str,
    request: ModuleEnableRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Enable a module for an organisation"""
    module_service = ModuleService(db)
    
    try:
        org_module = await module_service.enable_module_for_organisation(
            module_id,
            request.organisation_id,
            request.configuration,
            current_user.id
        )
        
        return {
            "id": org_module.id,
            "message": f"Module {module_id} enabled for organisation {request.organisation_id}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to enable module: {str(e)}"
        )


@router.post("/modules/{module_id}/disable")
async def disable_module_for_organisation(
    module_id: str,
    organisation_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    reason: Optional[str] = Query(None)
):
    """Disable a module for an organisation"""
    module_service = ModuleService(db)
    
    try:
        await module_service.disable_module_for_organisation(
            module_id,
            organisation_id,
            current_user.id,
            reason
        )
        
        return {
            "message": f"Module {module_id} disabled for organisation {organisation_id}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to disable module: {str(e)}"
        )


@router.get("/modules/{module_id}/analytics")
async def get_module_analytics(
    module_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    organisation_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Get usage analytics for a module"""
    module_service = ModuleService(db)
    
    try:
        analytics = await module_service.get_module_usage_analytics(
            module_id,
            organisation_id,
            days
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get analytics: {str(e)}"
        )


# SIC Code Management

@router.get("/sic-codes")
async def list_sic_codes(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    supported_only: bool = Query(False)
):
    """List SIC codes"""
    query = db.query(SICCode)
    
    if supported_only:
        query = query.filter(SICCode.is_supported == True)
    
    sic_codes = query.order_by(SICCode.code).all()
    
    return {
        "sic_codes": [
            {
                "code": sic.code,
                "title": sic.title,
                "description": sic.description,
                "section": sic.section,
                "is_supported": sic.is_supported,
                "competitive_factors": sic.competitive_factors,
                "default_metrics": sic.default_metrics
            }
            for sic in sic_codes
        ]
    }


# Audit and Monitoring Endpoints

@router.get("/audit-logs")
async def get_audit_logs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None),
    organisation_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),  # Last 24 hours by default, max 1 week
    limit: int = Query(100, ge=1, le=1000)
):
    """Get audit logs for monitoring"""
    audit_service = AuditService(db)
    
    start_date = datetime.utcnow() - timedelta(hours=hours)
    
    try:
        logs = await audit_service.get_audit_logs(
            user_id=user_id,
            organisation_id=organisation_id,
            resource_type=resource_type,
            action=action,
            start_date=start_date,
            limit=limit
        )
        
        return {
            "audit_logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp,
                    "user_id": log.user_id,
                    "organisation_id": log.organisation_id,
                    "action": log.action.value,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "severity": log.severity.value,
                    "success": log.success,
                    "ip_address": str(log.ip_address) if log.ip_address else None,
                    "changes": log.changes
                }
                for log in logs
            ],
            "total_hours": hours,
            "total_logs": len(logs)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@router.get("/security-events")
async def get_security_events(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168)
):
    """Get recent security events"""
    audit_service = AuditService(db)
    
    try:
        events = await audit_service.get_security_events(hours=hours)
        
        return {
            "security_events": [
                {
                    "id": event.id,
                    "timestamp": event.timestamp,
                    "user_id": event.user_id,
                    "action": event.action.value,
                    "resource_type": event.resource_type,
                    "description": event.description,
                    "severity": event.severity.value,
                    "success": event.success,
                    "ip_address": str(event.ip_address) if event.ip_address else None
                }
                for event in events
            ],
            "period_hours": hours,
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get security events: {str(e)}"
        )


# Dashboard Statistics

@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Get dashboard statistics for admin overview"""
    
    from sqlalchemy import select, func
    
    # Get feature flag counts
    total_flags_result = await db.execute(select(func.count()).select_from(FeatureFlag))
    total_flags = total_flags_result.scalar()
    
    enabled_flags_result = await db.execute(
        select(func.count()).select_from(FeatureFlag).where(FeatureFlag.is_enabled == True)
    )
    enabled_flags = enabled_flags_result.scalar()
    
    # Get module counts
    total_modules_result = await db.execute(select(func.count()).select_from(AnalyticsModule))
    total_modules = total_modules_result.scalar()
    
    active_modules_result = await db.execute(
        select(func.count()).select_from(AnalyticsModule).where(AnalyticsModule.status == ModuleStatus.ACTIVE)
    )
    active_modules = active_modules_result.scalar()
    
    # Get recent activity (last 24 hours)
    recent_logs_result = await db.execute(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        )
    )
    recent_logs = recent_logs_result.scalar()
    
    # Get organisation module enablements
    enabled_org_modules_result = await db.execute(
        select(func.count()).select_from(OrganisationModule).where(OrganisationModule.is_enabled == True)
    )
    enabled_org_modules = enabled_org_modules_result.scalar()
    
    return {
        "feature_flags": {
            "total": total_flags,
            "enabled": enabled_flags,
            "disabled": total_flags - enabled_flags
        },
        "modules": {
            "total": total_modules,
            "active": active_modules,
            "enabled_for_organisations": enabled_org_modules
        },
        "activity": {
            "recent_actions_24h": recent_logs
        },
        "system": {
            "supported_sectors": (await db.execute(
                select(func.count()).select_from(SICCode).where(SICCode.is_supported == True)
            )).scalar()
        }
    }


# Rate Limiting Management Endpoints

class RateLimitStatusRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID to check")
    user_id: str = Field(..., description="User ID to check")
    industry_type: IndustryType = Field(..., description="Industry type for rate limiting")


class RateLimitResetRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID to reset")
    user_id: str = Field(..., description="User ID to reset")
    window: Optional[str] = Field(None, description="Specific window to reset (minute/hour/day)")


@router.get("/rate-limits/status")
async def get_rate_limit_status(
    tenant_id: str = Query(..., description="Tenant ID"),
    user_id: str = Query(..., description="User ID"),
    industry_type: IndustryType = Query(..., description="Industry type"),
    current_user: User = Depends(require_admin),
    rate_limiting_service: RateLimitingService = Depends(get_rate_limiting_service)
):
    """Get rate limit status for a specific tenant/user"""
    try:
        status = await rate_limiting_service.get_rate_limit_status(
            tenant_id=tenant_id,
            user_id=user_id,
            industry_type=industry_type
        )
        
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@router.post("/rate-limits/reset")
async def reset_rate_limits(
    request: RateLimitResetRequest,
    current_user: User = Depends(require_admin),
    rate_limiting_service: RateLimitingService = Depends(get_rate_limiting_service),
    db: Session = Depends(get_db)
):
    """Reset rate limits for a specific tenant/user"""
    try:
        success = await rate_limiting_service.reset_rate_limit(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            window=request.window
        )
        
        if success:
            # Log the admin action
            audit_service = AuditService(db)
            await audit_service.log_admin_action(
                admin_user_id=str(current_user.id),
                action_type="rate_limit_reset",
                summary=f"Rate limits reset for tenant {request.tenant_id}, user {request.user_id}, window: {request.window or 'all'}",
                configuration_changes={
                    "tenant_id": request.tenant_id,
                    "user_id": request.user_id,
                    "window": request.window,
                    "reset_by": str(current_user.id)
                }
            )
            
            return {
                "success": True,
                "message": "Rate limits reset successfully",
                "tenant_id": request.tenant_id,
                "user_id": request.user_id,
                "window": request.window or "all",
                "timestamp": datetime.utcnow()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset rate limits"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limits: {str(e)}"
        )


@router.get("/rate-limits/statistics")
async def get_rate_limit_statistics(
    current_user: User = Depends(require_admin),
    rate_limiting_service: RateLimitingService = Depends(get_rate_limiting_service)
):
    """Get rate limiting statistics for monitoring"""
    try:
        stats = await rate_limiting_service.get_statistics()
        
        return {
            "statistics": stats,
            "industry_limits": {
                industry.value: {
                    "requests_per_minute": config.requests_per_minute,
                    "requests_per_hour": config.requests_per_hour,
                    "requests_per_day": config.requests_per_day,
                    "burst_limit": config.burst_limit
                }
                for industry, config in rate_limiting_service.INDUSTRY_LIMITS.items()
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limiting statistics: {str(e)}"
        )


@router.get("/rate-limits/industry-limits")
async def get_industry_rate_limits(
    current_user: User = Depends(require_admin),
    rate_limiting_service: RateLimitingService = Depends(get_rate_limiting_service)
):
    """Get rate limit configurations for all industry types"""
    return {
        "industry_limits": {
            industry.value: {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour, 
                "requests_per_day": config.requests_per_day,
                "burst_limit": config.burst_limit,
                "description": f"Rate limits for {industry.value} industry"
            }
            for industry, config in rate_limiting_service.INDUSTRY_LIMITS.items()
        },
        "note": "Cinema industry has the highest limits due to real-time ticketing requirements"
    }

@router.get("/rate-limits")
async def get_organization_rate_limits(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
    org_id: Optional[str] = Query(None)
):
    """Get rate limit configurations for organizations"""
    try:
        rate_limits = await RateLimitAdminService.get_organization_rate_limits(db, org_id)
        return {"rate_limits": rate_limits}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rate limits: {str(e)}"
        )


@router.put("/rate-limits/{org_id}")
async def update_organization_rate_limit(
    org_id: str,
    updates: RateLimitUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Update rate limit configuration for an organization"""
    try:
        result = await RateLimitAdminService.update_organization_rate_limit(
            db, 
            org_id, 
            rate_limit_per_hour=updates.rate_limit_per_hour,
            burst_limit=updates.burst_limit,
            rate_limit_enabled=updates.rate_limit_enabled
        )
        return {
            "message": "Rate limits updated successfully",
            "organization": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rate limits: {str(e)}"
        )


@router.post("/rate-limits/bulk-update")
async def bulk_update_rate_limits_by_plan(
    updates: BulkRateLimitUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db)
):
    """Bulk update rate limits for all organizations with a specific subscription plan"""
    try:
        updated_orgs = await RateLimitAdminService.bulk_update_rate_limits_by_plan(
            db,
            updates.subscription_plan,
            updates.rate_limit_per_hour,
            updates.burst_limit
        )
        return {
            "message": f"Updated rate limits for {len(updated_orgs)} organizations",
            "subscription_plan": updates.subscription_plan,
            "updated_organizations": updated_orgs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update rate limits: {str(e)}"
        )


@router.get("/rate-limits/violations")
async def get_rate_limit_violations(
    current_user: User = Depends(require_admin),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent rate limit violations for monitoring"""
    try:
        violations = await RateLimitAdminService.get_rate_limit_violations(limit)
        return {
            "violations": violations,
            "total": len(violations)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch rate limit violations: {str(e)}"
        )