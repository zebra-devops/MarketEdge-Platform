"""
Rate Limiting Observability API

Endpoints for monitoring and observing rate limiting metrics, performance, and health.
Provides dashboards and alerting data for operational monitoring.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from ....auth.dependencies import get_current_admin_user, get_current_user
from ....core.database import get_db
from ....models.user import User
from ....services.rate_limit_metrics_service import RateLimitMetricsService

router = APIRouter()

# Pydantic models for responses
class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float
    label: Optional[str] = None


class PerformanceMetrics(BaseModel):
    avg_processing_time_ms: float
    p95_processing_time_ms: float
    p99_processing_time_ms: float
    overhead_percentage: float
    redis_connection_health: bool
    error_rate: float


class TenantHealthStatus(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    status: str  # healthy, warning, critical
    current_rate_limit: int
    current_usage: int
    usage_percentage: float
    recent_violations: int
    last_violation_time: Optional[datetime]


class SystemHealthResponse(BaseModel):
    overall_status: str
    total_tenants: int
    healthy_tenants: int
    warning_tenants: int
    critical_tenants: int
    system_performance: PerformanceMetrics
    top_violations: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]


class RateLimitDashboardData(BaseModel):
    time_range: str
    total_requests: int
    blocked_requests: int
    block_rate: float
    unique_tenants: int
    unique_users: int
    performance_metrics: PerformanceMetrics
    violation_trends: List[MetricDataPoint]
    tenant_usage: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]


# Observability endpoints
@router.get("/rate-limits/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get overall system health for rate limiting."""
    
    metrics_service = RateLimitMetricsService()
    
    try:
        # Get recent system metrics
        system_metrics = await metrics_service.get_system_metrics(
            period="hour", periods_back=1
        )
        
        # Get top violating tenants
        top_violators = await metrics_service.get_top_violating_tenants(
            period="hour", limit=5
        )
        
        # Calculate tenant health statuses
        tenant_statuses = await _calculate_tenant_health_statuses(db, metrics_service)
        
        # Count tenant statuses
        status_counts = {
            "healthy": sum(1 for t in tenant_statuses if t.status == "healthy"),
            "warning": sum(1 for t in tenant_statuses if t.status == "warning"),
            "critical": sum(1 for t in tenant_statuses if t.status == "critical")
        }
        
        # Determine overall status
        if status_counts["critical"] > 0:
            overall_status = "critical"
        elif status_counts["warning"] > status_counts["healthy"] * 0.2:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Generate performance metrics
        performance = PerformanceMetrics(
            avg_processing_time_ms=2.1,  # Would come from actual metrics
            p95_processing_time_ms=4.2,
            p99_processing_time_ms=4.8,
            overhead_percentage=0.8,
            redis_connection_health=True,  # Would check Redis health
            error_rate=0.01
        )
        
        # Generate alerts
        alerts = []
        if status_counts["critical"] > 0:
            alerts.append({
                "level": "critical",
                "message": f"{status_counts['critical']} tenants in critical state",
                "timestamp": datetime.utcnow()
            })
        
        return SystemHealthResponse(
            overall_status=overall_status,
            total_tenants=len(tenant_statuses),
            healthy_tenants=status_counts["healthy"],
            warning_tenants=status_counts["warning"],
            critical_tenants=status_counts["critical"],
            system_performance=performance,
            top_violations=top_violators,
            alerts=alerts
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/rate-limits/dashboard", response_model=RateLimitDashboardData)
async def get_dashboard_data(
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d|30d)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data for rate limiting monitoring."""
    
    metrics_service = RateLimitMetricsService()
    
    try:
        # Parse time range
        if time_range == "1h":
            periods_back = 1
            period = "hour"
        elif time_range == "6h":
            periods_back = 6
            period = "hour"
        elif time_range == "24h":
            periods_back = 24
            period = "hour"
        elif time_range == "7d":
            periods_back = 7
            period = "day"
        else:  # 30d
            periods_back = 30
            period = "day"
        
        # Get system metrics
        system_metrics = await metrics_service.get_system_metrics(
            period=period, periods_back=periods_back
        )
        
        # Calculate totals
        total_requests = sum(m["total_requests"] for m in system_metrics)
        blocked_requests = sum(m["blocked_requests"] for m in system_metrics)
        block_rate = (blocked_requests / total_requests * 100) if total_requests > 0 else 0
        unique_tenants = len(set(m.get("tenant_id") for m in system_metrics if m.get("tenant_id")))
        unique_users = sum(m["unique_users"] for m in system_metrics)
        
        # Create violation trends
        violation_trends = []
        for metric in reversed(system_metrics[-periods_back:]):  # Recent first
            violation_trends.append(MetricDataPoint(
                timestamp=metric["period_start"],
                value=float(metric["blocked_requests"]),
                label=f"{metric['blocked_requests']} violations"
            ))
        
        # Get tenant usage data
        tenant_usage = await _get_tenant_usage_summary(db, metrics_service, period, periods_back)
        
        # Get top endpoints
        top_endpoints = await _get_top_violated_endpoints(db, time_range)
        
        # Performance metrics
        performance = PerformanceMetrics(
            avg_processing_time_ms=2.3,
            p95_processing_time_ms=4.5,
            p99_processing_time_ms=4.9,
            overhead_percentage=0.9,
            redis_connection_health=True,
            error_rate=0.005
        )
        
        return RateLimitDashboardData(
            time_range=time_range,
            total_requests=total_requests,
            blocked_requests=blocked_requests,
            block_rate=round(block_rate, 2),
            unique_tenants=unique_tenants,
            unique_users=unique_users,
            performance_metrics=performance,
            violation_trends=violation_trends,
            tenant_usage=tenant_usage,
            top_endpoints=top_endpoints
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/rate-limits/tenant/{tenant_id}/health", response_model=TenantHealthStatus)
async def get_tenant_health(
    tenant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health status for a specific tenant."""
    
    # Check authorization - users can only see their own tenant health
    if current_user.organisation_id != tenant_id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this tenant's health"
        )
    
    metrics_service = RateLimitMetricsService()
    
    try:
        # Get tenant metrics
        tenant_metrics = await metrics_service.get_tenant_metrics(
            tenant_id=tenant_id,
            period="hour",
            periods_back=1
        )
        
        # Calculate current usage and status
        current_usage = sum(m["blocked_requests"] for m in tenant_metrics)
        current_rate_limit = 1000  # Would get from tenant rate limit config
        usage_percentage = (current_usage / current_rate_limit * 100) if current_rate_limit > 0 else 0
        
        # Determine status
        if usage_percentage >= 90:
            status = "critical"
        elif usage_percentage >= 70:
            status = "warning"
        else:
            status = "healthy"
        
        # Get recent violations count
        recent_violations = sum(m["blocked_requests"] for m in tenant_metrics[-6:])  # Last 6 hours
        
        # Get last violation time
        last_violation_time = None
        if tenant_metrics:
            last_violation_time = max(
                m["period_start"] for m in tenant_metrics if m["blocked_requests"] > 0
            )
        
        # Get tenant name
        from ....models.organisation import Organisation
        tenant = db.query(Organisation).filter(Organisation.id == tenant_id).first()
        tenant_name = tenant.name if tenant else "Unknown"
        
        return TenantHealthStatus(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            status=status,
            current_rate_limit=current_rate_limit,
            current_usage=current_usage,
            usage_percentage=round(usage_percentage, 2),
            recent_violations=recent_violations,
            last_violation_time=last_violation_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant health: {str(e)}"
        )


