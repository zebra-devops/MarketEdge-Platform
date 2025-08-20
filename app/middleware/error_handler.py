from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.exc import SQLAlchemyError
from ..core.logging import logger
import traceback


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    def _add_cors_headers(self, response: JSONResponse, request: Request) -> JSONResponse:
        """Add CORS headers to error responses"""
        origin = request.headers.get("origin")
        if origin and origin in [
            "http://localhost:3000", "http://localhost:3001", "http://localhost:3002",
            "https://app.zebra.associates"
        ]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response
        
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
            response = JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "type": "http_exception"}
            )
            return self._add_cors_headers(response, request)
        except SQLAlchemyError as exc:
            logger.error(
                "Database error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                error_type=type(exc).__name__,
                traceback=traceback.format_exc()
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Database error occurred", 
                    "type": "database_error",
                    "error_details": str(exc) if hasattr(exc, '__str__') else None
                }
            )
            return self._add_cors_headers(response, request)
        except Exception as exc:
            logger.error(
                "Unexpected error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                traceback=traceback.format_exc()
            )
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error", 
                    "type": "internal_error",
                    "debug_error": str(exc)[:200] if hasattr(exc, '__str__') else "Unknown error",
                    "error_type": type(exc).__name__
                }
            )
            return self._add_cors_headers(response, request)