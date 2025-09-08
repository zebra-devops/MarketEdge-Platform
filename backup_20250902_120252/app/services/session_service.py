"""
US-102: Session Persistence and Timeout Handling Service

Provides persistent session storage, timeout management, and session analytics
for the shared authentication context system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, select, and_, or_
from sqlalchemy.sql import func
from redis import asyncio as aioredis

from ..models.base import Base
from ..models.user import User
from ..core.database import get_db
from ..core.auth_context import AuthenticationContext

logger = logging.getLogger(__name__)


class SessionEvent(str, Enum):
    """Session lifecycle events"""
    CREATED = "created"
    ACCESSED = "accessed"
    REFRESHED = "refreshed"
    EXPIRED = "expired"
    TIMEOUT = "timeout"
    INVALIDATED = "invalidated"
    DESTROYED = "destroyed"


@dataclass
class SessionMetrics:
    """Session usage metrics"""
    session_id: str
    user_id: str
    created_at: datetime
    last_accessed_at: datetime
    access_count: int = 0
    modules_accessed: Set[str] = None
    total_duration_seconds: int = 0
    is_active: bool = True
    
    def __post_init__(self):
        if self.modules_accessed is None:
            self.modules_accessed = set()
    
    def update_access(self, module_id: Optional[str] = None):
        """Update access metrics"""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
        if module_id:
            self.modules_accessed.add(module_id)
        self.total_duration_seconds = int(
            (self.last_accessed_at - self.created_at).total_seconds()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "access_count": self.access_count,
            "modules_accessed": list(self.modules_accessed),
            "total_duration_seconds": self.total_duration_seconds,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetrics':
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed_at=datetime.fromisoformat(data["last_accessed_at"]),
            access_count=data.get("access_count", 0),
            modules_accessed=set(data.get("modules_accessed", [])),
            total_duration_seconds=data.get("total_duration_seconds", 0),
            is_active=data.get("is_active", True)
        )


class SessionStore(Base):
    """Database model for persistent session storage"""
    __tablename__ = "user_sessions"
    
    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    organisation_id = Column(String(255), nullable=False, index=True)
    
    # Session data
    context_data = Column(Text, nullable=False)  # JSON serialized AuthenticationContext
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Session management
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Session metrics
    access_count = Column(Integer, default=0, nullable=False)
    modules_accessed = Column(Text, nullable=True)  # JSON array of module IDs
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    invalidated_at = Column(DateTime(timezone=True), nullable=True)
    invalidation_reason = Column(String(100), nullable=True)


class SessionEventLog(Base):
    """Database model for session event logging"""
    __tablename__ = "session_events"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)
    event_data = Column(Text, nullable=True)  # JSON data
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    module_id = Column(String(255), nullable=True)


class SessionCache:
    """Redis-based session caching with fallback to memory"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from cache"""
        try:
            # Try Redis first
            if self.redis:
                cached_data = await self.redis.get(f"session:{session_id}")
                if cached_data:
                    return json.loads(cached_data)
            
            # Fallback to memory cache
            if session_id in self.memory_cache:
                timestamp = self.cache_timestamps.get(session_id, 0)
                if time.time() - timestamp < self.cache_ttl:
                    return self.memory_cache[session_id]
                else:
                    # Remove expired entry
                    del self.memory_cache[session_id]
                    if session_id in self.cache_timestamps:
                        del self.cache_timestamps[session_id]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session from cache: {str(e)}")
            return None
    
    async def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None):
        """Cache session data"""
        try:
            ttl = ttl or self.cache_ttl
            
            # Cache in Redis
            if self.redis:
                await self.redis.setex(
                    f"session:{session_id}",
                    ttl,
                    json.dumps(session_data, default=str)
                )
            
            # Cache in memory
            self.memory_cache[session_id] = session_data
            self.cache_timestamps[session_id] = time.time()
            
        except Exception as e:
            logger.error(f"Error caching session: {str(e)}")
    
    async def delete_session(self, session_id: str):
        """Remove session from cache"""
        try:
            # Remove from Redis
            if self.redis:
                await self.redis.delete(f"session:{session_id}")
            
            # Remove from memory cache
            if session_id in self.memory_cache:
                del self.memory_cache[session_id]
            if session_id in self.cache_timestamps:
                del self.cache_timestamps[session_id]
                
        except Exception as e:
            logger.error(f"Error deleting session from cache: {str(e)}")
    
    async def cleanup_expired(self):
        """Clean up expired memory cache entries"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.cache_timestamps.items()
                if current_time - timestamp > self.cache_ttl
            ]
            
            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                del self.cache_timestamps[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired session cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up session cache: {str(e)}")


class SessionService:
    """
    US-102: Session persistence and timeout handling service
    
    Features:
    - Persistent session storage in database
    - Redis caching for performance
    - Session timeout management
    - Session analytics and metrics
    - Event logging and auditing
    - Cleanup of expired sessions
    """
    
    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        session_timeout_minutes: int = 30,
        cleanup_interval_minutes: int = 5
    ):
        self.cache = SessionCache(redis_client)
        self.session_timeout_minutes = session_timeout_minutes
        self.cleanup_interval_minutes = cleanup_interval_minutes
        
        # Background task management
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Session metrics
        self.session_metrics: Dict[str, SessionMetrics] = {}
        
        logger.info("Session Service initialized")
    
    async def start(self):
        """Start background tasks"""
        if not self.is_running:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session Service background tasks started")
    
    async def stop(self):
        """Stop background tasks"""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Session Service stopped")
    
    async def create_session(
        self,
        auth_context: AuthenticationContext,
        session_timeout_hours: int = 8
    ) -> str:
        """
        Create a new persistent session
        
        Args:
            auth_context: Authentication context to persist
            session_timeout_hours: Session timeout in hours
            
        Returns:
            str: Session ID
        """
        try:
            async for db_session in get_db():
                try:
                    expires_at = datetime.utcnow() + timedelta(hours=session_timeout_hours)
                    
                    # Create database session record
                    session_store = SessionStore(
                        session_id=auth_context.session_id,
                        user_id=auth_context.user_id,
                        organisation_id=auth_context.organisation_id,
                        context_data=json.dumps(auth_context.to_dict(), default=str),
                        ip_address=auth_context.ip_address,
                        user_agent=auth_context.user_agent,
                        expires_at=expires_at,
                        modules_accessed=json.dumps([])
                    )
                    
                    db_session.add(session_store)
                    await db_session.commit()
                    
                    # Cache session data
                    await self.cache.set_session(
                        auth_context.session_id,
                        auth_context.to_dict()
                    )
                    
                    # Create session metrics
                    self.session_metrics[auth_context.session_id] = SessionMetrics(
                        session_id=auth_context.session_id,
                        user_id=auth_context.user_id,
                        created_at=auth_context.created_at,
                        last_accessed_at=auth_context.last_accessed_at
                    )
                    
                    # Log session creation event
                    await self._log_session_event(
                        session_id=auth_context.session_id,
                        user_id=auth_context.user_id,
                        event_type=SessionEvent.CREATED,
                        event_data={"expires_at": expires_at.isoformat()},
                        ip_address=auth_context.ip_address,
                        user_agent=auth_context.user_agent
                    )
                    
                    logger.info(f"Created persistent session {auth_context.session_id} for user {auth_context.user_id}")
                    return auth_context.session_id
                    
                except Exception as db_error:
                    logger.error(f"Database error creating session: {str(db_error)}")
                    await db_session.rollback()
                    raise
                finally:
                    break
                    
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str, load_user: bool = True) -> Optional[AuthenticationContext]:
        """
        Retrieve session from storage
        
        Args:
            session_id: Session identifier
            load_user: Whether to load user from database
            
        Returns:
            AuthenticationContext: Session context or None if not found/expired
        """
        try:
            # Try cache first
            cached_data = await self.cache.get_session(session_id)
            if cached_data:
                # Check if session is expired or timed out
                if await self._is_session_expired(cached_data):
                    await self.invalidate_session(session_id, "expired")
                    return None
                
                # Update access time
                cached_data["last_accessed_at"] = datetime.utcnow().isoformat()
                await self.cache.set_session(session_id, cached_data)
                
                # Convert to AuthenticationContext
                if load_user:
                    user = await self._load_user(cached_data["user_id"])
                    if not user or not user.is_active:
                        return None
                    return AuthenticationContext.from_dict(cached_data, user)
                else:
                    # Create minimal context without user
                    return AuthenticationContext.from_dict(cached_data, None)
            
            # Fallback to database
            return await self._get_session_from_db(session_id, load_user)
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None
    
    async def update_session(self, auth_context: AuthenticationContext):
        """
        Update session with new context data
        
        Args:
            auth_context: Updated authentication context
        """
        try:
            # Update cache
            await self.cache.set_session(auth_context.session_id, auth_context.to_dict())
            
            # Update session metrics
            if auth_context.session_id in self.session_metrics:
                metrics = self.session_metrics[auth_context.session_id]
                metrics.update_access(auth_context.last_module_accessed)
            
            # Update database asynchronously (don't wait)
            asyncio.create_task(self._update_session_in_db(auth_context))
            
            # Log access event
            await self._log_session_event(
                session_id=auth_context.session_id,
                user_id=auth_context.user_id,
                event_type=SessionEvent.ACCESSED,
                event_data={"module_id": auth_context.last_module_accessed},
                module_id=auth_context.last_module_accessed
            )
            
        except Exception as e:
            logger.error(f"Error updating session {auth_context.session_id}: {str(e)}")
    
    async def invalidate_session(self, session_id: str, reason: str = "manual"):
        """
        Invalidate a session
        
        Args:
            session_id: Session to invalidate
            reason: Reason for invalidation
        """
        try:
            # Remove from cache
            await self.cache.delete_session(session_id)
            
            # Update database
            async for db_session in get_db():
                try:
                    # Update session record
                    stmt = select(SessionStore).where(SessionStore.session_id == session_id)
                    result = await db_session.execute(stmt)
                    session_store = result.scalar_one_or_none()
                    
                    if session_store:
                        session_store.is_active = False
                        session_store.invalidated_at = datetime.utcnow()
                        session_store.invalidation_reason = reason
                        await db_session.commit()
                        
                        # Log invalidation event
                        await self._log_session_event(
                            session_id=session_id,
                            user_id=session_store.user_id,
                            event_type=SessionEvent.INVALIDATED,
                            event_data={"reason": reason}
                        )
                    
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error invalidating session: {str(db_error)}")
                    break
            
            # Remove from metrics
            if session_id in self.session_metrics:
                del self.session_metrics[session_id]
            
            logger.info(f"Invalidated session {session_id}, reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error invalidating session {session_id}: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            async for db_session in get_db():
                try:
                    # Find expired sessions
                    stmt = select(SessionStore).where(
                        and_(
                            SessionStore.is_active == True,
                            or_(
                                SessionStore.expires_at < current_time,
                                SessionStore.last_accessed_at < (
                                    current_time - timedelta(minutes=self.session_timeout_minutes)
                                )
                            )
                        )
                    )
                    
                    result = await db_session.execute(stmt)
                    expired_sessions = result.scalars().all()
                    
                    for session in expired_sessions:
                        # Determine expiration reason
                        if session.expires_at < current_time:
                            reason = "expired"
                        else:
                            reason = "timeout"
                        
                        # Mark as inactive
                        session.is_active = False
                        session.invalidated_at = current_time
                        session.invalidation_reason = reason
                        
                        # Remove from cache
                        await self.cache.delete_session(session.session_id)
                        
                        # Log event
                        await self._log_session_event(
                            session_id=session.session_id,
                            user_id=session.user_id,
                            event_type=SessionEvent.EXPIRED if reason == "expired" else SessionEvent.TIMEOUT,
                            event_data={"cleanup_time": current_time.isoformat()}
                        )
                        
                        cleaned_count += 1
                    
                    if expired_sessions:
                        await db_session.commit()
                    
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error during session cleanup: {str(db_error)}")
                    break
            
            # Clean up memory cache
            await self.cache.cleanup_expired()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            return 0
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(SessionStore).where(
                        and_(
                            SessionStore.user_id == user_id,
                            SessionStore.is_active == True
                        )
                    ).order_by(SessionStore.last_accessed_at.desc())
                    
                    result = await db_session.execute(stmt)
                    sessions = result.scalars().all()
                    
                    session_list = []
                    for session in sessions:
                        session_data = {
                            "session_id": session.session_id,
                            "created_at": session.created_at.isoformat(),
                            "last_accessed_at": session.last_accessed_at.isoformat(),
                            "expires_at": session.expires_at.isoformat(),
                            "access_count": session.access_count,
                            "ip_address": session.ip_address,
                            "user_agent": session.user_agent,
                            "modules_accessed": json.loads(session.modules_accessed or "[]")
                        }
                        session_list.append(session_data)
                    
                    return session_list
                    
                except Exception as db_error:
                    logger.error(f"Database error getting user sessions: {str(db_error)}")
                    break
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    async def get_session_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get session analytics for the specified period"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            async for db_session in get_db():
                try:
                    # Get session stats
                    sessions_stmt = select(SessionStore).where(
                        SessionStore.created_at >= start_date
                    )
                    result = await db_session.execute(sessions_stmt)
                    sessions = result.scalars().all()
                    
                    # Calculate analytics
                    total_sessions = len(sessions)
                    active_sessions = sum(1 for s in sessions if s.is_active)
                    unique_users = len(set(s.user_id for s in sessions))
                    
                    # Average session duration
                    durations = []
                    for session in sessions:
                        if not session.is_active and session.invalidated_at:
                            duration = (session.invalidated_at - session.created_at).total_seconds()
                            durations.append(duration)
                    
                    avg_duration = sum(durations) / len(durations) if durations else 0
                    
                    return {
                        "period": {"start": start_date.isoformat(), "end": datetime.utcnow().isoformat(), "days": days},
                        "total_sessions": total_sessions,
                        "active_sessions": active_sessions,
                        "expired_sessions": total_sessions - active_sessions,
                        "unique_users": unique_users,
                        "average_session_duration_seconds": avg_duration,
                        "average_session_duration_minutes": avg_duration / 60
                    }
                    
                except Exception as db_error:
                    logger.error(f"Database error getting session analytics: {str(db_error)}")
                    break
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {str(e)}")
            return {}
    
    # Private helper methods
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
                if self.is_running:
                    await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """Check if session data indicates expiration"""
        try:
            expires_at = datetime.fromisoformat(session_data["session_expires_at"])
            last_accessed = datetime.fromisoformat(session_data["last_accessed_at"])
            
            now = datetime.utcnow()
            timeout_threshold = last_accessed + timedelta(minutes=self.session_timeout_minutes)
            
            return now > expires_at or now > timeout_threshold
            
        except Exception:
            return True  # Assume expired if can't parse
    
    async def _get_session_from_db(self, session_id: str, load_user: bool) -> Optional[AuthenticationContext]:
        """Get session from database"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(SessionStore).where(
                        and_(
                            SessionStore.session_id == session_id,
                            SessionStore.is_active == True
                        )
                    )
                    result = await db_session.execute(stmt)
                    session_store = result.scalar_one_or_none()
                    
                    if not session_store:
                        return None
                    
                    # Check expiration
                    now = datetime.utcnow()
                    if (now > session_store.expires_at or 
                        now > session_store.last_accessed_at + timedelta(minutes=self.session_timeout_minutes)):
                        await self.invalidate_session(session_id, "expired")
                        return None
                    
                    # Parse context data
                    context_data = json.loads(session_store.context_data)
                    
                    # Update access time
                    session_store.last_accessed_at = now
                    session_store.access_count += 1
                    await db_session.commit()
                    
                    # Load user if requested
                    user = None
                    if load_user:
                        user = await self._load_user(session_store.user_id)
                        if not user or not user.is_active:
                            return None
                    
                    # Create context
                    auth_context = AuthenticationContext.from_dict(context_data, user)
                    auth_context.last_accessed_at = now
                    
                    # Cache for future requests
                    await self.cache.set_session(session_id, auth_context.to_dict())
                    
                    return auth_context
                    
                except Exception as db_error:
                    logger.error(f"Database error getting session from DB: {str(db_error)}")
                    break
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session from database: {str(e)}")
            return None
    
    async def _update_session_in_db(self, auth_context: AuthenticationContext):
        """Update session in database (async task)"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(SessionStore).where(SessionStore.session_id == auth_context.session_id)
                    result = await db_session.execute(stmt)
                    session_store = result.scalar_one_or_none()
                    
                    if session_store:
                        session_store.context_data = json.dumps(auth_context.to_dict(), default=str)
                        session_store.last_accessed_at = auth_context.last_accessed_at
                        session_store.access_count += 1
                        
                        # Update modules accessed
                        modules = list(auth_context.module_contexts.keys())
                        session_store.modules_accessed = json.dumps(modules)
                        
                        await db_session.commit()
                    
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error updating session: {str(db_error)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error updating session in database: {str(e)}")
    
    async def _load_user(self, user_id: str) -> Optional[User]:
        """Load user from database"""
        try:
            async for db_session in get_db():
                try:
                    stmt = select(User).where(User.id == user_id)
                    result = await db_session.execute(stmt)
                    user = result.scalar_one_or_none()
                    return user
                except Exception as db_error:
                    logger.error(f"Database error loading user: {str(db_error)}")
                    break
            return None
        except Exception as e:
            logger.error(f"Error loading user: {str(e)}")
            return None
    
    async def _log_session_event(
        self,
        session_id: str,
        user_id: str,
        event_type: SessionEvent,
        event_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        module_id: Optional[str] = None
    ):
        """Log session event to database"""
        try:
            async for db_session in get_db():
                try:
                    event_log = SessionEventLog(
                        session_id=session_id,
                        user_id=user_id,
                        event_type=event_type.value,
                        event_data=json.dumps(event_data or {}, default=str),
                        ip_address=ip_address,
                        user_agent=user_agent,
                        module_id=module_id
                    )
                    
                    db_session.add(event_log)
                    await db_session.commit()
                    break
                    
                except Exception as db_error:
                    logger.error(f"Database error logging session event: {str(db_error)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error logging session event: {str(e)}")


# Global instance
session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Get the global session service instance"""
    global session_service
    if session_service is None:
        raise RuntimeError("Session service not initialized")
    return session_service


async def initialize_session_service(
    redis_client: Optional[aioredis.Redis] = None,
    session_timeout_minutes: int = 30
) -> SessionService:
    """Initialize the global session service"""
    global session_service
    if session_service is None:
        session_service = SessionService(
            redis_client=redis_client,
            session_timeout_minutes=session_timeout_minutes
        )
        await session_service.start()
        logger.info("Global session service initialized")
    return session_service