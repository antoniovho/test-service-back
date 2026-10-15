"""Execution persistence contract."""

from typing import Protocol
from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import Execution, ExecutionStatus


class ExecutionPersistencePort(Protocol):
    """Persistence contract for executions and their immutable history."""

    async def save_execution(self, execution: Execution) -> Execution:
        """Persist an execution."""
        ...

    async def transition_execution(
        self, execution: Execution, expected_statuses: tuple[ExecutionStatus, ...]
    ) -> Execution | None:
        """Persist a lifecycle transition only if its current status is expected.

        Returns the persisted execution, including the current state when the
        transition loses a race, or ``None`` if the execution no longer exists.
        """
        ...

    async def find_execution(self, identifier: UUID) -> Execution | None:
        """Find an execution by UUID."""
        ...

    async def claim_next_created(self) -> Execution | None:
        """Atomically claim the oldest execution waiting for a runner."""
        ...

    async def mark_stale_running_as_error(self) -> int:
        """Mark RUNNING executions abandoned by a worker as ERROR and return their count."""
        ...

    async def find_page(self, project_key: str, pagination: PaginationParams) -> Page[Execution]:
        """Find executions owned by one project."""
        ...
