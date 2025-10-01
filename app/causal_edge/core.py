"""
Core Causal Analysis Engine

This module provides the main causal inference algorithms and analysis
capabilities for the Causal Edge application.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import scipy.stats as stats
from datetime import datetime
import logging

from .utils import CausalValidators, StatisticalHelpers

logger = logging.getLogger(__name__)


class CausalMethod(str, Enum):
    """Available causal inference methods"""
    T_TEST = "t_test"
    WELCH_T_TEST = "welch_t_test"
    MANN_WHITNEY_U = "mann_whitney_u"
    PROPENSITY_SCORE_MATCHING = "propensity_score_matching"
    INSTRUMENTAL_VARIABLE = "instrumental_variable"
    REGRESSION_DISCONTINUITY = "regression_discontinuity"
    DIFFERENCE_IN_DIFFERENCES = "difference_in_differences"
    INTERRUPTED_TIME_SERIES = "interrupted_time_series"
    BAYESIAN_CAUSAL = "bayesian_causal"


class CausalAnalysisResult:
    """Container for causal analysis results"""

    def __init__(
        self,
        method: CausalMethod,
        effect_size: float,
        confidence_interval: Tuple[float, float],
        p_value: float,
        statistical_power: float = None,
        sample_sizes: Dict[str, int] = None,
        additional_metrics: Dict[str, Any] = None
    ):
        self.method = method
        self.effect_size = effect_size
        self.confidence_interval = confidence_interval
        self.p_value = p_value
        self.statistical_power = statistical_power
        self.sample_sizes = sample_sizes or {}
        self.additional_metrics = additional_metrics or {}
        self.analysis_timestamp = datetime.utcnow()

    @property
    def is_significant(self) -> bool:
        """Check if result is statistically significant at α=0.05"""
        return self.p_value < 0.05

    @property
    def effect_size_interpretation(self) -> str:
        """Interpret effect size magnitude"""
        abs_effect = abs(self.effect_size)
        if abs_effect < 0.2:
            return "negligible"
        elif abs_effect < 0.5:
            return "small"
        elif abs_effect < 0.8:
            return "medium"
        else:
            return "large"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            "method": self.method.value,
            "effect_size": self.effect_size,
            "confidence_interval": list(self.confidence_interval),
            "p_value": self.p_value,
            "statistical_power": self.statistical_power,
            "sample_sizes": self.sample_sizes,
            "additional_metrics": self.additional_metrics,
            "is_significant": self.is_significant,
            "effect_size_interpretation": self.effect_size_interpretation,
            "analysis_timestamp": self.analysis_timestamp.isoformat()
        }


class CausalAnalyzer:
    """
    Main causal analysis engine

    This class provides methods for conducting various types of causal analysis
    suitable for business intelligence and competitive analysis scenarios.
    """

    def __init__(self, significance_level: float = 0.05, random_state: int = 42):
        self.significance_level = significance_level
        self.random_state = random_state
        self.validators = CausalValidators()
        self.stats_helpers = StatisticalHelpers()

        # Set random seed for reproducibility
        np.random.seed(random_state)

    def ab_test_analysis(
        self,
        treatment_data: Union[List[float], np.ndarray],
        control_data: Union[List[float], np.ndarray],
        method: CausalMethod = CausalMethod.WELCH_T_TEST,
        equal_variance: bool = False
    ) -> CausalAnalysisResult:
        """
        Conduct A/B test analysis using specified statistical method

        Args:
            treatment_data: Outcome values for treatment group
            control_data: Outcome values for control group
            method: Statistical method to use
            equal_variance: Whether to assume equal variances (for t-tests)

        Returns:
            CausalAnalysisResult with test statistics and interpretation
        """
        treatment_data = np.array(treatment_data)
        control_data = np.array(control_data)

        # Validate data
        if not self.validators.validate_ab_test_data(treatment_data, control_data):
            raise ValueError("Invalid A/B test data")

        if method == CausalMethod.T_TEST:
            return self._t_test_analysis(treatment_data, control_data, equal_variance=True)
        elif method == CausalMethod.WELCH_T_TEST:
            return self._t_test_analysis(treatment_data, control_data, equal_variance=False)
        elif method == CausalMethod.MANN_WHITNEY_U:
            return self._mann_whitney_analysis(treatment_data, control_data)
        else:
            raise ValueError(f"Method {method} not supported for A/B testing")

    def _t_test_analysis(
        self,
        treatment_data: np.ndarray,
        control_data: np.ndarray,
        equal_variance: bool = False
    ) -> CausalAnalysisResult:
        """Conduct t-test analysis"""

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(
            treatment_data, control_data, equal_var=equal_variance
        )

        # Calculate effect size (Cohen's d)
        pooled_std = self.stats_helpers.pooled_standard_deviation(
            treatment_data, control_data
        )
        cohens_d = (np.mean(treatment_data) - np.mean(control_data)) / pooled_std

        # Calculate confidence interval for mean difference
        mean_diff = np.mean(treatment_data) - np.mean(control_data)
        se_diff = self.stats_helpers.standard_error_difference(
            treatment_data, control_data
        )

        # Degrees of freedom
        if equal_variance:
            dof = len(treatment_data) + len(control_data) - 2
        else:
            # Welch's t-test degrees of freedom
            s1_sq = np.var(treatment_data, ddof=1)
            s2_sq = np.var(control_data, ddof=1)
            n1, n2 = len(treatment_data), len(control_data)
            dof = ((s1_sq/n1 + s2_sq/n2)**2) / (
                (s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1)
            )

        t_critical = stats.t.ppf(1 - self.significance_level/2, dof)
        margin_error = t_critical * se_diff

        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error

        # Calculate statistical power
        statistical_power = self._calculate_power_t_test(
            treatment_data, control_data, cohens_d
        )

        method = CausalMethod.T_TEST if equal_variance else CausalMethod.WELCH_T_TEST

        return CausalAnalysisResult(
            method=method,
            effect_size=cohens_d,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            statistical_power=statistical_power,
            sample_sizes={
                "treatment": len(treatment_data),
                "control": len(control_data)
            },
            additional_metrics={
                "t_statistic": t_stat,
                "degrees_of_freedom": dof,
                "mean_difference": mean_diff,
                "treatment_mean": np.mean(treatment_data),
                "control_mean": np.mean(control_data),
                "treatment_std": np.std(treatment_data, ddof=1),
                "control_std": np.std(control_data, ddof=1)
            }
        )

    def _mann_whitney_analysis(
        self,
        treatment_data: np.ndarray,
        control_data: np.ndarray
    ) -> CausalAnalysisResult:
        """Conduct Mann-Whitney U test (non-parametric)"""

        # Perform Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(
            treatment_data, control_data, alternative='two-sided'
        )

        # Calculate effect size (rank-biserial correlation)
        n1, n2 = len(treatment_data), len(control_data)
        effect_size = 1 - (2 * u_stat) / (n1 * n2)

        # Bootstrap confidence interval for median difference
        ci_lower, ci_upper = self._bootstrap_median_difference_ci(
            treatment_data, control_data
        )

        return CausalAnalysisResult(
            method=CausalMethod.MANN_WHITNEY_U,
            effect_size=effect_size,
            confidence_interval=(ci_lower, ci_upper),
            p_value=p_value,
            sample_sizes={
                "treatment": len(treatment_data),
                "control": len(control_data)
            },
            additional_metrics={
                "u_statistic": u_stat,
                "treatment_median": np.median(treatment_data),
                "control_median": np.median(control_data),
                "median_difference": np.median(treatment_data) - np.median(control_data)
            }
        )

    def propensity_score_matching(
        self,
        data: pd.DataFrame,
        treatment_col: str,
        outcome_col: str,
        covariate_cols: List[str],
        caliper: float = 0.1
    ) -> CausalAnalysisResult:
        """
        Conduct causal analysis using propensity score matching

        Args:
            data: DataFrame containing all variables
            treatment_col: Name of treatment indicator column
            outcome_col: Name of outcome variable column
            covariate_cols: List of covariate column names
            caliper: Maximum allowable difference for matching

        Returns:
            CausalAnalysisResult with matched analysis
        """
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.neighbors import NearestNeighbors
        except ImportError:
            raise ImportError("scikit-learn is required for propensity score matching")

        # Validate inputs
        required_cols = [treatment_col, outcome_col] + covariate_cols
        if not all(col in data.columns for col in required_cols):
            raise ValueError("Missing required columns in data")

        # Fit propensity score model
        X = data[covariate_cols]
        y = data[treatment_col]

        ps_model = LogisticRegression(random_state=self.random_state)
        ps_model.fit(X, y)

        # Calculate propensity scores
        propensity_scores = ps_model.predict_proba(X)[:, 1]
        data_with_ps = data.copy()
        data_with_ps['propensity_score'] = propensity_scores

        # Perform matching
        treated = data_with_ps[data_with_ps[treatment_col] == 1]
        control = data_with_ps[data_with_ps[treatment_col] == 0]

        matched_pairs = self._match_propensity_scores(
            treated, control, caliper
        )

        if len(matched_pairs) == 0:
            raise ValueError("No matches found within specified caliper")

        # Extract matched data
        matched_treatment = [pair[0][outcome_col] for pair in matched_pairs]
        matched_control = [pair[1][outcome_col] for pair in matched_pairs]

        # Analyze matched data
        result = self.ab_test_analysis(
            matched_treatment,
            matched_control,
            method=CausalMethod.WELCH_T_TEST
        )

        # Update method and add PS-specific metrics
        result.method = CausalMethod.PROPENSITY_SCORE_MATCHING
        result.additional_metrics.update({
            "original_treatment_size": len(treated),
            "original_control_size": len(control),
            "matched_pairs": len(matched_pairs),
            "caliper": caliper,
            "propensity_score_auc": self._calculate_ps_auc(X, y)
        })

        return result

    def difference_in_differences(
        self,
        data: pd.DataFrame,
        outcome_col: str,
        treatment_col: str,
        time_col: str,
        pre_period: Any,
        post_period: Any
    ) -> CausalAnalysisResult:
        """
        Conduct difference-in-differences analysis

        Args:
            data: Panel data with units, time, treatment, and outcomes
            outcome_col: Name of outcome variable
            treatment_col: Binary treatment indicator
            time_col: Time period identifier
            pre_period: Value(s) identifying pre-treatment periods
            post_period: Value(s) identifying post-treatment periods

        Returns:
            CausalAnalysisResult with DiD estimate
        """
        # Filter to relevant periods
        relevant_data = data[
            data[time_col].isin([pre_period, post_period])
        ].copy()

        # Create period indicator
        relevant_data['post'] = (relevant_data[time_col] == post_period).astype(int)

        # Calculate group means
        group_means = relevant_data.groupby([treatment_col, 'post'])[outcome_col].mean()

        # DiD calculation
        pre_treatment = group_means.loc[(1, 0)]
        post_treatment = group_means.loc[(1, 1)]
        pre_control = group_means.loc[(0, 0)]
        post_control = group_means.loc[(0, 1)]

        treatment_effect = pre_treatment - post_treatment
        control_effect = pre_control - post_control
        did_estimate = treatment_effect - control_effect

        # Statistical inference using regression
        try:
            import statsmodels.api as sm

            # Create interaction term
            relevant_data['treatment_post'] = (
                relevant_data[treatment_col] * relevant_data['post']
            )

            # Fit regression model
            X = relevant_data[[treatment_col, 'post', 'treatment_post']]
            X = sm.add_constant(X)
            y = relevant_data[outcome_col]

            model = sm.OLS(y, X).fit()

            # Extract DiD coefficient (interaction term)
            did_coef = model.params['treatment_post']
            did_se = model.bse['treatment_post']
            did_pvalue = model.pvalues['treatment_post']

            # Confidence interval
            ci_lower, ci_upper = model.conf_int().loc['treatment_post']

        except ImportError:
            # Fallback to basic statistical test
            logger.warning("statsmodels not available, using basic statistical test")
            did_coef = did_estimate
            # Approximate standard error and p-value
            did_se = np.sqrt(
                relevant_data[relevant_data[treatment_col] == 1][outcome_col].var() /
                len(relevant_data[relevant_data[treatment_col] == 1]) +
                relevant_data[relevant_data[treatment_col] == 0][outcome_col].var() /
                len(relevant_data[relevant_data[treatment_col] == 0])
            )
            t_stat = did_coef / did_se
            did_pvalue = 2 * (1 - stats.t.cdf(abs(t_stat), len(relevant_data) - 4))

            t_critical = stats.t.ppf(1 - self.significance_level/2, len(relevant_data) - 4)
            margin_error = t_critical * did_se
            ci_lower = did_coef - margin_error
            ci_upper = did_coef + margin_error

        return CausalAnalysisResult(
            method=CausalMethod.DIFFERENCE_IN_DIFFERENCES,
            effect_size=did_coef,
            confidence_interval=(ci_lower, ci_upper),
            p_value=did_pvalue,
            additional_metrics={
                "pre_treatment_mean": pre_treatment,
                "post_treatment_mean": post_treatment,
                "pre_control_mean": pre_control,
                "post_control_mean": post_control,
                "treatment_change": treatment_effect,
                "control_change": control_effect,
                "standard_error": did_se
            }
        )

    # Helper methods

    def _calculate_power_t_test(
        self,
        treatment_data: np.ndarray,
        control_data: np.ndarray,
        effect_size: float
    ) -> float:
        """Calculate statistical power for t-test"""
        try:
            from scipy.stats import power
            n1, n2 = len(treatment_data), len(control_data)
            # Simplified power calculation
            return float(
                1 - stats.t.cdf(
                    stats.t.ppf(1 - self.significance_level/2, n1 + n2 - 2),
                    n1 + n2 - 2,
                    loc=effect_size * np.sqrt(n1 * n2 / (n1 + n2))
                )
            )
        except:
            return None

    def _bootstrap_median_difference_ci(
        self,
        treatment_data: np.ndarray,
        control_data: np.ndarray,
        n_bootstrap: int = 1000
    ) -> Tuple[float, float]:
        """Bootstrap confidence interval for median difference"""
        bootstrap_diffs = []

        for _ in range(n_bootstrap):
            treatment_sample = np.random.choice(
                treatment_data, size=len(treatment_data), replace=True
            )
            control_sample = np.random.choice(
                control_data, size=len(control_data), replace=True
            )

            diff = np.median(treatment_sample) - np.median(control_sample)
            bootstrap_diffs.append(diff)

        bootstrap_diffs = np.array(bootstrap_diffs)
        alpha = self.significance_level

        ci_lower = np.percentile(bootstrap_diffs, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))

        return ci_lower, ci_upper

    def _match_propensity_scores(
        self,
        treated_df: pd.DataFrame,
        control_df: pd.DataFrame,
        caliper: float
    ) -> List[Tuple]:
        """Match treated and control units based on propensity scores"""
        matched_pairs = []
        used_control_indices = set()

        for _, treated_unit in treated_df.iterrows():
            treated_ps = treated_unit['propensity_score']

            # Find closest control unit within caliper
            best_match = None
            best_distance = float('inf')

            for control_idx, control_unit in control_df.iterrows():
                if control_idx in used_control_indices:
                    continue

                control_ps = control_unit['propensity_score']
                distance = abs(treated_ps - control_ps)

                if distance <= caliper and distance < best_distance:
                    best_distance = distance
                    best_match = (control_idx, control_unit)

            if best_match is not None:
                matched_pairs.append((treated_unit, best_match[1]))
                used_control_indices.add(best_match[0])

        return matched_pairs

    def _calculate_ps_auc(self, X: pd.DataFrame, y: pd.Series) -> float:
        """Calculate AUC for propensity score model"""
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import roc_auc_score

            model = LogisticRegression(random_state=self.random_state)
            model.fit(X, y)
            y_pred_proba = model.predict_proba(X)[:, 1]

            return roc_auc_score(y, y_pred_proba)
        except:
            return None