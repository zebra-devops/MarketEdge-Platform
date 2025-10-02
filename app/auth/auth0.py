import asyncio
import httpx
import hashlib
import secrets
import time
from typing import Optional, Dict, Any, List
from ..core.config import settings
from ..core.logging import logger


class Auth0Client:
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.base_url = f"https://{self.domain}"
        self.timeout = 30  # Request timeout in seconds
        self.max_retries = 3  # Maximum retry attempts
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Auth0 using access token with retry logic"""
        for attempt in range(self.max_retries):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    logger.debug(
                        "Fetching user info from Auth0",
                        extra={
                            "event": "userinfo_request",
                            "attempt": attempt + 1,
                            "max_attempts": self.max_retries
                        }
                    )
                    
                    response = await client.get(
                        f"{self.base_url}/userinfo",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"
                        }
                    )
                    response.raise_for_status()
                    
                    user_info = response.json()
                    logger.info(
                        "Successfully retrieved user info from Auth0",
                        extra={
                            "event": "userinfo_success",
                            "user_email": user_info.get("email"),
                            "user_id": user_info.get("sub")
                        }
                    )
                    return user_info
                    
                except httpx.TimeoutException as e:
                    logger.warning(
                        f"Timeout getting user info (attempt {attempt + 1})",
                        extra={
                            "event": "userinfo_timeout",
                            "attempt": attempt + 1,
                            "error": str(e)
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
                except httpx.HTTPError as e:
                    status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                    response_body = getattr(e.response, 'text', None) if hasattr(e, 'response') else None
                    logger.error(
                        "HTTP error getting user info from Auth0",
                        extra={
                            "event": "userinfo_http_error",
                            "status_code": status_code,
                            "error": str(e),
                            "response_body": response_body[:500] if response_body else None,
                            "attempt": attempt + 1,
                            "hint": "If 401/403: check access_token audience and scopes. Token may be for Management API instead of userinfo."
                        }
                    )
                    # Don't retry on 4xx errors (client errors)
                    if status_code and 400 <= status_code < 500:
                        return None
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
                except Exception as e:
                    logger.error(
                        "Unexpected error getting user info",
                        extra={
                            "event": "userinfo_unexpected_error",
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "attempt": attempt + 1
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
        return None
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str, state: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token with enhanced security"""
        # Validate input parameters
        if not code or not redirect_uri:
            logger.error(
                "Missing required parameters for token exchange",
                extra={
                    "event": "token_exchange_invalid_params",
                    "has_code": bool(code),
                    "has_redirect_uri": bool(redirect_uri)
                }
            )
            return None
            
        for attempt in range(self.max_retries):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    data = {
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    }
                    
                    # Include state parameter if provided for CSRF protection
                    if state:
                        data["state"] = state
                    
                    logger.debug(
                        "Initiating token exchange request",
                        extra={
                            "event": "token_exchange_start",
                            "endpoint": f"{self.base_url}/oauth/token",
                            "grant_type": "authorization_code",
                            "attempt": attempt + 1,
                            "has_state": bool(state),
                            "redirect_uri_domain": redirect_uri.split('/')[2] if '//' in redirect_uri else redirect_uri
                        }
                    )
                    
                    response = await client.post(
                        f"{self.base_url}/oauth/token",
                        data=data,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json"
                        }
                    )
                    
                    logger.debug(
                        "Token exchange response received",
                        extra={
                            "event": "token_exchange_response",
                            "status_code": response.status_code,
                            "success": response.is_success,
                            "attempt": attempt + 1
                        }
                    )
                    
                    response.raise_for_status()
                    token_data = response.json()
                    
                    # Validate token response
                    if not self._validate_token_response(token_data):
                        logger.error(
                            "Invalid token response from Auth0",
                            extra={
                                "event": "token_exchange_invalid_response",
                                "has_access_token": "access_token" in token_data,
                                "has_token_type": "token_type" in token_data
                            }
                        )
                        return None
                    
                    logger.info(
                        "Token exchange successful",
                        extra={
                            "event": "token_exchange_success",
                            "token_type": token_data.get("token_type"),
                            "expires_in": token_data.get("expires_in"),
                            "scope": token_data.get("scope")
                        }
                    )
                    
                    return token_data
                    
                except httpx.TimeoutException as e:
                    logger.warning(
                        f"Timeout during token exchange (attempt {attempt + 1})",
                        extra={
                            "event": "token_exchange_timeout",
                            "error": str(e),
                            "attempt": attempt + 1,
                            "timeout_duration": self.timeout
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
                except httpx.HTTPError as e:
                    status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                    response_text = getattr(e.response, 'text', 'No response body') if hasattr(e, 'response') else 'No response'
                    
                    logger.error(
                        "HTTP error during token exchange",
                        extra={
                            "event": "token_exchange_http_error",
                            "error": str(e),
                            "status_code": status_code,
                            "response_body": response_text[:500] if response_text else None,  # Truncate for logging
                            "attempt": attempt + 1
                        }
                    )
                    
                    # Don't retry on 4xx errors (client errors)
                    if status_code and 400 <= status_code < 500:
                        return None
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
                except Exception as e:
                    logger.error(
                        "Unexpected error during token exchange",
                        extra={
                            "event": "token_exchange_unexpected_error",
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "attempt": attempt + 1
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)
                    
        return None
    
    def get_authorization_url(self, redirect_uri: str, state: str = None, additional_scopes: List[str] = None, organization_hint: str = None) -> str:
        """Generate Auth0 authorization URL with enhanced security and multi-tenant organization context"""
        from urllib.parse import urlencode, quote
        
        # Validate redirect URI
        if not self._validate_redirect_uri(redirect_uri):
            logger.error(
                "Invalid redirect URI provided",
                extra={
                    "event": "invalid_redirect_uri",
                    "redirect_uri": redirect_uri
                }
            )
            raise ValueError("Invalid redirect URI")
        
        # Generate secure state if not provided
        if not state:
            state = self._generate_secure_state()
            
        # Base scopes for multi-tenant authentication
        base_scopes = ["openid", "profile", "email"]

        # CRITICAL FIX: Add offline_access scope to enable refresh token rotation
        # This is required when Auth0 Refresh Token Rotation is enabled
        base_scopes.append("offline_access")

        # Add multi-tenant specific scopes
        tenant_scopes = ["read:organization", "read:roles"]
        base_scopes.extend(tenant_scopes)

        # Add additional scopes if provided
        if additional_scopes:
            base_scopes.extend(additional_scopes)

        # Remove duplicates while preserving order
        scopes = list(dict.fromkeys(base_scopes))

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "prompt": "select_account",  # Force user to select account for security
            "max_age": "3600",  # Force re-authentication after 1 hour
            # CRITICAL FIX: Remove Management API audience for regular login flow
            # The Management API audience causes access_token to be scoped for /api/v2/ only,
            # preventing it from being used with /userinfo endpoint (causing 401 errors).
            # Management API access should be obtained separately when needed.
            # "audience": f"https://{self.domain}/api/v2/"
        }
        
        # Add organization hint if provided for multi-tenant routing
        if organization_hint:
            params["organization"] = organization_hint
            logger.info(
                "Organization hint added to auth URL",
                extra={
                    "event": "auth_url_org_hint",
                    "organization_hint": organization_hint
                }
            )
        
        query_string = urlencode(params, quote_via=quote)
        auth_url = f"{self.base_url}/authorize?{query_string}"
        
        logger.info(
            "Generated Auth0 authorization URL with tenant context",
            extra={
                "event": "auth_url_generated",
                "redirect_uri_domain": redirect_uri.split('/')[2] if '//' in redirect_uri else redirect_uri,
                "scopes": scopes,
                "has_state": bool(state),
                "has_org_hint": bool(organization_hint),
                "tenant_scopes_added": tenant_scopes
            }
        )
        
        return auth_url
    
    async def get_user_organizations(self, access_token: str) -> Optional[List[Dict[str, Any]]]:
        """Get user's organizations from Auth0 Management API with secure token management"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Fetching user organizations from Auth0",
                    extra={
                        "event": "user_orgs_request",
                        "attempt": attempt + 1,
                        "max_attempts": self.max_retries
                    }
                )
                
                # Get user info first to extract user ID
                user_info = await self._get_user_info_secure(access_token)
                if not user_info:
                    logger.error("Failed to get user info for organization lookup")
                    return None
                    
                user_id = user_info.get("sub")
                if not user_id:
                    logger.error("No user ID found in Auth0 user info")
                    return None
                
                # Get Management API token with proper security
                mgmt_token = await self._get_management_api_token()
                if not mgmt_token:
                    logger.warning("Management API token not available, using user metadata fallback")
                    return self._extract_org_from_user_metadata(user_info)
                
                # Use Management API to get user's organizations
                organizations = await self._fetch_user_orgs_from_management_api(user_id, mgmt_token)
                
                logger.info(
                    "Successfully retrieved user organizations",
                    extra={
                        "event": "user_orgs_success",
                        "user_id": user_id,
                        "org_count": len(organizations) if organizations else 0
                    }
                )
                
                return organizations or self._extract_org_from_user_metadata(user_info)
                    
            except httpx.TimeoutException as e:
                logger.warning(
                    f"Timeout getting user organizations (attempt {attempt + 1})",
                    extra={
                        "event": "user_orgs_timeout",
                        "attempt": attempt + 1,
                        "error": str(e)
                    }
                )
                if attempt == self.max_retries - 1:
                    return None
                await self._exponential_backoff(attempt)
                
            except httpx.HTTPError as e:
                status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                logger.error(
                    "HTTP error getting user organizations from Auth0",
                    extra={
                        "event": "user_orgs_http_error",
                        "status_code": status_code,
                        "error": str(e),
                        "attempt": attempt + 1
                    }
                )
                # Don't retry on 4xx errors (client errors)
                if status_code and 400 <= status_code < 500:
                    return None
                if attempt == self.max_retries - 1:
                    return None
                await self._exponential_backoff(attempt)
                
            except Exception as e:
                logger.error(
                    "Unexpected error getting user organizations",
                    extra={
                        "event": "user_orgs_unexpected_error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1
                    }
                )
                if attempt == self.max_retries - 1:
                    return None
                await self._exponential_backoff(attempt)
                    
        return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh Auth0 access token using refresh token (CRITICAL SECURITY FIX).

        This implements the Auth0 refresh token flow to fix CRITICAL ISSUE #3 from
        code review - token refresh flow inconsistency where login returns Auth0
        tokens but refresh endpoint expected internal tokens.

        Args:
            refresh_token: Auth0 refresh token received during login

        Returns:
            Token response with new access_token and optionally new refresh_token,
            or None if refresh fails
        """
        for attempt in range(self.max_retries):
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    logger.debug(
                        "Initiating Auth0 token refresh",
                        extra={
                            "event": "token_refresh_start",
                            "attempt": attempt + 1,
                            "max_attempts": self.max_retries
                        }
                    )

                    data = {
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token
                    }

                    response = await client.post(
                        f"{self.base_url}/oauth/token",
                        data=data,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json"
                        }
                    )

                    logger.debug(
                        "Token refresh response received",
                        extra={
                            "event": "token_refresh_response",
                            "status_code": response.status_code,
                            "success": response.is_success,
                            "attempt": attempt + 1
                        }
                    )

                    response.raise_for_status()
                    token_data = response.json()

                    # Validate token response
                    if not self._validate_token_response(token_data):
                        logger.error(
                            "Invalid token refresh response from Auth0",
                            extra={
                                "event": "token_refresh_invalid_response",
                                "has_access_token": "access_token" in token_data,
                                "has_token_type": "token_type" in token_data
                            }
                        )
                        return None

                    logger.info(
                        "Token refresh successful",
                        extra={
                            "event": "token_refresh_success",
                            "token_type": token_data.get("token_type"),
                            "expires_in": token_data.get("expires_in"),
                            "has_new_refresh_token": "refresh_token" in token_data
                        }
                    )

                    return token_data

                except httpx.TimeoutException as e:
                    logger.warning(
                        f"Timeout during token refresh (attempt {attempt + 1})",
                        extra={
                            "event": "token_refresh_timeout",
                            "error": str(e),
                            "attempt": attempt + 1,
                            "timeout_duration": self.timeout
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)

                except httpx.HTTPError as e:
                    status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                    response_text = getattr(e.response, 'text', 'No response body') if hasattr(e, 'response') else 'No response'

                    logger.error(
                        "HTTP error during token refresh",
                        extra={
                            "event": "token_refresh_http_error",
                            "error": str(e),
                            "status_code": status_code,
                            "response_body": response_text[:500] if response_text else None,
                            "attempt": attempt + 1
                        }
                    )

                    # Don't retry on 4xx errors (client errors like invalid refresh token)
                    if status_code and 400 <= status_code < 500:
                        logger.warning(
                            "Refresh token invalid or expired (4xx error)",
                            extra={
                                "event": "token_refresh_invalid_token",
                                "status_code": status_code
                            }
                        )
                        return None
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)

                except Exception as e:
                    logger.error(
                        "Unexpected error during token refresh",
                        extra={
                            "event": "token_refresh_unexpected_error",
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "attempt": attempt + 1
                        }
                    )
                    if attempt == self.max_retries - 1:
                        return None
                    await self._exponential_backoff(attempt)

        return None

    async def revoke_token(self, token: str, token_type: str = "refresh_token") -> bool:
        """Revoke Auth0 token for secure logout"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                data = {
                    "token": token,
                    "token_type_hint": token_type,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }

                response = await client.post(
                    f"{self.base_url}/oauth/revoke",
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

                response.raise_for_status()

                logger.info(
                    "Successfully revoked token",
                    extra={
                        "event": "token_revoked",
                        "token_type": token_type
                    }
                )

                return True

            except Exception as e:
                logger.error(
                    "Failed to revoke token",
                    extra={
                        "event": "token_revoke_error",
                        "error": str(e),
                        "token_type": token_type
                    }
                )
                return False
    
    def _validate_redirect_uri(self, redirect_uri: str) -> bool:
        """Validate redirect URI format and security"""
        if not redirect_uri:
            return False
            
        # Basic URL validation
        if not (redirect_uri.startswith('http://') or redirect_uri.startswith('https://')):
            return False
            
        # For production, only allow HTTPS
        if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
            if not redirect_uri.startswith('https://'):
                return False
                
        return True
    
    def _generate_secure_state(self) -> str:
        """Generate cryptographically secure state parameter"""
        return secrets.token_urlsafe(32)
    
    def _validate_token_response(self, token_data: Dict[str, Any]) -> bool:
        """Validate Auth0 token response"""
        required_fields = ["access_token", "token_type"]
        is_valid = all(field in token_data for field in required_fields)

        # CRITICAL WARNING: Check if refresh_token is missing or empty
        if is_valid:
            refresh_token = token_data.get("refresh_token")
            if not refresh_token or not refresh_token.strip():
                logger.warning(
                    "Auth0 token response missing refresh_token - check Auth0 application settings",
                    extra={
                        "event": "token_response_missing_refresh_token",
                        "has_refresh_token_key": "refresh_token" in token_data,
                        "refresh_token_empty": not refresh_token if refresh_token else True,
                        "token_type": token_data.get("token_type"),
                        "hint": "Ensure 'Refresh Token Rotation' is enabled in Auth0 Application settings"
                    }
                )

        return is_valid
    
    async def _get_management_api_token(self) -> Optional[str]:
        """Get Auth0 Management API token with secure caching and rotation"""
        # Check if we have a cached token that's still valid
        if hasattr(self, '_mgmt_token_cache') and hasattr(self, '_mgmt_token_expiry'):
            if time.time() < self._mgmt_token_expiry - 300:  # Refresh 5 minutes before expiry
                return self._mgmt_token_cache
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "audience": f"https://{self.domain}/api/v2/",
                        "grant_type": "client_credentials"
                    },
                    headers={
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                
                if access_token:
                    # Cache token with expiry tracking
                    self._mgmt_token_cache = access_token
                    self._mgmt_token_expiry = time.time() + expires_in
                    
                    logger.info(
                        "Management API token acquired",
                        extra={
                            "event": "mgmt_token_acquired",
                            "expires_in": expires_in
                        }
                    )
                    return access_token
                    
        except Exception as e:
            logger.error(
                "Failed to get Management API token",
                extra={
                    "event": "mgmt_token_error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
        return None
    
    async def _get_user_info_secure(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Securely get user info with input validation"""
        if not access_token or not isinstance(access_token, str):
            logger.error("Invalid access token provided")
            return None
            
        # Sanitize access token
        access_token = access_token.strip()
        if not access_token:
            logger.error("Empty access token after sanitization")
            return None
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(
                    "Error getting secure user info",
                    extra={
                        "event": "secure_userinfo_error",
                        "error": str(e)
                    }
                )
                return None
    
    async def _fetch_user_orgs_from_management_api(self, user_id: str, mgmt_token: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch user organizations using Management API with tenant isolation"""
        if not user_id or not mgmt_token:
            return None
            
        # Sanitize user_id to prevent injection
        user_id = user_id.strip()
        if not user_id or '/' in user_id or '\\' in user_id:
            logger.error("Invalid user ID format")
            return None
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v2/users/{user_id}/organizations",
                    headers={
                        "Authorization": f"Bearer {mgmt_token}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.info("User has no organizations in Auth0")
                    return []
                logger.error(
                    "Management API error fetching organizations",
                    extra={
                        "event": "mgmt_api_orgs_error",
                        "status_code": e.response.status_code,
                        "error": str(e)
                    }
                )
                return None
            except Exception as e:
                logger.error(
                    "Unexpected error fetching organizations from Management API",
                    extra={
                        "event": "mgmt_api_orgs_unexpected_error",
                        "error": str(e)
                    }
                )
                return None
    
    def _extract_org_from_user_metadata(self, user_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract organization info from user metadata as fallback"""
        organizations = []
        
        # Safely extract organization info from user metadata
        org_id = user_info.get("org_id") or user_info.get("organization")
        if org_id:
            # Sanitize org data
            org_name = user_info.get("org_name", "Default Organization")
            if isinstance(org_name, str):
                org_name = org_name.strip()[:100]  # Limit length
            else:
                org_name = "Default Organization"
                
            organizations.append({
                "id": str(org_id).strip()[:50],  # Sanitize and limit length
                "name": org_name,
                "display_name": user_info.get("org_display_name", org_name),
                "metadata": user_info.get("org_metadata", {})
            })
        
        return organizations
    
    async def _exponential_backoff(self, attempt: int) -> None:
        """Implement exponential backoff for retries"""
        delay = min(2 ** attempt, 10)  # Cap at 10 seconds
        await asyncio.sleep(delay + secrets.randbelow(1000) / 1000)  # Add jitter


auth0_client = Auth0Client()