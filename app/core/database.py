from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
import redis
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
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

async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
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