"""SQLAlchemy engine and session factory configuration."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from test_service.config import PostgresDatabaseSettings


class PostgresDatabaseConfiguration:
    """Own the process-wide async database engine and session factory."""

    def __init__(self, settings: PostgresDatabaseSettings) -> None:
        self._engine: AsyncEngine = create_async_engine(
            settings.connection_url,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Return the configured factory for short-lived async sessions."""
        return self._session_factory

    async def dispose(self) -> None:
        """Close all pooled database connections."""
        await self._engine.dispose()
