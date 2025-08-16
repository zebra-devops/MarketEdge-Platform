from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
import redis
import os
import sys
from .config import settings

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

database_url = get_database_url()

engine = create_engine(
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

async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
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

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

redis_client = redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
    max_connections=settings.REDIS_CONNECTION_POOL_SIZE
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_redis():
    return redis_client