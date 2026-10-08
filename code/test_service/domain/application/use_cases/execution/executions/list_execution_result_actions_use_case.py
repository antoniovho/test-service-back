"""Use case implementation: list action results."""

from test_service.domain.application.queries.execution import ListExecutionResultActionsQuery
from test_service.domain.application.services.resolvers.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.resolvers.execution_result_access_resolver import (
    ExecutionResultAccessResolver,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import ActionResult
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCase,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)


class ListExecutionResultActionsUseCaseImpl(ListExecutionResultActionsUseCase):
    """List action results only through their project-owned result."""

    def __init__(
        self,
        execution_access_resolver: ExecutionAccessResolver,
        execution_result_access_resolver: ExecutionResultAccessResolver,
        execution_results_repository: ExecutionResultsPersistencePort,
    ) -> None:
        self._execution_access_resolver = execution_access_resolver
        self._execution_result_access_resolver = execution_result_access_resolver
        self._execution_results_repository = execution_results_repository

    async def execute(self, request: ListExecutionResultActionsQuery) -> Page[ActionResult]:
        """Return a page of action results after checking the ownership chain."""
        await self._execution_access_resolver.resolve(request.project_key, request.execution_id)
        await self._execution_result_access_resolver.resolve(
            request.execution_id, request.test_result_id
        )
        return await self._execution_results_repository.find_actions_page(
            request.test_result_id, request.pagination
        )
