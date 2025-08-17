from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.exc import SQLAlchemyError
from ..core.logging import logger
from ..core.config import settings
import traceback


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            logger.warning(
                "HTTP exception occurred",
                path=request.url.path,
                method=request.method,
                status_code=exc.status_code,
                detail=exc.detail
            )
            return self._create_error_response(
                request,
                exc.status_code,
                {"detail": exc.detail, "type": "http_exception"}
            )
        except SQLAlchemyError as exc:
            logger.error(
                "Database error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc)
            )
            return self._create_error_response(
                request,
                500,
                {"detail": "Database error occurred", "type": "database_error"}
            )
        except Exception as exc:
            logger.error(
                "Unexpected error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                traceback=traceback.format_exc()
            )
            return self._create_error_response(
                request,
                500,
                {"detail": "Internal server error", "type": "internal_error"}
            )
    
    def _create_error_response(self, request: Request, status_code: int, content: dict) -> JSONResponse:
        """Create an error response with appropriate CORS headers"""
        response = JSONResponse(
            status_code=status_code,
            content=content
        )
        
        # Add CORS headers to error responses
        origin = request.headers.get("origin")
        if origin:
            # Check if origin is in allowed origins
            allowed_origins = settings.CORS_ORIGINS
            if isinstance(allowed_origins, str):
                allowed_origins = [allowed_origins]
            
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Expose-Headers"] = "Content-Type, Authorization, X-Tenant-ID"
        
        return response