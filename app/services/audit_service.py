from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from datetime import datetime
import json

from ..models.audit_log import AuditLog, AdminAction, AuditAction, AuditSeverity


class AuditService:
    """
    Service for comprehensive audit logging and administrative action tracking
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        user_id: Optional[str],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        description: str = "",
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        organisation_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an auditable action
        """
        audit_log = AuditLog(
            user_id=user_id,
            organisation_id=organisation_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            severity=severity,
            changes=changes or {},
            context_data=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        return audit_log
    
    async def log_admin_action(
        self,
        admin_user_id: str,
        action_type: str,
        summary: str,
        target_organisation_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        justification: Optional[str] = None,
        configuration_changes: Optional[Dict[str, Any]] = None,
        affected_users_count: int = 0,
        affected_organisations_count: int = 0,
        requires_approval: bool = False
    ) -> AdminAction:
        """
        Log a high-level administrative action
        """
        admin_action = AdminAction(
            admin_user_id=admin_user_id,
            action_type=action_type,
            target_organisation_id=target_organisation_id,
            target_user_id=target_user_id,
            summary=summary,
            justification=justification,
            affected_users_count=affected_users_count,
            affected_organisations_count=affected_organisations_count,
            configuration_changes=configuration_changes or {},
            requires_approval=requires_approval
        )
        
        self.db.add(admin_action)
        await self.db.commit()
        await self.db.refresh(admin_action)
        
        return admin_action
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        organisation_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        severity: Optional[AuditSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit logs with filtering options
        """
        query = select(AuditLog)
        
        # Apply filters
        conditions = []
        
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        
        if organisation_id:
            conditions.append(AuditLog.organisation_id == organisation_id)
        
        if resource_type:
            conditions.append(AuditLog.resource_type == resource_type)
        
        if action:
            conditions.append(AuditLog.action == action)
        
        if severity:
            conditions.append(AuditLog.severity == severity)
        
        if start_date:
            conditions.append(AuditLog.timestamp >= start_date)
        
        if end_date:
            conditions.append(AuditLog.timestamp <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by timestamp descending
        query = query.order_by(desc(AuditLog.timestamp))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_admin_actions(
        self,
        admin_user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        target_organisation_id: Optional[str] = None,
        requires_approval: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AdminAction]:
        """
        Get administrative actions with filtering
        """
        query = select(AdminAction)
        
        # Apply filters
        conditions = []
        
        if admin_user_id:
            conditions.append(AdminAction.admin_user_id == admin_user_id)
        
        if action_type:
            conditions.append(AdminAction.action_type == action_type)
        
        if target_organisation_id:
            conditions.append(AdminAction.target_organisation_id == target_organisation_id)
        
        if requires_approval is not None:
            conditions.append(AdminAction.requires_approval == requires_approval)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by creation date descending
        query = query.order_by(desc(AdminAction.created_at))
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_security_events(
        self,
        severity_threshold: AuditSeverity = AuditSeverity.MEDIUM,
        hours: int = 24
    ) -> List[AuditLog]:
        """
        Get recent security-relevant events
        """
        from datetime import timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Define security-relevant actions and resource types
        security_actions = [
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
            AuditAction.CREATE,
            AuditAction.DELETE,
            AuditAction.ENABLE,
            AuditAction.DISABLE
        ]
        
        security_resources = [
            "user",
            "feature_flag",
            "module",
            "organisation",
            "feature_flag_override"
        ]
        
        query = select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_time,
                or_(
                    AuditLog.severity >= severity_threshold,
                    AuditLog.action.in_(security_actions),
                    AuditLog.resource_type.in_(security_resources),
                    AuditLog.success == False  # Failed operations
                )
            )
        ).order_by(desc(AuditLog.timestamp))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity summary for a specific user
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date
                )
            )
        )
        logs = result.scalars().all()
        
        # Calculate summary statistics
        total_actions = len(logs)
        actions_by_type = {}
        actions_by_resource = {}
        failed_actions = 0
        
        for log in logs:
            # Count by action type
            action_key = log.action.value
            actions_by_type[action_key] = actions_by_type.get(action_key, 0) + 1
            
            # Count by resource type
            resource_key = log.resource_type
            actions_by_resource[resource_key] = actions_by_resource.get(resource_key, 0) + 1
            
            # Count failures
            if not log.success:
                failed_actions += 1
        
        return {
            "period": {"start": start_date, "end": datetime.utcnow(), "days": days},
            "total_actions": total_actions,
            "failed_actions": failed_actions,
            "success_rate": (total_actions - failed_actions) / total_actions if total_actions > 0 else 1.0,
            "actions_by_type": actions_by_type,
            "actions_by_resource": actions_by_resource,
            "most_recent_login": self._get_most_recent_login(logs),
            "security_events": [
                log for log in logs 
                if log.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL] or not log.success
            ]
        }
    
    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """
        Export audit logs for compliance reporting
        """
        result = await self.db.execute(
            select(AuditLog).where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date
                )
            ).order_by(AuditLog.timestamp)
        )
        logs = result.scalars().all()
        
        if format.lower() == "json":
            return self._export_logs_as_json(logs)
        elif format.lower() == "csv":
            return self._export_logs_as_csv(logs)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    # Private helper methods
    
    def _get_most_recent_login(self, logs: List[AuditLog]) -> Optional[datetime]:
        """Get the most recent login timestamp from logs"""
        login_logs = [log for log in logs if log.action == AuditAction.LOGIN and log.success]
        return max(log.timestamp for log in login_logs) if login_logs else None
    
    def _export_logs_as_json(self, logs: List[AuditLog]) -> str:
        """Export logs as JSON"""
        log_data = []
        for log in logs:
            log_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "organisation_id": log.organisation_id,
                "action": log.action.value,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "severity": log.severity.value,
                "success": log.success,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "changes": log.changes,
                "metadata": log.metadata
            })
        
        return json.dumps(log_data, indent=2, default=str)
    
    def _export_logs_as_csv(self, logs: List[AuditLog]) -> str:
        """Export logs as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Timestamp", "User ID", "Organisation ID", "Action", "Resource Type",
            "Resource ID", "Description", "Severity", "Success", "IP Address"
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.user_id or "",
                log.organisation_id or "",
                log.action.value,
                log.resource_type,
                log.resource_id or "",
                log.description,
                log.severity.value,
                log.success,
                str(log.ip_address) if log.ip_address else ""
            ])
        
        return output.getvalue()