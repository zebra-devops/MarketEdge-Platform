from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.exc import SQLAlchemyError
from ..core.logging import logger
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
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "type": "http_exception"}
            )
        except SQLAlchemyError as exc:
            logger.error(
                "Database error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                error_type=type(exc).__name__,
                traceback=traceback.format_exc()
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Database error occurred", 
                    "type": "database_error",
                    "error_details": str(exc) if hasattr(exc, '__str__') else None
                }
            )
        except Exception as exc:
            logger.error(
                "Unexpected error occurred",
                path=request.url.path,
                method=request.method,
                error=str(exc),
                traceback=traceback.format_exc()
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "type": "internal_error"}
            )