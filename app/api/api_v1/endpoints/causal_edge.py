"""
Causal Edge API Endpoints

This module provides REST API endpoints for causal analysis functionality
within the MarketEdge platform.
"""

from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from ....core.database import get_async_db
from ....auth.dependencies import get_current_active_user, require_application_access
from ....models.user import User
from ....core.exceptions import ValidationError, NotFoundError, BusinessLogicError
from ....causal_edge.models import ExperimentType, ExperimentStatus, InterventionType
from ....causal_edge.services import CausalAnalysisService, ExperimentService
from ....causal_edge.core import CausalMethod
from ....middleware.feature_flags import feature_flag_required

router = APIRouter()


# Pydantic Models for Request/Response

class ExperimentCreateRequest(BaseModel):
    """Request model for creating experiments"""
    name: str = Field(..., min_length=1, max_length=255, description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    experiment_type: ExperimentType = Field(..., description="Type of experiment")
    hypothesis: str = Field(..., min_length=10, description="Research hypothesis")
    success_metrics: List[str] = Field(..., min_items=1, description="Success metrics to measure")
    treatment_description: Optional[str] = Field(None, description="Description of treatment")
    control_description: Optional[str] = Field(None, description="Description of control")
    statistical_power: Optional[float] = Field(0.8, ge=0.1, le=0.99, description="Desired statistical power")
    significance_level: Optional[float] = Field(0.05, ge=0.001, le=0.2, description="Significance level")
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")


class ExperimentResponse(BaseModel):
    """Response model for experiments"""
    id: UUID
    name: str
    description: Optional[str]
    experiment_type: str
    status: str
    hypothesis: str
    success_metrics: List[str]
    statistical_power: Optional[float]
    significance_level: Optional[float]
    planned_start_date: Optional[datetime]
    planned_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterventionCreateRequest(BaseModel):
    """Request model for creating interventions"""
    name: str = Field(..., min_length=1, max_length=255, description="Intervention name")
    intervention_type: InterventionType = Field(..., description="Type of intervention")
    description: Optional[str] = Field(None, description="Intervention description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Intervention parameters")
    target_criteria: Optional[Dict[str, Any]] = Field(None, description="Target selection criteria")


class ABTestAnalysisRequest(BaseModel):
    """Request model for A/B test analysis"""
    treatment_data: List[float] = Field(..., min_items=10, description="Treatment group outcomes")
    control_data: List[float] = Field(..., min_items=10, description="Control group outcomes")
    method: CausalMethod = Field(CausalMethod.WELCH_T_TEST, description="Statistical method")
    metric_name: str = Field("primary_metric", description="Name of the metric")

    @validator('treatment_data', 'control_data')
    def validate_numeric_data(cls, v):
        """Validate that all values are finite numbers"""
        if not all(isinstance(x, (int, float)) and not (abs(x) == float('inf') or x != x) for x in v):
            raise ValueError("All values must be finite numbers")
        return v


class PropensityScoreAnalysisRequest(BaseModel):
    """Request model for propensity score analysis"""
    treatment_col: str = Field(..., description="Treatment indicator column name")
    outcome_col: str = Field(..., description="Outcome variable column name")
    covariate_cols: List[str] = Field(..., min_items=1, description="Covariate column names")
    metric_name: str = Field("primary_metric", description="Name of the metric")
    caliper: float = Field(0.1, ge=0.01, le=0.5, description="Matching caliper")


class BusinessImpactRequest(BaseModel):
    """Request model for business impact calculation"""
    baseline_value: float = Field(..., description="Baseline value of the metric")
    volume: int = Field(..., gt=0, description="Scale factor (customers, transactions, etc.)")
    cost_of_intervention: Optional[float] = Field(0, ge=0, description="Cost of implementing intervention")
    time_horizon_months: int = Field(12, ge=1, le=60, description="Time horizon for impact calculation")


class CausalResultResponse(BaseModel):
    """Response model for causal analysis results"""
    id: UUID
    metric_name: str
    analysis_method: str
    effect_size: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    p_value: float
    is_significant: bool
    treatment_group_size: Optional[int]
    control_group_size: Optional[int]
    statistical_details: Optional[Dict[str, Any]]
    practical_impact: Optional[Dict[str, Any]]
    analysis_date: datetime

    @property
    def is_significant(self) -> bool:
        return self.p_value < 0.05

    class Config:
        from_attributes = True


# API Endpoints

@router.post("/experiments", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
@feature_flag_required("causal_edge_enabled")
async def create_experiment(
    request: ExperimentCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> ExperimentResponse:
    """
    Create a new causal experiment

    This endpoint allows users to create new causal experiments for their organization.
    Requires CAUSAL_EDGE application access and the causal_edge_enabled feature flag.
    """
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        experiment = await service.create_experiment(
            name=request.name,
            description=request.description,
            experiment_type=request.experiment_type,
            hypothesis=request.hypothesis,
            success_metrics=request.success_metrics,
            treatment_description=request.treatment_description,
            control_description=request.control_description,
            statistical_power=request.statistical_power,
            significance_level=request.significance_level,
            planned_start_date=request.planned_start_date,
            planned_end_date=request.planned_end_date
        )

        return ExperimentResponse.from_orm(experiment)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/experiments", response_model=List[ExperimentResponse])
@feature_flag_required("causal_edge_enabled")
async def list_experiments(
    status_filter: Optional[ExperimentStatus] = None,
    experiment_type: Optional[ExperimentType] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> List[ExperimentResponse]:
    """
    List causal experiments for the current organization

    Supports filtering by status and experiment type, with pagination.
    """
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        experiments = await service.list_experiments(
            status=status_filter,
            experiment_type=experiment_type,
            limit=limit,
            offset=offset
        )

        return [ExperimentResponse.from_orm(exp) for exp in experiments]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
@feature_flag_required("causal_edge_enabled")
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> ExperimentResponse:
    """Get detailed information about a specific experiment"""
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        experiment = await service.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

        return ExperimentResponse.from_orm(experiment)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.patch("/experiments/{experiment_id}/status")
@feature_flag_required("causal_edge_enabled")
async def update_experiment_status(
    experiment_id: UUID,
    new_status: ExperimentStatus,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> ExperimentResponse:
    """Update the status of an experiment"""
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        experiment = await service.update_experiment_status(experiment_id, new_status)
        return ExperimentResponse.from_orm(experiment)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/experiments/{experiment_id}/interventions", status_code=status.HTTP_201_CREATED)
@feature_flag_required("causal_edge_enabled")
async def create_intervention(
    experiment_id: UUID,
    request: InterventionCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
):
    """Create an intervention for an experiment"""
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        intervention = await service.create_intervention(
            experiment_id=experiment_id,
            name=request.name,
            intervention_type=request.intervention_type,
            description=request.description,
            parameters=request.parameters,
            target_criteria=request.target_criteria
        )

        return {"id": intervention.id, "message": "Intervention created successfully"}

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/experiments/{experiment_id}/analysis/ab-test", response_model=CausalResultResponse)
@feature_flag_required("causal_inference")
async def conduct_ab_test_analysis(
    experiment_id: UUID,
    request: ABTestAnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> CausalResultResponse:
    """
    Conduct A/B test analysis on experiment data

    Requires the causal_inference feature flag to be enabled.
    """
    try:
        service = CausalAnalysisService(db, current_user.organisation_id, current_user.id)

        result = await service.conduct_ab_test_analysis(
            experiment_id=experiment_id,
            treatment_data=request.treatment_data,
            control_data=request.control_data,
            method=request.method,
            metric_name=request.metric_name
        )

        return CausalResultResponse.from_orm(result)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/experiments/{experiment_id}/analysis/propensity-score")
@feature_flag_required("causal_inference")
async def conduct_propensity_score_analysis(
    experiment_id: UUID,
    request: PropensityScoreAnalysisRequest,
    file: UploadFile = File(..., description="CSV file with experiment data"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> CausalResultResponse:
    """
    Conduct propensity score matching analysis

    Upload a CSV file with your experiment data and specify the column names
    for treatment, outcome, and covariates.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

        # Read CSV data
        content = await file.read()
        from io import StringIO
        data = pd.read_csv(StringIO(content.decode('utf-8')))

        service = CausalAnalysisService(db, current_user.organisation_id, current_user.id)

        result = await service.conduct_propensity_score_analysis(
            experiment_id=experiment_id,
            data=data,
            treatment_col=request.treatment_col,
            outcome_col=request.outcome_col,
            covariate_cols=request.covariate_cols,
            metric_name=request.metric_name,
            caliper=request.caliper
        )

        return CausalResultResponse.from_orm(result)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty or invalid CSV file")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/experiments/{experiment_id}/results", response_model=List[CausalResultResponse])
@feature_flag_required("causal_edge_enabled")
async def get_experiment_results(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> List[CausalResultResponse]:
    """Get all analysis results for an experiment"""
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        results = await service.get_experiment_results(experiment_id)
        return [CausalResultResponse.from_orm(result) for result in results]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/results/{result_id}/business-impact")
@feature_flag_required("causal_inference")
async def calculate_business_impact(
    result_id: UUID,
    request: BusinessImpactRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> Dict[str, Any]:
    """
    Calculate business impact from causal analysis results

    Translates statistical effect sizes into business metrics like revenue impact,
    ROI, and payback period.
    """
    try:
        service = CausalAnalysisService(db, current_user.organisation_id, current_user.id)

        impact = await service.calculate_business_impact(
            result_id=result_id,
            baseline_value=request.baseline_value,
            volume=request.volume,
            cost_of_intervention=request.cost_of_intervention,
            time_horizon_months=request.time_horizon_months
        )

        return impact

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/experiments/{experiment_id}")
@feature_flag_required("causal_edge_enabled")
async def delete_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> Dict[str, str]:
    """
    Delete an experiment

    Only draft experiments that haven't been started can be deleted.
    """
    try:
        service = ExperimentService(db, current_user.organisation_id, current_user.id)

        await service.delete_experiment(experiment_id)
        return {"message": "Experiment deleted successfully"}

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Health and utility endpoints

@router.get("/health")
async def causal_edge_health_check():
    """Health check endpoint for Causal Edge module"""
    try:
        # Basic functionality test
        from ....causal_edge.core import CausalAnalyzer
        analyzer = CausalAnalyzer()

        # Test with minimal data
        treatment_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        control_data = [0.8, 1.8, 2.8, 3.8, 4.8]

        result = analyzer.ab_test_analysis(treatment_data, control_data)

        return {
            "status": "healthy",
            "module": "causal_edge",
            "version": "1.0.0",
            "test_analysis_successful": result is not None,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "module": "causal_edge",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/methods", response_model=List[Dict[str, str]])
@feature_flag_required("causal_edge_enabled")
async def list_causal_methods(
    current_user: User = Depends(require_application_access("CAUSAL_EDGE"))
) -> List[Dict[str, str]]:
    """List available causal inference methods"""
    methods = [
        {
            "method": method.value,
            "name": method.value.replace("_", " ").title(),
            "description": _get_method_description(method)
        }
        for method in CausalMethod
    ]

    return methods


def _get_method_description(method: CausalMethod) -> str:
    """Get description for causal method"""
    descriptions = {
        CausalMethod.T_TEST: "Two-sample t-test assuming equal variances",
        CausalMethod.WELCH_T_TEST: "Welch's t-test not assuming equal variances (recommended)",
        CausalMethod.MANN_WHITNEY_U: "Non-parametric Mann-Whitney U test",
        CausalMethod.PROPENSITY_SCORE_MATCHING: "Propensity score matching for observational data",
        CausalMethod.INSTRUMENTAL_VARIABLE: "Instrumental variable estimation",
        CausalMethod.REGRESSION_DISCONTINUITY: "Regression discontinuity design",
        CausalMethod.DIFFERENCE_IN_DIFFERENCES: "Difference-in-differences for panel data",
        CausalMethod.INTERRUPTED_TIME_SERIES: "Interrupted time series analysis",
        CausalMethod.BAYESIAN_CAUSAL: "Bayesian causal inference"
    }

    return descriptions.get(method, "Advanced causal inference method")