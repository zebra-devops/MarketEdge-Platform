"""
Admin Security Service

Provides secure utilities for super admin operations that require cross-tenant access.
All operations are logged and require proper justification for compliance.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from ..models.user import User, UserRole
from ..models.audit_log import AuditLog, AuditAction, AuditSeverity
from ..core.database import get_db
from ..middleware.tenant_context import SuperAdminContextManager

logger = logging.getLogger(__name__)


class AdminSecurityService:
    """
    Service for secure super admin operations with audit logging.
    
    All cross-tenant operations must provide justification and are automatically
    logged for compliance and security monitoring.
    """
    
    def __init__(self, admin_user: User):
        """Initialize with authenticated super admin user."""
        if admin_user.role != UserRole.admin:
            raise ValueError("AdminSecurityService requires super admin user")
        self.admin_user = admin_user
    
    async def enable_cross_tenant_access(
        self, 
        db: Session, 
        justification: str,
        duration_context: Optional[str] = None
    ) -> None:
        """
        Enable cross-tenant access for the current session.
        
        Args:
            db: Database session
            justification: Required justification for cross-tenant access
            duration_context: Optional context about expected duration
        """
        if not justification or len(justification.strip()) < 10:
            raise ValueError("Cross-tenant access requires detailed justification (min 10 characters)")
        
        try:
            # Enable cross-tenant access
            db.execute(text("SELECT set_config('app.allow_cross_tenant', 'true', true)"))
            db.execute(text("SELECT set_config('app.current_user_role', 'super_admin', true)"))
            db.commit()
            
            # Log the cross-tenant access enablement
            await self._log_security_event(
                db=db,
                action=AuditAction.ENABLE,
                resource_type="cross_tenant_access",
                description=f"Cross-tenant access enabled: {justification}",
                severity=AuditSeverity.HIGH,
                context_data={
                    "justification": justification,
                    "duration_context": duration_context,
                    "admin_user_id": str(self.admin_user.id)
                }
            )
            
            logger.warning(
                "Cross-tenant access enabled",
                extra={
                    "event": "cross_tenant_enabled",
                    "admin_user_id": str(self.admin_user.id),
                    "justification": justification,
                    "duration_context": duration_context
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to enable cross-tenant access",
                extra={
                    "event": "cross_tenant_enable_failed",
                    "admin_user_id": str(self.admin_user.id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def disable_cross_tenant_access(self, db: Session) -> None:
        """Disable cross-tenant access for the current session."""
        try:
            # Disable cross-tenant access
            db.execute(text("SELECT set_config('app.allow_cross_tenant', 'false', true)"))
            db.commit()
            
            # Log the cross-tenant access disabling
            await self._log_security_event(
                db=db,
                action=AuditAction.DISABLE,
                resource_type="cross_tenant_access", 
                description="Cross-tenant access disabled",
                severity=AuditSeverity.MEDIUM,
                context_data={
                    "admin_user_id": str(self.admin_user.id)
                }
            )
            
            logger.info(
                "Cross-tenant access disabled",
                extra={
                    "event": "cross_tenant_disabled",
                    "admin_user_id": str(self.admin_user.id)
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to disable cross-tenant access",
                extra={
                    "event": "cross_tenant_disable_failed",
                    "admin_user_id": str(self.admin_user.id),
                    "error": str(e)
                },
                exc_info=True
            )
            # Don't raise - we want to ensure security context is cleared
    
    @asynccontextmanager
    async def cross_tenant_context(
        self, 
        justification: str,
        duration_context: Optional[str] = None
    ):
        """
        Context manager for safe cross-tenant operations.
        
        Usage:
            admin_service = AdminSecurityService(admin_user)
            async with admin_service.cross_tenant_context("Data migration for org consolidation"):
                # Perform cross-tenant operations
                all_users = db.query(User).all()
        """
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            await self.enable_cross_tenant_access(db, justification, duration_context)
            yield db
        finally:
            await self.disable_cross_tenant_access(db)
            db.close()
    
    async def get_cross_tenant_data(
        self,
        model_class,
        filters: Optional[Dict[str, Any]] = None,
        justification: str = "",
        limit: Optional[int] = 1000
    ) -> List[Any]:
        """
        Safely retrieve cross-tenant data with audit logging.
        
        Args:
            model_class: SQLAlchemy model class to query
            filters: Optional filters to apply
            justification: Required justification for data access
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        if not justification:
            raise ValueError("Cross-tenant data access requires justification")
        
        async with self.cross_tenant_context(justification) as db:
            query = db.query(model_class)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if hasattr(model_class, key):
                        query = query.filter(getattr(model_class, key) == value)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            
            # Log the cross-tenant data access
            await self._log_security_event(
                db=db,
                action=AuditAction.READ,
                resource_type=model_class.__tablename__,
                description=f"Cross-tenant data access: {justification}",
                severity=AuditSeverity.HIGH,
                context_data={
                    "justification": justification,
                    "model_class": model_class.__name__,
                    "filters": filters,
                    "record_count": len(results),
                    "limit": limit
                }
            )
            
            return results
    
    async def execute_cross_tenant_update(
        self,
        model_class,
        filters: Dict[str, Any],
        updates: Dict[str, Any],
        justification: str,
        max_records: int = 100
    ) -> int:
        """
        Safely execute cross-tenant updates with audit logging.
        
        Args:
            model_class: SQLAlchemy model class to update
            filters: Filters to identify records to update
            updates: Fields and values to update
            justification: Required justification for update
            max_records: Maximum number of records to update (safety limit)
            
        Returns:
            Number of records updated
        """
        if not justification:
            raise ValueError("Cross-tenant updates require justification")
        
        if not filters:
            raise ValueError("Cross-tenant updates require specific filters")
        
        async with self.cross_tenant_context(justification) as db:
            # First, count records that would be affected
            query = db.query(model_class)
            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)
            
            affected_count = query.count()
            
            if affected_count > max_records:
                raise ValueError(f"Update would affect {affected_count} records, exceeding limit of {max_records}")
            
            # Perform the update
            updated_count = query.update(updates)
            db.commit()
            
            # Log the cross-tenant update
            await self._log_security_event(
                db=db,
                action=AuditAction.UPDATE,
                resource_type=model_class.__tablename__,
                description=f"Cross-tenant bulk update: {justification}",
                severity=AuditSeverity.CRITICAL,
                context_data={
                    "justification": justification,
                    "model_class": model_class.__name__,
                    "filters": filters,
                    "updates": updates,
                    "affected_count": updated_count,
                    "max_records_limit": max_records
                }
            )
            
            logger.warning(
                "Cross-tenant bulk update executed",
                extra={
                    "event": "cross_tenant_bulk_update",
                    "admin_user_id": str(self.admin_user.id),
                    "model_class": model_class.__name__,
                    "affected_count": updated_count,
                    "justification": justification
                }
            )
            
            return updated_count
    
    async def _log_security_event(
        self,
        db: Session,
        action: AuditAction,
        resource_type: str,
        description: str,
        severity: AuditSeverity,
        context_data: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> None:
        """Log security event to audit log."""
        try:
            audit_log = AuditLog(
                user_id=str(self.admin_user.id),
                organisation_id=str(self.admin_user.organisation_id),
                action=action,
                resource_type=resource_type,
                description=description,
                severity=severity,
                context_data=context_data or {},
                success=success
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            logger.error(
                "Failed to log security event",
                extra={
                    "event": "audit_log_failed",
                    "admin_user_id": str(self.admin_user.id),
                    "error": str(e)
                },
                exc_info=True
            )
            # Don't raise - we don't want audit logging failures to break operations
    
    async def validate_tenant_access_request(
        self,
        target_organisation_id: UUID,
        justification: str,
        requested_operations: List[str]
    ) -> bool:
        """
        Validate a request for cross-tenant access.
        
        This method can be extended with additional validation logic,
        approval workflows, or integration with external approval systems.
        
        Args:
            target_organisation_id: Organisation to access
            justification: Justification for access
            requested_operations: List of operations to perform
            
        Returns:
            True if access is approved
        """
        # Basic validation
        if not justification or len(justification.strip()) < 20:
            logger.warning(
                "Cross-tenant access denied: insufficient justification",
                extra={
                    "event": "access_denied_justification",
                    "admin_user_id": str(self.admin_user.id),
                    "target_organisation_id": str(target_organisation_id)
                }
            )
            return False
        
        if not requested_operations:
            logger.warning(
                "Cross-tenant access denied: no operations specified",
                extra={
                    "event": "access_denied_no_operations",
                    "admin_user_id": str(self.admin_user.id),
                    "target_organisation_id": str(target_organisation_id)
                }
            )
            return False
        
        # Log access request for audit
        logger.info(
            "Cross-tenant access request validated",
            extra={
                "event": "access_request_validated",
                "admin_user_id": str(self.admin_user.id),
                "target_organisation_id": str(target_organisation_id),
                "justification": justification,
                "operations": requested_operations
            }
        )
        
        return True


# Utility functions for common admin operations

async def get_admin_security_service(admin_user: User) -> AdminSecurityService:
    """Factory function to create AdminSecurityService with validation."""
    if not admin_user or admin_user.role != UserRole.admin:
        raise ValueError("AdminSecurityService requires authenticated super admin user")
    
    return AdminSecurityService(admin_user)


async def safe_cross_tenant_query(
    admin_user: User,
    model_class,
    justification: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 1000
):
    """Convenience function for safe cross-tenant queries."""
    admin_service = await get_admin_security_service(admin_user)
    return await admin_service.get_cross_tenant_data(
        model_class=model_class,
        filters=filters,
        justification=justification,
        limit=limit
    )