"""
Rate Limit Models

Database models for storing and managing tenant-specific rate limiting configurations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from .base import Base
import uuid


class TenantRateLimit(Base):
    """
    Tenant-specific rate limiting configuration.
    
    Stores rate limits per tenant with different tiers and endpoint-specific overrides.
    """
    __tablename__ = "tenant_rate_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Rate limit configuration
    tier = Column(String(50), nullable=False, default="standard")  # standard, premium, enterprise
    requests_per_hour = Column(Integer, nullable=False, default=1000)
    burst_size = Column(Integer, nullable=False, default=100)  # Burst allowance
    
    # Endpoint-specific overrides (JSON format)
    endpoint_overrides = Column(JSON, nullable=True)
    
    # Time-based restrictions
    enabled = Column(Boolean, nullable=False, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Emergency controls
    emergency_bypass = Column(Boolean, nullable=False, default=False)
    bypass_reason = Column(Text, nullable=True)
    bypass_until = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Ensure one rate limit config per tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', name='uq_tenant_rate_limit'),
    )


class RateLimitViolation(Base):
    """
    Log of rate limit violations for monitoring and analysis.
    """
    __tablename__ = "rate_limit_violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request context
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Violation details
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    rate_limit = Column(Integer, nullable=False)  # The rate limit that was exceeded
    request_count = Column(Integer, nullable=False)  # Number of requests made
    
    # Request metadata
    client_ip = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)
    headers = Column(JSON, nullable=True)  # Selected request headers
    
    # Timing
    violation_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Response
    retry_after_seconds = Column(Integer, nullable=True)
    
    # Analysis fields
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    automated_response = Column(String(100), nullable=True)  # Action taken by system
    admin_notes = Column(Text, nullable=True)
    
    # Indexing for performance
    __table_args__ = (
        {'postgresql_partition_by': 'RANGE (violation_time)'},  # Partition by time for performance
    )


class RateLimitMetrics(Base):
    """
    Aggregated rate limiting metrics for monitoring and dashboards.
    """
    __tablename__ = "rate_limit_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Aggregation context
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Null for system-wide metrics
    aggregation_period = Column(String(10), nullable=False)  # hour, day, week, month
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Request metrics
    total_requests = Column(Integer, nullable=False, default=0)
    blocked_requests = Column(Integer, nullable=False, default=0)
    unique_users = Column(Integer, nullable=False, default=0)
    unique_ips = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    avg_processing_time_ms = Column(Integer, nullable=True)
    max_processing_time_ms = Column(Integer, nullable=True)
    rate_limit_overhead_ms = Column(Integer, nullable=True)
    
    # Top endpoints (JSON format)
    top_endpoints = Column(JSON, nullable=True)
    top_violating_ips = Column(JSON, nullable=True)
    
    # System health
    redis_errors = Column(Integer, nullable=False, default=0)
    bypass_events = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint for aggregation periods
    __table_args__ = (
        UniqueConstraint('tenant_id', 'aggregation_period', 'period_start', 
                        name='uq_rate_limit_metrics_period'),
    )