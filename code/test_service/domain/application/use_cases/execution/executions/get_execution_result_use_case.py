"""Use case implementation: get an execution result."""

from test_service.domain.application.queries.execution import ExecutionResultQuery
from test_service.domain.application.services.resolvers.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.resolvers.execution_result_access_resolver import (
    ExecutionResultAccessResolver,
)
from test_service.domain.model.execution.execution import TestResult
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCase,
)


class GetExecutionResultUseCaseImpl(GetExecutionResultUseCase):
    """Retrieve a result only through its project-owned execution."""

    def __init__(
        self,
        execution_access_resolver: ExecutionAccessResolver,
        execution_result_access_resolver: ExecutionResultAccessResolver,
    ) -> None:
        self._execution_access_resolver = execution_access_resolver
        self._execution_result_access_resolver = execution_result_access_resolver

    async def execute(self, request: ExecutionResultQuery) -> TestResult:
        """Return the requested result after checking its complete ownership chain."""
        await self._execution_access_resolver.resolve(request.project_key, request.execution_id)
        return await self._execution_result_access_resolver.resolve(
            request.execution_id, request.test_result_id
        )
