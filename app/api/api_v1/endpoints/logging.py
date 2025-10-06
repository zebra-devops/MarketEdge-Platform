"""
Frontend Error Logging API endpoints
Handles error logs sent from the frontend application
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.auth.dependencies import get_current_user_optional
from app.models.user import User
from app.core.database import get_async_db


router = APIRouter()


class ErrorContext(BaseModel):
    component: Optional[str] = None
    action: Optional[str] = None
    userId: Optional[str] = None
    organizationId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ErrorLogEntry(BaseModel):
    timestamp: str
    level: str = Field(..., pattern="^(error|warning|info)$")
    message: str
    stack: Optional[str] = None
    context: Optional[ErrorContext] = None
    userAgent: str
    url: str
    buildTime: Optional[str] = None


class FrontendErrorBatch(BaseModel):
    errors: List[ErrorLogEntry]
    sessionId: str
    timestamp: str


@router.post("/frontend-errors")
async def log_frontend_errors(
    error_batch: FrontendErrorBatch,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Log frontend errors sent from the client application.

    PUBLIC ENDPOINT - No authentication required.
    Errors can occur before authentication or when authentication fails,
    so this endpoint must be accessible without valid credentials.
    """
    # Optional: Extract user info from Authorization header if present (but don't require it)
    current_user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from app.auth.dependencies import get_current_user_optional
            # Try to get user if token is valid, but don't fail if it's not
            credentials = type('obj', (object,), {'credentials': auth_header.split(" ")[1]})()
            current_user = await get_current_user_optional(request, credentials, db)
        except Exception:
            # Ignore auth errors - this is a public endpoint
            pass
    try:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Process each error in the batch
        for error in error_batch.errors:
            # Build log entry data
            log_data = {
                "timestamp": error.timestamp,
                "level": error.level,
                "message": error.message,
                "stack": error.stack,
                "context": error.context.dict() if error.context else None,
                "user_agent": error.userAgent,
                "url": error.url,
                "build_time": error.buildTime,
                "session_id": error_batch.sessionId,
                "client_ip": client_ip,
                "user_id": current_user.id if current_user else None,
                "user_email": current_user.email if current_user else None,
                "organization_id": getattr(current_user, 'organisation_id', None) if current_user else None,
                "created_at": datetime.utcnow()
            }

            # Insert into database using raw SQL for simplicity
            # In a production system, you might want to use a proper model
            insert_query = text("""
                INSERT INTO frontend_error_logs (
                    timestamp, level, message, stack, context, user_agent, url,
                    build_time, session_id, client_ip, user_id, user_email,
                    organization_id, created_at
                ) VALUES (
                    :timestamp, :level, :message, :stack, :context, :user_agent, :url,
                    :build_time, :session_id, :client_ip, :user_id, :user_email,
                    :organization_id, :created_at
                )
            """)

            # Convert context to JSON string if present
            context_json = None
            if log_data["context"]:
                import json
                context_json = json.dumps(log_data["context"])

            await db.execute(insert_query, {
                "timestamp": log_data["timestamp"],
                "level": log_data["level"],
                "message": log_data["message"],
                "stack": log_data["stack"],
                "context": context_json,
                "user_agent": log_data["user_agent"],
                "url": log_data["url"],
                "build_time": log_data["build_time"],
                "session_id": log_data["session_id"],
                "client_ip": log_data["client_ip"],
                "user_id": log_data["user_id"],
                "user_email": log_data["user_email"],
                "organization_id": log_data["organization_id"],
                "created_at": log_data["created_at"]
            })

        await db.commit()

        # Log to console for development
        print(f"📝 Logged {len(error_batch.errors)} frontend errors for session {error_batch.sessionId}")
        for error in error_batch.errors:
            print(f"  {error.level.upper()}: {error.message}")
            if error.context and error.context.component:
                print(f"    Component: {error.context.component}")

        return {
            "status": "success",
            "logged_count": len(error_batch.errors),
            "session_id": error_batch.sessionId
        }

    except Exception as e:
        print(f"❌ Error logging frontend errors: {e}")
        # Don't raise HTTP exception for logging endpoint - just return error status
        return {
            "status": "error",
            "message": str(e),
            "logged_count": 0
        }


@router.get("/frontend-errors")
async def get_frontend_errors(
    limit: int = 100,
    level: Optional[str] = None,
    component: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Retrieve frontend error logs (admin only)
    """
    # Simple permission check - only allow admin/super_admin users
    if not current_user or current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Build query with filters
        where_conditions = []
        params = {"limit": limit}

        if level:
            where_conditions.append("level = :level")
            params["level"] = level

        if component:
            where_conditions.append("context->>'component' = :component")
            params["component"] = component

        if session_id:
            where_conditions.append("session_id = :session_id")
            params["session_id"] = session_id

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        query = text(f"""
            SELECT
                timestamp, level, message, stack, context, user_agent, url,
                build_time, session_id, client_ip, user_id, user_email,
                organization_id, created_at
            FROM frontend_error_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await db.execute(query, params)
        errors = result.fetchall()

        return {
            "errors": [dict(error._mapping) for error in errors],
            "count": len(errors)
        }

    except Exception as e:
        print(f"❌ Error retrieving frontend errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error logs")


@router.get("/frontend-errors/stats")
async def get_frontend_error_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get statistics about frontend errors (admin only)
    """
    # Simple permission check - only allow admin/super_admin users
    if not current_user or current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Get error counts by level
        level_stats_query = text("""
            SELECT level, COUNT(*) as count
            FROM frontend_error_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY level
        """)

        # Get error counts by component
        component_stats_query = text("""
            SELECT context->>'component' as component, COUNT(*) as count
            FROM frontend_error_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            AND context->>'component' IS NOT NULL
            GROUP BY context->>'component'
            ORDER BY count DESC
            LIMIT 10
        """)

        # Get total counts
        total_stats_query = text("""
            SELECT
                COUNT(*) as total_24h,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as total_1h
            FROM frontend_error_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)

        level_result = await db.execute(level_stats_query)
        component_result = await db.execute(component_stats_query)
        total_result = await db.execute(total_stats_query)

        level_stats = {row.level: row.count for row in level_result.fetchall()}
        component_stats = [{"component": row.component, "count": row.count} for row in component_result.fetchall()]
        total_stats = total_result.fetchone()

        return {
            "period": "24 hours",
            "totals": {
                "last_24h": total_stats.total_24h if total_stats else 0,
                "last_1h": total_stats.total_1h if total_stats else 0
            },
            "by_level": level_stats,
            "by_component": component_stats
        }

    except Exception as e:
        print(f"❌ Error retrieving frontend error stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error statistics")