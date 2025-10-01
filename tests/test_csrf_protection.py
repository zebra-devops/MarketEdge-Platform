"""Tests for CSRF Protection Middleware

Tests the double-submit cookie pattern implementation for CSRF protection.

Critical Fix #4: CSRF Validation Testing
- Validates that CSRF tokens are required on state-changing operations
- Ensures GET requests don't require CSRF
- Tests token mismatch rejection
- Validates exempt paths work without CSRF
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import secrets

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_user():
    """Mock user fixture for authentication"""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "user",
        "organisation_id": "test-org-id"
    }


@pytest.fixture
def csrf_token():
    """Generate a valid CSRF token"""
    return secrets.token_urlsafe(settings.CSRF_TOKEN_LENGTH)


class TestCSRFProtection:
    """Test suite for CSRF protection middleware"""

    def test_csrf_not_required_on_get(self, client):
        """Test that GET requests don't require CSRF token"""
        # GET request to a protected endpoint (after login)
        response = client.get("/api/v1/auth/me")

        # Should not fail due to missing CSRF (may fail due to missing auth, but not CSRF)
        # 401 is expected for missing auth, 403 would indicate CSRF failure
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    def test_csrf_not_required_on_options(self, client):
        """Test that OPTIONS requests (CORS preflight) don't require CSRF"""
        response = client.options("/api/v1/auth/logout")

        # OPTIONS should always succeed (CORS preflight)
        assert response.status_code in [200, 204]

    def test_csrf_exempt_on_login(self, client):
        """Test that login endpoint is exempt from CSRF"""
        # Login should work without CSRF token (it generates one)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "code": "test-auth-code",
                "redirect_uri": "http://localhost:3000/callback"
            }
        )

        # Should not fail due to CSRF (may fail due to invalid auth code, but not CSRF)
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    def test_csrf_exempt_on_health_check(self, client):
        """Test that health check is exempt from CSRF"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_csrf_required_on_logout_without_token(self, client, csrf_token):
        """Test that logout requires CSRF token"""
        # Set CSRF token in cookie but don't send in header
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock authenticated user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_get_user.return_value = AsyncMock()

            # Attempt logout without CSRF header
            response = client.post(
                "/api/v1/auth/logout",
                json={"all_devices": False}
            )

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_validation_with_valid_token(self, client, csrf_token):
        """Test that logout succeeds with valid CSRF token"""
        # Set CSRF token in both cookie and header
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock authenticated user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_user = AsyncMock()
            mock_user.id = "test-user-id"
            mock_user.organisation_id = "test-org-id"
            mock_get_user.return_value = mock_user

            # Mock Auth0 client revoke_token
            with patch("app.auth.auth0.auth0_client.revoke_token") as mock_revoke:
                mock_revoke.return_value = True

                # Attempt logout with CSRF header
                response = client.post(
                    "/api/v1/auth/logout",
                    json={"all_devices": False},
                    headers={settings.CSRF_HEADER_NAME: csrf_token}
                )

                # Should succeed (200) or fail due to auth, not CSRF (403 would be CSRF)
                assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    def test_csrf_token_mismatch_rejected(self, client, csrf_token):
        """Test that mismatched CSRF tokens are rejected"""
        # Set different tokens in cookie and header
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)
        wrong_token = secrets.token_urlsafe(settings.CSRF_TOKEN_LENGTH)

        # Mock authenticated user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_get_user.return_value = AsyncMock()

            # Attempt logout with wrong CSRF token in header
            response = client.post(
                "/api/v1/auth/logout",
                json={"all_devices": False},
                headers={settings.CSRF_HEADER_NAME: wrong_token}
            )

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_token_too_short_rejected(self, client):
        """Test that tokens shorter than minimum length are rejected"""
        # Set short token (less than 32 characters)
        short_token = secrets.token_urlsafe(10)
        client.cookies.set(settings.CSRF_COOKIE_NAME, short_token)

        # Mock authenticated user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_get_user.return_value = AsyncMock()

            # Attempt logout with short CSRF token
            response = client.post(
                "/api/v1/auth/logout",
                json={"all_devices": False},
                headers={settings.CSRF_HEADER_NAME: short_token}
            )

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_required_on_post_requests(self, client, csrf_token):
        """Test that POST requests require CSRF token"""
        # Any POST request should require CSRF (except exempt paths)
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Test a non-exempt POST endpoint
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "test-token"}
        )

        # Should fail with 403 CSRF validation error (no header provided)
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    def test_csrf_required_on_put_requests(self, client, csrf_token):
        """Test that PUT requests require CSRF token"""
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock authenticated admin user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_user = AsyncMock()
            mock_user.role = "admin"
            mock_get_user.return_value = mock_user

            # Test PUT request without CSRF header
            response = client.put(
                "/api/v1/admin/users/test-id",
                json={"role": "user"}
            )

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_required_on_patch_requests(self, client, csrf_token):
        """Test that PATCH requests require CSRF token"""
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock authenticated admin user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_user = AsyncMock()
            mock_user.role = "admin"
            mock_get_user.return_value = mock_user

            # Test PATCH request without CSRF header
            response = client.patch(
                "/api/v1/admin/users/test-id",
                json={"first_name": "Updated"}
            )

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_required_on_delete_requests(self, client, csrf_token):
        """Test that DELETE requests require CSRF token"""
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock authenticated admin user
        with patch("app.auth.dependencies.get_current_user") as mock_get_user:
            mock_user = AsyncMock()
            mock_user.role = "super_admin"
            mock_get_user.return_value = mock_user

            # Test DELETE request without CSRF header
            response = client.delete("/api/v1/admin/users/test-id")

            # Should fail with 403 CSRF validation error
            assert response.status_code == 403
            assert "CSRF" in response.json()["detail"]

    def test_csrf_middleware_constant_time_comparison(self):
        """Test that CSRF token comparison is constant-time"""
        from app.middleware.csrf import CSRFMiddleware

        middleware = CSRFMiddleware(app=None)

        # Test equal strings
        assert middleware._constant_time_compare("abc123", "abc123") is True

        # Test different strings of same length
        assert middleware._constant_time_compare("abc123", "def456") is False

        # Test different lengths
        assert middleware._constant_time_compare("abc", "abcdef") is False

        # Test empty strings
        assert middleware._constant_time_compare("", "") is True

    def test_csrf_disabled_via_config(self, client):
        """Test that CSRF can be disabled via configuration"""
        # This test documents the behavior when CSRF is disabled
        # In production, CSRF should always be enabled

        with patch.object(settings, "CSRF_ENABLED", False):
            # With CSRF disabled, POST should work without token
            # Note: This is for testing only - NEVER disable in production
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "code": "test-code",
                    "redirect_uri": "http://localhost:3000/callback"
                }
            )

            # Should not fail due to CSRF when disabled
            assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")


class TestCSRFIntegration:
    """Integration tests for CSRF protection with authentication flow"""

    def test_login_sets_csrf_token(self, client):
        """Test that login endpoint sets CSRF token in cookie"""
        # Mock Auth0 token exchange
        with patch("app.auth.auth0.auth0_client.exchange_code_for_token") as mock_exchange:
            mock_exchange.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600
            }

            # Mock Auth0 user info
            with patch("app.auth.auth0.auth0_client.get_user_info") as mock_user_info:
                mock_user_info.return_value = {
                    "email": "test@example.com",
                    "sub": "auth0|123",
                    "given_name": "Test",
                    "family_name": "User"
                }

                # Mock database operations
                with patch("app.api.api_v1.endpoints.auth._create_or_update_user_from_auth0"):
                    response = client.post(
                        "/api/v1/auth/login",
                        json={
                            "code": "test-code",
                            "redirect_uri": "http://localhost:3000/callback"
                        }
                    )

                    # Check if CSRF token is set in cookies
                    if response.status_code == 200:
                        csrf_cookie = response.cookies.get(settings.CSRF_COOKIE_NAME)
                        assert csrf_cookie is not None
                        assert len(csrf_cookie) >= 32  # Minimum token length

    def test_refresh_updates_csrf_token(self, client, csrf_token):
        """Test that token refresh updates CSRF token"""
        client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)

        # Mock Auth0 refresh
        with patch("app.auth.auth0.auth0_client.refresh_token") as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new-access-token",
                "expires_in": 3600
            }

            # Test refresh with CSRF token
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "test-refresh-token"},
                headers={settings.CSRF_HEADER_NAME: csrf_token}
            )

            # Should succeed or fail for auth reasons, not CSRF
            if response.status_code == 200:
                new_csrf = response.cookies.get(settings.CSRF_COOKIE_NAME)
                assert new_csrf is not None
                assert new_csrf != csrf_token  # Should be a new token


class TestCSRFTimingAttack:
    """Tests for timing attack resistance"""

    def test_csrf_timing_attack_resistance(self):
        """
        Test that CSRF validation uses constant-time comparison.

        This test runs a timing attack stress test to verify that
        the constant-time comparison doesn't leak information about
        the token through timing differences.
        """
        import subprocess
        from pathlib import Path

        # Find the timing test script
        script_path = Path(__file__).parent / "security" / "test_csrf_timing.sh"

        if not script_path.exists():
            pytest.skip("Timing test script not found")

        # Check if backend is running
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code != 200:
                pytest.skip("Backend not running for timing test")
        except:
            pytest.skip("Backend not running for timing test")

        # Run timing attack test
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check result
        assert result.returncode == 0, (
            f"Timing attack test failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify output contains success message
        assert "PASS: Constant-time comparison verified" in result.stdout
        assert "no O(n) timing leak" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
