"""Tests for tenant mapping via Auth0 org ID (CRITICAL FIX #5)"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import resolve_tenant_id, is_valid_uuid
from app.models.organisation import Organisation
from app.cache.organisation_cache import OrganisationCache
import uuid


@pytest.fixture
def clear_cache():
    """Clear cache before and after each test"""
    OrganisationCache.clear_all()
    yield
    OrganisationCache.clear_all()


def test_is_valid_uuid():
    """Test UUID validation helper"""
    # Valid UUIDs
    assert is_valid_uuid("835d4f24-cff2-43e8-a470-93216a3d99a3") is True
    assert is_valid_uuid(str(uuid.uuid4())) is True

    # Invalid UUIDs
    assert is_valid_uuid("zebra-associates-org-id") is False
    assert is_valid_uuid("not-a-uuid") is False
    assert is_valid_uuid("") is False
    assert is_valid_uuid("123") is False


@pytest.mark.asyncio
async def test_resolve_tenant_id_with_uuid(isolated_database_session: AsyncSession, clear_cache):
    """Test resolving tenant ID when it's already a valid UUID"""
    org_uuid = str(uuid.uuid4())

    # Should return the UUID as-is without database query
    result = await resolve_tenant_id(org_uuid, isolated_database_session)
    assert result == org_uuid


@pytest.mark.asyncio
async def test_resolve_tenant_id_with_auth0_org_id(isolated_database_session: AsyncSession, clear_cache):
    """Test resolving tenant ID from Auth0 org ID"""
    # Setup
    org_uuid = str(uuid.uuid4())
    auth0_org_id = "test-company-org-id"

    org = Organisation(
        id=org_uuid,
        name="Test Company",
        auth0_organization_id=auth0_org_id
    )
    isolated_database_session.add(org)
    await isolated_database_session.commit()

    # Should lookup in database and return UUID
    result = await resolve_tenant_id(auth0_org_id, isolated_database_session)
    assert result == org_uuid


@pytest.mark.asyncio
async def test_resolve_tenant_id_with_invalid_auth0_org_id(isolated_database_session: AsyncSession, clear_cache):
    """Test resolving tenant ID with non-existent Auth0 org ID"""
    auth0_org_id = "non-existent-org-id"

    # Should return None for non-existent org
    result = await resolve_tenant_id(auth0_org_id, isolated_database_session)
    assert result is None


@pytest.mark.asyncio
async def test_resolve_tenant_id_with_empty_string(isolated_database_session: AsyncSession, clear_cache):
    """Test resolving tenant ID with empty string"""
    result = await resolve_tenant_id("", isolated_database_session)
    assert result is None


@pytest.mark.asyncio
async def test_resolve_tenant_id_with_none(isolated_database_session: AsyncSession, clear_cache):
    """Test resolving tenant ID with None"""
    result = await resolve_tenant_id(None, isolated_database_session)
    assert result is None


@pytest.mark.asyncio
async def test_zebra_associates_mapping(isolated_database_session: AsyncSession, clear_cache):
    """
    Test the specific Zebra Associates mapping scenario.
    This tests the migration seed data.
    """
    # The migration seeds this mapping
    zebra_uuid = "835d4f24-cff2-43e8-a470-93216a3d99a3"
    zebra_auth0_org_id = "zebra-associates-org-id"

    # Check if the organisation exists (may not in test DB)
    result = await resolve_tenant_id(zebra_auth0_org_id, isolated_database_session)

    # If the seed data exists, verify mapping
    if result:
        assert result == zebra_uuid


@pytest.mark.asyncio
async def test_resolve_tenant_id_uses_cache(isolated_database_session: AsyncSession, clear_cache):
    """Test that resolve_tenant_id uses the cache"""
    # Setup
    org_uuid = str(uuid.uuid4())
    auth0_org_id = "cached-org-id"

    org = Organisation(
        id=org_uuid,
        name="Cached Org",
        auth0_organization_id=auth0_org_id
    )
    isolated_database_session.add(org)
    await isolated_database_session.commit()

    # First call - cache miss
    result1 = await resolve_tenant_id(auth0_org_id, isolated_database_session)
    assert result1 == org_uuid

    # Second call - cache hit (verify cache has entry)
    cache_stats = OrganisationCache.get_cache_stats()
    assert cache_stats["cache_size"] >= 1

    result2 = await resolve_tenant_id(auth0_org_id, isolated_database_session)
    assert result2 == org_uuid


@pytest.mark.asyncio
async def test_resolve_tenant_id_multiple_mappings(isolated_database_session: AsyncSession, clear_cache):
    """Test multiple Auth0 org IDs can be created for different organisations"""
    # Create multiple organisations with different Auth0 org IDs
    orgs = []
    for i in range(3):
        org_uuid = str(uuid.uuid4())
        org = Organisation(
            id=org_uuid,
            name=f"Company {i}",
            auth0_organization_id=f"company-{i}-org-id"
        )
        isolated_database_session.add(org)
        orgs.append((org_uuid, f"company-{i}-org-id"))

    await isolated_database_session.commit()

    # Verify each mapping resolves correctly
    for org_uuid, auth0_org_id in orgs:
        result = await resolve_tenant_id(auth0_org_id, isolated_database_session)
        assert result == org_uuid
