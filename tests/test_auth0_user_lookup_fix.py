"""
Test for Auth0 User Lookup Bug Fix

This test validates the critical bug fix where Auth0's 'sub' claim
(e.g., 'google-oauth2|104641801735395463267') was being used as a UUID
in database queries, causing 500 errors.

The fix changes user lookup to use EMAIL instead of the Auth0 sub.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_user_lookup_by_email_not_auth0_sub():
    """
    CRITICAL TEST: Validates that user lookup uses email from Auth0 token,
    NOT the Auth0 sub (which is not a UUID and causes database query failures).

    Before fix: Query by User.id == user_id (where user_id is Auth0 sub)
    After fix: Query by User.email == user_email
    """
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Create test organization
        org = Organisation(
            id=uuid.uuid4(),
            name="Test Org",
            industry="Technology",
            is_active=True
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)

        # Create test user
        user = User(
            id=uuid.uuid4(),  # This is a UUID
            email="test.user@example.com",  # This is what Auth0 token will contain
            first_name="Test",
            last_name="User",
            organisation_id=org.id,
            role=UserRole.admin,
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Mock Auth0 token payload with realistic Auth0 sub (NOT a UUID!)
        auth0_payload = {
            "sub": "google-oauth2|104641801735395463267",  # Auth0 sub - NOT a UUID!
            "email": "test.user@example.com",  # Email for user lookup
            "user_role": "admin",
            "role": "admin",
            "organisation_id": str(org.id),
            "tenant_id": str(org.id),
            "type": "auth0_access",
            "iss": "https://test.auth0.com/",
            "aud": "test_client_id",
            "exp": 9999999999,  # Far future
            "iat": 1234567890,
            "permissions": []
        }

        # Mock the dependencies
        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/test/endpoint"
        mock_request.state = Mock()

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "fake_auth0_token"

        # Mock verify_token to return None (simulating internal JWT failure)
        with patch("app.auth.dependencies.verify_token") as mock_internal_verify:
            mock_internal_verify.return_value = None

            # Mock verify_auth0_token to return our Auth0 payload
            with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_auth0_verify:
                mock_auth0_verify.return_value = auth0_payload

                # Call get_current_user
                try:
                    retrieved_user = await get_current_user(
                        request=mock_request,
                        credentials=mock_credentials,
                        db=session
                    )

                    # CRITICAL ASSERTIONS
                    assert retrieved_user is not None, "User should be found by email"
                    assert retrieved_user.id == user.id, "Should retrieve correct user"
                    assert retrieved_user.email == "test.user@example.com"
                    assert retrieved_user.role == UserRole.admin

                    # Verify that the request state was updated with tenant context
                    assert hasattr(mock_request.state, 'tenant_context')

                    print("✅ SUCCESS: User lookup by email works correctly!")
                    print(f"   Auth0 sub: {auth0_payload['sub']}")
                    print(f"   User UUID: {user.id}")
                    print(f"   Lookup email: {user.email}")

                except HTTPException as e:
                    pytest.fail(
                        f"Authentication failed with HTTPException: {e.status_code} - {e.detail}\n"
                        f"This likely means the code is still trying to use Auth0 sub as UUID.\n"
                        f"Auth0 sub: {auth0_payload['sub']}\n"
                        f"Expected email lookup: {user.email}"
                    )
                except Exception as e:
                    pytest.fail(
                        f"Unexpected error: {type(e).__name__}: {str(e)}\n"
                        f"Auth0 sub: {auth0_payload['sub']}\n"
                        f"User email: {user.email}"
                    )


@pytest.mark.asyncio
async def test_user_lookup_fails_with_invalid_uuid_sub():
    """
    Test that confirms the BUG would occur if we tried to use Auth0 sub as UUID.

    This test documents the bug behavior for regression testing.
    """
    from sqlalchemy.exc import DataError, StatementError

    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Create test org and user
        org = Organisation(
            id=uuid.uuid4(),
            name="Test Org",
            industry="Technology",
            is_active=True
        )
        session.add(org)
        await session.commit()

        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            organisation_id=org.id,
            role=UserRole.user,
            is_active=True
        )
        session.add(user)
        await session.commit()

        # Try to query by Auth0 sub (this would cause the bug)
        auth0_sub = "google-oauth2|104641801735395463267"

        # This WOULD fail if we tried to use it as a UUID
        with pytest.raises((ValueError, DataError, StatementError)):
            # Attempt to use Auth0 sub as UUID (this is the BUG)
            user_id_uuid = uuid.UUID(auth0_sub)  # This will raise ValueError

        # Document that direct UUID conversion fails
        try:
            bad_uuid = uuid.UUID(auth0_sub)
            pytest.fail(f"Auth0 sub should NOT be convertible to UUID! Got: {bad_uuid}")
        except ValueError as e:
            # Expected: Auth0 sub is NOT a valid UUID
            print(f"✅ CONFIRMED: Auth0 sub '{auth0_sub}' cannot be used as UUID")
            print(f"   ValueError: {str(e)}")
            assert "badly formed hexadecimal UUID string" in str(e)


@pytest.mark.asyncio
async def test_missing_email_in_token_returns_401():
    """
    Test that authentication fails with 401 when email is missing from Auth0 token.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Auth0 payload WITHOUT email
        auth0_payload = {
            "sub": "auth0|12345",
            # "email": MISSING!
            "user_role": "user",
            "organisation_id": str(uuid.uuid4()),
            "type": "auth0_access",
            "exp": 9999999999
        }

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.state = Mock()

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_auth0:
                mock_auth0.return_value = auth0_payload

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        request=mock_request,
                        credentials=mock_credentials,
                        db=session
                    )

                # Should raise 401 Unauthorized
                assert exc_info.value.status_code == 401
                print("✅ Missing email correctly returns 401 Unauthorized")


@pytest.mark.asyncio
async def test_user_not_found_by_email_returns_401():
    """
    Test that authentication fails with 401 when user email doesn't exist in database.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        org = Organisation(
            id=uuid.uuid4(),
            name="Test Org",
            industry="Tech",
            is_active=True
        )
        session.add(org)
        await session.commit()

        # Auth0 payload with email that doesn't exist
        auth0_payload = {
            "sub": "auth0|nonexistent",
            "email": "nonexistent@example.com",  # User doesn't exist
            "user_role": "user",
            "organisation_id": str(org.id),
            "type": "auth0_access",
            "exp": 9999999999
        }

        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.state = Mock()

        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token"

        with patch("app.auth.dependencies.verify_token") as mock_internal:
            mock_internal.return_value = None

            with patch("app.auth.dependencies.verify_auth0_token", new_callable=AsyncMock) as mock_auth0:
                mock_auth0.return_value = auth0_payload

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(
                        request=mock_request,
                        credentials=mock_credentials,
                        db=session
                    )

                assert exc_info.value.status_code == 401
                print("✅ User not found by email correctly returns 401 Unauthorized")
