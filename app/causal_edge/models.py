"""
Causal Edge Database Models

This module defines the database models for causal analysis and experiments
within the MarketEdge platform's multi-tenant architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from ..models.base import Base


class ExperimentType(str, Enum):
    """Types of causal experiments"""
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    INTERRUPTED_TIME_SERIES = "interrupted_time_series"
    REGRESSION_DISCONTINUITY = "regression_discontinuity"
    INSTRUMENTAL_VARIABLE = "instrumental_variable"
    DIFFERENCE_IN_DIFFERENCES = "difference_in_differences"


class ExperimentStatus(str, Enum):
    """Status of causal experiments"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ANALYZING = "analyzing"


class InterventionType(str, Enum):
    """Types of interventions in causal analysis"""
    PRICING = "pricing"
    MARKETING = "marketing"
    PRODUCT_FEATURE = "product_feature"
    OPERATIONAL = "operational"
    POLICY = "policy"
    EXTERNAL_FACTOR = "external_factor"


class CausalExperiment(Base):
    """
    Represents a causal experiment within an organization

    This model stores the configuration, metadata, and results of causal
    experiments conducted for competitive intelligence and business optimization.
    """
    __tablename__ = "causal_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Experiment Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    experiment_type = Column(String(50), nullable=False)  # ExperimentType enum
    status = Column(String(50), nullable=False, default=ExperimentStatus.DRAFT)

    # Experiment Configuration
    hypothesis = Column(Text, nullable=False)
    treatment_description = Column(Text)
    control_description = Column(Text)
    success_metrics = Column(JSON)  # List of metrics to measure
    config = Column(JSON)  # Experiment-specific configuration

    # Statistical Configuration
    statistical_power = Column(Float, default=0.8)
    significance_level = Column(Float, default=0.05)
    minimum_detectable_effect = Column(Float)
    expected_sample_size = Column(Integer)

    # Timing
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)

    # Results
    results = Column(JSON)  # Statistical results and analysis
    conclusions = Column(Text)
    recommendations = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organisation = relationship("Organisation")
    created_by_user = relationship("User", foreign_keys=[created_by])
    interventions = relationship("Intervention", back_populates="experiment", cascade="all, delete-orphan")
    results_records = relationship("CausalResult", back_populates="experiment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_causal_experiments_organisation_status', 'organisation_id', 'status'),
        Index('ix_causal_experiments_created_by', 'created_by'),
        Index('ix_causal_experiments_dates', 'actual_start_date', 'actual_end_date'),
    )


class Intervention(Base):
    """
    Represents an intervention applied in a causal experiment

    Interventions are the treatments or changes applied to test units
    in causal experiments.
    """
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("causal_experiments.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)

    # Intervention Details
    name = Column(String(255), nullable=False)
    intervention_type = Column(String(50), nullable=False)  # InterventionType enum
    description = Column(Text)

    # Configuration
    parameters = Column(JSON)  # Intervention-specific parameters
    target_criteria = Column(JSON)  # Criteria for selecting intervention targets

    # Implementation
    is_active = Column(Boolean, default=False)
    implementation_date = Column(DateTime)
    rollback_date = Column(DateTime)

    # Impact Tracking
    estimated_impact = Column(JSON)  # Predicted impact on metrics
    measured_impact = Column(JSON)  # Actual measured impact

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("CausalExperiment", back_populates="interventions")
    organisation = relationship("Organisation")

    __table_args__ = (
        Index('ix_interventions_experiment_type', 'experiment_id', 'intervention_type'),
        Index('ix_interventions_organisation', 'organisation_id'),
        Index('ix_interventions_active', 'is_active'),
    )


class CausalResult(Base):
    """
    Stores detailed results and analysis from causal experiments

    This model captures the statistical results, effect sizes, confidence intervals,
    and other analytical outputs from causal inference algorithms.
    """
    __tablename__ = "causal_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("causal_experiments.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)

    # Result Metadata
    metric_name = Column(String(255), nullable=False)
    analysis_method = Column(String(100), nullable=False)  # e.g., "t_test", "regression", "propensity_score"
    analysis_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Statistical Results
    effect_size = Column(Float)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    p_value = Column(Float)
    standard_error = Column(Float)

    # Sample Information
    treatment_group_size = Column(Integer)
    control_group_size = Column(Integer)
    treatment_mean = Column(Float)
    control_mean = Column(Float)

    # Detailed Analysis
    statistical_details = Column(JSON)  # Raw statistical output
    assumptions_met = Column(JSON)  # Which statistical assumptions were satisfied
    validity_checks = Column(JSON)  # Results of validity checks

    # Business Context
    business_significance = Column(Text)
    practical_impact = Column(JSON)  # Business impact estimates

    # Quality Metrics
    data_quality_score = Column(Float)  # 0-1 score for data quality
    analysis_confidence = Column(Float)  # 0-1 confidence in analysis

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    experiment = relationship("CausalExperiment", back_populates="results_records")
    organisation = relationship("Organisation")

    __table_args__ = (
        Index('ix_causal_results_experiment_metric', 'experiment_id', 'metric_name'),
        Index('ix_causal_results_organisation', 'organisation_id'),
        Index('ix_causal_results_method', 'analysis_method'),
        Index('ix_causal_results_significance', 'p_value'),
    )


class CausalModel(Base):
    """
    Represents causal models and their configurations

    This model stores reusable causal models that can be applied
    to multiple experiments or business scenarios.
    """
    __tablename__ = "causal_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Model Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model_type = Column(String(100), nullable=False)  # e.g., "linear_regression", "propensity_score", "iv"
    version = Column(String(50), default="1.0.0")

    # Model Configuration
    variables = Column(JSON)  # Variable definitions and relationships
    assumptions = Column(JSON)  # Model assumptions and requirements
    configuration = Column(JSON)  # Model-specific parameters

    # Validation and Performance
    validation_results = Column(JSON)  # Model validation metrics
    performance_metrics = Column(JSON)  # Historical performance

    # Usage Tracking
    times_used = Column(Integer, default=0)
    last_used = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organisation = relationship("Organisation")
    created_by_user = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('ix_causal_models_organisation_type', 'organisation_id', 'model_type'),
        Index('ix_causal_models_active', 'is_active'),
        Index('ix_causal_models_validated', 'is_validated'),
    )


