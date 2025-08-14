from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from ....backend.app.models.base import Base


class Market(Base):
    __tablename__ = "markets"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    geographic_bounds: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    competitor_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tracking_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    competitors: Mapped[List["Competitor"]] = relationship("Competitor", back_populates="market", cascade="all, delete-orphan")
    market_alerts: Mapped[List["MarketAlert"]] = relationship("MarketAlert", back_populates="market", cascade="all, delete-orphan")
    user_preferences: Mapped[List["UserMarketPreference"]] = relationship("UserMarketPreference", back_populates="market", cascade="all, delete-orphan")


class Competitor(Base):
    __tablename__ = "competitors"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    locations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    tracking_priority: Mapped[int] = mapped_column(Integer, default=3)  # 1-5 scale
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_share_estimate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # Percentage
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="competitors")
    pricing_data: Mapped[List["PricingData"]] = relationship("PricingData", back_populates="competitor", cascade="all, delete-orphan")


class PricingData(Base):
    __tablename__ = "pricing_data"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("competitors.id"), nullable=False)
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    product_service: Mapped[str] = mapped_column(String(255), nullable=False)
    price_point: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    date_collected: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_promotion: Mapped[bool] = mapped_column(Boolean, default=False)
    promotion_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="pricing_data")


class MarketAlert(Base):
    __tablename__ = "market_alerts"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'price_change', 'new_competitor', 'anomaly'
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # 'low', 'medium', 'high', 'critical'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="market_alerts")


class UserMarketPreference(Base):
    __tablename__ = "user_market_preferences"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    dashboard_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    alert_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    favorite_competitors: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)  # List of competitor IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="user_preferences")


class CompetitiveInsight(Base):
    __tablename__ = "competitive_insights"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'pricing_trend', 'market_gap', 'positioning'
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)  # 0-10 scale
    confidence_level: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)  # 0-1 scale
    data_points: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketAnalytics(Base):
    __tablename__ = "market_analytics"
    
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    market_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("markets.id"), nullable=False)
    organisation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("organisations.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'average_price', 'market_share', 'growth_rate'
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    calculation_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)