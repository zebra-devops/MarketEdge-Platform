"""
Feature Flag Middleware

Simple decorator for feature flag validation in API endpoints.
"""

from functools import wraps
from fastapi import HTTPException, status


def feature_flag_required(flag_name: str):
    """
    Decorator to require a feature flag to be enabled for an endpoint.

    For now, this is a simple implementation that allows all requests.
    In production, this would check against the FeatureFlagService.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement actual feature flag checking
            # For now, we'll just allow all requests to pass through
            # In production, you would:
            # 1. Get the current user/organization
            # 2. Check the feature flag using FeatureFlagService
            # 3. Raise HTTPException if not enabled

            return await func(*args, **kwargs)
        return wrapper
    return decorator