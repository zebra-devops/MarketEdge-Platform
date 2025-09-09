"""
Rate limit administration service for managing tenant rate limits.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog
from ..models.organisation import Organisation

logger = structlog.get_logger()


class RateLimitAdminService:
    """Service for managing rate limits across organizations."""
    
    @staticmethod
    async def get_organization_rate_limits(session: AsyncSession, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rate limit configurations for organizations."""
        try:
            query = select(Organisation).where(Organisation.is_active == True)
            if org_id:
                query = query.where(Organisation.id == org_id)
            
            result = await session.execute(query)
            organizations = result.scalars().all()
            
            rate_limits = []
            for org in organizations:
                rate_limits.append({
                    'organization_id': str(org.id),
                    'organization_name': org.name,
                    'subscription_plan': org.subscription_plan.value,
                    'rate_limit_per_hour': org.rate_limit_per_hour,
                    'burst_limit': org.burst_limit,
                    'rate_limit_enabled': org.rate_limit_enabled,
                    'industry': org.industry,
                    'sic_code': org.sic_code
                })
            
            return rate_limits
            
        except Exception as e:
            logger.error("Failed to fetch organization rate limits", error=str(e))
            raise
    
    @staticmethod
    async def update_organization_rate_limit(
        session: AsyncSession, 
        org_id: str, 
        rate_limit_per_hour: Optional[int] = None,
        burst_limit: Optional[int] = None,
        rate_limit_enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update rate limit configuration for an organization."""
        try:
            org = await session.get(Organisation, org_id)
            if not org:
                raise ValueError(f"Organization with ID {org_id} not found")
            
            # Update fields if provided
            if rate_limit_per_hour is not None:
                org.rate_limit_per_hour = rate_limit_per_hour
            if burst_limit is not None:
                org.burst_limit = burst_limit
            if rate_limit_enabled is not None:
                org.rate_limit_enabled = rate_limit_enabled
            
            await session.commit()
            await session.refresh(org)
            
            logger.info(
                "Updated organization rate limits",
                org_id=org_id,
                rate_limit_per_hour=org.rate_limit_per_hour,
                burst_limit=org.burst_limit,
                enabled=org.rate_limit_enabled
            )
            
            return {
                'organization_id': str(org.id),
                'organization_name': org.name,
                'subscription_plan': org.subscription_plan.value,
                'rate_limit_per_hour': org.rate_limit_per_hour,
                'burst_limit': org.burst_limit,
                'rate_limit_enabled': org.rate_limit_enabled
            }
            
        except Exception as e:
            await session.rollback()
            logger.error("Failed to update organization rate limits", org_id=org_id, error=str(e))
            raise
    
    @staticmethod
    async def bulk_update_rate_limits_by_plan(
        session: AsyncSession,
        subscription_plan: str,
        rate_limit_per_hour: int,
        burst_limit: int
    ) -> List[str]:
        """Bulk update rate limits for all organizations with a specific subscription plan."""
        try:
            query = update(Organisation).where(
                Organisation.subscription_plan == subscription_plan,
                Organisation.is_active == True
            ).values(
                rate_limit_per_hour=rate_limit_per_hour,
                burst_limit=burst_limit
            ).returning(Organisation.id)
            
            result = await session.execute(query)
            updated_org_ids = [str(org_id) for org_id in result.scalars().all()]
            
            await session.commit()
            
            logger.info(
                "Bulk updated rate limits by subscription plan",
                subscription_plan=subscription_plan,
                rate_limit_per_hour=rate_limit_per_hour,
                burst_limit=burst_limit,
                updated_count=len(updated_org_ids)
            )
            
            return updated_org_ids
            
        except Exception as e:
            await session.rollback()
            logger.error(
                "Failed to bulk update rate limits",
                subscription_plan=subscription_plan,
                error=str(e)
            )
            raise
    
    @staticmethod
    async def get_rate_limit_violations(limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent rate limit violations from Redis."""
        try:
            import redis.asyncio as redis
            from ..core.config import settings
            import json
            
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            
            violations = await redis_client.lrange("rate_limit_violations", 0, limit - 1)
            
            parsed_violations = []
            for violation in violations:
                try:
                    parsed_violations.append(json.loads(violation))
                except json.JSONDecodeError:
                    continue
            
            await redis_client.close()
            return parsed_violations
            
        except Exception as e:
            logger.error("Failed to fetch rate limit violations", error=str(e))
            return []