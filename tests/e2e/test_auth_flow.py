"""
End-to-End Authentication Flow Tests

Tests the complete authentication flow from login to protected endpoint access,
catching bugs like the Auth0 sub vs UUID mismatch.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.organisation import Organisation


@pytest.mark.asyncio
async def test_auth0_token_with_protected_endpoint(async_client, async_session: AsyncSession):
    """
    Test complete Auth0 authentication flow with protected endpoint access.

    This test catches the critical bug where Auth0's 'sub' claim (e.g., 'google-oauth2|123')
    was being used as a UUID in database queries, causing 500 errors.

    CRITICAL: This validates that:
    1. Auth0 tokens with string 'sub' claims work
    2. User lookup happens by EMAIL, not by Auth0 sub
    3. Protected endpoints return 200 OK, not 500 errors
    """
    # Create test organization
    org = Organisation(
        name="Test Auth0 Org",
        industry="Technology",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)

    # Create test user with email that matches Auth0 token
    user = User(
        email="test@auth0.com",
        first_name="Test",
        last_name="User",
        organisation_id=org.id,
        role=UserRole.admin,
        is_active=True
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Mock Auth0 token payload with realistic Auth0 sub format
    auth0_token_payload = {
        "sub": "google-oauth2|104641801735395463267",  # Auth0 sub format (NOT a UUID!)
        "email": "test@auth0.com",
        "email_verified": True,
        "user_role": "admin",
        "role": "admin",
        "organisation_id": str(org.id),
        "tenant_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://test.auth0.com/",
        "aud": "test_client_id",
        "iat": 1234567890,
        "exp": 9999999999,  # Far future expiry
        "permissions": ["read:users", "write:users"]
    }

    # Mock verify_auth0_token to return our payload
    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_token_payload

        # Mock verify_token (internal JWT) to return None so it falls back to Auth0
        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            # Test 1: Access protected endpoint with Auth0 token
            response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer fake_auth0_token"}
            )

            # CRITICAL ASSERTION: Should return 200 OK, NOT 500 Internal Server Error
            assert response.status_code == 200, \
                f"Expected 200 OK but got {response.status_code}. " \
                f"This likely means Auth0 sub is being used as UUID in database query. " \
                f"Response: {response.text}"

            # Verify response contains organization data
            data = response.json()
            assert data["id"] == str(org.id)
            assert data["name"] == "Test Auth0 Org"

            # Verify mock was called with the token
            mock_verify.assert_called_once_with("fake_auth0_token")


@pytest.mark.asyncio
async def test_auth0_user_lookup_by_email_not_uuid(async_client, async_session: AsyncSession):
    """
    Test that user lookup uses email from Auth0 token, NOT the Auth0 sub as a UUID.

    This is a focused unit test for the specific bug fix.
    """
    # Create test organization
    org = Organisation(
        name="Email Lookup Test Org",
        industry="Technology",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)

    # Create user
    user = User(
        email="lookup@test.com",
        first_name="Lookup",
        last_name="Test",
        organisation_id=org.id,
        role=UserRole.user,
        is_active=True
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Auth0 token with non-UUID sub
    auth0_payload = {
        "sub": "auth0|non-uuid-string-12345",  # NOT a UUID
        "email": "lookup@test.com",  # THIS is what should be used for lookup
        "user_role": "user",
        "role": "user",
        "organisation_id": str(org.id),
        "tenant_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://test.auth0.com/",
        "aud": "test_client_id",
        "iat": 1234567890,
        "exp": 9999999999,
        "permissions": []
    }

    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_payload

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            # Access any protected endpoint
            response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer test_token"}
            )

            # Should succeed because we look up by email, not by sub
            assert response.status_code == 200, \
                f"User lookup failed. Expected 200 but got {response.status_code}. " \
                f"Ensure user lookup uses email field, not Auth0 sub. " \
                f"Response: {response.text}"


@pytest.mark.asyncio
async def test_missing_email_in_auth0_token(async_client, async_session: AsyncSession):
    """
    Test that authentication fails gracefully when Auth0 token is missing email.
    """
    org = Organisation(
        name="Missing Email Test Org",
        industry="Technology",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()

    # Auth0 token WITHOUT email (edge case)
    auth0_payload = {
        "sub": "auth0|12345",
        # "email": missing!
        "user_role": "user",
        "organisation_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://test.auth0.com/",
        "aud": "test_client_id",
        "exp": 9999999999
    }

    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_payload

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer test_token"}
            )

            # Should return 401 Unauthorized when email is missing
            assert response.status_code == 401, \
                f"Expected 401 when email is missing from token, got {response.status_code}"


@pytest.mark.asyncio
async def test_user_not_found_by_email(async_client, async_session: AsyncSession):
    """
    Test that authentication fails when user email from Auth0 doesn't exist in database.
    """
    org = Organisation(
        name="User Not Found Org",
        industry="Technology",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)

    # Auth0 token for user that doesn't exist in database
    auth0_payload = {
        "sub": "auth0|new-user-99999",
        "email": "nonexistent@test.com",  # User with this email doesn't exist
        "user_role": "user",
        "organisation_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://test.auth0.com/",
        "aud": "test_client_id",
        "exp": 9999999999
    }

    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_payload

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer test_token"}
            )

            # Should return 401 when user doesn't exist
            assert response.status_code == 401, \
                f"Expected 401 when user not found by email, got {response.status_code}"


@pytest.mark.asyncio
async def test_inactive_user_with_auth0_token(async_client, async_session: AsyncSession):
    """
    Test that inactive users are rejected even with valid Auth0 token.
    """
    org = Organisation(
        name="Inactive User Org",
        industry="Technology",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)

    # Create INACTIVE user
    user = User(
        email="inactive@test.com",
        first_name="Inactive",
        last_name="User",
        organisation_id=org.id,
        role=UserRole.user,
        is_active=False  # User is inactive
    )
    async_session.add(user)
    await async_session.commit()

    auth0_payload = {
        "sub": "auth0|inactive-user",
        "email": "inactive@test.com",
        "user_role": "user",
        "organisation_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://test.auth0.com/",
        "aud": "test_client_id",
        "exp": 9999999999
    }

    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_payload

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer test_token"}
            )

            # Should return 403 Forbidden for inactive user
            assert response.status_code == 403, \
                f"Expected 403 for inactive user, got {response.status_code}"
            assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_complete_login_to_protected_endpoint_flow(async_client, async_session: AsyncSession):
    """
    Integration test: Complete flow from login to accessing protected data.

    This simulates a real user journey:
    1. User logs in via Auth0
    2. Receives Auth0 token
    3. Accesses protected endpoint with token
    4. Gets their organization data
    """
    # Setup
    org = Organisation(
        name="Integration Test Org",
        industry="Cinema",
        is_active=True
    )
    async_session.add(org)
    await async_session.commit()
    await async_session.refresh(org)

    user = User(
        email="matt.lindop@zebra.associates",  # The Zebra opportunity user
        first_name="Matt",
        last_name="Lindop",
        organisation_id=org.id,
        role=UserRole.super_admin,
        is_active=True
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # Simulate Auth0 token
    auth0_payload = {
        "sub": "google-oauth2|104641801735395463267",  # Realistic Auth0 sub
        "email": "matt.lindop@zebra.associates",
        "email_verified": True,
        "user_role": "super_admin",
        "role": "super_admin",
        "organisation_id": str(org.id),
        "tenant_id": str(org.id),
        "type": "auth0_access",
        "iss": "https://marketedge.auth0.com/",
        "aud": "marketedge_api",
        "iat": 1234567890,
        "exp": 9999999999,
        "permissions": ["read:all", "write:all", "admin:all"]
    }

    with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = auth0_payload

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            # STEP 1: Access current organization
            org_response = await async_client.get(
                "/api/v1/organisations/current",
                headers={"Authorization": "Bearer auth0_token"}
            )

            assert org_response.status_code == 200
            org_data = org_response.json()
            assert org_data["name"] == "Integration Test Org"
            assert org_data["industry"] == "Cinema"

            # STEP 2: Access admin endpoint (requires super_admin role)
            admin_response = await async_client.get(
                "/api/v1/admin/dashboard/stats",
                headers={"Authorization": "Bearer auth0_token"}
            )

            # Should succeed because user has super_admin role
            assert admin_response.status_code == 200

            # STEP 3: Verify user context is set correctly
            # (This would be checked in the actual endpoint implementation)
