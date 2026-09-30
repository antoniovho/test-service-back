"""Execution persistence contract."""

from typing import Protocol
from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import Execution


class ExecutionPersistencePort(Protocol):
    """Persistence contract for executions and their immutable history."""

    async def save_execution(self, execution: Execution) -> Execution:
        """Persist an execution."""
        ...

    async def find_execution(self, identifier: UUID) -> Execution | None:
        """Find an execution by UUID."""
        ...

    async def find_page(self, project_key: str, pagination: PaginationParams) -> Page[Execution]:
        """Find executions owned by one project."""
        ...
