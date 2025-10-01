"""Tests for organisation caching layer (CRITICAL FIX #5)"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.cache.organisation_cache import OrganisationCache
from app.models.organisation import Organisation
import uuid


@pytest.fixture
def clear_cache():
    """Clear cache before and after each test"""
    OrganisationCache.clear_all()
    yield
    OrganisationCache.clear_all()


@pytest.mark.asyncio
async def test_cache_hit(isolated_database_session: AsyncSession, clear_cache):
    """Test cache hit scenario"""
    # Setup
    auth0_org_id = "test-org-id-001"
    org_id = str(uuid.uuid4())
    org = Organisation(
        id=org_id,
        name="Test Org Cache Hit",
        auth0_organization_id=auth0_org_id
    )
    isolated_database_session.add(org)
    await isolated_database_session.commit()

    # First call - cache miss (queries database)
    result1 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result1 is not None
    assert result1.name == "Test Org Cache Hit"
    assert str(result1.id) == org_id

    # Second call - cache hit (no DB query)
    result2 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result2 is not None
    assert result2.name == "Test Org Cache Hit"
    assert str(result2.id) == org_id


@pytest.mark.asyncio
async def test_cache_miss(isolated_database_session: AsyncSession, clear_cache):
    """Test cache miss returns None"""
    auth0_org_id = "non-existent-org-id"

    result = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result is None


@pytest.mark.asyncio
async def test_cache_invalidation(isolated_database_session: AsyncSession, clear_cache):
    """Test cache invalidation"""
    # Setup
    auth0_org_id = "test-org-id-002"
    org = Organisation(
        id=str(uuid.uuid4()),
        name="Test Org Invalidation",
        auth0_organization_id=auth0_org_id
    )
    isolated_database_session.add(org)
    await isolated_database_session.commit()

    # Cache the org
    result1 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result1 is not None

    # Invalidate
    OrganisationCache.invalidate(auth0_org_id)

    # Next call should query DB again (but still work)
    result2 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result2 is not None
    assert result2.name == "Test Org Invalidation"


@pytest.mark.asyncio
async def test_cache_ttl_expiration(isolated_database_session: AsyncSession, clear_cache):
    """Test cache TTL expiration"""
    # Setup with very short TTL (1 second)
    OrganisationCache.set_ttl(1)

    auth0_org_id = "test-org-id-003"
    org = Organisation(
        id=str(uuid.uuid4()),
        name="Test Org TTL",
        auth0_organization_id=auth0_org_id
    )
    isolated_database_session.add(org)
    await isolated_database_session.commit()

    # First call - cache miss
    result1 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result1 is not None

    # Wait for TTL to expire
    await asyncio.sleep(1.1)

    # Second call - cache expired, queries DB again
    result2 = await OrganisationCache.get_by_auth0_org_id(auth0_org_id, isolated_database_session)
    assert result2 is not None
    assert result2.name == "Test Org TTL"

    # Reset TTL to default
    OrganisationCache.set_ttl(300)


@pytest.mark.asyncio
async def test_new_tenant_creation(isolated_database_session: AsyncSession, clear_cache):
    """Test creating new tenant with Auth0 org ID"""
    new_org = Organisation(
        name="New Customer Org",
        auth0_organization_id="new-customer-org-id"
    )
    isolated_database_session.add(new_org)
    await isolated_database_session.commit()

    # Should be retrievable
    result = await OrganisationCache.get_by_auth0_org_id(
        "new-customer-org-id",
        isolated_database_session
    )
    assert result is not None
    assert result.name == "New Customer Org"


@pytest.mark.asyncio
async def test_cache_stats(isolated_database_session: AsyncSession, clear_cache):
    """Test cache statistics"""
    # Initially empty
    stats = OrganisationCache.get_cache_stats()
    assert stats["cache_size"] == 0
    assert stats["ttl_seconds"] == 300

    # Add some entries
    for i in range(3):
        org = Organisation(
            name=f"Test Org {i}",
            auth0_organization_id=f"test-org-{i}"
        )
        isolated_database_session.add(org)
    await isolated_database_session.commit()

    # Cache 3 organisations
    for i in range(3):
        await OrganisationCache.get_by_auth0_org_id(f"test-org-{i}", isolated_database_session)

    # Check stats
    stats = OrganisationCache.get_cache_stats()
    assert stats["cache_size"] == 3


@pytest.mark.asyncio
async def test_multiple_auth0_org_ids_to_same_organisation(isolated_database_session: AsyncSession, clear_cache):
    """
    Test that different Auth0 org IDs can map to same organisation.
    This is the Zebra Associates use case.
    """
    # Create one organisation
    zebra_org_id = str(uuid.uuid4())
    zebra_org = Organisation(
        id=zebra_org_id,
        name="Zebra Associates",
        auth0_organization_id="zebra-associates-org-id"
    )
    isolated_database_session.add(zebra_org)
    await isolated_database_session.commit()

    # Lookup by Auth0 org ID
    result = await OrganisationCache.get_by_auth0_org_id(
        "zebra-associates-org-id",
        isolated_database_session
    )
    assert result is not None
    assert result.name == "Zebra Associates"
    assert str(result.id) == zebra_org_id


@pytest.mark.asyncio
async def test_cache_clear_all(isolated_database_session: AsyncSession):
    """Test clearing all cache entries"""
    # Add multiple organisations
    for i in range(5):
        org = Organisation(
            name=f"Test Org Clear {i}",
            auth0_organization_id=f"test-clear-{i}"
        )
        isolated_database_session.add(org)
    await isolated_database_session.commit()

    # Cache them
    for i in range(5):
        await OrganisationCache.get_by_auth0_org_id(f"test-clear-{i}", isolated_database_session)

    # Verify cache has entries
    stats = OrganisationCache.get_cache_stats()
    assert stats["cache_size"] == 5

    # Clear all
    OrganisationCache.clear_all()

    # Verify cache is empty
    stats = OrganisationCache.get_cache_stats()
    assert stats["cache_size"] == 0
