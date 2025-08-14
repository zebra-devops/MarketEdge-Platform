"""
Security Exception Handling Middleware

Provides comprehensive exception handling with security logging,
proper error responses, and threat detection capabilities.
"""

import json
import time
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.logging import logger
from ..core.validators import ValidationError


class SecurityExceptionHandler(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions with security-focused logging and response handling.
    
    Features:
    - Sanitized error responses (no sensitive data leakage)
    - Comprehensive security logging
    - Threat pattern detection
    - Performance monitoring
    - Graceful degradation
    """

    def __init__(self, app):
        super().__init__(app)
        self.security_events = {
            'validation_errors': 0,
            'authentication_failures': 0,
            'authorization_failures': 0,
            'injection_attempts': 0,
            'suspicious_activity': 0
        }

    async def dispatch(self, request: Request, call_next):
        """Main exception handling logic."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            response = await call_next(request)
            
            # Log performance metrics
            processing_time = (time.time() - start_time) * 1000
            if processing_time > 1000:  # Log slow requests
                logger.warning(
                    f"Slow request detected: {processing_time:.2f}ms",
                    extra={
                        "event": "slow_request",
                        "processing_time_ms": processing_time,
                        "path": request.url.path,
                        "method": request.method,
                        "request_id": request_id
                    }
                )
            
            return response
            
        except ValidationError as e:
            # Handle input validation errors with security logging
            self.security_events['validation_errors'] += 1
            
            logger.warning(
                f"Input validation failed: {str(e)}",
                extra={
                    "event": "validation_error",
                    "field": getattr(e, 'field', None),
                    "violation_type": getattr(e, 'violation_type', 'unknown'),
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid input",
                    "message": "The provided input failed validation",
                    "request_id": request_id
                }
            )
            
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions with enhanced logging
            if e.status_code == 401:
                self.security_events['authentication_failures'] += 1
                logger.warning(
                    "Authentication failure",
                    extra={
                        "event": "authentication_failure",
                        "status_code": e.status_code,
                        "path": request.url.path,
                        "method": request.method,
                        "request_id": request_id,
                        "client_ip": self._get_client_ip(request)
                    }
                )
            elif e.status_code == 403:
                self.security_events['authorization_failures'] += 1
                logger.warning(
                    "Authorization failure",
                    extra={
                        "event": "authorization_failure",
                        "status_code": e.status_code,
                        "path": request.url.path,
                        "method": request.method,
                        "request_id": request_id,
                        "client_ip": self._get_client_ip(request)
                    }
                )
            
            # Return the original HTTP exception response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail if isinstance(e.detail, str) else "Request failed",
                    "request_id": request_id
                }
            )
            
        except Exception as e:
            # Handle unexpected exceptions with comprehensive logging
            error_type = type(e).__name__
            
            # Check for potential security threats
            error_str = str(e).lower()
            threat_indicators = [
                'injection', 'xss', 'csrf', 'sql', 'script',
                'eval', 'exec', 'system', 'file', 'path'
            ]
            
            if any(indicator in error_str for indicator in threat_indicators):
                self.security_events['injection_attempts'] += 1
                logger.error(
                    f"Potential security threat detected: {error_type}",
                    extra={
                        "event": "security_threat_detected",
                        "error_type": error_type,
                        "threat_indicators": [ind for ind in threat_indicators if ind in error_str],
                        "path": request.url.path,
                        "method": request.method,
                        "request_id": request_id,
                        "client_ip": self._get_client_ip(request)
                    }
                )
            else:
                logger.error(
                    f"Unhandled exception: {error_type}",
                    extra={
                        "event": "unhandled_exception",
                        "error_type": error_type,
                        "error_message": str(e),
                        "path": request.url.path,
                        "method": request.method,
                        "request_id": request_id,
                        "traceback": traceback.format_exc()
                    }
                )
            
            # Return sanitized error response (no sensitive data)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id
                }
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request headers."""
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client address
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics for monitoring."""
        return {
            "security_events": self.security_events.copy(),
            "timestamp": time.time()
        }

    def reset_security_metrics(self):
        """Reset security event counters (for periodic reporting)."""
        self.security_events = {key: 0 for key in self.security_events.keys()}


class GracefulDegradationHandler:
    """
    Handler for graceful degradation when critical services are unavailable.
    
    Provides fallback responses when dependencies like Redis or external services fail.
    """
    
    @staticmethod
    def handle_redis_failure(operation: str, fallback_value: Any = None) -> Any:
        """Handle Redis connection failures gracefully."""
        logger.warning(
            f"Redis operation failed, using fallback: {operation}",
            extra={
                "event": "redis_fallback",
                "operation": operation,
                "fallback_used": True
            }
        )
        return fallback_value

    @staticmethod
    def handle_database_failure(operation: str) -> JSONResponse:
        """Handle database connection failures."""
        logger.error(
            f"Database operation failed: {operation}",
            extra={
                "event": "database_failure",
                "operation": operation,
                "severity": "critical"
            }
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service temporarily unavailable",
                "message": "Database service is currently unavailable. Please try again later.",
                "retry_after": 30
            }
        )

    @staticmethod
    def handle_external_service_failure(service: str) -> Dict[str, Any]:
        """Handle external service failures with appropriate fallbacks."""
        logger.warning(
            f"External service unavailable: {service}",
            extra={
                "event": "external_service_failure",
                "service": service,
                "fallback_used": True
            }
        )
        
        return {
            "service": service,
            "status": "unavailable",
            "fallback_active": True,
            "message": f"{service} is temporarily unavailable"
        }


def setup_security_monitoring():
    """Setup security monitoring and alerting."""
    
    # This would typically integrate with monitoring systems like:
    # - Prometheus/Grafana
    # - Datadog
    # - New Relic
    # - Custom alerting systems
    
    logger.info("Security monitoring initialized")