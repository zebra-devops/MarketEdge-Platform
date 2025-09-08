from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
import hashlib
import random

from ..models.feature_flags import FeatureFlag, FeatureFlagOverride, FeatureFlagUsage, FeatureFlagScope
from ..models.user import User
from ..models.organisation import Organisation
from ..services.audit_service import AuditService


class FeatureFlagService:
    """
    Service for managing feature flags with percentage rollouts,
    sector restrictions, and usage tracking
    """
    
    def __init__(self, db: AsyncSession, audit_service: Optional[AuditService] = None):
        self.db = db
        self.audit_service = audit_service or AuditService(db)
    
    async def is_feature_enabled(
        self, 
        flag_key: str, 
        user: User, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a specific user
        Considers rollout percentage, sector restrictions, and overrides
        """
        context = context or {}
        
        # Get the feature flag
        result = await self.db.execute(
            select(FeatureFlag)
            .where(FeatureFlag.flag_key == flag_key)
            .options(selectinload(FeatureFlag.overrides))
        )
        feature_flag = result.scalar_one_or_none()
        
        if not feature_flag:
            # Log usage for non-existent flag
            await self._log_usage(flag_key, user, False, context, "Flag not found")
            return False
        
        # Check if flag is globally disabled
        if not feature_flag.is_enabled:
            await self._log_usage(feature_flag.id, user, False, context, "Flag disabled")
            return False
        
        # Check for user-specific override
        user_override = await self._get_user_override(feature_flag.id, user.id)
        if user_override:
            enabled = user_override.is_enabled and (
                user_override.expires_at is None or 
                user_override.expires_at > datetime.utcnow()
            )
            await self._log_usage(feature_flag.id, user, enabled, context, "User override")
            return enabled
        
        # Check for organisation-specific override
        org_override = await self._get_organisation_override(feature_flag.id, user.organisation_id)
        if org_override:
            enabled = org_override.is_enabled and (
                org_override.expires_at is None or 
                org_override.expires_at > datetime.utcnow()
            )
            await self._log_usage(feature_flag.id, user, enabled, context, "Organisation override")
            return enabled
        
        # Check sector restrictions
        if not await self._is_sector_allowed(feature_flag, user):
            await self._log_usage(feature_flag.id, user, False, context, "Sector restricted")
            return False
        
        # Check rollout percentage
        if feature_flag.rollout_percentage >= 100:
            await self._log_usage(feature_flag.id, user, True, context, "Full rollout")
            return True
        
        if feature_flag.rollout_percentage <= 0:
            await self._log_usage(feature_flag.id, user, False, context, "Zero rollout")
            return False
        
        # Deterministic percentage rollout based on user ID and flag key
        user_hash = self._get_user_hash(user.id, flag_key)
        enabled = user_hash < feature_flag.rollout_percentage
        
        await self._log_usage(
            feature_flag.id, 
            user, 
            enabled, 
            context, 
            f"Percentage rollout: {feature_flag.rollout_percentage}%"
        )
        return enabled
    
    async def get_enabled_features(
        self, 
        user: User, 
        module_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all enabled features for a user, optionally filtered by module
        """
        query = select(FeatureFlag).where(FeatureFlag.is_enabled == True)
        
        if module_id:
            query = query.where(FeatureFlag.module_id == module_id)
        
        result = await self.db.execute(query)
        feature_flags = result.scalars().all()
        
        enabled_features = {}
        for flag in feature_flags:
            is_enabled = await self.is_feature_enabled(flag.flag_key, user)
            if is_enabled:
                enabled_features[flag.flag_key] = {
                    "name": flag.name,
                    "config": flag.config,
                    "module_id": flag.module_id
                }
        
        return enabled_features
    
    async def create_feature_flag(
        self, 
        flag_data: Dict[str, Any], 
        created_by: str
    ) -> FeatureFlag:
        """Create a new feature flag"""
        feature_flag = FeatureFlag(
            **flag_data,
            created_by=created_by
        )
        
        self.db.add(feature_flag)
        await self.db.commit()
        await self.db.refresh(feature_flag)
        
        # Log the creation
        await self.audit_service.log_action(
            user_id=created_by,
            action="CREATE",
            resource_type="feature_flag",
            resource_id=feature_flag.id,
            description=f"Created feature flag: {feature_flag.flag_key}",
            changes={"created": flag_data}
        )
        
        return feature_flag
    
    async def update_feature_flag(
        self, 
        flag_id: str, 
        updates: Dict[str, Any], 
        updated_by: str
    ) -> FeatureFlag:
        """Update an existing feature flag"""
        result = await self.db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
        feature_flag = result.scalar_one_or_none()
        
        if not feature_flag:
            raise ValueError(f"Feature flag {flag_id} not found")
        
        # Store old values for audit
        old_values = {
            key: getattr(feature_flag, key) 
            for key in updates.keys()
            if hasattr(feature_flag, key)
        }
        
        # Update the flag
        for key, value in updates.items():
            if hasattr(feature_flag, key):
                setattr(feature_flag, key, value)
        
        feature_flag.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(feature_flag)
        
        # Log the update
        await self.audit_service.log_action(
            user_id=updated_by,
            action="UPDATE",
            resource_type="feature_flag",
            resource_id=feature_flag.id,
            description=f"Updated feature flag: {feature_flag.flag_key}",
            changes={"old": old_values, "new": updates}
        )
        
        return feature_flag
    
    async def create_override(
        self, 
        flag_id: str, 
        override_data: Dict[str, Any], 
        created_by: str
    ) -> FeatureFlagOverride:
        """Create a feature flag override"""
        override = FeatureFlagOverride(
            feature_flag_id=flag_id,
            created_by=created_by,
            **override_data
        )
        
        self.db.add(override)
        await self.db.commit()
        await self.db.refresh(override)
        
        # Log the override creation
        target = f"org:{override.organisation_id}" if override.organisation_id else f"user:{override.user_id}"
        await self.audit_service.log_action(
            user_id=created_by,
            action="CREATE",
            resource_type="feature_flag_override",
            resource_id=override.id,
            description=f"Created feature flag override for {target}",
            changes={"created": override_data}
        )
        
        return override
    
    async def get_usage_analytics(
        self, 
        flag_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage analytics for a feature flag"""
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage data
        result = await self.db.execute(
            select(FeatureFlagUsage)
            .where(
                and_(
                    FeatureFlagUsage.feature_flag_id == flag_id,
                    FeatureFlagUsage.accessed_at >= start_date,
                    FeatureFlagUsage.accessed_at <= end_date
                )
            )
        )
        usage_records = result.scalars().all()
        
        # Calculate metrics
        total_checks = len(usage_records)
        enabled_checks = sum(1 for record in usage_records if record.was_enabled)
        unique_users = len(set(record.user_id for record in usage_records))
        unique_orgs = len(set(record.organisation_id for record in usage_records))
        
        return {
            "period": {"start": start_date, "end": end_date, "days": days},
            "total_checks": total_checks,
            "enabled_checks": enabled_checks,
            "disabled_checks": total_checks - enabled_checks,
            "enable_rate": enabled_checks / total_checks if total_checks > 0 else 0,
            "unique_users": unique_users,
            "unique_organisations": unique_orgs,
            "daily_usage": self._group_usage_by_day(usage_records)
        }
    
    # Private helper methods
    
    async def _get_user_override(self, flag_id: str, user_id: str) -> Optional[FeatureFlagOverride]:
        """Get user-specific override"""
        result = await self.db.execute(
            select(FeatureFlagOverride).where(
                and_(
                    FeatureFlagOverride.feature_flag_id == flag_id,
                    FeatureFlagOverride.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_organisation_override(self, flag_id: str, org_id: str) -> Optional[FeatureFlagOverride]:
        """Get organisation-specific override"""
        result = await self.db.execute(
            select(FeatureFlagOverride).where(
                and_(
                    FeatureFlagOverride.feature_flag_id == flag_id,
                    FeatureFlagOverride.organisation_id == org_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _is_sector_allowed(self, feature_flag: FeatureFlag, user: User) -> bool:
        """Check if the user's organisation sector is allowed for this flag"""
        # Get user's organisation with SIC code
        result = await self.db.execute(
            select(Organisation)
            .where(Organisation.id == user.organisation_id)
            .options(selectinload(Organisation.sic_code_rel))
        )
        organisation = result.scalar_one_or_none()
        
        if not organisation or not organisation.sic_code:
            # If no SIC code, allow unless explicitly blocked
            return True
        
        sic_code = organisation.sic_code
        
        # Check if sector is explicitly blocked
        if sic_code in feature_flag.blocked_sectors:
            return False
        
        # Check if sector is explicitly allowed (empty list means all allowed)
        if feature_flag.allowed_sectors and sic_code not in feature_flag.allowed_sectors:
            return False
        
        return True
    
    def _get_user_hash(self, user_id: str, flag_key: str) -> int:
        """Generate deterministic hash for percentage rollout"""
        hash_input = f"{user_id}:{flag_key}"
        hash_object = hashlib.md5(hash_input.encode())
        hash_hex = hash_object.hexdigest()
        # Convert first 8 characters to int and get percentage (0-99)
        return int(hash_hex[:8], 16) % 100
    
    async def _log_usage(
        self, 
        flag_id: str, 
        user: User, 
        was_enabled: bool, 
        context: Dict[str, Any],
        reason: str = ""
    ):
        """Log feature flag usage for analytics"""
        usage = FeatureFlagUsage(
            feature_flag_id=flag_id,
            organisation_id=user.organisation_id,
            user_id=user.id,
            was_enabled=was_enabled,
            evaluation_context={**context, "reason": reason}
        )
        
        self.db.add(usage)
        # Don't commit here - let the calling method handle commits
    
    def _group_usage_by_day(self, usage_records: List[FeatureFlagUsage]) -> Dict[str, Dict[str, int]]:
        """Group usage records by day for analytics"""
        daily_usage = {}
        
        for record in usage_records:
            day_key = record.accessed_at.strftime("%Y-%m-%d")
            if day_key not in daily_usage:
                daily_usage[day_key] = {"total": 0, "enabled": 0, "disabled": 0}
            
            daily_usage[day_key]["total"] += 1
            if record.was_enabled:
                daily_usage[day_key]["enabled"] += 1
            else:
                daily_usage[day_key]["disabled"] += 1
        
        return daily_usage