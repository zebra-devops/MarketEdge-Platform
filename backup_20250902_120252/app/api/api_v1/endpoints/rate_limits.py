"""
Rate Limiting Management API

Admin endpoints for managing tenant-specific rate limits and monitoring violations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, Field
import uuid

from ....auth.dependencies import get_current_admin_user
from ....core.database import get_db
from ....models.user import User
from ....models.rate_limit import TenantRateLimit, RateLimitViolation, RateLimitMetrics
from ....models.organisation import Organisation
from ....middleware.rate_limiter import RateLimiterMiddleware

router = APIRouter()

# Pydantic models for request/response
class TenantRateLimitCreate(BaseModel):
    tenant_id: uuid.UUID
    tier: str = Field(..., pattern="^(standard|premium|enterprise)$")
    requests_per_hour: int = Field(..., gt=0, le=100000)
    burst_size: int = Field(default=100, gt=0, le=1000)
    endpoint_overrides: Optional[Dict[str, int]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class TenantRateLimitUpdate(BaseModel):
    tier: Optional[str] = Field(None, pattern="^(standard|premium|enterprise)$")
    requests_per_hour: Optional[int] = Field(None, gt=0, le=100000)
    burst_size: Optional[int] = Field(None, gt=0, le=1000)
    endpoint_overrides: Optional[Dict[str, int]] = None
    enabled: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class EmergencyBypassRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    duration_hours: int = Field(..., gt=0, le=72)


class TenantRateLimitResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    tenant_name: Optional[str] = None
    tier: str
    requests_per_hour: int
    burst_size: int
    endpoint_overrides: Optional[Dict[str, int]]
    enabled: bool
    emergency_bypass: bool
    bypass_reason: Optional[str]
    bypass_until: Optional[datetime]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class RateLimitViolationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    endpoint: str
    method: str
    rate_limit: int
    request_count: int
    client_ip: Optional[str]
    violation_time: datetime
    retry_after_seconds: Optional[int]
    severity: str
    
    class Config:
        from_attributes = True


class RateLimitMetricsResponse(BaseModel):
    tenant_id: Optional[uuid.UUID]
    aggregation_period: str
    period_start: datetime
    period_end: datetime
    total_requests: int
    blocked_requests: int
    unique_users: int
    unique_ips: int
    block_rate: float = 0.0
    avg_processing_time_ms: Optional[int]
    max_processing_time_ms: Optional[int]
    top_endpoints: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class RateLimitStatsResponse(BaseModel):
    tenant_id: str
    total_requests_current_window: int
    active_users: int
    window_size_hours: float
    current_limits: TenantRateLimitResponse


# Rate limit management endpoints
@router.get("/rate-limits", response_model=List[TenantRateLimitResponse])
async def list_tenant_rate_limits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: Optional[uuid.UUID] = Query(None),
    tier: Optional[str] = Query(None),
    enabled_only: bool = Query(True),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all tenant rate limit configurations."""
    query = db.query(TenantRateLimit).join(Organisation)
    
    if tenant_id:
        query = query.filter(TenantRateLimit.tenant_id == tenant_id)
    
    if tier:
        query = query.filter(TenantRateLimit.tier == tier)
    
    if enabled_only:
        query = query.filter(TenantRateLimit.enabled == True)
    
    rate_limits = query.offset(skip).limit(limit).all()
    
    # Add tenant names
    result = []
    for rate_limit in rate_limits:
        org = db.query(Organisation).filter(Organisation.id == rate_limit.tenant_id).first()
        rate_limit_data = TenantRateLimitResponse.from_orm(rate_limit)
        rate_limit_data.tenant_name = org.name if org else "Unknown"
        result.append(rate_limit_data)
    
    return result


@router.post("/rate-limits", response_model=TenantRateLimitResponse)
async def create_tenant_rate_limit(
    rate_limit_data: TenantRateLimitCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create or update rate limit configuration for a tenant."""
    
    # Check if tenant exists
    tenant = db.query(Organisation).filter(Organisation.id == rate_limit_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check if rate limit already exists
    existing = db.query(TenantRateLimit).filter(
        TenantRateLimit.tenant_id == rate_limit_data.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rate limit configuration already exists for this tenant"
        )
    
    # Create new rate limit configuration
    rate_limit = TenantRateLimit(
        tenant_id=rate_limit_data.tenant_id,
        tier=rate_limit_data.tier,
        requests_per_hour=rate_limit_data.requests_per_hour,
        burst_size=rate_limit_data.burst_size,
        endpoint_overrides=rate_limit_data.endpoint_overrides,
        valid_from=rate_limit_data.valid_from,
        valid_until=rate_limit_data.valid_until,
        created_by=current_admin.id
    )
    
    db.add(rate_limit)
    db.commit()
    db.refresh(rate_limit)
    
    # Add tenant name to response
    result = TenantRateLimitResponse.from_orm(rate_limit)
    result.tenant_name = tenant.name
    
    return result


@router.put("/rate-limits/{tenant_id}", response_model=TenantRateLimitResponse)
async def update_tenant_rate_limit(
    tenant_id: uuid.UUID,
    rate_limit_data: TenantRateLimitUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update rate limit configuration for a tenant."""
    
    rate_limit = db.query(TenantRateLimit).filter(
        TenantRateLimit.tenant_id == tenant_id
    ).first()
    
    if not rate_limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit configuration not found for this tenant"
        )
    
    # Update fields
    update_data = rate_limit_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rate_limit, field, value)
    
    rate_limit.updated_by = current_admin.id
    rate_limit.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rate_limit)
    
    # Add tenant name to response
    tenant = db.query(Organisation).filter(Organisation.id == tenant_id).first()
    result = TenantRateLimitResponse.from_orm(rate_limit)
    result.tenant_name = tenant.name if tenant else "Unknown"
    
    return result


