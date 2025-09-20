"""
Admin Module Compatibility Bridge

This file provides a compatibility layer to ensure the admin module
can be imported from app.api.admin for backward compatibility while
the actual implementation remains at app.api.api_v1.endpoints.admin

CRITICAL FIX for ModuleNotFoundError: No module named 'app.api.admin'
"""

# Re-export everything from the actual admin module location
from .api_v1.endpoints.admin import *
from .api_v1.endpoints.admin import router

# Ensure all functions and classes are available
__all__ = ['router']

print("✅ Admin compatibility bridge loaded - app.api.admin now available")