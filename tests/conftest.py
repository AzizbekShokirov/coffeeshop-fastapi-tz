"""
Pytest configuration and shared fixtures.

This module provides:
- Database session fixtures
- HTTP client fixtures
- Common test utilities
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.database import Base, get_db
from src.main import app

# Test database URL (use a separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/coffeeshop_db", "/coffeeshop_test_db")

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Disable pooling for tests
)

# Create async session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    This fixture:
    1. Creates all tables before the test
    2. Provides a clean database session
    3. Commits data during the test (mimics production behavior)
    4. Drops all tables after the test

    Note: We commit during tests to match production behavior where
    get_db() dependency commits after successful operations.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        try:
            yield session
            # Commit any pending changes (mimics production get_db behavior)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing.

    This fixture overrides the database dependency to use the test database.
    The overridden dependency mimics production behavior by committing on success.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """
        Override get_db to use test session.
        Mimics production behavior: commit on success, rollback on error.
        """
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
