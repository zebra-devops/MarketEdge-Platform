from sqlalchemy import String, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from .base import Base
import enum
from ..core.rate_limit_config import Industry


class SubscriptionPlan(str, enum.Enum):
    basic = "basic"
    professional = "professional"
    enterprise = "enterprise"


class Organisation(Base):
    __tablename__ = "organisations"
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100))  # Legacy field - to be deprecated
    industry_type: Mapped[Industry] = mapped_column(Enum(Industry, name='industry', create_constraint=False, values_callable=lambda x: [e.value for e in x]), default=Industry.DEFAULT, nullable=False, server_default='default')
    subscription_plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.basic, server_default='basic')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    
    # Rate limiting configuration
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    burst_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    rate_limit_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # SIC code relationship
    sic_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("sic_codes.code"), nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organisation")
    tool_access: Mapped[List["OrganisationToolAccess"]] = relationship("OrganisationToolAccess", back_populates="organisation")
    
    # SIC relationship
    sic_code_rel = relationship("SICCode", back_populates="organisations")
    
    # Feature flag relationships
    feature_flag_overrides = relationship("FeatureFlagOverride", back_populates="organisation")
    feature_flag_usage = relationship("FeatureFlagUsage", back_populates="organisation")
    
    # Module relationships
    organisation_modules = relationship("OrganisationModule", back_populates="organisation")
    module_configurations = relationship("ModuleConfiguration", back_populates="organisation")
    module_usage_logs = relationship("ModuleUsageLog", back_populates="organisation")
    
    # Audit relationships
    audit_logs = relationship("AuditLog", back_populates="organisation")
    
    # Hierarchical organization relationships
    hierarchy_nodes = relationship("OrganizationHierarchy", back_populates="legacy_organisation")
    template_applications = relationship("OrganizationTemplateApplication", back_populates="organization")
    
    def get_root_hierarchy_node(self):
        """Get the root hierarchy node for this organization"""
        for node in self.hierarchy_nodes:
            if node.level.value == "organization" and node.parent_id is None:
                return node
        return None
        
    def get_all_hierarchy_nodes(self):
        """Get all hierarchy nodes for this organization"""
        return self.hierarchy_nodes