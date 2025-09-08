from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..models.modules import AnalyticsModule, OrganisationModule, ModuleConfiguration, ModuleUsageLog, ModuleStatus
from ..models.sectors import SectorModule
from ..models.user import User
from ..services.audit_service import AuditService


class ModuleService:
    """
    Service for managing analytics modules, configurations, and usage tracking
    """
    
    def __init__(self, db: AsyncSession, audit_service: Optional[AuditService] = None):
        self.db = db
        self.audit_service = audit_service or AuditService(db)
    
    async def get_available_modules(
        self, 
        user: User, 
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get modules available to a user based on their organisation and sector
        """
        # Base query for active modules (unless including inactive)
        query = select(AnalyticsModule)
        if not include_inactive:
            query = query.where(AnalyticsModule.status == ModuleStatus.ACTIVE)
        
        result = await self.db.execute(query)
        all_modules = result.scalars().all()
        
        available_modules = []
        
        for module in all_modules:
            # Check if module is enabled for the organisation
            org_module = await self._get_organisation_module(module.id, user.organisation_id)
            
            if org_module and org_module.is_enabled:
                # Check user-specific access
                if self._is_user_allowed_access(org_module, user.id):
                    module_data = {
                        "id": module.id,
                        "name": module.name,
                        "description": module.description,
                        "version": module.version,
                        "module_type": module.module_type.value,
                        "status": module.status.value,
                        "is_core": module.is_core,
                        "requires_license": module.requires_license,
                        "pricing_tier": module.pricing_tier,
                        "configuration": org_module.configuration,
                        "last_accessed": org_module.last_accessed_at,
                        "access_count": org_module.access_count
                    }
                    available_modules.append(module_data)
        
        return available_modules
    
    async def get_sector_modules(self, sic_code: str) -> List[Dict[str, Any]]:
        """
        Get modules available for a specific sector
        """
        result = await self.db.execute(
            select(SectorModule)
            .where(SectorModule.sic_code == sic_code)
            .options(selectinload(SectorModule.module))
            .order_by(SectorModule.display_order)
        )
        sector_modules = result.scalars().all()
        
        modules_data = []
        for sector_module in sector_modules:
            if sector_module.is_enabled and sector_module.module:
                module_data = {
                    "id": sector_module.module.id,
                    "name": sector_module.module.name,
                    "description": sector_module.module.description,
                    "module_type": sector_module.module.module_type.value,
                    "is_default": sector_module.is_default,
                    "sector_configuration": sector_module.configuration,
                    "display_order": sector_module.display_order
                }
                modules_data.append(module_data)
        
        return modules_data
    
    async def enable_module_for_organisation(
        self, 
        module_id: str, 
        organisation_id: str, 
        enabled_by: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> OrganisationModule:
        """
        Enable a module for an organisation
        """
        # Check if module exists
        result = await self.db.execute(select(AnalyticsModule).where(AnalyticsModule.id == module_id))
        module = result.scalar_one_or_none()
        
        if not module:
            raise ValueError(f"Module {module_id} not found")
        
        # Check if already enabled
        existing = await self._get_organisation_module(module_id, organisation_id)
        
        if existing:
            # Update existing
            existing.is_enabled = True
            existing.configuration = configuration or existing.configuration
            existing.updated_by = enabled_by
            org_module = existing
        else:
            # Create new
            org_module = OrganisationModule(
                organisation_id=organisation_id,
                module_id=module_id,
                is_enabled=True,
                configuration=configuration or {},
                created_by=enabled_by
            )
            self.db.add(org_module)
        
        await self.db.commit()
        await self.db.refresh(org_module)
        
        # Log the action
        await self.audit_service.log_action(
            user_id=enabled_by,
            action="ENABLE",
            resource_type="organisation_module",
            resource_id=org_module.id,
            description=f"Enabled module {module_id} for organisation {organisation_id}",
            changes={"module_id": module_id, "configuration": configuration}
        )
        
        return org_module
    
    async def disable_module_for_organisation(
        self, 
        module_id: str, 
        organisation_id: str, 
        disabled_by: str,
        reason: Optional[str] = None
    ):
        """
        Disable a module for an organisation
        """
        org_module = await self._get_organisation_module(module_id, organisation_id)
        
        if not org_module:
            raise ValueError(f"Module {module_id} not enabled for organisation {organisation_id}")
        
        org_module.is_enabled = False
        org_module.updated_by = disabled_by
        
        await self.db.commit()
        
        # Log the action
        await self.audit_service.log_action(
            user_id=disabled_by,
            action="DISABLE",
            resource_type="organisation_module",
            resource_id=org_module.id,
            description=f"Disabled module {module_id} for organisation {organisation_id}",
            metadata={"reason": reason} if reason else {}
        )
    
    async def configure_module(
        self, 
        module_id: str, 
        organisation_id: str, 
        config_key: str, 
        config_value: Dict[str, Any],
        configured_by: str
    ) -> ModuleConfiguration:
        """
        Set module-specific configuration
        """
        # Check if configuration already exists
        result = await self.db.execute(
            select(ModuleConfiguration).where(
                and_(
                    ModuleConfiguration.module_id == module_id,
                    ModuleConfiguration.organisation_id == organisation_id,
                    ModuleConfiguration.config_key == config_key
                )
            )
        )
        existing_config = result.scalar_one_or_none()
        
        if existing_config:
            # Update existing
            old_value = existing_config.config_value
            existing_config.config_value = config_value
            existing_config.updated_by = configured_by
            config = existing_config
        else:
            # Create new
            config = ModuleConfiguration(
                module_id=module_id,
                organisation_id=organisation_id,
                config_key=config_key,
                config_value=config_value,
                created_by=configured_by
            )
            self.db.add(config)
            old_value = None
        
        await self.db.commit()
        await self.db.refresh(config)
        
        # Log the configuration change
        await self.audit_service.log_action(
            user_id=configured_by,
            action="CONFIGURE",
            resource_type="module_configuration",
            resource_id=config.id,
            description=f"Configured {config_key} for module {module_id}",
            changes={"old_value": old_value, "new_value": config_value}
        )
        
        return config
    
    async def log_module_usage(
        self, 
        module_id: str, 
        user: User, 
        action: str,
        endpoint: Optional[str] = None,
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log module usage for analytics and billing
        """
        usage_log = ModuleUsageLog(
            module_id=module_id,
            organisation_id=user.organisation_id,
            user_id=user.id,
            action=action,
            endpoint=endpoint,
            duration_ms=duration_ms,
            context=context or {},
            success=success,
            error_message=error_message
        )
        
        self.db.add(usage_log)
        
        # Update organisation module access tracking
        org_module = await self._get_organisation_module(module_id, user.organisation_id)
        if org_module:
            org_module.last_accessed_at = datetime.utcnow()
            org_module.access_count += 1
        
        await self.db.commit()
    
    async def get_module_usage_analytics(
        self, 
        module_id: str, 
        organisation_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage analytics for a module
        """
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = select(ModuleUsageLog).where(
            and_(
                ModuleUsageLog.module_id == module_id,
                ModuleUsageLog.timestamp >= start_date,
                ModuleUsageLog.timestamp <= end_date
            )
        )
        
        if organisation_id:
            query = query.where(ModuleUsageLog.organisation_id == organisation_id)
        
        result = await self.db.execute(query)
        usage_logs = result.scalars().all()
        
        # Calculate analytics
        total_usage = len(usage_logs)
        successful_usage = sum(1 for log in usage_logs if log.success)
        unique_users = len(set(log.user_id for log in usage_logs))
        unique_organisations = len(set(log.organisation_id for log in usage_logs))
        
        # Group by action
        actions_count = {}
        for log in usage_logs:
            actions_count[log.action] = actions_count.get(log.action, 0) + 1
        
        # Calculate average duration
        durations = [log.duration_ms for log in usage_logs if log.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else None
        
        return {
            "period": {"start": start_date, "end": end_date, "days": days},
            "total_usage": total_usage,
            "successful_usage": successful_usage,
            "failed_usage": total_usage - successful_usage,
            "success_rate": successful_usage / total_usage if total_usage > 0 else 1.0,
            "unique_users": unique_users,
            "unique_organisations": unique_organisations,
            "actions_breakdown": actions_count,
            "average_duration_ms": avg_duration,
            "daily_usage": self._group_usage_by_day(usage_logs)
        }
    
    async def get_organisation_module_summary(self, organisation_id: str) -> Dict[str, Any]:
        """
        Get summary of module usage for an organisation
        """
        result = await self.db.execute(
            select(OrganisationModule)
            .where(OrganisationModule.organisation_id == organisation_id)
            .options(selectinload(OrganisationModule.module))
        )
        org_modules = result.scalars().all()
        
        enabled_modules = []
        total_access_count = 0
        
        for org_module in org_modules:
            if org_module.is_enabled and org_module.module:
                module_data = {
                    "id": org_module.module.id,
                    "name": org_module.module.name,
                    "module_type": org_module.module.module_type.value,
                    "access_count": org_module.access_count,
                    "last_accessed": org_module.last_accessed_at,
                    "first_enabled": org_module.first_enabled_at
                }
                enabled_modules.append(module_data)
                total_access_count += org_module.access_count
        
        return {
            "organisation_id": organisation_id,
            "enabled_modules_count": len(enabled_modules),
            "total_access_count": total_access_count,
            "enabled_modules": enabled_modules
        }
    
    # Private helper methods
    
    async def _get_organisation_module(
        self, 
        module_id: str, 
        organisation_id: str
    ) -> Optional[OrganisationModule]:
        """Get organisation module configuration"""
        result = await self.db.execute(
            select(OrganisationModule).where(
                and_(
                    OrganisationModule.module_id == module_id,
                    OrganisationModule.organisation_id == organisation_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    def _is_user_allowed_access(self, org_module: OrganisationModule, user_id: str) -> bool:
        """Check if user has access to the module"""
        # If user is explicitly disabled, deny access
        if user_id in org_module.disabled_for_users:
            return False
        
        # If enabled_for_users is empty, allow all users
        if not org_module.enabled_for_users:
            return True
        
        # If user is explicitly enabled, allow access
        return user_id in org_module.enabled_for_users
    
    def _group_usage_by_day(self, usage_logs: List[ModuleUsageLog]) -> Dict[str, Dict[str, int]]:
        """Group usage logs by day for analytics"""
        daily_usage = {}
        
        for log in usage_logs:
            day_key = log.timestamp.strftime("%Y-%m-%d")
            if day_key not in daily_usage:
                daily_usage[day_key] = {"total": 0, "successful": 0, "failed": 0}
            
            daily_usage[day_key]["total"] += 1
            if log.success:
                daily_usage[day_key]["successful"] += 1
            else:
                daily_usage[day_key]["failed"] += 1
        
        return daily_usage