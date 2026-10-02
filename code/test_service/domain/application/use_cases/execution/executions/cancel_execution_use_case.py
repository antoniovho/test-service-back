"""Use case implementation: cancel execution."""

from test_service.domain.application.commands.execution import CancelExecutionCommand
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCase,
)
from test_service.domain.ports.output.executions.execution_cancellation_port import (
    ExecutionCancellationPort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)


class CancelExecutionUseCaseImpl(CancelExecutionUseCase):
    """Cancels an execution only within its owning project."""

    def __init__(
        self,
        execution_repository: ExecutionPersistencePort,
        cancellation: ExecutionCancellationPort,
    ) -> None:
        self._execution_repository = execution_repository
        self._cancellation = cancellation

    async def execute(self, request: CancelExecutionCommand) -> Execution:
        """Persist the execution's cancellation state."""
        execution = await self._execution_repository.find_execution(request.identifier)
        if execution is None or execution.project_key != request.project_key:
            raise EntityNotFoundException(
                "execution", str(request.identifier), f"project '{request.project_key}'"
            )
        cancelled = await self._execution_repository.save_execution(execution.cancel())
        self._cancellation.request_cancellation(request.identifier)
        return cancelled
