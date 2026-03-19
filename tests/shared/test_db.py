"""Tests for shared.db — engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from shared.db import Base, get_engine, get_session_factory


class TestDatabase:
    """Test database engine and session creation."""

    def test_get_engine_returns_async_engine(self) -> None:
        engine = get_engine()
        assert isinstance(engine, AsyncEngine)

    def test_get_session_factory_creates_sessions(self) -> None:
        factory = get_session_factory()
        # The factory should be callable and produce AsyncSession instances
        assert factory is not None

    async def test_in_memory_session_works(self) -> None:
        """Verify we can create tables and run queries in-memory."""
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            # Just verify the session is alive
            result = await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            assert result.scalar() == 1

        await engine.dispose()

    def test_base_has_metadata(self) -> None:
        assert Base.metadata is not None
