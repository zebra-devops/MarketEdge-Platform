"""
Simple test to validate Auth0 sub cannot be used as UUID

This documents the bug that was fixed: Auth0's 'sub' claim cannot be used
directly as a UUID in database queries.
"""

import pytest
import uuid


def test_auth0_sub_is_not_valid_uuid():
    """
    Confirms that Auth0 'sub' claims cannot be converted to UUID.

    This is the root cause of the 500 error bug.
    Auth0 sub values like 'google-oauth2|104641801735395463267' are NOT UUIDs.
    """
    # Real Auth0 sub from the error logs
    auth0_sub = "google-oauth2|104641801735395463267"

    # Attempting to convert Auth0 sub to UUID raises ValueError
    with pytest.raises(ValueError, match="badly formed hexadecimal UUID string"):
        uuid_attempt = uuid.UUID(auth0_sub)

    print(f"✅ CONFIRMED: Auth0 sub '{auth0_sub}' cannot be used as UUID")


def test_various_auth0_sub_formats_not_valid_uuid():
    """
    Tests various Auth0 sub formats to confirm none are valid UUIDs.
    """
    auth0_subs = [
        "google-oauth2|104641801735395463267",  # Google OAuth
        "auth0|507f1f77bcf86cd799439011",  # Auth0 database
        "github|12345678",  # GitHub
        "windowslive|abcd1234",  # Windows Live
        "twitter|username",  # Twitter
        "facebook|10223456789",  # Facebook
    ]

    for sub in auth0_subs:
        with pytest.raises(ValueError):
            uuid.UUID(sub)

    print(f"✅ Confirmed {len(auth0_subs)} Auth0 sub formats are NOT valid UUIDs")


def test_fix_uses_email_for_lookup():
    """
    Documents the fix: User lookup should use email, not Auth0 sub.

    This is a documentation test showing the before/after of the fix.
    """
    # Example Auth0 token payload
    auth0_payload = {
        "sub": "google-oauth2|104641801735395463267",  # NOT a UUID!
        "email": "matt.lindop@zebra.associates",  # USE THIS for lookup
        "user_role": "super_admin",
        "organisation_id": "835d4f24-cff2-43e8-a470-93216a3d99a3"
    }

    # BEFORE (WRONG - causes 500 error):
    # user_id = payload.get("sub")  # "google-oauth2|104641801735395463267"
    # query: WHERE users.id = user_id  # FAILS! user_id is not a UUID

    # AFTER (CORRECT - uses email):
    user_email = auth0_payload.get("email")
    # query: WHERE users.email = user_email  # SUCCESS!

    assert user_email == "matt.lindop@zebra.associates"
    print(f"✅ User lookup should use email: {user_email}")
    print(f"   NOT Auth0 sub: {auth0_payload['sub']}")
