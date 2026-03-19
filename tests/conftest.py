"""Shared test fixtures.

Provides database sessions with rollback, mock API responses,
and configuration overrides for testing.
"""

from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import get_settings
from shared.db import Base


@pytest.fixture()
def settings() -> Generator[None]:
    """Clear the settings cache so each test gets a fresh config."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Provide an in-memory SQLite session that rolls back after each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
