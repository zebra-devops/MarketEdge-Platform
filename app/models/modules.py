from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base


class ModuleType(str, enum.Enum):
    """Types of analytics modules"""
    CORE = "core"                    # Core platform modules
    ANALYTICS = "analytics"          # Data analytics modules
    INTEGRATION = "integration"      # External data integration
    VISUALIZATION = "visualization"  # Chart and dashboard modules
    REPORTING = "reporting"          # Report generation modules
    AI_ML = "ai_ml"                 # AI/ML powered modules


class ModuleStatus(str, enum.Enum):
    """Module lifecycle status"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class AnalyticsModule(Base):
    """
    Registry for analytics modules in the platform
    Defines pluggable components that can be enabled per organisation/sector
    """
    __tablename__ = "analytics_modules"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # e.g., "pricing_intelligence", "market_trends"
    
    # Basic module information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    
    # Module classification
    module_type: Mapped[ModuleType] = mapped_column(SQLEnum(ModuleType), nullable=False)
    status: Mapped[ModuleStatus] = mapped_column(SQLEnum(ModuleStatus), default=ModuleStatus.DEVELOPMENT)
    
    # Configuration
    is_core: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Core modules can't be disabled
    requires_license: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Module definition
    entry_point: Mapped[str] = mapped_column(String(500), nullable=False)  # Python module path
    config_schema: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)  # JSON schema for config
    default_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Requirements and dependencies
    dependencies: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)  # Module IDs
    min_data_requirements: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # API endpoints this module provides
    api_endpoints: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    frontend_components: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    
    # Documentation and help
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing and licensing
    pricing_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # free, basic, premium, enterprise
    license_requirements: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_modules")
    organisation_modules = relationship("OrganisationModule", back_populates="module")
    sector_assignments = relationship("SectorModule", back_populates="module")
    module_configs = relationship("ModuleConfiguration", back_populates="module")

    def __repr__(self):
        return f"<AnalyticsModule(id='{self.id}', name='{self.name}', status={self.status})>"


class OrganisationModule(Base):
    """
    Track which modules are enabled for each organisation
    Allows per-organisation module configuration
    """
    __tablename__ = "organisation_modules"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    module_id: Mapped[str] = mapped_column(String(255), ForeignKey("analytics_modules.id"), nullable=False)
    
    # Configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Access control
    enabled_for_users: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)  # User IDs, empty = all users
    disabled_for_users: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)  # User IDs to exclude
    
    # Usage tracking
    first_enabled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organisation = relationship("Organisation", back_populates="organisation_modules")
    module = relationship("AnalyticsModule", back_populates="organisation_modules")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<OrganisationModule(org={self.organisation_id}, module={self.module_id}, enabled={self.is_enabled})>"


class ModuleConfiguration(Base):
    """
    Store module-specific configuration data
    Allows modules to persist their own settings
    """
    __tablename__ = "module_configurations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    module_id: Mapped[str] = mapped_column(String(255), ForeignKey("analytics_modules.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    
    # Configuration data
    config_key: Mapped[str] = mapped_column(String(255), nullable=False)
    config_value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Validation and schema
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    module = relationship("AnalyticsModule", back_populates="module_configs")
    organisation = relationship("Organisation", back_populates="module_configurations")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self):
        return f"<ModuleConfiguration(module={self.module_id}, org={self.organisation_id}, key='{self.config_key}')>"


class ModuleUsageLog(Base):
    """
    Track module usage for analytics and billing
    """
    __tablename__ = "module_usage_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    module_id: Mapped[str] = mapped_column(String(255), ForeignKey("analytics_modules.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    
    # Usage details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # viewed, executed, configured, etc.
    endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Context data
    context: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Result tracking
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamp
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    module = relationship("AnalyticsModule")
    organisation = relationship("Organisation", back_populates="module_usage_logs")
    user = relationship("User", back_populates="module_usage_logs")

    def __repr__(self):
        return f"<ModuleUsageLog(module={self.module_id}, action='{self.action}', success={self.success})>"