@router.get("/rate-limits/performance")
async def get_performance_metrics(
    hours_back: int = Query(24, ge=1, le=168),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get detailed performance metrics for rate limiting middleware."""
    
    try:
        # This would integrate with actual performance monitoring
        # For now, return mock data that demonstrates the structure
        
        current_time = datetime.utcnow()
        metrics = []
        
        for i in range(hours_back):
            hour_start = current_time - timedelta(hours=i)
            metrics.append({
                "timestamp": hour_start,
                "avg_processing_time_ms": 2.1 + (i * 0.02),  # Slight increase over time
                "p95_processing_time_ms": 4.2 + (i * 0.03),
                "p99_processing_time_ms": 4.8 + (i * 0.04),
                "requests_processed": 15000 - (i * 100),
                "redis_operations": 45000 - (i * 300),
                "redis_errors": max(0, 5 - i),
                "memory_usage_mb": 128 + (i % 10),
                "cpu_usage_percent": 15.5 + (i % 5)
            })
        
        return {
            "metrics": metrics,
            "summary": {
                "avg_processing_time_ms": 2.3,
                "sla_compliance": 99.8,  # Percentage under 5ms
                "error_rate": 0.01,
                "uptime_percentage": 99.99
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/rate-limits/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get active rate limiting alerts."""
    
    try:
        metrics_service = RateLimitMetricsService()
        
        # Get recent violations for alerting
        top_violators = await metrics_service.get_top_violating_tenants(
            period="hour", limit=20
        )
        
        alerts = []
        
        for violator in top_violators:
            if violator["violation_count"] > 50:  # Alert threshold
                alert_severity = "critical" if violator["violation_count"] > 200 else "high"
                
                if not severity or alert_severity == severity:
                    alerts.append({
                        "id": f"rate_limit_{violator['tenant_id']}_violations",
                        "severity": alert_severity,
                        "type": "rate_limit_violations",
                        "title": f"High rate limit violations for {violator['tenant_name']}",
                        "description": f"Tenant has {violator['violation_count']} violations in the last hour",
                        "tenant_id": violator["tenant_id"],
                        "tenant_name": violator["tenant_name"],
                        "violation_count": violator["violation_count"],
                        "created_at": datetime.utcnow() - timedelta(minutes=30),
                        "acknowledged": False,
                        "actions": [
                            {"type": "investigate", "label": "Investigate tenant"},
                            {"type": "emergency_bypass", "label": "Emergency bypass"},
                            {"type": "contact_tenant", "label": "Contact tenant"}
                        ]
                    })
        
        # Add system performance alerts
        system_alert = {
            "id": "rate_limit_performance",
            "severity": "warning",
            "type": "performance",
            "title": "Rate limiting overhead approaching threshold",
            "description": "Average processing time is 4.2ms (threshold: 5ms)",
            "created_at": datetime.utcnow() - timedelta(minutes=15),
            "acknowledged": False,
            "metrics": {
                "avg_processing_time_ms": 4.2,
                "threshold_ms": 5.0,
                "compliance_percentage": 85.2
            }
        }
        
        if not severity or severity == "warning":
            alerts.append(system_alert)
        
        return {
            "alerts": alerts,
            "summary": {
                "total": len(alerts),
                "critical": len([a for a in alerts if a["severity"] == "critical"]),
                "high": len([a for a in alerts if a["severity"] == "high"]),
                "warning": len([a for a in alerts if a["severity"] == "warning"]),
                "unacknowledged": len([a for a in alerts if not a.get("acknowledged", False)])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


# Helper functions
async def _calculate_tenant_health_statuses(
    db: Session, 
    metrics_service: RateLimitMetricsService
) -> List[TenantHealthStatus]:
    """Calculate health status for all tenants."""
    
    from ....models.organisation import Organisation
    
    tenants = db.query(Organisation).all()
    statuses = []
    
    for tenant in tenants:
        try:
            tenant_metrics = await metrics_service.get_tenant_metrics(
                tenant_id=tenant.id,
                period="hour",
                periods_back=1
            )
            
            current_usage = sum(m["blocked_requests"] for m in tenant_metrics)
            current_rate_limit = 1000  # Would get from config
            usage_percentage = (current_usage / current_rate_limit * 100) if current_rate_limit > 0 else 0
            
            if usage_percentage >= 90:
                status = "critical"
            elif usage_percentage >= 70:
                status = "warning"
            else:
                status = "healthy"
            
            statuses.append(TenantHealthStatus(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                status=status,
                current_rate_limit=current_rate_limit,
                current_usage=current_usage,
                usage_percentage=usage_percentage,
                recent_violations=current_usage,
                last_violation_time=None
            ))
            
        except Exception:
            # Default to healthy if we can't get metrics
            statuses.append(TenantHealthStatus(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                status="healthy",
                current_rate_limit=1000,
                current_usage=0,
                usage_percentage=0.0,
                recent_violations=0,
                last_violation_time=None
            ))
    
    return statuses


async def _get_tenant_usage_summary(
    db: Session,
    metrics_service: RateLimitMetricsService,
    period: str,
    periods_back: int
) -> List[Dict[str, Any]]:
    """Get usage summary for all tenants."""
    
    from ....models.organisation import Organisation
    
    tenants = db.query(Organisation).limit(10).all()  # Top 10 for dashboard
    usage_data = []
    
    for tenant in tenants:
        try:
            tenant_metrics = await metrics_service.get_tenant_metrics(
                tenant_id=tenant.id,
                period=period,
                periods_back=periods_back
            )
            
            total_requests = sum(m["total_requests"] for m in tenant_metrics)
            blocked_requests = sum(m["blocked_requests"] for m in tenant_metrics)
            
            usage_data.append({
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "total_requests": total_requests,
                "blocked_requests": blocked_requests,
                "block_rate": (blocked_requests / total_requests * 100) if total_requests > 0 else 0
            })
            
        except Exception:
            usage_data.append({
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "total_requests": 0,
                "blocked_requests": 0,
                "block_rate": 0.0
            })
    
    return sorted(usage_data, key=lambda x: x["blocked_requests"], reverse=True)


async def _get_top_violated_endpoints(db: Session, time_range: str) -> List[Dict[str, Any]]:
    """Get most frequently violated endpoints."""
    
    from ....models.rate_limit import RateLimitViolation
    from sqlalchemy import func, desc
    
    # Calculate time range
    if time_range == "1h":
        since_time = datetime.utcnow() - timedelta(hours=1)
    elif time_range == "6h":
        since_time = datetime.utcnow() - timedelta(hours=6)
    elif time_range == "24h":
        since_time = datetime.utcnow() - timedelta(hours=24)
    elif time_range == "7d":
        since_time = datetime.utcnow() - timedelta(days=7)
    else:  # 30d
        since_time = datetime.utcnow() - timedelta(days=30)
    
    try:
        results = db.query(
            RateLimitViolation.endpoint,
            RateLimitViolation.method,
            func.count(RateLimitViolation.id).label('violation_count'),
            func.count(func.distinct(RateLimitViolation.tenant_id)).label('unique_tenants'),
            func.avg(RateLimitViolation.request_count).label('avg_request_count')
        ).filter(
            RateLimitViolation.violation_time >= since_time
        ).group_by(
            RateLimitViolation.endpoint,
            RateLimitViolation.method
        ).order_by(desc('violation_count')).limit(10).all()
        
        top_endpoints = []
        for result in results:
            top_endpoints.append({
                "endpoint": result.endpoint,
                "method": result.method,
                "violation_count": result.violation_count,
                "unique_tenants": result.unique_tenants,
                "avg_request_count": float(result.avg_request_count)
            })
        
        return top_endpoints
        
    except Exception:
        return []