"""Simple tests for tenant mapping helpers (CRITICAL FIX #5)"""
import pytest
from app.auth.dependencies import is_valid_uuid
import uuid


def test_is_valid_uuid_with_valid_uuids():
    """Test UUID validation helper with valid UUIDs"""
    # Valid UUIDs
    assert is_valid_uuid("835d4f24-cff2-43e8-a470-93216a3d99a3") is True
    assert is_valid_uuid(str(uuid.uuid4())) is True
    assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000") is True


def test_is_valid_uuid_with_invalid_values():
    """Test UUID validation helper with invalid values"""
    # Invalid UUIDs
    assert is_valid_uuid("zebra-associates-org-id") is False
    assert is_valid_uuid("not-a-uuid") is False
    assert is_valid_uuid("") is False
    assert is_valid_uuid("123") is False
    assert is_valid_uuid("company-name") is False


def test_is_valid_uuid_with_none_and_edge_cases():
    """Test UUID validation helper with None and edge cases"""
    # Edge cases
    assert is_valid_uuid(None) is False

    # Valid UUID formats
    assert is_valid_uuid("00000000-0000-0000-0000-000000000000") is True


def test_organisation_cache_stats():
    """Test cache statistics tracking"""
    from app.cache.organisation_cache import OrganisationCache

    # Clear cache first
    OrganisationCache.clear_all()

    # Check initial stats
    stats = OrganisationCache.get_cache_stats()
    assert "cache_size" in stats
    assert "ttl_seconds" in stats
    assert stats["cache_size"] == 0


def test_organisation_cache_ttl_configuration():
    """Test cache TTL configuration"""
    from app.cache.organisation_cache import OrganisationCache

    # Set TTL
    OrganisationCache.set_ttl(600)
    stats = OrganisationCache.get_cache_stats()
    assert stats["ttl_seconds"] == 600

    # Reset to default
    OrganisationCache.set_ttl(300)
    stats = OrganisationCache.get_cache_stats()
    assert stats["ttl_seconds"] == 300


def test_organisation_cache_clear_all():
    """Test clearing all cache entries"""
    from app.cache.organisation_cache import OrganisationCache

    # Clear cache
    OrganisationCache.clear_all()

    # Verify cache is empty
    stats = OrganisationCache.get_cache_stats()
    assert stats["cache_size"] == 0


def test_organisation_cache_invalidate():
    """Test cache invalidation for specific entry"""
    from app.cache.organisation_cache import OrganisationCache

    # Invalidate a specific entry (should not error even if not exists)
    OrganisationCache.invalidate("test-org-id")

    # Should not raise any exceptions
    stats = OrganisationCache.get_cache_stats()
    assert "cache_size" in stats
