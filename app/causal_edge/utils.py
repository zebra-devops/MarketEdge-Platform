"""
Causal Edge Utility Functions

This module provides utility functions and validators for causal analysis
operations within the MarketEdge platform.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CausalValidators:
    """Validation utilities for causal analysis inputs"""

    @staticmethod
    def validate_ab_test_data(
        treatment_data: np.ndarray,
        control_data: np.ndarray,
        min_sample_size: int = 10
    ) -> bool:
        """
        Validate A/B test data for basic requirements

        Args:
            treatment_data: Treatment group outcomes
            control_data: Control group outcomes
            min_sample_size: Minimum required sample size per group

        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check for minimum sample sizes
            if len(treatment_data) < min_sample_size or len(control_data) < min_sample_size:
                logger.warning(f"Sample sizes too small: treatment={len(treatment_data)}, control={len(control_data)}")
                return False

            # Check for missing or infinite values
            if np.any(~np.isfinite(treatment_data)) or np.any(~np.isfinite(control_data)):
                logger.warning("Data contains NaN or infinite values")
                return False

            # Check for sufficient variance
            if np.var(treatment_data) == 0 and np.var(control_data) == 0:
                logger.warning("No variance in either group")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating A/B test data: {e}")
            return False

    @staticmethod
    def validate_time_series_data(
        data: pd.DataFrame,
        time_col: str,
        outcome_col: str,
        min_periods: int = 5
    ) -> bool:
        """
        Validate time series data for interrupted time series analysis

        Args:
            data: DataFrame with time series data
            time_col: Name of time column
            outcome_col: Name of outcome column
            min_periods: Minimum number of time periods required

        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required columns exist
            if time_col not in data.columns or outcome_col not in data.columns:
                logger.warning("Required columns missing from data")
                return False

            # Check minimum number of periods
            if len(data) < min_periods:
                logger.warning(f"Insufficient time periods: {len(data)} < {min_periods}")
                return False

            # Check for missing values in key columns
            if data[time_col].isnull().any() or data[outcome_col].isnull().any():
                logger.warning("Missing values in key columns")
                return False

            # Check time column is properly ordered
            if not data[time_col].is_monotonic_increasing:
                logger.warning("Time column is not properly ordered")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating time series data: {e}")
            return False

    @staticmethod
    def validate_panel_data(
        data: pd.DataFrame,
        unit_col: str,
        time_col: str,
        treatment_col: str,
        outcome_col: str
    ) -> bool:
        """
        Validate panel data for difference-in-differences analysis

        Args:
            data: Panel DataFrame
            unit_col: Unit identifier column
            time_col: Time identifier column
            treatment_col: Treatment indicator column
            outcome_col: Outcome variable column

        Returns:
            True if data is valid, False otherwise
        """
        try:
            required_cols = [unit_col, time_col, treatment_col, outcome_col]

            # Check all required columns exist
            if not all(col in data.columns for col in required_cols):
                missing_cols = [col for col in required_cols if col not in data.columns]
                logger.warning(f"Missing columns: {missing_cols}")
                return False

            # Check for sufficient variation in treatment
            treatment_variation = data[treatment_col].nunique()
            if treatment_variation < 2:
                logger.warning("Insufficient variation in treatment variable")
                return False

            # Check for balanced panel (optional warning)
            unit_counts = data.groupby(unit_col).size()
            if unit_counts.std() > 0:
                logger.info("Panel is unbalanced (different number of observations per unit)")

            # Check for pre and post periods
            time_periods = data[time_col].nunique()
            if time_periods < 2:
                logger.warning("Need at least 2 time periods for difference-in-differences")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating panel data: {e}")
            return False


class StatisticalHelpers:
    """Statistical calculation helpers for causal analysis"""

    @staticmethod
    def pooled_standard_deviation(
        group1: np.ndarray,
        group2: np.ndarray
    ) -> float:
        """
        Calculate pooled standard deviation for two groups

        Args:
            group1: First group data
            group2: Second group data

        Returns:
            Pooled standard deviation
        """
        n1, n2 = len(group1), len(group2)
        s1_sq = np.var(group1, ddof=1)
        s2_sq = np.var(group2, ddof=1)

        pooled_var = ((n1 - 1) * s1_sq + (n2 - 1) * s2_sq) / (n1 + n2 - 2)
        return np.sqrt(pooled_var)

    @staticmethod
    def standard_error_difference(
        group1: np.ndarray,
        group2: np.ndarray
    ) -> float:
        """
        Calculate standard error of the difference between two means

        Args:
            group1: First group data
            group2: Second group data

        Returns:
            Standard error of the difference
        """
        n1, n2 = len(group1), len(group2)
        s1_sq = np.var(group1, ddof=1)
        s2_sq = np.var(group2, ddof=1)

        se_diff = np.sqrt(s1_sq / n1 + s2_sq / n2)
        return se_diff

    @staticmethod
    def cohens_d(
        group1: np.ndarray,
        group2: np.ndarray
    ) -> float:
        """
        Calculate Cohen's d effect size

        Args:
            group1: First group data (typically treatment)
            group2: Second group data (typically control)

        Returns:
            Cohen's d effect size
        """
        mean1, mean2 = np.mean(group1), np.mean(group2)
        pooled_std = StatisticalHelpers.pooled_standard_deviation(group1, group2)

        if pooled_std == 0:
            return 0.0

        return (mean1 - mean2) / pooled_std

    @staticmethod
    def calculate_minimum_detectable_effect(
        baseline_std: float,
        sample_size_per_group: int,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> float:
        """
        Calculate minimum detectable effect size for experiment planning

        Args:
            baseline_std: Standard deviation of the baseline metric
            sample_size_per_group: Sample size per experimental group
            alpha: Significance level (Type I error rate)
            power: Desired statistical power (1 - Type II error rate)

        Returns:
            Minimum detectable effect size
        """
        from scipy import stats

        # Critical values for two-tailed test
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(power)

        # MDE calculation
        mde = (z_alpha + z_beta) * baseline_std * np.sqrt(2 / sample_size_per_group)

        return mde

    @staticmethod
    def sample_size_calculator(
        effect_size: float,
        alpha: float = 0.05,
        power: float = 0.8,
        two_tailed: bool = True
    ) -> int:
        """
        Calculate required sample size for detecting a given effect size

        Args:
            effect_size: Effect size to detect (Cohen's d)
            alpha: Significance level
            power: Desired statistical power
            two_tailed: Whether to use two-tailed test

        Returns:
            Required sample size per group
        """
        from scipy import stats

        # Adjust alpha for one vs two-tailed test
        if two_tailed:
            alpha_adj = alpha / 2
        else:
            alpha_adj = alpha

        # Critical values
        z_alpha = stats.norm.ppf(1 - alpha_adj)
        z_beta = stats.norm.ppf(power)

        # Sample size calculation
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2

        return int(np.ceil(n))


class ExperimentDesignHelpers:
    """Helpers for designing causal experiments"""

    @staticmethod
    def randomization_check(
        data: pd.DataFrame,
        treatment_col: str,
        covariate_cols: List[str],
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """
        Check balance of covariates across treatment groups

        Args:
            data: DataFrame with experiment data
            treatment_col: Treatment assignment column
            covariate_cols: List of covariate columns to check
            significance_level: Significance level for balance tests

        Returns:
            Dictionary with balance test results
        """
        from scipy import stats

        balance_results = {}
        overall_balanced = True

        treatment_groups = data[treatment_col].unique()

        for covariate in covariate_cols:
            try:
                # Get covariate values for each treatment group
                groups_data = [
                    data[data[treatment_col] == group][covariate].dropna().values
                    for group in treatment_groups
                ]

                # Remove empty groups
                groups_data = [group for group in groups_data if len(group) > 0]

                if len(groups_data) < 2:
                    continue

                # Conduct ANOVA or t-test depending on number of groups
                if len(groups_data) == 2:
                    stat, p_value = stats.ttest_ind(groups_data[0], groups_data[1])
                    test_name = "t-test"
                else:
                    stat, p_value = stats.f_oneway(*groups_data)
                    test_name = "ANOVA"

                is_balanced = p_value > significance_level
                if not is_balanced:
                    overall_balanced = False

                balance_results[covariate] = {
                    "test_statistic": stat,
                    "p_value": p_value,
                    "is_balanced": is_balanced,
                    "test_name": test_name,
                    "group_means": {
                        str(group): np.mean(data[data[treatment_col] == group][covariate])
                        for group in treatment_groups
                    }
                }

            except Exception as e:
                logger.warning(f"Could not perform balance check for {covariate}: {e}")
                balance_results[covariate] = {
                    "error": str(e),
                    "is_balanced": None
                }

        balance_results["overall_balanced"] = overall_balanced
        balance_results["significance_level"] = significance_level

        return balance_results

    @staticmethod
    def power_analysis(
        effect_sizes: List[float],
        sample_sizes: List[int],
        alpha: float = 0.05
    ) -> pd.DataFrame:
        """
        Conduct power analysis for different effect sizes and sample sizes

        Args:
            effect_sizes: List of effect sizes to analyze
            sample_sizes: List of sample sizes to analyze
            alpha: Significance level

        Returns:
            DataFrame with power analysis results
        """
        from scipy import stats

        results = []

        for effect_size in effect_sizes:
            for sample_size in sample_sizes:
                # Calculate power for two-sample t-test
                # Using non-centrality parameter approach
                ncp = effect_size * np.sqrt(sample_size / 2)
                df = 2 * sample_size - 2

                # Critical value for two-tailed test
                t_critical = stats.t.ppf(1 - alpha / 2, df)

                # Power calculation
                power = 1 - stats.nct.cdf(t_critical, df, ncp) + stats.nct.cdf(-t_critical, df, ncp)

                results.append({
                    "effect_size": effect_size,
                    "sample_size": sample_size,
                    "power": power,
                    "alpha": alpha
                })

        return pd.DataFrame(results)


class BusinessMetricsHelpers:
    """Helpers for translating statistical results to business metrics"""

    @staticmethod
    def calculate_business_impact(
        effect_size: float,
        baseline_value: float,
        volume: int,
        confidence_interval: Tuple[float, float] = None
    ) -> Dict[str, Any]:
        """
        Calculate business impact from statistical effect size

        Args:
            effect_size: Statistical effect size (absolute or percentage)
            baseline_value: Baseline value of the metric
            volume: Volume/scale factor (e.g., customers, transactions)
            confidence_interval: Optional confidence interval for effect size

        Returns:
            Dictionary with business impact calculations
        """
        # Calculate absolute impact
        absolute_impact = effect_size * volume

        # Calculate percentage impact
        if baseline_value != 0:
            percentage_impact = (effect_size / baseline_value) * 100
        else:
            percentage_impact = None

        result = {
            "effect_size": effect_size,
            "absolute_impact": absolute_impact,
            "percentage_impact": percentage_impact,
            "baseline_value": baseline_value,
            "volume": volume
        }

        # Add confidence intervals if provided
        if confidence_interval is not None:
            ci_lower, ci_upper = confidence_interval

            result["confidence_interval"] = {
                "lower": {
                    "effect_size": ci_lower,
                    "absolute_impact": ci_lower * volume,
                    "percentage_impact": (ci_lower / baseline_value) * 100 if baseline_value != 0 else None
                },
                "upper": {
                    "effect_size": ci_upper,
                    "absolute_impact": ci_upper * volume,
                    "percentage_impact": (ci_upper / baseline_value) * 100 if baseline_value != 0 else None
                }
            }

        return result

    @staticmethod
    def roi_calculation(
        revenue_impact: float,
        cost_of_intervention: float,
        time_horizon_months: int = 12
    ) -> Dict[str, float]:
        """
        Calculate ROI metrics for causal interventions

        Args:
            revenue_impact: Monthly revenue impact from intervention
            cost_of_intervention: Total cost of implementing intervention
            time_horizon_months: Time horizon for ROI calculation

        Returns:
            Dictionary with ROI metrics
        """
        # Total revenue over time horizon
        total_revenue_impact = revenue_impact * time_horizon_months

        # Calculate ROI
        if cost_of_intervention != 0:
            roi_percentage = ((total_revenue_impact - cost_of_intervention) / cost_of_intervention) * 100
            payback_months = cost_of_intervention / revenue_impact if revenue_impact > 0 else float('inf')
        else:
            roi_percentage = float('inf') if total_revenue_impact > 0 else 0
            payback_months = 0

        return {
            "roi_percentage": roi_percentage,
            "total_revenue_impact": total_revenue_impact,
            "net_benefit": total_revenue_impact - cost_of_intervention,
            "payback_months": payback_months,
            "cost_of_intervention": cost_of_intervention,
            "monthly_revenue_impact": revenue_impact,
            "time_horizon_months": time_horizon_months
        }