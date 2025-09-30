"""
Causal Edge Module

This module provides advanced causal analysis and inference capabilities
for the MarketEdge platform. It includes:

- Causal inference algorithms
- A/B testing frameworks
- Intervention analysis
- Root cause analysis
- Predictive modeling with causal constraints

The module integrates with MarketEdge's multi-tenant architecture,
feature flag system, and analytics modules framework.
"""

from .core import CausalAnalyzer
from .models import CausalExperiment, CausalResult, Intervention
from .services import CausalAnalysisService, ExperimentService
from .utils import CausalValidators, StatisticalHelpers

__version__ = "1.0.0"
__author__ = "MarketEdge Team"

__all__ = [
    "CausalAnalyzer",
    "CausalExperiment",
    "CausalResult",
    "Intervention",
    "CausalAnalysisService",
    "ExperimentService",
    "CausalValidators",
    "StatisticalHelpers"
]