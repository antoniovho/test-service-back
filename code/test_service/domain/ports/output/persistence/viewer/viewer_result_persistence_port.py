"""Durable persistence contract for external execution-result publication."""

from typing import Protocol
from uuid import UUID

from test_service.domain.model.execution.execution import Execution, ExecutionStatus
from test_service.domain.model.viewer.execution_results import ViewerResultPublication
from test_service.domain.model.viewer.records import ViewerType


class ViewerResultPersistencePort(Protocol):
    """Persist and claim external execution-result publication work."""

    async def enqueue_result_publication(
        self, execution: Execution, viewer_type: ViewerType
    ) -> ViewerResultPublication:
        """Create or return the unique durable publication for an execution."""
        ...

    async def transition_execution_and_enqueue_result_publication(
        self,
        execution: Execution,
        expected_statuses: tuple[ExecutionStatus, ...],
        viewer_type: ViewerType,
    ) -> Execution | None:
        """Atomically persist a terminal execution and its unique publication work."""
        ...

    async def claim_next_result_publication(self) -> ViewerResultPublication | None:
        """Atomically claim the oldest result publication that is due."""
        ...

    async def save_result_publication(
        self, publication: ViewerResultPublication
    ) -> ViewerResultPublication:
        """Persist a publication state transition."""
        ...

    async def find_result_publication(
        self, execution_id: UUID, viewer_type: ViewerType
    ) -> ViewerResultPublication | None:
        """Find the durable publication for one execution and viewer."""
        ...
