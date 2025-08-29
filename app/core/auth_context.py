"""
US-102: Shared Authentication Context Manager

This module provides centralized authentication context management across all modules,
ensuring consistent session handling, JWT token validation, and cross-module navigation.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import jwt
from redis import asyncio as aioredis

from ..models.user import User, UserRole
from ..models.modules import ModuleUsageLog
from ..auth.dependencies import verify_token
from ..core.database import get_db
from ..services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Authentication session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    TIMEOUT = "timeout"


class ModuleAccessLevel(Enum):
    """Module access levels for context sharing"""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    ADMIN = "admin"


@dataclass
class AuthenticationContext:
    """Comprehensive authentication context for cross-module sharing"""
    
    # Core authentication data
    user_id: str
    user: User
    session_id: str
    organisation_id: str
    
    # Token and session management
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))
    session_expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=8))
    
    # Authorization data
    permissions: Set[str] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)
    module_access: Dict[str, ModuleAccessLevel] = field(default_factory=dict)
    
    # Session metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = field(default_factory=datetime.utcnow)
    last_module_accessed: Optional[str] = None
    access_count: int = 0
    
    # Security and tracking
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    security_flags: Dict[str, Any] = field(default_factory=dict)
    
    # Feature flags and preferences
    enabled_features: Set[str] = field(default_factory=set)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Cross-module data
    module_contexts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session has expired"""
        now = datetime.utcnow()
        return now > self.session_expires_at or now > self.token_expires_at
    
    def is_timeout(self, timeout_minutes: int = 30) -> bool:
        """Check if session has timed out due to inactivity"""
        if timeout_minutes <= 0:
            return False
        timeout_threshold = self.last_accessed_at + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > timeout_threshold
    
    def update_access(self, module_id: Optional[str] = None):
        """Update access tracking"""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
        if module_id:
            self.last_module_accessed = module_id
    
    def set_module_context(self, module_id: str, context_data: Dict[str, Any]):
        """Set module-specific context data"""
        self.module_contexts[module_id] = {
            **context_data,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def get_module_context(self, module_id: str) -> Dict[str, Any]:
        """Get module-specific context data"""
        return self.module_contexts.get(module_id, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "organisation_id": self.organisation_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expires_at": self.token_expires_at.isoformat(),
            "session_expires_at": self.session_expires_at.isoformat(),
            "permissions": list(self.permissions),
            "roles": list(self.roles),
            "module_access": {k: v.value for k, v in self.module_access.items()},
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "last_module_accessed": self.last_module_accessed,
            "access_count": self.access_count,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "security_flags": self.security_flags,
            "enabled_features": list(self.enabled_features),
            "user_preferences": self.user_preferences,
            "module_contexts": self.module_contexts,
            "shared_state": self.shared_state
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user: User) -> 'AuthenticationContext':
        """Create context from dictionary"""
        ctx = cls(
            user_id=data["user_id"],
            user=user,
            session_id=data["session_id"],
            organisation_id=data["organisation_id"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_expires_at=datetime.fromisoformat(data["token_expires_at"]),
            session_expires_at=datetime.fromisoformat(data["session_expires_at"]),
            permissions=set(data.get("permissions", [])),
            roles=set(data.get("roles", [])),
            module_access={
                k: ModuleAccessLevel(v) for k, v in data.get("module_access", {}).items()
            },
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed_at=datetime.fromisoformat(data["last_accessed_at"]),
            last_module_accessed=data.get("last_module_accessed"),
            access_count=data.get("access_count", 0),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            security_flags=data.get("security_flags", {}),
            enabled_features=set(data.get("enabled_features", [])),
            user_preferences=data.get("user_preferences", {}),
            module_contexts=data.get("module_contexts", {}),
            shared_state=data.get("shared_state", {})
        )
        return ctx


class AuthContextCache:
    """Redis-based caching for authentication contexts"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
        self.local_cache: Dict[str, AuthenticationContext] = {}
        self.cache_timestamps: Dict[str, float] = {}
    
    async def get_context(self, session_id: str, verify_user: bool = True) -> Optional[AuthenticationContext]:
        """Get authentication context from cache with proper user verification"""
        try:
            cached_context = None
            
            # Try Redis first if available
            if self.redis:
                cached_data = await self.redis.get(f"auth_context:{session_id}")
                if cached_data:
                    try:
                        data = json.loads(cached_data)
                        if verify_user:
                            # SECURITY FIX: Verify user exists and is still active
                            user = await self._verify_cached_user(data.get("user_id"))
                            if not user:
                                logger.warning(f"Cached user verification failed for session {session_id}")
                                await self.invalidate_context(session_id)
                                return None
                            cached_context = AuthenticationContext.from_dict(data, user)
                        else:
                            # Skip user verification (only for internal use)
                            from ..models.user import User
                            cached_context = AuthenticationContext.from_dict(data, None)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.error(f"Invalid cached data format for session {session_id}: {str(e)}")
                        await self.invalidate_context(session_id)
                        return None
            
            # Fallback to local cache if Redis failed or unavailable
            if not cached_context and session_id in self.local_cache:
                timestamp = self.cache_timestamps.get(session_id, 0)
                if time.time() - timestamp < self.ttl:
                    cached_context = self.local_cache[session_id]
                    if verify_user:
                        # SECURITY FIX: Verify cached user is still valid
                        user = await self._verify_cached_user(cached_context.user_id)
                        if not user:
                            logger.warning(f"Local cached user verification failed for session {session_id}")
                            await self.invalidate_context(session_id)
                            return None
                        # Update context with fresh user data
                        cached_context.user = user
                else:
                    # Clean up expired local cache
                    del self.local_cache[session_id]
                    if session_id in self.cache_timestamps:
                        del self.cache_timestamps[session_id]
            
            return cached_context
        
        except Exception as e:
            logger.error(f"Error retrieving auth context from cache: {str(e)}")
            # Invalidate potentially corrupted cache entry
            await self.invalidate_context(session_id)
        
        return None
    
    async def set_context(self, context: AuthenticationContext):
        """Cache authentication context"""
        try:
            # Cache in Redis if available
            if self.redis:
                await self.redis.setex(
                    f"auth_context:{context.session_id}",
                    self.ttl,
                    json.dumps(context.to_dict())
                )
            
            # Also cache locally
            self.local_cache[context.session_id] = context
            self.cache_timestamps[context.session_id] = time.time()
            
        except Exception as e:
            logger.error(f"Error caching auth context: {str(e)}")
    
    async def invalidate_context(self, session_id: str):
        """Remove context from cache with comprehensive cleanup"""
        try:
            # Remove from Redis
            if self.redis:
                await self.redis.delete(f"auth_context:{session_id}")
            
            # Remove from local cache
            if session_id in self.local_cache:
                del self.local_cache[session_id]
            if session_id in self.cache_timestamps:
                del self.cache_timestamps[session_id]
            
            logger.debug(f"Invalidated auth context cache for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error invalidating auth context: {str(e)}")
    
    async def _verify_cached_user(self, user_id: str) -> Optional['User']:
        """Verify cached user is still active and valid"""
        try:
            from sqlalchemy import select
            from ..models.user import User
            from ..core.database import get_db
            
            async for db_session in get_db():
                try:
                    stmt = select(User).where(User.id == user_id)
                    result = await db_session.execute(stmt)
                    user = result.scalar_one_or_none()
                    
                    # Verify user exists and is active
                    if user and user.is_active:
                        return user
                    elif user and not user.is_active:
                        logger.warning(f"Cached user {user_id} is inactive")
                    else:
                        logger.warning(f"Cached user {user_id} not found in database")
                    break
                except Exception as db_error:
                    logger.error(f"Database error verifying user {user_id}: {str(db_error)}")
                    break
            
            return None
        except Exception as e:
            logger.error(f"Error verifying cached user {user_id}: {str(e)}")
            return None


class AuthenticationContextManager:
    """
    US-102: Central manager for shared authentication context across all modules
    
    Provides:
    - Cross-module session management
    - JWT token validation and refresh
    - Session timeout handling
    - Module-specific permissions enforcement
    - Authentication context caching
    """
    
    def __init__(
        self,
        feature_flag_service: FeatureFlagService,
        redis_client: Optional[aioredis.Redis] = None,
        session_timeout_minutes: int = 30,
        token_refresh_threshold_minutes: int = 15
    ):
        self.feature_flag_service = feature_flag_service
        self.session_timeout_minutes = session_timeout_minutes
        self.token_refresh_threshold_minutes = token_refresh_threshold_minutes
        
        # Context storage and caching
        self.cache = AuthContextCache(redis_client, ttl=3600)
        self.active_contexts: Dict[str, AuthenticationContext] = {}
        
        # Session management
        self.session_cleanup_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="session-cleanup")
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        # Event handlers for context changes
        self.context_event_handlers: Dict[str, List[Callable]] = {
            "created": [],
            "updated": [],
            "expired": [],
            "invalidated": []
        }
        
        # Security monitoring
        self.security_events: Dict[str, List[Dict[str, Any]]] = {
            "failed_verifications": [],
            "suspicious_activities": [],
            "cache_invalidations": []
        }
        self.max_security_events = 1000
        
        logger.info("Authentication Context Manager initialized with enhanced security")
    
    async def create_context(
        self,
        user: User,
        access_token: str,
        refresh_token: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> AuthenticationContext:
        """
        Create a new authentication context for cross-module sharing
        
        Args:
            user: Authenticated user
            access_token: JWT access token
            refresh_token: Optional refresh token
            ip_address: Client IP address
            user_agent: Client user agent
            additional_data: Additional context data
            
        Returns:
            AuthenticationContext: New context instance
        """
        try:
            session_id = str(uuid.uuid4())
            
            # Decode token to get expiration
            token_payload = verify_token(access_token)
            token_expires_at = datetime.fromtimestamp(token_payload.get("exp", time.time() + 3600))
            
            # Create context
            context = AuthenticationContext(
                user_id=user.id,
                user=user,
                session_id=session_id,
                organisation_id=user.organisation_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Load user permissions and roles
            await self._load_user_authorization(context)
            
            # Load enabled features
            await self._load_user_features(context)
            
            # Load module access permissions
            await self._load_module_access(context)
            
            # Add additional data if provided
            if additional_data:
                context.shared_state.update(additional_data)
            
            # Store context
            self.active_contexts[session_id] = context
            await self.cache.set_context(context)
            
            # Fire event handlers
            await self._fire_event_handlers("created", context)
            
            logger.info(f"Created auth context for user {user.id} with session {session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error creating auth context: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication context"
            )
    
    async def get_context(
        self,
        session_id: Optional[str] = None,
        access_token: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[AuthenticationContext]:
        """
        Retrieve authentication context by session ID, token, or user ID
        with comprehensive security validation
        
        Args:
            session_id: Session identifier
            access_token: JWT access token
            user_id: User identifier
            
        Returns:
            AuthenticationContext or None if not found/expired
        """
        try:
            context = None
            
            # Try to get by session ID first
            if session_id:
                context = await self._get_context_by_session(session_id)
            
            # Try to get by access token
            elif access_token:
                context = await self._get_context_by_token(access_token)
            
            # Try to get by user ID (get most recent)
            elif user_id:
                context = await self._get_context_by_user(user_id)
            
            if not context:
                return None
            
            # SECURITY: Comprehensive context validation
            validation_result = await self._validate_context_security(context)
            if not validation_result['valid']:
                logger.warning(f"Context security validation failed: {validation_result['reason']}")
                await self.invalidate_context(context.session_id)
                return None
            
            # Check if context is expired or timed out
            if context.is_expired():
                logger.info(f"Auth context {context.session_id} expired")
                await self.invalidate_context(context.session_id)
                return None
            
            if context.is_timeout(self.session_timeout_minutes):
                logger.info(f"Auth context {context.session_id} timed out")
                await self.invalidate_context(context.session_id)
                return None
            
            # Update access time and persist
            context.update_access()
            await self.cache.set_context(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving auth context: {str(e)}")
            return None
    
    async def validate_context(
        self,
        context: AuthenticationContext,
        module_id: Optional[str] = None,
        required_permissions: Optional[List[str]] = None
    ) -> bool:
        """
        Validate authentication context for module access
        
        Args:
            context: Authentication context
            module_id: Module identifier for access check
            required_permissions: Required permissions list
            
        Returns:
            bool: True if context is valid for the request
        """
        try:
            # Basic validation
            if context.is_expired() or context.is_timeout(self.session_timeout_minutes):
                return False
            
            # Module access validation
            if module_id:
                module_access = context.module_access.get(module_id)
                if not module_access or module_access == ModuleAccessLevel.PUBLIC:
                    # Check if user has access to this module
                    has_access = await self._check_module_access(context.user, module_id)
                    if not has_access:
                        return False
                    
                    # Update context with module access
                    context.module_access[module_id] = ModuleAccessLevel.AUTHENTICATED
            
            # Permission validation
            if required_permissions:
                if not context.permissions.intersection(set(required_permissions)):
                    return False
            
            # Update context access
            context.update_access(module_id)
            return True
            
        except Exception as e:
            logger.error(f"Error validating auth context: {str(e)}")
            return False
    
    async def refresh_context(self, context: AuthenticationContext) -> Optional[AuthenticationContext]:
        """
        Refresh authentication context with new tokens if needed
        
        Args:
            context: Current authentication context
            
        Returns:
            AuthenticationContext: Refreshed context or None if refresh failed
        """
        try:
            now = datetime.utcnow()
            refresh_threshold = now + timedelta(minutes=self.token_refresh_threshold_minutes)
            
            # Check if token needs refresh
            if context.token_expires_at > refresh_threshold:
                return context  # No refresh needed
            
            if not context.refresh_token:
                logger.warning(f"No refresh token available for context {context.session_id}")
                return None
            
            # Attempt token refresh
            # SECURITY FIX: Check JWT blacklist before refresh
            from ..services.jwt_service import get_jwt_service
            jwt_service = get_jwt_service()
            
            # Validate refresh token isn't blacklisted
            refresh_validation = await jwt_service.validate_token(context.refresh_token)
            if not refresh_validation.is_valid:
                logger.warning(f"Refresh token validation failed for context {context.session_id}: {refresh_validation.error_message}")
                return None
            
            # Attempt token refresh
            new_token_pair = await jwt_service.refresh_token_pair(context.refresh_token)
            if not new_token_pair:
                logger.error(f"Failed to refresh token for context {context.session_id}")
                return None
            
            new_access_token = new_token_pair.access_token
            
            # Update context with new token pair
            context.access_token = new_access_token
            context.refresh_token = new_token_pair.refresh_token
            context.token_expires_at = new_token_pair.access_expires_at
            
            # Update cache
            await self.cache.set_context(context)
            
            # Fire event handlers
            await self._fire_event_handlers("updated", context)
            
            logger.info(f"Refreshed auth context {context.session_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error refreshing auth context: {str(e)}")
            return None
    
    async def invalidate_context(self, session_id: str, reason: str = "manual"):
        """
        Invalidate authentication context with comprehensive cleanup
        
        Args:
            session_id: Session to invalidate
            reason: Reason for invalidation
        """
        try:
            context = self.active_contexts.get(session_id)
            if context:
                # Log security event if forced invalidation
                if reason in ['security', 'suspicious_activity', 'session_anomaly']:
                    await self._log_security_event('cache_invalidation', {
                        'session_id': session_id,
                        'user_id': context.user_id,
                        'reason': reason,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                # Remove from active contexts
                del self.active_contexts[session_id]
                
                # Remove from cache
                await self.cache.invalidate_context(session_id)
                
                # Clear user validation cache if exists
                if hasattr(self, '_user_validation_cache'):
                    cache_key = f"user_valid:{context.user_id}"
                    if cache_key in self._user_validation_cache:
                        del self._user_validation_cache[cache_key]
                
                # Fire event handlers
                await self._fire_event_handlers("invalidated", context)
                
                logger.info(f"Invalidated auth context {session_id}, reason: {reason}")
            else:
                # Still try to clean cache even if not in active contexts
                await self.cache.invalidate_context(session_id)
            
        except Exception as e:
            logger.error(f"Error invalidating auth context: {str(e)}")
    
    async def update_module_context(
        self,
        session_id: str,
        module_id: str,
        context_data: Dict[str, Any]
    ):
        """
        Update module-specific context data
        
        Args:
            session_id: Session identifier
            module_id: Module identifier
            context_data: Data to store in module context
        """
        try:
            context = await self.get_context(session_id=session_id)
            if context:
                context.set_module_context(module_id, context_data)
                await self.cache.set_context(context)
                
                logger.debug(f"Updated module context for {module_id} in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error updating module context: {str(e)}")
    
    async def cleanup_expired_contexts(self):
        """Clean up expired authentication contexts"""
        try:
            expired_sessions = []
            now = datetime.utcnow()
            
            for session_id, context in list(self.active_contexts.items()):
                if (context.is_expired() or 
                    context.is_timeout(self.session_timeout_minutes)):
                    expired_sessions.append(session_id)
            
            # Clean up expired contexts
            for session_id in expired_sessions:
                context = self.active_contexts.get(session_id)
                if context:
                    await self._fire_event_handlers("expired", context)
                await self.invalidate_context(session_id, "expired")
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired auth contexts")
            
            self.last_cleanup = time.time()
            
        except Exception as e:
            logger.error(f"Error during context cleanup: {str(e)}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """
        Add event handler for context lifecycle events
        
        Args:
            event_type: Type of event (created, updated, expired, invalidated)
            handler: Async callable to handle the event
        """
        if event_type in self.context_event_handlers:
            self.context_event_handlers[event_type].append(handler)
    
    # Private helper methods
    
    async def _get_context_by_session(self, session_id: str) -> Optional[AuthenticationContext]:
        """Get context by session ID with proper verification"""
        # Try active contexts first
        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            # SECURITY: Verify user is still valid even from active contexts
            if not await self._verify_context_user(context):
                logger.warning(f"Active context user verification failed for session {session_id}")
                del self.active_contexts[session_id]
                await self.cache.invalidate_context(session_id)
                return None
            return context
        
        # Try cache with user verification
        context = await self.cache.get_context(session_id, verify_user=True)
        if context:
            # Re-add to active contexts if valid
            self.active_contexts[session_id] = context
        return context
    
    async def _get_context_by_token(self, access_token: str) -> Optional[AuthenticationContext]:
        """Get context by access token"""
        for context in self.active_contexts.values():
            if context.access_token == access_token:
                return context
        return None
    
    async def _get_context_by_user(self, user_id: str) -> Optional[AuthenticationContext]:
        """Get most recent context by user ID"""
        user_contexts = [
            ctx for ctx in self.active_contexts.values() 
            if ctx.user_id == user_id
        ]
        if user_contexts:
            return max(user_contexts, key=lambda x: x.last_accessed_at)
        return None
    
    async def _load_user_authorization(self, context: AuthenticationContext):
        """Load user permissions and roles"""
        try:
            user = context.user
            
            # Load roles
            if hasattr(user, 'role'):
                context.roles.add(user.role.value)
            
            # Load permissions (would come from a permission system)
            # For now, assign basic permissions based on role
            if user.role == UserRole.ADMIN:
                context.permissions.update([
                    "admin:read", "admin:write", "admin:delete",
                    "user:read", "user:write", "module:manage"
                ])
            elif user.role == UserRole.SUPER_ADMIN:
                context.permissions.update([
                    "admin:read", "admin:write", "admin:delete",
                    "user:read", "user:write", "user:delete",
                    "module:manage", "system:manage"
                ])
            else:
                context.permissions.update(["user:read"])
            
        except Exception as e:
            logger.error(f"Error loading user authorization: {str(e)}")
    
    async def _load_user_features(self, context: AuthenticationContext):
        """Load enabled features for user"""
        try:
            # This would integrate with the feature flag service
            # For now, we'll add some basic features
            context.enabled_features.add("core_features")
            
            if context.user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                context.enabled_features.add("admin_features")
            
        except Exception as e:
            logger.error(f"Error loading user features: {str(e)}")
    
    async def _load_module_access(self, context: AuthenticationContext):
        """Load module access permissions"""
        try:
            # This would integrate with the module service to get available modules
            # For now, we'll set basic access
            context.module_access["core"] = ModuleAccessLevel.AUTHENTICATED
            
            if context.user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                context.module_access["admin"] = ModuleAccessLevel.ADMIN
            
        except Exception as e:
            logger.error(f"Error loading module access: {str(e)}")
    
    async def _check_module_access(self, user: User, module_id: str) -> bool:
        """Check if user has access to module"""
        try:
            # This would integrate with the module service
            # For now, return True for basic access check
            return True
            
        except Exception as e:
            logger.error(f"Error checking module access: {str(e)}")
            return False
    
    async def _refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            # This would integrate with your token refresh endpoint
            # For now, return None to indicate refresh not implemented
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return None
    
    async def _fire_event_handlers(self, event_type: str, context: AuthenticationContext):
        """Fire event handlers for context lifecycle events"""
        try:
            handlers = self.context_event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(context)
                    else:
                        handler(context)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error firing event handlers: {str(e)}")
    
    async def _validate_context_security(self, context: AuthenticationContext) -> Dict[str, Any]:
        """Comprehensive security validation for authentication context"""
        try:
            # Basic validation
            if not context or not context.user:
                return {'valid': False, 'reason': 'Missing context or user'}
            
            # Check user is still active
            if not context.user.is_active:
                return {'valid': False, 'reason': 'User account deactivated'}
            
            # Check for suspicious activity patterns
            if await self._detect_suspicious_activity(context):
                await self._log_security_event('suspicious_activity', {
                    'session_id': context.session_id,
                    'user_id': context.user_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'access_count': context.access_count,
                    'ip_address': context.ip_address
                })
                return {'valid': False, 'reason': 'Suspicious activity detected'}
            
            # Validate session hasn't been hijacked
            if await self._detect_session_anomalies(context):
                await self._log_security_event('session_anomaly', {
                    'session_id': context.session_id,
                    'user_id': context.user_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
                return {'valid': False, 'reason': 'Session anomaly detected'}
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error in context security validation: {str(e)}")
            return {'valid': False, 'reason': f'Validation error: {str(e)}'}
    
    async def _verify_context_user(self, context: AuthenticationContext) -> bool:
        """Verify context user is still valid and active"""
        try:
            if not context.user:
                return False
            
            # Check cache first to avoid DB hits
            cache_key = f"user_valid:{context.user_id}"
            if hasattr(self, '_user_validation_cache'):
                cached_result = self._user_validation_cache.get(cache_key)
                if cached_result and time.time() - cached_result['timestamp'] < 300:  # 5 min cache
                    return cached_result['is_valid']
            
            # Verify with database
            user = await self.cache._verify_cached_user(context.user_id)
            is_valid = user is not None and user.is_active
            
            # Cache result
            if not hasattr(self, '_user_validation_cache'):
                self._user_validation_cache = {}
            self._user_validation_cache[cache_key] = {
                'is_valid': is_valid,
                'timestamp': time.time()
            }
            
            if not is_valid:
                await self._log_security_event('failed_verification', {
                    'user_id': context.user_id,
                    'session_id': context.session_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying context user: {str(e)}")
            return False
    
    async def _detect_suspicious_activity(self, context: AuthenticationContext) -> bool:
        """Detect suspicious patterns in context usage"""
        try:
            # Check for rapid access patterns (potential bot/automated access)
            if context.access_count > 1000:  # More than 1000 accesses
                time_since_creation = (datetime.utcnow() - context.created_at).total_seconds()
                if time_since_creation < 3600:  # Within 1 hour
                    rate = context.access_count / (time_since_creation / 60)  # accesses per minute
                    if rate > 10:  # More than 10 accesses per minute
                        return True
            
            # Check for unusual access times (e.g., middle of night for business users)
            current_hour = datetime.utcnow().hour
            if context.user.role != 'ADMIN' and (current_hour < 6 or current_hour > 22):
                # This is just an example - adjust based on business requirements
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {str(e)}")
            return False
    
    async def _detect_session_anomalies(self, context: AuthenticationContext) -> bool:
        """Detect session anomalies that might indicate hijacking"""
        try:
            # Check if IP address changed suddenly (basic check)
            if hasattr(context, '_previous_ip') and context.ip_address:
                if context._previous_ip != context.ip_address:
                    # Allow some grace for legitimate IP changes (mobile users, etc.)
                    # More sophisticated geolocation checks could be implemented here
                    pass
            
            # Check session duration vs typical patterns
            session_duration = (datetime.utcnow() - context.created_at).total_seconds()
            if session_duration > 86400:  # More than 24 hours
                return True  # Unusually long session
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting session anomalies: {str(e)}")
            return False
    
    async def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events for monitoring and analysis"""
        try:
            if event_type in self.security_events:
                self.security_events[event_type].append(event_data)
                
                # Limit stored events to prevent memory growth
                if len(self.security_events[event_type]) > self.max_security_events:
                    self.security_events[event_type] = self.security_events[event_type][-self.max_security_events:]
                
                # Log to system logger
                logger.warning(f"Security event - {event_type}", extra=event_data)
                
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")


# Global instance
auth_context_manager: Optional[AuthenticationContextManager] = None


def get_auth_context_manager() -> AuthenticationContextManager:
    """Get the global authentication context manager"""
    global auth_context_manager
    if auth_context_manager is None:
        raise RuntimeError("Authentication context manager not initialized")
    return auth_context_manager


async def initialize_auth_context_manager(
    feature_flag_service: FeatureFlagService,
    redis_client: Optional[aioredis.Redis] = None
) -> AuthenticationContextManager:
    """Initialize the global authentication context manager"""
    global auth_context_manager
    if auth_context_manager is None:
        auth_context_manager = AuthenticationContextManager(
            feature_flag_service=feature_flag_service,
            redis_client=redis_client
        )
        logger.info("Global authentication context manager initialized")
    return auth_context_manager


def require_auth_context(
    module_id: Optional[str] = None,
    required_permissions: Optional[List[str]] = None
):
    """
    Decorator to require authentication context for module endpoints
    
    Args:
        module_id: Module identifier for access validation
        required_permissions: Required permissions list
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get auth context manager
            context_manager = get_auth_context_manager()
            
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'headers'):  # Likely a Request object
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context required"
                )
            
            # Get authentication header
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token required"
                )
            
            access_token = auth_header.split(" ")[1]
            
            # Get authentication context
            context = await context_manager.get_context(access_token=access_token)
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication context"
                )
            
            # Validate context for module access
            is_valid = await context_manager.validate_context(
                context, module_id, required_permissions
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this module"
                )
            
            # Add context to kwargs
            kwargs['auth_context'] = context
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator