from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings

_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None

_sync_engine = None
_sync_session_factory = None


def get_async_engine() -> AsyncEngine:
    """Returns or initializes the singleton SQLAlchemy async engine."""
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            echo=settings.DEBUG and settings.ENVIRONMENT == "development",
        )
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Returns or initializes the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine()
        _async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an isolated async database session."""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_engine():
    """Returns or initializes the singleton SQLAlchemy sync engine."""
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        _sync_engine = create_engine(
            settings.DATABASE_SYNC_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            echo=False,
        )
    return _sync_engine


def get_sync_session_factory() -> sessionmaker[Session]:
    """Returns or initializes the sync session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sync_session_factory


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Context manager yielding a synchronous database session (for Celery workers)."""
    factory = get_sync_session_factory()
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


async def check_database_health() -> bool:
    """Performs a lightweight SELECT 1 check to verify database connectivity."""
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False
