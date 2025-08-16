"""
Rate Limit Metrics Service

Service for collecting, aggregating, and reporting rate limiting metrics.
Provides observability into rate limiting performance and violations.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
import uuid

from ..core.database import get_db
from ..models.rate_limit import RateLimitViolation, RateLimitMetrics
from ..models.organisation import Organisation
from ..data.cache.redis_cache import RedisCacheManager

logger = logging.getLogger(__name__)


class RateLimitMetricsService:
    """
    Service for collecting and aggregating rate limiting metrics.
    
    Provides real-time and historical metrics for monitoring rate limiting
    effectiveness and identifying patterns.
    """
    
    def __init__(self, redis_manager: Optional[RedisCacheManager] = None):
        self.redis_manager = redis_manager
        
    async def log_violation(
        self,
        tenant_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        endpoint: str,
        method: str,
        rate_limit: int,
        request_count: int,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        retry_after_seconds: Optional[int] = None
    ) -> uuid.UUID:
        """Log a rate limit violation."""
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Determine severity based on how much the limit was exceeded
            if request_count > rate_limit * 2:
                severity = "critical"
            elif request_count > rate_limit * 1.5:
                severity = "high"
            elif request_count > rate_limit * 1.2:
                severity = "medium"
            else:
                severity = "low"
            
            # Create violation record
            violation = RateLimitViolation(
                tenant_id=tenant_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                rate_limit=rate_limit,
                request_count=request_count,
                client_ip=client_ip,
                user_agent=user_agent[:1000] if user_agent else None,  # Truncate long user agents
                headers=self._sanitize_headers(headers) if headers else None,
                window_start=datetime.utcnow() - timedelta(hours=1),
                window_end=datetime.utcnow(),
                retry_after_seconds=retry_after_seconds,
                severity=severity
            )
            
            db.add(violation)
            db.commit()
            db.refresh(violation)
            
            # Update real-time metrics in Redis
            if self.redis_manager:
                await self._update_realtime_metrics(tenant_id, endpoint, severity)
            
            logger.info(
                "Rate limit violation logged",
                extra={
                    "event": "rate_limit_violation_logged",
                    "violation_id": str(violation.id),
                    "tenant_id": str(tenant_id),
                    "endpoint": endpoint,
                    "severity": severity,
                    "request_count": request_count,
                    "rate_limit": rate_limit
                }
            )
            
            return violation.id
            
        except Exception as e:
            logger.error(
                "Failed to log rate limit violation",
                extra={
                    "event": "violation_logging_error",
                    "error": str(e),
                    "tenant_id": str(tenant_id),
                    "endpoint": endpoint
                },
                exc_info=True
            )
            raise
        finally:
            db.close()
    
    def _sanitize_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize headers to remove sensitive information."""
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'proxy-authorization', 'x-csrf-token'
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _update_realtime_metrics(
        self, 
        tenant_id: uuid.UUID, 
        endpoint: str, 
        severity: str
    ):
        """Update real-time metrics in Redis."""
        if not self.redis_manager:
            return
        
        try:
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            # Update violation count
            violation_key = f"metrics:violations:{tenant_id}:{current_hour.isoformat()}"
            await self.redis_manager.increment(violation_key)
            await self.redis_manager.expire(violation_key, 86400)  # 24 hours
            
            # Update endpoint metrics
            endpoint_key = f"metrics:endpoints:{tenant_id}:{endpoint}:{current_hour.isoformat()}"
            await self.redis_manager.increment(endpoint_key)
            await self.redis_manager.expire(endpoint_key, 86400)
            
            # Update severity metrics
            severity_key = f"metrics:severity:{severity}:{current_hour.isoformat()}"
            await self.redis_manager.increment(severity_key)
            await self.redis_manager.expire(severity_key, 86400)
            
        except Exception as e:
            logger.error(
                "Failed to update real-time metrics",
                extra={
                    "event": "realtime_metrics_error",
                    "error": str(e),
                    "tenant_id": str(tenant_id)
                }
            )
    
    async def aggregate_metrics(
        self,
        period: str = "hour",
        batch_size: int = 100
    ) -> int:
        """
        Aggregate rate limiting metrics for the specified period.
        
        Args:
            period: Aggregation period ('hour', 'day', 'week', 'month')
            batch_size: Number of time periods to process at once
            
        Returns:
            Number of metric records created/updated
        """
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Calculate time range based on period
            now = datetime.utcnow()
            
            if period == "hour":
                time_delta = timedelta(hours=1)
                truncate_func = func.date_trunc('hour', RateLimitViolation.violation_time)
            elif period == "day":
                time_delta = timedelta(days=1)
                truncate_func = func.date_trunc('day', RateLimitViolation.violation_time)
            elif period == "week":
                time_delta = timedelta(weeks=1)
                truncate_func = func.date_trunc('week', RateLimitViolation.violation_time)
            else:  # month
                time_delta = timedelta(days=30)
                truncate_func = func.date_trunc('month', RateLimitViolation.violation_time)
            
            # Find periods that need aggregation
            cutoff_time = now - (time_delta * batch_size)
            
            # Get violations grouped by tenant and period
            violation_query = db.query(
                RateLimitViolation.tenant_id,
                truncate_func.label('period_start'),
                func.count(RateLimitViolation.id).label('total_violations'),
                func.count(func.distinct(RateLimitViolation.user_id)).label('unique_users'),
                func.count(func.distinct(RateLimitViolation.client_ip)).label('unique_ips'),
                func.json_agg(
                    func.json_build_object(
                        'endpoint', RateLimitViolation.endpoint,
                        'count', func.count(RateLimitViolation.id)
                    )
                ).label('endpoints')
            ).filter(
                RateLimitViolation.violation_time >= cutoff_time,
                RateLimitViolation.violation_time < now
            ).group_by(
                RateLimitViolation.tenant_id,
                truncate_func
            ).all()
            
            records_created = 0
            
            for violation_data in violation_query:
                period_end = violation_data.period_start + time_delta
                
                # Check if metrics record already exists
                existing_metric = db.query(RateLimitMetrics).filter(
                    RateLimitMetrics.tenant_id == violation_data.tenant_id,
                    RateLimitMetrics.aggregation_period == period,
                    RateLimitMetrics.period_start == violation_data.period_start
                ).first()
                
                if existing_metric:
                    # Update existing record
                    existing_metric.blocked_requests = violation_data.total_violations
                    existing_metric.unique_users = violation_data.unique_users
                    existing_metric.unique_ips = violation_data.unique_ips
                    existing_metric.top_endpoints = violation_data.endpoints
                    existing_metric.updated_at = now
                else:
                    # Create new record
                    new_metric = RateLimitMetrics(
                        tenant_id=violation_data.tenant_id,
                        aggregation_period=period,
                        period_start=violation_data.period_start,
                        period_end=period_end,
                        total_requests=0,  # Would need additional tracking
                        blocked_requests=violation_data.total_violations,
                        unique_users=violation_data.unique_users,
                        unique_ips=violation_data.unique_ips,
                        top_endpoints=violation_data.endpoints
                    )
                    db.add(new_metric)
                    records_created += 1
            
            # Also create system-wide metrics (tenant_id = None)
            system_violations = db.query(
                truncate_func.label('period_start'),
                func.count(RateLimitViolation.id).label('total_violations'),
                func.count(func.distinct(RateLimitViolation.tenant_id)).label('unique_tenants'),
                func.count(func.distinct(RateLimitViolation.user_id)).label('unique_users'),
                func.count(func.distinct(RateLimitViolation.client_ip)).label('unique_ips')
            ).filter(
                RateLimitViolation.violation_time >= cutoff_time,
                RateLimitViolation.violation_time < now
            ).group_by(truncate_func).all()
            
            for system_data in system_violations:
                period_end = system_data.period_start + time_delta
                
                existing_system_metric = db.query(RateLimitMetrics).filter(
                    RateLimitMetrics.tenant_id.is_(None),
                    RateLimitMetrics.aggregation_period == period,
                    RateLimitMetrics.period_start == system_data.period_start
                ).first()
                
                if existing_system_metric:
                    existing_system_metric.blocked_requests = system_data.total_violations
                    existing_system_metric.unique_users = system_data.unique_users
                    existing_system_metric.unique_ips = system_data.unique_ips
                    existing_system_metric.updated_at = now
                else:
                    new_system_metric = RateLimitMetrics(
                        tenant_id=None,
                        aggregation_period=period,
                        period_start=system_data.period_start,
                        period_end=period_end,
                        total_requests=0,
                        blocked_requests=system_data.total_violations,
                        unique_users=system_data.unique_users,
                        unique_ips=system_data.unique_ips
                    )
                    db.add(new_system_metric)
                    records_created += 1
            
            db.commit()
            
            logger.info(
                "Rate limiting metrics aggregated",
                extra={
                    "event": "metrics_aggregated",
                    "period": period,
                    "records_created": records_created,
                    "violations_processed": len(violation_query)
                }
            )
            
            return records_created
            
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to aggregate rate limiting metrics",
                extra={
                    "event": "metrics_aggregation_error",
                    "error": str(e),
                    "period": period
                },
                exc_info=True
            )
            raise
        finally:
            db.close()
    
    async def get_tenant_metrics(
        self,
        tenant_id: uuid.UUID,
        period: str = "hour",
        periods_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Get metrics for a specific tenant."""
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            if period == "hour":
                time_delta = timedelta(hours=periods_back)
            elif period == "day":
                time_delta = timedelta(days=periods_back)
            elif period == "week":
                time_delta = timedelta(weeks=periods_back)
            else:  # month
                time_delta = timedelta(days=periods_back * 30)
            
            since_time = now - time_delta
            
            metrics = db.query(RateLimitMetrics).filter(
                RateLimitMetrics.tenant_id == tenant_id,
                RateLimitMetrics.aggregation_period == period,
                RateLimitMetrics.period_start >= since_time
            ).order_by(desc(RateLimitMetrics.period_start)).all()
            
            result = []
            for metric in metrics:
                result.append({
                    "period_start": metric.period_start,
                    "period_end": metric.period_end,
                    "total_requests": metric.total_requests,
                    "blocked_requests": metric.blocked_requests,
                    "unique_users": metric.unique_users,
                    "unique_ips": metric.unique_ips,
                    "block_rate": (metric.blocked_requests / metric.total_requests * 100) 
                                if metric.total_requests > 0 else 0,
                    "avg_processing_time_ms": metric.avg_processing_time_ms,
                    "max_processing_time_ms": metric.max_processing_time_ms,
                    "top_endpoints": metric.top_endpoints
                })
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to get tenant metrics",
                extra={
                    "event": "get_tenant_metrics_error",
                    "error": str(e),
                    "tenant_id": str(tenant_id)
                },
                exc_info=True
            )
            raise
        finally:
            db.close()
    
    async def get_system_metrics(
        self,
        period: str = "hour",
        periods_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Get system-wide rate limiting metrics."""
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            if period == "hour":
                time_delta = timedelta(hours=periods_back)
            elif period == "day":
                time_delta = timedelta(days=periods_back)
            elif period == "week":
                time_delta = timedelta(weeks=periods_back)
            else:  # month
                time_delta = timedelta(days=periods_back * 30)
            
            since_time = now - time_delta
            
            metrics = db.query(RateLimitMetrics).filter(
                RateLimitMetrics.tenant_id.is_(None),
                RateLimitMetrics.aggregation_period == period,
                RateLimitMetrics.period_start >= since_time
            ).order_by(desc(RateLimitMetrics.period_start)).all()
            
            result = []
            for metric in metrics:
                result.append({
                    "period_start": metric.period_start,
                    "period_end": metric.period_end,
                    "total_requests": metric.total_requests,
                    "blocked_requests": metric.blocked_requests,
                    "unique_users": metric.unique_users,
                    "unique_ips": metric.unique_ips,
                    "block_rate": (metric.blocked_requests / metric.total_requests * 100)
                                if metric.total_requests > 0 else 0,
                    "redis_errors": metric.redis_errors,
                    "bypass_events": metric.bypass_events
                })
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to get system metrics",
                extra={
                    "event": "get_system_metrics_error",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        finally:
            db.close()
    
    async def get_top_violating_tenants(
        self,
        period: str = "day",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get tenants with the most rate limit violations."""
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Calculate time range
            if period == "hour":
                time_delta = timedelta(hours=1)
            elif period == "day":
                time_delta = timedelta(days=1)
            elif period == "week":
                time_delta = timedelta(weeks=1)
            else:  # month
                time_delta = timedelta(days=30)
            
            since_time = datetime.utcnow() - time_delta
            
            # Query for top violating tenants
            results = db.query(
                RateLimitViolation.tenant_id,
                Organisation.name.label('tenant_name'),
                func.count(RateLimitViolation.id).label('violation_count'),
                func.count(func.distinct(RateLimitViolation.user_id)).label('unique_users'),
                func.avg(RateLimitViolation.request_count).label('avg_request_count'),
                func.max(RateLimitViolation.request_count).label('max_request_count')
            ).join(
                Organisation, RateLimitViolation.tenant_id == Organisation.id
            ).filter(
                RateLimitViolation.violation_time >= since_time
            ).group_by(
                RateLimitViolation.tenant_id, Organisation.name
            ).order_by(
                desc('violation_count')
            ).limit(limit).all()
            
            top_violators = []
            for result in results:
                top_violators.append({
                    "tenant_id": str(result.tenant_id),
                    "tenant_name": result.tenant_name,
                    "violation_count": result.violation_count,
                    "unique_users": result.unique_users,
                    "avg_request_count": float(result.avg_request_count),
                    "max_request_count": result.max_request_count
                })
            
            return top_violators
            
        except Exception as e:
            logger.error(
                "Failed to get top violating tenants",
                extra={
                    "event": "get_top_violators_error",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        finally:
            db.close()
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old rate limiting data."""
        
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old violations
            violations_deleted = db.query(RateLimitViolation).filter(
                RateLimitViolation.violation_time < cutoff_date
            ).delete()
            
            # Delete old metrics (keep longer for historical analysis)
            metrics_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 2)
            metrics_deleted = db.query(RateLimitMetrics).filter(
                RateLimitMetrics.period_start < metrics_cutoff
            ).delete()
            
            db.commit()
            
            total_deleted = violations_deleted + metrics_deleted
            
            logger.info(
                "Rate limiting data cleanup completed",
                extra={
                    "event": "data_cleanup_completed",
                    "violations_deleted": violations_deleted,
                    "metrics_deleted": metrics_deleted,
                    "total_deleted": total_deleted,
                    "cutoff_date": cutoff_date.isoformat()
                }
            )
            
            return total_deleted
            
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to cleanup rate limiting data",
                extra={
                    "event": "data_cleanup_error",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        finally:
            db.close()


# Scheduled task functions
async def scheduled_metrics_aggregation():
    """Scheduled task for metrics aggregation."""
    service = RateLimitMetricsService()
    
    try:
        # Aggregate hourly metrics
        await service.aggregate_metrics(period="hour", batch_size=24)
        
        # Aggregate daily metrics (less frequent)
        await service.aggregate_metrics(period="day", batch_size=7)
        
        logger.info("Scheduled metrics aggregation completed")
        
    except Exception as e:
        logger.error(
            "Scheduled metrics aggregation failed",
            extra={
                "event": "scheduled_aggregation_error",
                "error": str(e)
            },
            exc_info=True
        )


async def scheduled_data_cleanup():
    """Scheduled task for data cleanup."""
    service = RateLimitMetricsService()
    
    try:
        deleted_count = await service.cleanup_old_data(days_to_keep=30)
        
        logger.info(
            "Scheduled data cleanup completed",
            extra={
                "event": "scheduled_cleanup_completed",
                "records_deleted": deleted_count
            }
        )
        
    except Exception as e:
        logger.error(
            "Scheduled data cleanup failed",
            extra={
                "event": "scheduled_cleanup_error",
                "error": str(e)
            },
            exc_info=True
        )