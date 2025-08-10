import httpx
from typing import Optional, Dict, Any
from ..core.config import settings
from ..core.logging import logger


class Auth0Client:
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.base_url = f"https://{self.domain}"
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Auth0 using access token"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error("Failed to get user info from Auth0", error=str(e))
                return None
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            try:
                data = {
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
                logger.debug(
                    "Initiating token exchange request",
                    extra={
                        "event": "token_exchange_start",
                        "endpoint": f"{self.base_url}/oauth/token",
                        "grant_type": "authorization_code"
                    }
                )
                
                response = await client.post(
                    f"{self.base_url}/oauth/token",
                    data=data
                )
                
                logger.debug(
                    "Token exchange response received",
                    extra={
                        "event": "token_exchange_response",
                        "status_code": response.status_code,
                        "success": response.is_success
                    }
                )
                
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                logger.error(
                    "Timeout during token exchange", 
                    extra={
                        "event": "token_exchange_timeout",
                        "error": str(e),
                        "timeout_duration": "default"
                    }
                )
                return None
            except httpx.HTTPError as e:
                logger.error(
                    "HTTP error during token exchange",
                    extra={
                        "event": "token_exchange_http_error",
                        "error": str(e),
                        "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                        "has_response": 'response' in locals()
                    }
                )
                return None
            except Exception as e:
                logger.error(
                    "Unexpected error during token exchange",
                    extra={
                        "event": "token_exchange_unexpected_error",
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                return None
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Generate Auth0 authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
        }
        if state:
            params["state"] = state
        
        query_string = urlencode(params)
        return f"{self.base_url}/authorize?{query_string}"


auth0_client = Auth0Client()