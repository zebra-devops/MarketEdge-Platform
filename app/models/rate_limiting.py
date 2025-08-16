from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, Float
from .database_types import CompatibleUUID, CompatibleJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base


class RateLimitScope(str, enum.Enum):
    """Rate limiting scope levels"""
    global_default = "global_default"
    subscription_plan = "subscription_plan"
    sic_code = "sic_code"
    organisation = "organisation"
    user = "user"


class RateLimitPeriod(str, enum.Enum):
    """Time period for rate limiting"""
    minute = "minute"
    hour = "hour"
    day = "day"
    month = "month"


class RateLimitRule(Base):
    """
    Rate limiting rules for different scopes and endpoints
    Hierarchical priority: user > organisation > sic_code > subscription_plan > global_default
    """
    __tablename__ = "rate_limit_rules"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Rule identification
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Scope configuration
    scope: Mapped[RateLimitScope] = mapped_column(String(50), nullable=False, index=True)
    scope_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # org_id, user_id, sic_code, plan
    
    # Rate limiting configuration
    endpoint_pattern: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # e.g., "/api/v1/market-edge/*"
    requests_per_period: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[RateLimitPeriod] = mapped_column(String(20), nullable=False)
    
    # Burst configuration
    burst_requests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Allow burst of requests
    burst_period_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=60)
    
    # Priority and status
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)  # Higher = more priority
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Additional configuration
    config: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)
    
    # Relationships for foreign keys
    organisation_id: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organisation = relationship("Organisation", foreign_keys=[organisation_id])
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<RateLimitRule(scope={self.scope}, endpoint='{self.endpoint_pattern}', rate={self.requests_per_period}/{self.period})>"

    @property
    def period_seconds(self) -> int:
        """Convert period to seconds"""
        period_map = {
            RateLimitPeriod.minute: 60,
            RateLimitPeriod.hour: 3600,
            RateLimitPeriod.day: 86400,
            RateLimitPeriod.month: 2592000  # 30 days
        }
        return period_map[RateLimitPeriod(self.period)]

    @property
    def identifier(self) -> str:
        """Get unique identifier for this rule"""
        if self.scope_value:
            return f"{self.scope}:{self.scope_value}:{self.endpoint_pattern}"
        return f"{self.scope}:{self.endpoint_pattern}"


class RateLimitUsage(Base):
    """
    Track rate limit usage for monitoring and analytics
    """
    __tablename__ = "rate_limit_usage"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Usage identification
    rule_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("rate_limit_rules.id"), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("organisations.id"), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=True, index=True)
    
    # Request details
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Rate limiting result
    was_limited: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    current_usage: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Performance metrics
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Additional context
    metadata: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)

    # Relationships
    rule = relationship("RateLimitRule")
    organisation = relationship("Organisation")
    user = relationship("User")

    def __repr__(self):
        status = "LIMITED" if self.was_limited else "ALLOWED"
        return f"<RateLimitUsage({status}, {self.current_usage}/{self.limit_threshold}, {self.processing_time_ms}ms)>"


class SICRateLimitConfig(Base):
    """
    Industry-specific rate limiting configuration based on SIC codes
    """
    __tablename__ = "sic_rate_limit_configs"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # SIC code reference
    sic_code: Mapped[str] = mapped_column(String(10), ForeignKey("sic_codes.code"), nullable=False, index=True)
    
    # Industry-specific limits
    base_requests_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    base_requests_per_hour: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    base_requests_per_day: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    
    # Endpoint-specific multipliers
    endpoint_multipliers: Mapped[Dict[str, float]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)
    
    # Industry characteristics affecting limits
    data_intensity_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # Higher for data-heavy industries
    real_time_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)     # Higher for real-time industries
    
    # Special configurations
    special_config: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON(), nullable=False, default=dict)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    sic_code_rel = relationship("SICCode")

    def __repr__(self):
        return f"<SICRateLimitConfig(sic={self.sic_code}, base_rpm={self.base_requests_per_minute})>"

    def get_effective_limit(self, endpoint_pattern: str, base_limit: int) -> int:
        """Calculate effective limit for an endpoint considering industry factors"""
        # Apply endpoint-specific multiplier if available
        multiplier = self.endpoint_multipliers.get(endpoint_pattern, 1.0)
        
        # Apply industry factors
        industry_factor = self.data_intensity_factor * self.real_time_factor
        
        return int(base_limit * multiplier * industry_factor)