"""Use case implementation: list execution results."""

from test_service.domain.application.queries.execution import ListExecutionResultsQuery
from test_service.domain.application.services.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import TestResult
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCase,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)


class ListExecutionResultsUseCaseImpl(ListExecutionResultsUseCase):
    """List immutable test results only after resolving the project-owned execution."""

    def __init__(
        self,
        execution_access_resolver: ExecutionAccessResolver,
        execution_results_repository: ExecutionResultsPersistencePort,
    ) -> None:
        self._execution_access_resolver = execution_access_resolver
        self._execution_results_repository = execution_results_repository

    async def execute(self, request: ListExecutionResultsQuery) -> Page[TestResult]:
        """Return a page of results owned by the requested execution."""
        await self._execution_access_resolver.resolve(request.project_key, request.execution_id)
        return await self._execution_results_repository.find_results_page(
            request.execution_id, request.pagination
        )
