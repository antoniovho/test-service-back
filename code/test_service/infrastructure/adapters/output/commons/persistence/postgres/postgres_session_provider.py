"""PostgreSQL session provider for persistence repositories."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_database_configuration import (  # noqa: E501
    PostgresDatabaseConfiguration,
)


class PostgresSessionProvider:
    """Open a distinct database session for every repository operation."""

    def __init__(self, database_configuration: PostgresDatabaseConfiguration) -> None:
        self._session_factory: async_sessionmaker[AsyncSession] = (
            database_configuration.session_factory
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Yield a session that is closed when the operation completes."""
        async with self._session_factory() as session:
            yield session
