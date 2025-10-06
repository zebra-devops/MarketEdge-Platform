from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator, Optional
import redis
import os
import sys
import threading
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Lazy initialization globals
_engine: Optional[object] = None
_async_engine: Optional[object] = None
_redis_client: Optional[redis.Redis] = None
_session_local: Optional[sessionmaker] = None
_async_session_local: Optional[async_sessionmaker] = None
_initialization_lock = threading.Lock()


def get_database_url() -> str:
    """Get appropriate database URL based on environment"""
    # Check if we're running tests using multiple indicators
    test_indicators = [
        os.getenv("PYTEST_CURRENT_TEST"),  # Set by pytest
        os.getenv("TESTING"),  # Custom environment variable
        "pytest" in os.getenv("_", "").lower(),  # Command line indicator
        any("pytest" in arg for arg in sys.argv),  # Command line args
    ]
    
    if any(test_indicators):
        return settings.get_test_database_url()
    
    # Use environment-aware database URL resolution
    return settings.get_database_url_for_environment()


def _initialize_database_engine():
    """Lazy initialization of database engine"""
    global _engine, _async_engine, _session_local, _async_session_local

    with _initialization_lock:
        if _engine is not None:
            return  # Already initialized

        try:
            logger.info("Initializing database engine with lazy loading...")
            database_url = get_database_url()

            # DIAGNOSTIC: Log the original DATABASE_URL scheme
            original_scheme = database_url.split('://')[0] if '://' in database_url else 'unknown'
            logger.info(f"[DATABASE-INIT] Starting database initialization, DATABASE_URL scheme: {original_scheme}")
            logger.info(f"Database URL scheme: {original_scheme}")

            _engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                echo=settings.DEBUG,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "platform_wrapper"
                }
            )

            # Transform to async driver (handles both postgresql:// and postgres:// schemes)
            async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            if async_database_url == database_url:  # No replacement happened
                async_database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

            # DIAGNOSTIC: Log the transformation to prove the fix is applied
            async_scheme = async_database_url.split('://')[0] if '://' in async_database_url else 'unknown'
            logger.info(f"[SCHEME-FIX] original={original_scheme} async={async_scheme}")
            logger.info(f"[SCHEME-FIX-DETAILS] Transformation applied: {original_scheme} -> {async_scheme}")

            logger.info(f"Async database URL scheme: {async_scheme}")

            _async_engine = create_async_engine(
                async_database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                echo=settings.DEBUG,
                connect_args={
                    "server_settings": {
                        "application_name": "platform_wrapper"
                    }
                }
            )
            
            _session_local = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            _async_session_local = async_sessionmaker(_async_engine, expire_on_commit=False)
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise


def _initialize_redis_client():
    """Lazy initialization of Redis client"""
    global _redis_client
    
    with _initialization_lock:
        if _redis_client is not None:
            return  # Already initialized
            
        try:
            logger.info("Initializing Redis client with lazy loading...")
            _redis_client = redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=settings.REDIS_CONNECTION_POOL_SIZE
            )
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise


# Lazy property accessors with backward compatibility
def get_engine():
    """Get database engine (lazy initialization)"""
    if _engine is None:
        _initialize_database_engine()
    return _engine


def get_async_engine():
    """Get async database engine (lazy initialization)"""
    if _async_engine is None:
        _initialize_database_engine()
    return _async_engine


def get_session_local():
    """Get session maker (lazy initialization)"""
    if _session_local is None:
        _initialize_database_engine()
    return _session_local


def get_async_session_local():
    """Get async session maker (lazy initialization)"""
    if _async_session_local is None:
        _initialize_database_engine()
    return _async_session_local


def get_redis_client():
    """Get Redis client (lazy initialization)"""
    if _redis_client is None:
        _initialize_redis_client()
    return _redis_client


# Backward compatibility - function-based access to avoid circular references
def engine():
    """Get database engine - function-based access to avoid property decorator race conditions"""
    return get_engine()


def async_engine():
    """Get async database engine - function-based access to avoid property decorator race conditions"""
    return get_async_engine()


def SessionLocal():
    """Get session maker - function-based access to avoid property decorator race conditions"""
    return get_session_local()


def AsyncSessionLocal():
    """Get async session maker - function-based access to avoid property decorator race conditions"""
    return get_async_session_local()


def redis_client():
    """Get Redis client - function-based access to avoid property decorator race conditions"""
    return get_redis_client()


# Create a class that provides lazy attribute access
class LazyDatabaseModule:
    """Module wrapper that provides lazy initialization for database objects"""
    
    def __init__(self, original_module):
        self._original_module = original_module
        
    def __getattr__(self, name):
        if name == 'engine':
            return get_engine()
        elif name == 'async_engine':
            return get_async_engine()
        elif name == 'SessionLocal':
            return get_session_local()
        elif name == 'AsyncSessionLocal':
            return get_async_session_local()
        elif name == 'redis_client':
            return get_redis_client()
        elif hasattr(self._original_module, name):
            return getattr(self._original_module, name)
        else:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_db() -> Generator[Session, None, None]:
    """Get database session with lazy initialization"""
    session_maker = get_session_local()
    db = session_maker()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with lazy initialization"""
    async_session_maker = get_async_session_local()
    async with async_session_maker() as session:
        yield session


def get_redis():
    """Get Redis client with lazy initialization"""
    return get_redis_client()


# Initialize lazy module for backward compatibility
_original_module = sys.modules[__name__]
sys.modules[__name__] = LazyDatabaseModule(_original_module)