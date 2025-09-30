"""Core exceptions for the application."""

from fastapi import HTTPException
from typing import Optional, Any


class ValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any = None):
        if identifier:
            self.message = f"{resource} with identifier '{identifier}' not found"
        else:
            self.message = f"{resource} not found"
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Raised when business logic constraints are violated."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class AnalysisError(Exception):
    """Raised when causal analysis fails."""

    def __init__(self, message: str, analysis_type: str, details: Optional[Any] = None):
        self.message = message
        self.analysis_type = analysis_type
        self.details = details
        super().__init__(self.message)


class InsufficientDataError(ValidationError):
    """Raised when there is insufficient data for analysis."""
    pass


class StatisticalError(AnalysisError):
    """Raised when statistical computations fail."""
    pass