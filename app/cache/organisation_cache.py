"""Organisation caching layer for Auth0 tenant mapping"""
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.organisation import Organisation

logger = logging.getLogger(__name__)


class OrganisationCache:
    """
    In-memory cache for Organisation lookups by Auth0 org ID.

    Uses LRU cache with TTL for performance optimization.
    Implements cache-aside pattern with database fallback.
    """

    # Class-level cache storage
    _cache: Dict[str, tuple[Organisation, datetime]] = {}
    _ttl_seconds: int = 300  # 5 minutes default

    @classmethod
    async def get_by_auth0_org_id(
        cls,
        auth0_org_id: str,
        db: AsyncSession
    ) -> Optional[Organisation]:
        """
        Get organisation by Auth0 org ID with caching.

        Args:
            auth0_org_id: Auth0 organization identifier
            db: Database session

        Returns:
            Organisation if found, None otherwise
        """
        # Check cache
        if auth0_org_id in cls._cache:
            org, cached_at = cls._cache[auth0_org_id]

            # Check TTL
            if datetime.utcnow() - cached_at < timedelta(seconds=cls._ttl_seconds):
                logger.debug(
                    "Cache hit for Auth0 org ID",
                    extra={"auth0_org_id": auth0_org_id, "org_id": str(org.id)}
                )
                return org
            else:
                # Expired - remove from cache
                del cls._cache[auth0_org_id]
                logger.debug("Cache expired", extra={"auth0_org_id": auth0_org_id})

        # Cache miss - query database
        logger.debug("Cache miss", extra={"auth0_org_id": auth0_org_id})

        result = await db.execute(
            select(Organisation).where(
                Organisation.auth0_organization_id == auth0_org_id
            )
        )
        org = result.scalar_one_or_none()

        if org:
            # Store in cache
            cls._cache[auth0_org_id] = (org, datetime.utcnow())
            logger.info(
                "Organisation cached",
                extra={
                    "auth0_org_id": auth0_org_id,
                    "org_id": str(org.id),
                    "org_name": org.name
                }
            )
        else:
            logger.warning(
                "Organisation not found for Auth0 org ID",
                extra={"auth0_org_id": auth0_org_id}
            )

        return org

    @classmethod
    def invalidate(cls, auth0_org_id: str):
        """Invalidate cache for specific Auth0 org ID"""
        if auth0_org_id in cls._cache:
            del cls._cache[auth0_org_id]
            logger.info("Cache invalidated", extra={"auth0_org_id": auth0_org_id})

    @classmethod
    def clear_all(cls):
        """Clear entire cache (for testing or admin operations)"""
        cls._cache.clear()
        logger.info("All organisation cache cleared")

    @classmethod
    def set_ttl(cls, seconds: int):
        """Set cache TTL (for configuration)"""
        cls._ttl_seconds = seconds
        logger.info("Cache TTL updated", extra={"ttl_seconds": seconds})

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Get cache statistics for monitoring"""
        return {
            "cache_size": len(cls._cache),
            "ttl_seconds": cls._ttl_seconds
        }
