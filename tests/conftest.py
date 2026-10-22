import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import Settings, get_settings
from src.core.database import get_async_session
from src.main import create_app
from src.models import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def override_settings() -> Settings:
    """Provides test-specific settings."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DATABASE_SYNC_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",
    )


@pytest.fixture
async def test_engine(override_settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """Initializes an in-memory SQLite database engine with all tables created."""
    engine = create_async_engine(
        override_settings.DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yields a transactional database session for tests."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(
    override_settings: Settings, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTPX AsyncClient with overridden database session dependency."""
    app = create_app()

    async def _get_test_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = _get_test_session
    app.dependency_overrides[get_settings] = lambda: override_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
