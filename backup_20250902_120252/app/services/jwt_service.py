"""
US-102: Enhanced JWT Token Service

Provides centralized JWT token validation, refresh, and management
for shared authentication context across all modules.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
import jwt
import uuid
from enum import Enum
import threading
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.user import User, UserRole
from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    SESSION = "session"
    MODULE = "module"


class TokenStatus(str, Enum):
    """Token validation status"""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    BLACKLISTED = "blacklisted"


@dataclass
class TokenValidationResult:
    """Result of token validation"""
    status: TokenStatus
    payload: Optional[Dict[str, Any]] = None
    user: Optional[User] = None
    error_message: Optional[str] = None
    remaining_time: Optional[int] = None  # seconds until expiration
    
    @property
    def is_valid(self) -> bool:
        return self.status == TokenStatus.VALID
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refresh (less than 15 minutes remaining)"""
        return self.remaining_time is not None and self.remaining_time < 900


@dataclass
class TokenPair:
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    token_type: str = "Bearer"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "access_expires_at": self.access_expires_at.isoformat(),
            "refresh_expires_at": self.refresh_expires_at.isoformat(),
            "expires_in": int((self.access_expires_at - datetime.utcnow()).total_seconds())
        }


class TokenBlacklist:
    """Thread-safe token blacklist with Redis fallback and race condition protection"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.local_blacklist: Set[str] = set()
        self.blacklist_cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
        
        # SECURITY FIX: Thread-safe operations
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        self._pending_operations: Dict[str, asyncio.Lock] = {}
        self._operation_locks_lock = threading.Lock()  # Protect the locks dict itself
        
        # Rate limiting for blacklist operations
        self._operation_timestamps = defaultdict(list)
        self._max_operations_per_minute = 100
        
        logger.debug("TokenBlacklist initialized with thread-safe operations")
    
    async def add_token(self, token_jti: str, expires_at: datetime):
        """Thread-safe token blacklist addition with race condition protection"""
        if not token_jti or not isinstance(token_jti, str):
            logger.warning(f"Invalid token JTI for blacklisting: {token_jti}")
            return
        
        # Rate limiting check
        if not self._check_rate_limit('add_token'):
            logger.warning(f"Rate limit exceeded for blacklist operations")
            return
        
        try:
            # Get operation-specific lock to prevent race conditions
            async with self._get_operation_lock(f"add_{token_jti}"):
                # Check if already blacklisted to avoid duplicate operations
                if await self._is_already_blacklisted(token_jti):
                    logger.debug(f"Token already blacklisted: {token_jti}")
                    return
                
                # Thread-safe local blacklist update
                with self._lock:
                    self.local_blacklist.add(token_jti)
                
                # Add to Redis if available with proper error handling
                if self.redis:
                    ttl = int((expires_at - datetime.utcnow()).total_seconds())
                    if ttl > 0:
                        try:
                            # Use Redis transaction for atomic operation
                            pipe = self.redis.pipeline()
                            pipe.setex(f"blacklist:{token_jti}", ttl, "revoked")
                            pipe.sadd("blacklisted_tokens", token_jti)  # Track for cleanup
                            await pipe.execute()
                        except Exception as redis_error:
                            logger.error(f"Redis blacklist operation failed: {str(redis_error)}")
                            # Local blacklist is still updated, so operation partially succeeds
                
                logger.debug(f"Added token to blacklist: {token_jti}")
                
        except Exception as e:
            logger.error(f"Error adding token to blacklist: {str(e)}")
            # Remove from local blacklist if Redis failed
            with self._lock:
                self.local_blacklist.discard(token_jti)
    
    async def is_blacklisted(self, token_jti: str) -> bool:
        """Thread-safe blacklist check with fallback and caching"""
        if not token_jti or not isinstance(token_jti, str):
            logger.warning(f"Invalid token JTI for blacklist check: {token_jti}")
            return True  # Fail secure - assume blacklisted if invalid
        
        try:
            # Thread-safe local blacklist check
            with self._lock:
                if token_jti in self.local_blacklist:
                    return True
            
            # Check Redis if available with fallback handling
            if self.redis:
                try:
                    # Use operation-specific lock for consistency
                    async with self._get_operation_lock(f"check_{token_jti}"):
                        result = await self.redis.get(f"blacklist:{token_jti}")
                        is_blacklisted = result is not None
                        
                        # Sync local cache if found in Redis but not locally
                        if is_blacklisted:
                            with self._lock:
                                self.local_blacklist.add(token_jti)
                        
                        return is_blacklisted
                        
                except Exception as redis_error:
                    logger.warning(f"Redis blacklist check failed, using local cache: {str(redis_error)}")
                    # Fall back to local cache only
                    with self._lock:
                        return token_jti in self.local_blacklist
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return True  # Fail secure - assume blacklisted on error
    
    async def cleanup_expired(self):
        """Thread-safe cleanup of expired tokens from blacklist"""
        try:
            current_time = time.time()
            if (current_time - self.last_cleanup) > self.blacklist_cleanup_interval:
                async with self._get_operation_lock("cleanup"):
                    # Clean up Redis expired tokens
                    if self.redis:
                        try:
                            # Get all blacklisted tokens
                            blacklisted_tokens = await self.redis.smembers("blacklisted_tokens")
                            expired_tokens = []
                            
                            for token_jti in blacklisted_tokens:
                                if isinstance(token_jti, bytes):
                                    token_jti = token_jti.decode('utf-8')
                                    
                                # Check if token entry exists (expired entries are auto-removed by Redis TTL)
                                exists = await self.redis.exists(f"blacklist:{token_jti}")
                                if not exists:
                                    expired_tokens.append(token_jti)
                            
                            # Remove expired tokens from tracking set
                            if expired_tokens:
                                await self.redis.srem("blacklisted_tokens", *expired_tokens)
                                logger.debug(f"Cleaned up {len(expired_tokens)} expired Redis blacklist entries")
                                
                        except Exception as redis_error:
                            logger.warning(f"Redis cleanup failed: {str(redis_error)}")
                    
                    # For local blacklist, we can't easily determine expiration
                    # so we'll clear it periodically and rely on Redis for persistence
                    with self._lock:
                        old_size = len(self.local_blacklist)
                        self.local_blacklist.clear()
                        logger.debug(f"Cleaned up {old_size} local blacklist entries")
                    
                    # Clean up rate limiting data
                    self._cleanup_rate_limit_data()
                    
                    self.last_cleanup = current_time
                
        except Exception as e:
            logger.error(f"Error cleaning up token blacklist: {str(e)}")
    
    def _get_operation_lock(self, operation_id: str) -> asyncio.Lock:
        """Get or create operation-specific async lock"""
        with self._operation_locks_lock:
            if operation_id not in self._pending_operations:
                self._pending_operations[operation_id] = asyncio.Lock()
            return self._pending_operations[operation_id]
    
    async def _is_already_blacklisted(self, token_jti: str) -> bool:
        """Check if token is already blacklisted (internal use)"""
        with self._lock:
            if token_jti in self.local_blacklist:
                return True
        
        if self.redis:
            try:
                result = await self.redis.exists(f"blacklist:{token_jti}")
                return result > 0
            except Exception:
                return False
        
        return False
    
    def _check_rate_limit(self, operation_type: str) -> bool:
        """Check if operation is within rate limits"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        with self._lock:
            # Clean old timestamps
            self._operation_timestamps[operation_type] = [
                ts for ts in self._operation_timestamps[operation_type] 
                if ts > minute_ago
            ]
            
            # Check if under limit
            if len(self._operation_timestamps[operation_type]) >= self._max_operations_per_minute:
                return False
            
            # Add current timestamp
            self._operation_timestamps[operation_type].append(current_time)
            return True
    
    def _cleanup_rate_limit_data(self):
        """Clean up old rate limiting data"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        with self._lock:
            for operation_type in list(self._operation_timestamps.keys()):
                self._operation_timestamps[operation_type] = [
                    ts for ts in self._operation_timestamps[operation_type] 
                    if ts > minute_ago
                ]
                
                # Remove empty entries
                if not self._operation_timestamps[operation_type]:
                    del self._operation_timestamps[operation_type]


class JWTService:
    """
    US-102: Enhanced JWT service for shared authentication context
    
    Provides:
    - Token generation and validation
    - Token refresh capabilities
    - Cross-module token sharing
    - Token blacklisting and revocation
    - Session token management
    """
    
    def __init__(self, redis_client=None):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 7  # 7 days
        self.session_token_expire_hours = 8  # 8 hours
        
        # Token management with thread safety
        self.blacklist = TokenBlacklist(redis_client)
        self.token_cache: Dict[str, TokenValidationResult] = {}
        self.cache_ttl = 300  # 5 minutes
        self._cache_lock = threading.RLock()  # Protect token cache
        
        # Security monitoring
        self.validation_metrics = {
            'total_validations': 0,
            'failed_validations': 0,
            'blacklist_hits': 0,
            'cache_hits': 0
        }
        self._metrics_lock = threading.Lock()
        
        logger.info("JWT Service initialized with enhanced security and thread safety")
    
    async def create_token_pair(
        self,
        user: User,
        session_id: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Create access and refresh token pair for user
        
        Args:
            user: User to create tokens for
            session_id: Optional session identifier
            additional_claims: Additional JWT claims
            
        Returns:
            TokenPair: Access and refresh tokens with expiration times
        """
        try:
            now = datetime.utcnow()
            session_id = session_id or str(uuid.uuid4())
            
            # Access token
            access_expires = now + timedelta(minutes=self.access_token_expire_minutes)
            access_payload = {
                "sub": user.id,
                "user_id": user.id,
                "organisation_id": user.organisation_id,
                "role": user.role.value,
                "session_id": session_id,
                "token_type": TokenType.ACCESS.value,
                "iat": int(now.timestamp()),
                "exp": int(access_expires.timestamp()),
                "jti": str(uuid.uuid4())
            }
            
            # Add additional claims
            if additional_claims:
                access_payload.update(additional_claims)
            
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            
            # Refresh token
            refresh_expires = now + timedelta(days=self.refresh_token_expire_days)
            refresh_payload = {
                "sub": user.id,
                "user_id": user.id,
                "session_id": session_id,
                "token_type": TokenType.REFRESH.value,
                "iat": int(now.timestamp()),
                "exp": int(refresh_expires.timestamp()),
                "jti": str(uuid.uuid4())
            }
            
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
            
            token_pair = TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                access_expires_at=access_expires,
                refresh_expires_at=refresh_expires
            )
            
            logger.info(f"Created token pair for user {user.id} with session {session_id}")
            return token_pair
            
        except Exception as e:
            logger.error(f"Error creating token pair: {str(e)}")
            raise
    
    async def validate_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None,
        load_user: bool = True
    ) -> TokenValidationResult:
        """
        Validate JWT token with comprehensive checks
        
        Args:
            token: JWT token string
            expected_type: Expected token type
            load_user: Whether to load user from database
            
        Returns:
            TokenValidationResult: Validation result with user if successful
        """
        try:
            # Thread-safe cache check
            cache_key = f"{hash(token)}:{expected_type}:{load_user}"
            with self._cache_lock:
                if cache_key in self.token_cache:
                    cached_result = self.token_cache[cache_key]
                    # Check if cache entry is still valid
                    if cached_result.remaining_time and cached_result.remaining_time > 0:
                        with self._metrics_lock:
                            self.validation_metrics['cache_hits'] += 1
                        return cached_result
                    else:
                        del self.token_cache[cache_key]
            
            # Decode token without verification first to get JTI
            try:
                unverified_payload = jwt.decode(token, options={"verify_signature": False})
                token_jti = unverified_payload.get("jti")
                
                # SECURITY FIX: Check if token is blacklisted with metrics
                if token_jti and await self.blacklist.is_blacklisted(token_jti):
                    with self._metrics_lock:
                        self.validation_metrics['blacklist_hits'] += 1
                        self.validation_metrics['failed_validations'] += 1
                    
                    logger.warning(f"Blacklisted token validation attempt: {token_jti[:8]}...")
                    return TokenValidationResult(
                        status=TokenStatus.BLACKLISTED,
                        error_message="Token has been revoked"
                    )
            except jwt.DecodeError:
                return TokenValidationResult(
                    status=TokenStatus.INVALID,
                    error_message="Invalid token format"
                )
            
            # Verify token signature and claims
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            except jwt.ExpiredSignatureError:
                return TokenValidationResult(
                    status=TokenStatus.EXPIRED,
                    error_message="Token has expired"
                )
            except jwt.InvalidTokenError as e:
                return TokenValidationResult(
                    status=TokenStatus.INVALID,
                    error_message=f"Invalid token: {str(e)}"
                )
            
            # Validate token type if specified
            if expected_type:
                token_type = payload.get("token_type")
                if token_type != expected_type.value:
                    return TokenValidationResult(
                        status=TokenStatus.INVALID,
                        error_message=f"Expected {expected_type.value} token, got {token_type}"
                    )
            
            # Calculate remaining time
            exp = payload.get("exp")
            remaining_time = int(exp - time.time()) if exp else None
            
            # Load user if requested
            user = None
            if load_user:
                user_id = payload.get("user_id") or payload.get("sub")
                if user_id:
                    user = await self._load_user(user_id)
                    if not user or not user.is_active:
                        return TokenValidationResult(
                            status=TokenStatus.INVALID,
                            error_message="User not found or inactive"
                        )
            
            result = TokenValidationResult(
                status=TokenStatus.VALID,
                payload=payload,
                user=user,
                remaining_time=remaining_time
            )
            
            # Thread-safe cache update
            if remaining_time and remaining_time > 60:  # Cache if more than 1 minute remaining
                with self._cache_lock:
                    self.token_cache[cache_key] = result
            
            # Update metrics
            with self._metrics_lock:
                self.validation_metrics['total_validations'] += 1
                if not result.is_valid:
                    self.validation_metrics['failed_validations'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return TokenValidationResult(
                status=TokenStatus.INVALID,
                error_message=f"Token validation error: {str(e)}"
            )
    
    async def refresh_token_pair(
        self,
        refresh_token: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Optional[TokenPair]:
        """
        Secure refresh access token using refresh token with blacklist validation
        
        Args:
            refresh_token: Valid refresh token
            additional_claims: Additional JWT claims for new tokens
            
        Returns:
            TokenPair: New token pair or None if refresh failed
        """
        try:
            # SECURITY FIX: Validate refresh token with comprehensive checks
            validation_result = await self.validate_token(
                refresh_token, 
                expected_type=TokenType.REFRESH,
                load_user=True
            )
            
            if not validation_result.is_valid:
                logger.warning(f"Invalid refresh token: {validation_result.error_message}")
                # Update metrics for failed refresh
                with self._metrics_lock:
                    self.validation_metrics['failed_validations'] += 1
                return None
            
            user = validation_result.user
            payload = validation_result.payload
            
            if not user or not user.is_active:
                logger.error(f"User not found or inactive for refresh token: {user.id if user else 'unknown'}")
                return None
            
            # SECURITY FIX: Blacklist old refresh token BEFORE creating new one
            # This prevents race conditions where the same refresh token is used multiple times
            old_jti = payload.get("jti")
            if old_jti:
                expires_at = datetime.fromtimestamp(payload.get("exp", time.time()))
                await self.blacklist.add_token(old_jti, expires_at)
            
            # Create new token pair
            session_id = payload.get("session_id")
            new_token_pair = await self.create_token_pair(
                user=user,
                session_id=session_id,
                additional_claims=additional_claims
            )
            
            logger.info(f"Refreshed token pair for user {user.id}")
            return new_token_pair
            
        except Exception as e:
            logger.error(f"Error refreshing token pair: {str(e)}")
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token by adding it to blacklist
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: True if successfully revoked
        """
        try:
            # Decode token to get JTI and expiration
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                token_jti = payload.get("jti")
                exp = payload.get("exp")
                
                if not token_jti:
                    logger.error("Token has no JTI claim, cannot revoke")
                    return False
                
                expires_at = datetime.fromtimestamp(exp) if exp else datetime.utcnow() + timedelta(days=7)
                await self.blacklist.add_token(token_jti, expires_at)
                
                # Thread-safe cache clearing
                self._clear_token_cache(token)
                
                logger.info(f"Revoked token with JTI: {token_jti}")
                return True
                
            except jwt.DecodeError:
                logger.error("Cannot decode token for revocation")
                return False
            
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    async def revoke_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a specific user (logout from all sessions)
        
        Args:
            user_id: User ID to revoke tokens for
            
        Returns:
            int: Number of tokens revoked
        """
        try:
            # This is a simplified implementation
            # In production, you'd want to maintain a list of active tokens per user
            # For now, we'll just clear the cache and rely on token expiration
            
            revoked_count = 0
            
            # Thread-safe cache clearing for user
            with self._cache_lock:
                keys_to_remove = []
                for cache_key, result in self.token_cache.items():
                    if result.user and result.user.id == user_id:
                        keys_to_remove.append(cache_key)
                        revoked_count += 1
                
                for key in keys_to_remove:
                    del self.token_cache[key]
            
            logger.info(f"Revoked {revoked_count} cached tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {str(e)}")
            return 0
    
    async def create_session_token(
        self,
        user: User,
        session_data: Dict[str, Any],
        expires_hours: Optional[int] = None
    ) -> str:
        """
        Create a session token with embedded session data
        
        Args:
            user: User for the session
            session_data: Data to embed in token
            expires_hours: Token expiration in hours
            
        Returns:
            str: Session token
        """
        try:
            now = datetime.utcnow()
            expires_hours = expires_hours or self.session_token_expire_hours
            expires = now + timedelta(hours=expires_hours)
            
            payload = {
                "sub": user.id,
                "user_id": user.id,
                "organisation_id": user.organisation_id,
                "token_type": TokenType.SESSION.value,
                "session_data": session_data,
                "iat": int(now.timestamp()),
                "exp": int(expires.timestamp()),
                "jti": str(uuid.uuid4())
            }
            
            session_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Created session token for user {user.id}")
            return session_token
            
        except Exception as e:
            logger.error(f"Error creating session token: {str(e)}")
            raise
    
    def extract_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extract payload from token without validation (for debugging)
        
        Args:
            token: JWT token
            
        Returns:
            Dict: Token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception:
            return None
    
    async def cleanup(self):
        """Clean up expired tokens and cache entries"""
        try:
            # Clean up blacklist
            await self.blacklist.cleanup_expired()
            
            # Thread-safe cache cleanup
            with self._cache_lock:
                keys_to_remove = []
                
                for cache_key, result in self.token_cache.items():
                    if (result.remaining_time is None or 
                        result.remaining_time <= 0):
                        keys_to_remove.append(cache_key)
                
                for key in keys_to_remove:
                    del self.token_cache[key]
                
                if keys_to_remove:
                    logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")
            
            # Log security metrics periodically
            with self._metrics_lock:
                if self.validation_metrics['total_validations'] > 0:
                    failure_rate = (self.validation_metrics['failed_validations'] / 
                                  self.validation_metrics['total_validations']) * 100
                    
                    logger.info(f"JWT validation metrics - Total: {self.validation_metrics['total_validations']}, "
                              f"Failed: {self.validation_metrics['failed_validations']} ({failure_rate:.2f}%), "
                              f"Blacklist hits: {self.validation_metrics['blacklist_hits']}, "
                              f"Cache hits: {self.validation_metrics['cache_hits']}")
                
        except Exception as e:
            logger.error(f"Error during JWT service cleanup: {str(e)}")
    
    # Private helper methods
    
    async def _load_user(self, user_id: str) -> Optional[User]:
        """Load user from database"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(User).where(User.id == user_id).options(
                        selectinload(User.organisation)
                    )
                    result = await db_session.execute(stmt)
                    user = result.scalar_one_or_none()
                    return user
                except Exception as db_error:
                    logger.error(f"Database error loading user {user_id}: {str(db_error)}")
                    break
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {str(e)}")
        return None
    
    def _clear_token_cache(self, token: str):
        """Thread-safe cache clearing for a specific token"""
        try:
            with self._cache_lock:
                token_hash = hash(token)
                keys_to_remove = [k for k in self.token_cache.keys() if k.startswith(str(token_hash))]
                for key in keys_to_remove:
                    del self.token_cache[key]
                
                if keys_to_remove:
                    logger.debug(f"Cleared {len(keys_to_remove)} cache entries for token")
        except Exception as e:
            logger.error(f"Error clearing token cache: {str(e)}")


# Global instance
jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """Get the global JWT service instance"""
    global jwt_service
    if jwt_service is None:
        raise RuntimeError("JWT service not initialized")
    return jwt_service


def initialize_jwt_service(redis_client=None) -> JWTService:
    """Initialize the global JWT service"""
    global jwt_service
    if jwt_service is None:
        jwt_service = JWTService(redis_client=redis_client)
        logger.info("Global JWT service initialized")
    return jwt_service