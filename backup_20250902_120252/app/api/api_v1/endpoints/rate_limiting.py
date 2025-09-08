from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ....auth.dependencies import get_current_user, require_admin
from ....core.database import get_db
from ....models.user import User
from ....models.rate_limiting import (
    RateLimitRule, RateLimitUsage, SICRateLimitConfig,
    RateLimitScope, RateLimitPeriod
)
from ....services.rate_limiter_service import rate_limiter_service
from ....middleware.rate_limiting import RateLimitManager

router = APIRouter()


# Pydantic models for API
class RateLimitRuleCreate(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    scope: RateLimitScope
    scope_value: Optional[str] = Field(None, max_length=255)
    endpoint_pattern: str = Field(..., min_length=1, max_length=255)
    requests_per_period: int = Field(..., gt=0)
    period: RateLimitPeriod
    burst_requests: Optional[int] = Field(None, gt=0)
    burst_period_seconds: Optional[int] = Field(None, gt=0)
    priority: int = Field(default=0)
    is_active: bool = Field(default=True)
    config: Dict[str, Any] = Field(default_factory=dict)


class RateLimitRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    endpoint_pattern: Optional[str] = Field(None, min_length=1, max_length=255)
    requests_per_period: Optional[int] = Field(None, gt=0)
    period: Optional[RateLimitPeriod] = None
    burst_requests: Optional[int] = Field(None, gt=0)
    burst_period_seconds: Optional[int] = Field(None, gt=0)
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class RateLimitRuleResponse(BaseModel):
    id: str
    rule_name: str
    description: Optional[str]
    scope: str
    scope_value: Optional[str]
    endpoint_pattern: str
    requests_per_period: int
    period: str
    burst_requests: Optional[int]
    burst_period_seconds: Optional[int]
    priority: int
    is_active: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RateLimitUsageResponse(BaseModel):
    id: str
    endpoint: str
    method: str
    ip_address: Optional[str]
    was_limited: bool
    current_usage: int
    limit_threshold: int
    processing_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True


class RateLimitStatsResponse(BaseModel):
    total_requests: int
    limited_requests: int
    success_rate: float
    avg_processing_time_ms: float
    top_endpoints: List[Dict[str, Any]]
    usage_by_hour: List[Dict[str, Any]]


class SICRateLimitConfigResponse(BaseModel):
    id: str
    sic_code: str
    base_requests_per_minute: int
    base_requests_per_hour: int
    base_requests_per_day: int
    data_intensity_factor: float
    real_time_factor: float
    endpoint_multipliers: Dict[str, float]
    special_config: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


class CurrentUsageResponse(BaseModel):
    tenant_id: str
    current_usage: Dict[str, int]
    active_rules: List[str]
    next_reset_times: Dict[str, datetime]


# Rate Limit Rule Management Endpoints
@router.get("/rules", response_model=List[RateLimitRuleResponse])
async def get_rate_limit_rules(
    scope: Optional[RateLimitScope] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get rate limit rules with optional filtering"""
    
    query = db.query(RateLimitRule)
    
    if scope:
        query = query.filter(RateLimitRule.scope == scope)
    
    if is_active is not None:
        query = query.filter(RateLimitRule.is_active == is_active)
    
    rules = query.order_by(
        RateLimitRule.priority.desc(),
        RateLimitRule.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return rules


@router.post("/rules", response_model=RateLimitRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_limit_rule(
    rule_data: RateLimitRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new rate limit rule"""
    
    # Validate scope-specific requirements
    if rule_data.scope in [RateLimitScope.organisation, RateLimitScope.user] and not rule_data.scope_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"scope_value is required for scope '{rule_data.scope}'"
        )
    
    # Check for duplicate rules
    existing = db.query(RateLimitRule).filter(
        RateLimitRule.rule_name == rule_data.rule_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A rule with this name already exists"
        )
    
    # Create rule
    rule = RateLimitRule(**rule_data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.get("/rules/{rule_id}", response_model=RateLimitRuleResponse)
async def get_rate_limit_rule(
    rule_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get a specific rate limit rule"""
    
    rule = db.query(RateLimitRule).filter(RateLimitRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit rule not found"
        )
    
    return rule


@router.put("/rules/{rule_id}", response_model=RateLimitRuleResponse)
async def update_rate_limit_rule(
    rule_id: str = Path(...),
    rule_update: RateLimitRuleUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a rate limit rule"""
    
    rule = db.query(RateLimitRule).filter(RateLimitRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit rule not found"
        )
    
    # Update fields
    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rate_limit_rule(
    rule_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a rate limit rule"""
    
    rule = db.query(RateLimitRule).filter(RateLimitRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit rule not found"
        )
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Rate limit rule deleted successfully"}


# Usage Monitoring Endpoints
@router.get("/usage", response_model=List[RateLimitUsageResponse])
async def get_rate_limit_usage(
    tenant_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    was_limited: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get rate limit usage logs with filtering"""
    
    query = db.query(RateLimitUsage)
    
    if tenant_id:
        query = query.filter(RateLimitUsage.tenant_id == tenant_id)
    
    if user_id:
        query = query.filter(RateLimitUsage.user_id == user_id)
    
    if was_limited is not None:
        query = query.filter(RateLimitUsage.was_limited == was_limited)
    
    if start_date:
        query = query.filter(RateLimitUsage.created_at >= start_date)
    
    if end_date:
        query = query.filter(RateLimitUsage.created_at <= end_date)
    
    usage = query.order_by(
        RateLimitUsage.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return usage


@router.get("/stats", response_model=RateLimitStatsResponse)
async def get_rate_limit_stats(
    tenant_id: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),  # Up to 7 days
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get rate limiting statistics"""
    
    from sqlalchemy import func, desc
    from datetime import timedelta
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Base query
    query = db.query(RateLimitUsage).filter(
        RateLimitUsage.created_at >= start_time,
        RateLimitUsage.created_at <= end_time
    )
    
    if tenant_id:
        query = query.filter(RateLimitUsage.tenant_id == tenant_id)
    
    # Total requests
    total_requests = query.count()
    
    # Limited requests
    limited_requests = query.filter(RateLimitUsage.was_limited == True).count()
    
    # Success rate
    success_rate = ((total_requests - limited_requests) / total_requests * 100) if total_requests > 0 else 100
    
    # Average processing time
    avg_processing_time = query.with_entities(
        func.avg(RateLimitUsage.processing_time_ms)
    ).scalar() or 0
    
    # Top endpoints by request count
    top_endpoints = db.query(
        RateLimitUsage.endpoint,
        func.count(RateLimitUsage.id).label('request_count'),
        func.sum(func.cast(RateLimitUsage.was_limited, int)).label('limited_count')
    ).filter(
        RateLimitUsage.created_at >= start_time,
        RateLimitUsage.created_at <= end_time
    )
    
    if tenant_id:
        top_endpoints = top_endpoints.filter(RateLimitUsage.tenant_id == tenant_id)
    
    top_endpoints = top_endpoints.group_by(
        RateLimitUsage.endpoint
    ).order_by(desc('request_count')).limit(10).all()
    
    top_endpoints_data = [
        {
            "endpoint": endpoint,
            "request_count": request_count,
            "limited_count": limited_count,
            "success_rate": ((request_count - limited_count) / request_count * 100) if request_count > 0 else 100
        }
        for endpoint, request_count, limited_count in top_endpoints
    ]
    
    # Usage by hour
    usage_by_hour = db.query(
        func.date_trunc('hour', RateLimitUsage.created_at).label('hour'),
        func.count(RateLimitUsage.id).label('request_count'),
        func.sum(func.cast(RateLimitUsage.was_limited, int)).label('limited_count')
    ).filter(
        RateLimitUsage.created_at >= start_time,
        RateLimitUsage.created_at <= end_time
    )
    
    if tenant_id:
        usage_by_hour = usage_by_hour.filter(RateLimitUsage.tenant_id == tenant_id)
    
    usage_by_hour = usage_by_hour.group_by('hour').order_by('hour').all()
    
    usage_by_hour_data = [
        {
            "hour": hour.isoformat(),
            "request_count": request_count,
            "limited_count": limited_count,
            "success_rate": ((request_count - limited_count) / request_count * 100) if request_count > 0 else 100
        }
        for hour, request_count, limited_count in usage_by_hour
    ]
    
    return RateLimitStatsResponse(
        total_requests=total_requests,
        limited_requests=limited_requests,
        success_rate=round(success_rate, 2),
        avg_processing_time_ms=round(float(avg_processing_time), 2),
        top_endpoints=top_endpoints_data,
        usage_by_hour=usage_by_hour_data
    )


# Current Usage and Management
@router.get("/current-usage/{tenant_id}", response_model=CurrentUsageResponse)
async def get_current_usage(
    tenant_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current rate limit usage for a tenant"""
    
    # Check authorization - users can only see their own tenant
    if current_user.organisation_id != tenant_id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view usage for this tenant"
        )
    
    # Get current usage from Redis
    usage_data = await rate_limiter_service.get_current_usage(tenant_id)
    
    # Get active rules for this tenant
    active_rules = db.query(RateLimitRule).filter(
        RateLimitRule.is_active == True
    ).filter(
        # This would need more sophisticated logic for rule matching
        (RateLimitRule.scope == RateLimitScope.organisation) & (RateLimitRule.scope_value == tenant_id) |
        (RateLimitRule.scope == RateLimitScope.global_default)
    ).all()
    
    return CurrentUsageResponse(
        tenant_id=tenant_id,
        current_usage=usage_data,
        active_rules=[rule.rule_name for rule in active_rules],
        next_reset_times={}  # This would be calculated based on active windows
    )


@router.post("/reset/{tenant_id}")
async def reset_rate_limits(
    tenant_id: str = Path(...),
    endpoint: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Reset rate limits for a tenant (admin only)"""
    
    success = await rate_limiter_service.reset_rate_limit(
        tenant_id=tenant_id,
        user_id=user_id,
        endpoint=endpoint
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limits"
        )
    
    scope = "user" if user_id else "tenant"
    target = user_id if user_id else tenant_id
    
    return {
        "message": f"Rate limits reset successfully for {scope} {target}",
        "endpoint": endpoint or "all endpoints"
    }


# Industry Configuration Management
@router.get("/sic-configs", response_model=List[SICRateLimitConfigResponse])
async def get_sic_rate_limit_configs(
    sic_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get SIC code rate limit configurations"""
    
    query = db.query(SICRateLimitConfig)
    
    if sic_code:
        query = query.filter(SICRateLimitConfig.sic_code == sic_code)
    
    if is_active is not None:
        query = query.filter(SICRateLimitConfig.is_active == is_active)
    
    configs = query.order_by(SICRateLimitConfig.sic_code).offset(skip).limit(limit).all()
    
    return configs


# Initialization and Management
@router.post("/initialize")
async def initialize_rate_limiting(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Initialize rate limiting with default rules and industry configs"""
    
    try:
        # Create default rules
        await RateLimitManager.create_default_rules(db)
        
        # Create industry-specific configurations
        await RateLimitManager.create_industry_rules(db)
        
        return {
            "message": "Rate limiting initialized successfully",
            "default_rules_created": True,
            "industry_configs_created": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize rate limiting: {str(e)}"
        )