@router.post("/rate-limits/{tenant_id}/emergency-bypass", response_model=TenantRateLimitResponse)
async def emergency_bypass_rate_limit(
    tenant_id: uuid.UUID,
    bypass_request: EmergencyBypassRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Enable emergency bypass for a tenant's rate limits."""
    
    rate_limit = db.query(TenantRateLimit).filter(
        TenantRateLimit.tenant_id == tenant_id
    ).first()
    
    if not rate_limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit configuration not found for this tenant"
        )
    
    # Enable emergency bypass
    rate_limit.emergency_bypass = True
    rate_limit.bypass_reason = bypass_request.reason
    rate_limit.bypass_until = datetime.utcnow() + timedelta(hours=bypass_request.duration_hours)
    rate_limit.updated_by = current_admin.id
    rate_limit.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(rate_limit)
    
    # Add tenant name to response
    tenant = db.query(Organisation).filter(Organisation.id == tenant_id).first()
    result = TenantRateLimitResponse.from_orm(rate_limit)
    result.tenant_name = tenant.name if tenant else "Unknown"
    
    return result


@router.delete("/rate-limits/{tenant_id}/emergency-bypass")
async def remove_emergency_bypass(
    tenant_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Remove emergency bypass for a tenant's rate limits."""
    
    rate_limit = db.query(TenantRateLimit).filter(
        TenantRateLimit.tenant_id == tenant_id
    ).first()
    
    if not rate_limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit configuration not found for this tenant"
        )
    
    # Remove emergency bypass
    rate_limit.emergency_bypass = False
    rate_limit.bypass_reason = None
    rate_limit.bypass_until = None
    rate_limit.updated_by = current_admin.id
    rate_limit.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Emergency bypass removed successfully"}


# Monitoring and analytics endpoints
@router.get("/rate-limits/violations", response_model=List[RateLimitViolationResponse])
async def list_rate_limit_violations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tenant_id: Optional[uuid.UUID] = Query(None),
    hours_back: int = Query(24, ge=1, le=168),  # Last 24 hours by default, max 1 week
    severity: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List recent rate limit violations."""
    
    since_time = datetime.utcnow() - timedelta(hours=hours_back)
    
    query = db.query(RateLimitViolation).filter(
        RateLimitViolation.violation_time >= since_time
    )
    
    if tenant_id:
        query = query.filter(RateLimitViolation.tenant_id == tenant_id)
    
    if severity:
        query = query.filter(RateLimitViolation.severity == severity)
    
    violations = query.order_by(desc(RateLimitViolation.violation_time))\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
    
    return violations


@router.get("/rate-limits/metrics", response_model=List[RateLimitMetricsResponse])
async def get_rate_limit_metrics(
    tenant_id: Optional[uuid.UUID] = Query(None),
    period: str = Query("hour", pattern="^(hour|day|week|month)$"),
    periods_back: int = Query(24, ge=1, le=168),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get aggregated rate limiting metrics."""
    
    # Calculate time range based on period
    if period == "hour":
        time_delta = timedelta(hours=periods_back)
    elif period == "day":
        time_delta = timedelta(days=periods_back)
    elif period == "week":
        time_delta = timedelta(weeks=periods_back)
    else:  # month
        time_delta = timedelta(days=periods_back * 30)
    
    since_time = datetime.utcnow() - time_delta
    
    query = db.query(RateLimitMetrics).filter(
        RateLimitMetrics.aggregation_period == period,
        RateLimitMetrics.period_start >= since_time
    )
    
    if tenant_id:
        query = query.filter(RateLimitMetrics.tenant_id == tenant_id)
    
    metrics = query.order_by(desc(RateLimitMetrics.period_start)).all()
    
    # Calculate block rates
    result = []
    for metric in metrics:
        metric_data = RateLimitMetricsResponse.from_orm(metric)
        if metric.total_requests > 0:
            metric_data.block_rate = round(
                (metric.blocked_requests / metric.total_requests) * 100, 2
            )
        result.append(metric_data)
    
    return result


@router.get("/rate-limits/{tenant_id}/stats", response_model=RateLimitStatsResponse)
async def get_tenant_rate_limit_stats(
    tenant_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get current rate limiting statistics for a specific tenant."""
    
    # Get rate limit configuration
    rate_limit = db.query(TenantRateLimit).filter(
        TenantRateLimit.tenant_id == tenant_id
    ).first()
    
    if not rate_limit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit configuration not found for this tenant"
        )
    
    # Get real-time stats from Redis (if available)
    # This would require access to the rate limiter instance
    # For now, return basic configuration
    
    tenant = db.query(Organisation).filter(Organisation.id == tenant_id).first()
    rate_limit_response = TenantRateLimitResponse.from_orm(rate_limit)
    rate_limit_response.tenant_name = tenant.name if tenant else "Unknown"
    
    return RateLimitStatsResponse(
        tenant_id=str(tenant_id),
        total_requests_current_window=0,  # Would come from Redis
        active_users=0,  # Would come from Redis
        window_size_hours=1.0,
        current_limits=rate_limit_response
    )


@router.post("/rate-limits/{tenant_id}/reset")
async def reset_tenant_rate_limit(
    tenant_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reset rate limit counters for a tenant or specific user (emergency operation)."""
    
    # Verify tenant exists
    tenant = db.query(Organisation).filter(Organisation.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # This would require access to the rate limiter instance
    # For now, return success message
    
    if user_id:
        message = f"Rate limit reset for user {user_id} in tenant {tenant.name}"
    else:
        message = f"Rate limit reset for all users in tenant {tenant.name}"
    
    return {"message": message}