"""
Causal Edge Services

This module provides service layer functionality for causal analysis operations,
integrating with MarketEdge's database models and business logic.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from .models import (
    CausalExperiment, Intervention, CausalResult, CausalModel,
    ExperimentType, ExperimentStatus, InterventionType
)
from .core import CausalAnalyzer, CausalAnalysisResult, CausalMethod
from .utils import CausalValidators, StatisticalHelpers, BusinessMetricsHelpers
from ..models.user import User
from ..models.organisation import Organisation
from ..core.exceptions import ValidationError, NotFoundError, BusinessLogicError

logger = logging.getLogger(__name__)


class CausalAnalysisService:
    """
    Service for conducting causal analysis operations

    This service provides high-level methods for running causal analyses,
    managing experiments, and storing results within the multi-tenant context.
    """

    def __init__(self, db: AsyncSession, organisation_id: UUID, user_id: UUID):
        self.db = db
        self.organisation_id = organisation_id
        self.user_id = user_id
        self.analyzer = CausalAnalyzer()
        self.validators = CausalValidators()

    async def conduct_ab_test_analysis(
        self,
        experiment_id: UUID,
        treatment_data: List[float],
        control_data: List[float],
        method: CausalMethod = CausalMethod.WELCH_T_TEST,
        metric_name: str = "primary_metric"
    ) -> CausalResult:
        """
        Conduct A/B test analysis and store results

        Args:
            experiment_id: ID of the experiment
            treatment_data: Treatment group outcome data
            control_data: Control group outcome data
            method: Statistical method to use
            metric_name: Name of the metric being analyzed

        Returns:
            CausalResult instance with stored analysis results

        Raises:
            ValidationError: If data validation fails
            NotFoundError: If experiment not found
        """
        # Validate experiment exists and belongs to organization
        experiment = await self._get_experiment(experiment_id)

        # Validate input data
        if not self.validators.validate_ab_test_data(
            np.array(treatment_data), np.array(control_data)
        ):
            raise ValidationError("Invalid A/B test data provided")

        # Conduct analysis
        analysis_result = self.analyzer.ab_test_analysis(
            treatment_data, control_data, method
        )

        # Create and store CausalResult
        causal_result = CausalResult(
            experiment_id=experiment_id,
            organisation_id=self.organisation_id,
            metric_name=metric_name,
            analysis_method=analysis_result.method.value,
            effect_size=analysis_result.effect_size,
            confidence_interval_lower=analysis_result.confidence_interval[0],
            confidence_interval_upper=analysis_result.confidence_interval[1],
            p_value=analysis_result.p_value,
            standard_error=analysis_result.additional_metrics.get("treatment_std", 0),
            treatment_group_size=analysis_result.sample_sizes.get("treatment", 0),
            control_group_size=analysis_result.sample_sizes.get("control", 0),
            treatment_mean=analysis_result.additional_metrics.get("treatment_mean", 0),
            control_mean=analysis_result.additional_metrics.get("control_mean", 0),
            statistical_details=analysis_result.additional_metrics,
            analysis_confidence=analysis_result.statistical_power or 0.8,
            data_quality_score=self._calculate_data_quality_score(
                treatment_data, control_data
            )
        )

        self.db.add(causal_result)
        await self.db.commit()
        await self.db.refresh(causal_result)

        # Update experiment with latest results
        await self._update_experiment_results(experiment, analysis_result)

        return causal_result

    async def conduct_propensity_score_analysis(
        self,
        experiment_id: UUID,
        data: pd.DataFrame,
        treatment_col: str,
        outcome_col: str,
        covariate_cols: List[str],
        metric_name: str = "primary_metric",
        caliper: float = 0.1
    ) -> CausalResult:
        """
        Conduct propensity score matching analysis

        Args:
            experiment_id: ID of the experiment
            data: DataFrame with all variables
            treatment_col: Treatment indicator column name
            outcome_col: Outcome variable column name
            covariate_cols: List of covariate column names
            metric_name: Name of the metric being analyzed
            caliper: Maximum distance for matching

        Returns:
            CausalResult with propensity score analysis results

        Raises:
            ValidationError: If data validation fails
            NotFoundError: If experiment not found
        """
        # Validate experiment
        experiment = await self._get_experiment(experiment_id)

        # Validate required columns
        required_cols = [treatment_col, outcome_col] + covariate_cols
        if not all(col in data.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in data.columns]
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # Conduct analysis
        analysis_result = self.analyzer.propensity_score_matching(
            data, treatment_col, outcome_col, covariate_cols, caliper
        )

        # Create and store result
        causal_result = CausalResult(
            experiment_id=experiment_id,
            organisation_id=self.organisation_id,
            metric_name=metric_name,
            analysis_method=analysis_result.method.value,
            effect_size=analysis_result.effect_size,
            confidence_interval_lower=analysis_result.confidence_interval[0],
            confidence_interval_upper=analysis_result.confidence_interval[1],
            p_value=analysis_result.p_value,
            treatment_group_size=analysis_result.additional_metrics.get("matched_pairs", 0),
            control_group_size=analysis_result.additional_metrics.get("matched_pairs", 0),
            statistical_details=analysis_result.additional_metrics,
            analysis_confidence=analysis_result.statistical_power or 0.8,
            data_quality_score=0.9  # PS matching typically improves data quality
        )

        self.db.add(causal_result)
        await self.db.commit()
        await self.db.refresh(causal_result)

        # Update experiment results
        await self._update_experiment_results(experiment, analysis_result)

        return causal_result

    async def conduct_difference_in_differences_analysis(
        self,
        experiment_id: UUID,
        data: pd.DataFrame,
        outcome_col: str,
        treatment_col: str,
        time_col: str,
        pre_period: Any,
        post_period: Any,
        metric_name: str = "primary_metric"
    ) -> CausalResult:
        """
        Conduct difference-in-differences analysis

        Args:
            experiment_id: ID of the experiment
            data: Panel data DataFrame
            outcome_col: Outcome variable column name
            treatment_col: Treatment indicator column name
            time_col: Time period column name
            pre_period: Pre-treatment period identifier
            post_period: Post-treatment period identifier
            metric_name: Name of the metric being analyzed

        Returns:
            CausalResult with difference-in-differences results
        """
        # Validate experiment
        experiment = await self._get_experiment(experiment_id)

        # Validate panel data
        if not self.validators.validate_panel_data(
            data, "unit_id", time_col, treatment_col, outcome_col
        ):
            raise ValidationError("Invalid panel data for difference-in-differences")

        # Conduct analysis
        analysis_result = self.analyzer.difference_in_differences(
            data, outcome_col, treatment_col, time_col, pre_period, post_period
        )

        # Create and store result
        causal_result = CausalResult(
            experiment_id=experiment_id,
            organisation_id=self.organisation_id,
            metric_name=metric_name,
            analysis_method=analysis_result.method.value,
            effect_size=analysis_result.effect_size,
            confidence_interval_lower=analysis_result.confidence_interval[0],
            confidence_interval_upper=analysis_result.confidence_interval[1],
            p_value=analysis_result.p_value,
            standard_error=analysis_result.additional_metrics.get("standard_error", 0),
            statistical_details=analysis_result.additional_metrics,
            analysis_confidence=0.85,  # DiD has moderate confidence
            data_quality_score=self._calculate_panel_data_quality_score(data)
        )

        self.db.add(causal_result)
        await self.db.commit()
        await self.db.refresh(causal_result)

        # Update experiment results
        await self._update_experiment_results(experiment, analysis_result)

        return causal_result

    async def calculate_business_impact(
        self,
        result_id: UUID,
        baseline_value: float,
        volume: int,
        cost_of_intervention: float = 0,
        time_horizon_months: int = 12
    ) -> Dict[str, Any]:
        """
        Calculate business impact from causal analysis results

        Args:
            result_id: ID of the causal result
            baseline_value: Baseline value of the metric
            volume: Scale factor (customers, transactions, etc.)
            cost_of_intervention: Cost of implementing the intervention
            time_horizon_months: Time horizon for impact calculation

        Returns:
            Dictionary with business impact metrics
        """
        # Get the causal result
        result = await self.db.execute(
            select(CausalResult)
            .where(
                and_(
                    CausalResult.id == result_id,
                    CausalResult.organisation_id == self.organisation_id
                )
            )
        )
        causal_result = result.scalar_one_or_none()

        if not causal_result:
            raise NotFoundError(f"Causal result {result_id} not found")

        # Calculate business impact
        business_impact = BusinessMetricsHelpers.calculate_business_impact(
            effect_size=causal_result.effect_size,
            baseline_value=baseline_value,
            volume=volume,
            confidence_interval=(
                causal_result.confidence_interval_lower,
                causal_result.confidence_interval_upper
            )
        )

        # Calculate ROI if cost provided
        if cost_of_intervention > 0:
            monthly_revenue_impact = business_impact["absolute_impact"] / time_horizon_months
            roi_metrics = BusinessMetricsHelpers.roi_calculation(
                revenue_impact=monthly_revenue_impact,
                cost_of_intervention=cost_of_intervention,
                time_horizon_months=time_horizon_months
            )
            business_impact["roi_analysis"] = roi_metrics

        # Store business impact in result
        causal_result.practical_impact = business_impact
        await self.db.commit()

        return business_impact

    async def _get_experiment(self, experiment_id: UUID) -> CausalExperiment:
        """Get experiment and validate access"""
        result = await self.db.execute(
            select(CausalExperiment)
            .where(
                and_(
                    CausalExperiment.id == experiment_id,
                    CausalExperiment.organisation_id == self.organisation_id
                )
            )
        )
        experiment = result.scalar_one_or_none()

        if not experiment:
            raise NotFoundError(f"Experiment {experiment_id} not found")

        return experiment

    async def _update_experiment_results(
        self,
        experiment: CausalExperiment,
        analysis_result: CausalAnalysisResult
    ):
        """Update experiment with analysis results"""
        if not experiment.results:
            experiment.results = {}

        experiment.results[analysis_result.method.value] = analysis_result.to_dict()
        experiment.updated_at = datetime.utcnow()

        # Auto-update status if experiment is active
        if experiment.status == ExperimentStatus.ACTIVE:
            experiment.status = ExperimentStatus.ANALYZING

        await self.db.commit()

    def _calculate_data_quality_score(
        self,
        treatment_data: List[float],
        control_data: List[float]
    ) -> float:
        """Calculate data quality score for A/B test data"""
        score = 1.0

        # Penalize for small sample sizes
        min_sample_size = min(len(treatment_data), len(control_data))
        if min_sample_size < 100:
            score -= 0.2
        elif min_sample_size < 50:
            score -= 0.4

        # Penalize for extreme imbalance
        balance_ratio = min(len(treatment_data), len(control_data)) / max(len(treatment_data), len(control_data))
        if balance_ratio < 0.5:
            score -= 0.2

        # Check for outliers (simple IQR method)
        all_data = np.array(treatment_data + control_data)
        q25, q75 = np.percentile(all_data, [25, 75])
        iqr = q75 - q25
        outliers = np.sum((all_data < q25 - 1.5 * iqr) | (all_data > q75 + 1.5 * iqr))
        outlier_rate = outliers / len(all_data)

        if outlier_rate > 0.1:
            score -= 0.3

        return max(0.0, score)

    def _calculate_panel_data_quality_score(self, data: pd.DataFrame) -> float:
        """Calculate data quality score for panel data"""
        score = 1.0

        # Check for missingness
        missing_rate = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        if missing_rate > 0.1:
            score -= 0.3
        elif missing_rate > 0.05:
            score -= 0.1

        # Check for balance
        unit_counts = data.groupby(data.columns[0]).size()
        balance_cv = unit_counts.std() / unit_counts.mean()
        if balance_cv > 0.5:
            score -= 0.2

        return max(0.0, score)


class ExperimentService:
    """
    Service for managing causal experiments

    This service handles CRUD operations for experiments, interventions,
    and related entities within the multi-tenant context.
    """

    def __init__(self, db: AsyncSession, organisation_id: UUID, user_id: UUID):
        self.db = db
        self.organisation_id = organisation_id
        self.user_id = user_id

    async def create_experiment(
        self,
        name: str,
        description: str,
        experiment_type: ExperimentType,
        hypothesis: str,
        success_metrics: List[str],
        **kwargs
    ) -> CausalExperiment:
        """
        Create a new causal experiment

        Args:
            name: Experiment name
            description: Experiment description
            experiment_type: Type of experiment
            hypothesis: Research hypothesis
            success_metrics: List of metrics to measure
            **kwargs: Additional experiment configuration

        Returns:
            Created CausalExperiment instance
        """
        experiment = CausalExperiment(
            organisation_id=self.organisation_id,
            created_by=self.user_id,
            name=name,
            description=description,
            experiment_type=experiment_type.value,
            hypothesis=hypothesis,
            success_metrics=success_metrics,
            **{k: v for k, v in kwargs.items() if hasattr(CausalExperiment, k)}
        )

        self.db.add(experiment)
        await self.db.commit()
        await self.db.refresh(experiment)

        return experiment

    async def get_experiment(self, experiment_id: UUID) -> Optional[CausalExperiment]:
        """Get experiment by ID"""
        result = await self.db.execute(
            select(CausalExperiment)
            .where(
                and_(
                    CausalExperiment.id == experiment_id,
                    CausalExperiment.organisation_id == self.organisation_id
                )
            )
            .options(
                selectinload(CausalExperiment.interventions),
                selectinload(CausalExperiment.results_records)
            )
        )
        return result.scalar_one_or_none()

    async def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CausalExperiment]:
        """List experiments with optional filtering"""
        query = select(CausalExperiment).where(
            CausalExperiment.organisation_id == self.organisation_id
        )

        if status:
            query = query.where(CausalExperiment.status == status.value)

        if experiment_type:
            query = query.where(CausalExperiment.experiment_type == experiment_type.value)

        query = query.order_by(desc(CausalExperiment.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_experiment_status(
        self,
        experiment_id: UUID,
        status: ExperimentStatus
    ) -> CausalExperiment:
        """Update experiment status"""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise NotFoundError(f"Experiment {experiment_id} not found")

        experiment.status = status.value
        experiment.updated_at = datetime.utcnow()

        # Set timestamps based on status
        if status == ExperimentStatus.ACTIVE and not experiment.actual_start_date:
            experiment.actual_start_date = datetime.utcnow()
        elif status in [ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED] and not experiment.actual_end_date:
            experiment.actual_end_date = datetime.utcnow()

        await self.db.commit()
        return experiment

    async def create_intervention(
        self,
        experiment_id: UUID,
        name: str,
        intervention_type: InterventionType,
        description: str,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Intervention:
        """Create intervention for experiment"""
        # Verify experiment exists
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise NotFoundError(f"Experiment {experiment_id} not found")

        intervention = Intervention(
            experiment_id=experiment_id,
            organisation_id=self.organisation_id,
            name=name,
            intervention_type=intervention_type.value,
            description=description,
            parameters=parameters,
            **{k: v for k, v in kwargs.items() if hasattr(Intervention, k)}
        )

        self.db.add(intervention)
        await self.db.commit()
        await self.db.refresh(intervention)

        return intervention

    async def get_experiment_results(self, experiment_id: UUID) -> List[CausalResult]:
        """Get all results for an experiment"""
        result = await self.db.execute(
            select(CausalResult)
            .where(
                and_(
                    CausalResult.experiment_id == experiment_id,
                    CausalResult.organisation_id == self.organisation_id
                )
            )
            .order_by(desc(CausalResult.analysis_date))
        )
        return result.scalars().all()

    async def delete_experiment(self, experiment_id: UUID) -> bool:
        """Delete experiment (only if not started)"""
        experiment = await self.get_experiment(experiment_id)
        if not experiment:
            raise NotFoundError(f"Experiment {experiment_id} not found")

        if experiment.status in [ExperimentStatus.ACTIVE, ExperimentStatus.COMPLETED]:
            raise BusinessLogicError("Cannot delete active or completed experiments")

        await self.db.delete(experiment)
        await self.db.commit()
        return True