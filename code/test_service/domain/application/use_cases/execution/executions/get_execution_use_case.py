"""Use case implementation: get execution."""

from test_service.domain.application.queries.execution import ExecutionQuery
from test_service.domain.application.services.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_use_case import (
    GetExecutionUseCase,
)


class GetExecutionUseCaseImpl(GetExecutionUseCase):
    """Retrieves one execution only within its owning project."""

    def __init__(self, execution_access_resolver: ExecutionAccessResolver) -> None:
        self._execution_access_resolver = execution_access_resolver

    async def execute(self, request: ExecutionQuery) -> Execution:
        """Return an execution if it belongs to the requested project."""
        return await self._execution_access_resolver.resolve(
            request.project_key, request.identifier
        )
