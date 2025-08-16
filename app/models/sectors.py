from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
from .database_types import CompatibleJSON, CompatibleUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class SICCode(Base):
    """
    UK Standard Industrial Classification (SIC) codes
    Official government classification system for business sectors
    """
    __tablename__ = "sic_codes"

    # Override Base columns - we use code as primary key and define our own timestamps
    id = None  # Remove inherited id column
    created_at = None  # Remove inherited created_at
    updated_at = None  # Remove inherited updated_at
    
    # SIC code is the primary key (e.g., "59140", "55100")
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    
    # Hierarchical structure
    section: Mapped[str] = mapped_column(String(1), nullable=False, index=True)  # A-U
    division: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # 01-99
    group: Mapped[str] = mapped_column(String(5), nullable=False, index=True)    # 01.1-99.9
    class_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)  # 01.11-99.99
    
    # Descriptions
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Market Edge specific configuration
    is_supported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    competitive_factors: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    default_metrics: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    
    # Analytics configuration
    analytics_config: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    
    # Audit fields
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organisations = relationship("Organisation", foreign_keys="Organisation.sic_code", back_populates="sic_code_rel")
    sector_modules = relationship("SectorModule", back_populates="sic_code_rel")

    def __repr__(self):
        return f"<SICCode(code='{self.code}', title='{self.title}')>"

    @property
    def sector_name(self) -> str:
        """Get friendly sector name for display"""
        return self.title

    @property
    def hierarchy_path(self) -> str:
        """Get full hierarchical path"""
        return f"{self.section}.{self.division}.{self.group}.{self.class_code}"


class SectorModule(Base):
    """
    Modules available for specific sectors
    Controls which analytics modules are enabled per SIC code
    """
    __tablename__ = "sector_modules"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    sic_code: Mapped[str] = mapped_column(String(10), ForeignKey("sic_codes.code"), nullable=False)
    module_id: Mapped[str] = mapped_column(String(255), ForeignKey("analytics_modules.id"), nullable=False)
    
    # Configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configuration: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    
    # Priority for display order
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sic_code_rel = relationship("SICCode", back_populates="sector_modules")
    module = relationship("AnalyticsModule", back_populates="sector_assignments")
    creator = relationship("User")

    def __repr__(self):
        return f"<SectorModule(sic={self.sic_code}, module={self.module_id}, enabled={self.is_enabled})>"


class CompetitiveFactorTemplate(Base):
    """
    Sector-specific competitive factor templates
    Define what factors are important for each sector
    """
    __tablename__ = "competitive_factor_templates"

    id: Mapped[str] = mapped_column(CompatibleUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    sic_code: Mapped[str] = mapped_column(String(10), ForeignKey("sic_codes.code"), nullable=False)
    
    # Factor definition
    factor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    factor_key: Mapped[str] = mapped_column(String(100), nullable=False)  # For programmatic access
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)  # numeric, categorical, boolean, text
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight: Mapped[float] = mapped_column(Integer, default=1.0, nullable=False)  # Importance weight
    
    # Validation rules
    validation_rules: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    
    # Display configuration
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_by: Mapped[str] = mapped_column(CompatibleUUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sic_code_rel = relationship("SICCode")
    creator = relationship("User")

    def __repr__(self):
        return f"<CompetitiveFactorTemplate(sic={self.sic_code}, factor='{self.factor_name}')>"