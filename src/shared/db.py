"""Database engine and session factory.

Provides an async SQLAlchemy engine and session factory backed by SQLite
(local dev) or Postgres (production), configured via ``shared.config``.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from shared.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""


def get_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine from the configured DATABASE_URL.

    Returns:
        AsyncEngine connected to the configured database.
    """
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False)


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory.

    Args:
        engine: Optional engine to bind. Uses default from config if None.

    Returns:
        Async session factory producing AsyncSession instances.
    """
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
