"""Environment persistence contract."""

from typing import Protocol
from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.environment import Environment


class EnvironmentPersistencePort(Protocol):
    """Persistence contract for execution environments."""

    async def save(self, environment: Environment) -> Environment:
        """Persist an environment."""
        ...

    async def find_by_id(self, identifier: UUID) -> Environment | None:
        """Find an environment by UUID."""
        ...

    async def find_by_key(self, environment_key: str) -> Environment | None:
        """Find an environment by its globally unique business key."""
        ...

    async def find_page(self, pagination: PaginationParams) -> Page[Environment]:
        """Find execution environments matching a page query."""
        ...
