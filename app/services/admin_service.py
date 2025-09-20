"""
Secure Admin Service
Handles admin operations with proper async support and security validations
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from ..models.feature_flags import FeatureFlag, FeatureFlagOverride, FeatureFlagUsage
from ..models.modules import AnalyticsModule, OrganisationModule
from ..models.audit_log import AuditLog, AdminAction, AuditAction
from ..models.sectors import SICCode
from ..models.user import User
from .audit_service import AuditService

logger = logging.getLogger(__name__)


class AdminService:
    """Secure admin service with proper async support"""
    
    def __init__(self, db: AsyncSession, audit_service: Optional[AuditService] = None):
        self.db = db
        self.audit_service = audit_service or AuditService(db)
    
    async def get_feature_flags(
        self,
        admin_user: User,
        module_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get feature flags with security validation"""
        try:
            query = select(FeatureFlag)
            
            if module_id:
                # Validate module_id to prevent injection
                module_result = await self.db.execute(
                    select(AnalyticsModule).where(AnalyticsModule.id == module_id)
                )
                module = module_result.scalar_one_or_none()
                if not module:
                    raise ValueError(f"Invalid module_id: {module_id}")
                query = query.where(FeatureFlag.module_id == module_id)
            
            if enabled_only:
                query = query.where(FeatureFlag.is_enabled == True)
            
            query = query.order_by(FeatureFlag.created_at.desc())
            result = await self.db.execute(query)
            flags = result.scalars().all()
            
            # Log admin access
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.READ,
                resource_type="feature_flags",
                description=f"Admin {admin_user.email} accessed feature flags list",
                success=True
            )
            
            return [
                {
                    "id": flag.id,
                    "flag_key": flag.flag_key,
                    "name": flag.name,
                    "description": flag.description,
                    "is_enabled": flag.is_enabled,
                    "rollout_percentage": flag.rollout_percentage,
                    "scope": flag.scope.value,
                    "status": flag.status.value,
                    "config": flag.config,
                    "allowed_sectors": flag.allowed_sectors,
                    "blocked_sectors": flag.blocked_sectors,
                    "module_id": flag.module_id,
                    "created_at": flag.created_at,
                    "updated_at": flag.updated_at
                }
                for flag in flags
            ]
            
        except Exception as e:
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.READ,
                resource_type="feature_flags",
                description=f"Failed to access feature flags: {str(e)}",
                success=False,
                error_message=str(e)
            )
            logger.error(f"Failed to get feature flags: {e}")
            raise
    
    async def update_feature_flag(
        self,
        flag_id: str,
        admin_user: User,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update feature flag with validation and auditing"""
        try:
            # Validate UUID format
            if not self._is_valid_uuid(flag_id):
                raise ValueError("Invalid flag ID format")
            
            # Get existing flag
            result = await self.db.execute(
                select(FeatureFlag).where(FeatureFlag.id == flag_id)
            )
            flag = result.scalar_one_or_none()
            
            if not flag:
                raise ValueError(f"Feature flag not found: {flag_id}")
            
            # Store original values for audit
            original_values = {
                "is_enabled": flag.is_enabled,
                "rollout_percentage": flag.rollout_percentage,
                "config": flag.config.copy() if flag.config else {}
            }
            
            # Apply validated updates
            for key, value in updates.items():
                if hasattr(flag, key) and key in ['is_enabled', 'rollout_percentage', 'config', 'name', 'description']:
                    # Validate specific fields
                    if key == 'rollout_percentage' and (not isinstance(value, int) or value < 0 or value > 100):
                        raise ValueError("rollout_percentage must be between 0 and 100")
                    
                    if key == 'config' and not isinstance(value, dict):
                        raise ValueError("config must be a dictionary")
                    
                    setattr(flag, key, value)
            
            flag.updated_by = admin_user.id
            flag.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(flag)
            
            # Log the change
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.UPDATE,
                resource_type="feature_flag",
                resource_id=flag_id,
                description=f"Admin {admin_user.email} updated feature flag {flag.flag_key}",
                success=True,
                changes={
                    "original": original_values,
                    "updated": updates
                }
            )
            
            return {
                "id": flag.id,
                "flag_key": flag.flag_key,
                "message": "Feature flag updated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.UPDATE,
                resource_type="feature_flag",
                resource_id=flag_id,
                description=f"Failed to update feature flag: {str(e)}",
                success=False,
                error_message=str(e)
            )
            logger.error(f"Failed to update feature flag {flag_id}: {e}")
            raise
    
    async def get_audit_logs(
        self,
        admin_user: User,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None,
        resource_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit logs with security validation"""
        try:
            # Validate pagination parameters
            limit = min(max(1, limit), 1000)  # Limit between 1-1000
            offset = max(0, offset)
            
            query = select(AuditLog).order_by(AuditLog.timestamp.desc())
            
            if action_filter:
                # Validate action filter against enum
                if action_filter.upper() in [action.value.upper() for action in AuditAction]:
                    query = query.where(AuditLog.action == action_filter.upper())
                else:
                    raise ValueError(f"Invalid action filter: {action_filter}")
            
            if resource_filter:
                # Sanitize resource filter
                resource_filter = resource_filter.replace('%', '').replace('_', '')
                query = query.where(AuditLog.resource_type.ilike(f"%{resource_filter}%"))
            
            # Get total count
            count_result = await self.db.execute(
                select(AuditLog).where(
                    query.whereclause if query.whereclause is not None else True
                )
            )
            total = len(count_result.scalars().all())
            
            # Get paginated results
            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            # Log admin access
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.READ,
                resource_type="audit_logs",
                description=f"Admin {admin_user.email} accessed audit logs",
                success=True
            )
            
            return {
                "audit_logs": [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp,
                        "user_id": log.user_id,
                        "organisation_id": log.organisation_id,
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "description": log.description,
                        "severity": log.severity.value,
                        "success": log.success,
                        "ip_address": str(log.ip_address) if log.ip_address else None
                    }
                    for log in logs
                ],
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            await self.audit_service.log_action(
                user_id=admin_user.id,
                action=AuditAction.READ,
                resource_type="audit_logs",
                description=f"Failed to access audit logs: {str(e)}",
                success=False,
                error_message=str(e)
            )
            logger.error(f"Failed to get audit logs: {e}")
            raise
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format"""
        import uuid
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False