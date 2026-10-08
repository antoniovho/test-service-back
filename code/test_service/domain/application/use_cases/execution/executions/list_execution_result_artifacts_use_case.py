"""Use case implementation: list result artifacts."""

from test_service.domain.application.queries.execution import ListExecutionResultArtifactsQuery
from test_service.domain.application.services.resolvers.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.resolvers.execution_result_access_resolver import (
    ExecutionResultAccessResolver,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import TestResultArtifact
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCase,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)


class ListExecutionResultArtifactsUseCaseImpl(ListExecutionResultArtifactsUseCase):
    """List evidence metadata only through its project-owned result."""

    def __init__(
        self,
        execution_access_resolver: ExecutionAccessResolver,
        execution_result_access_resolver: ExecutionResultAccessResolver,
        execution_results_repository: ExecutionResultsPersistencePort,
    ) -> None:
        self._execution_access_resolver = execution_access_resolver
        self._execution_result_access_resolver = execution_result_access_resolver
        self._execution_results_repository = execution_results_repository

    async def execute(self, request: ListExecutionResultArtifactsQuery) -> Page[TestResultArtifact]:
        """Return a page of artifact metadata after checking the ownership chain."""
        await self._execution_access_resolver.resolve(request.project_key, request.execution_id)
        await self._execution_result_access_resolver.resolve(
            request.execution_id, request.test_result_id
        )
        return await self._execution_results_repository.find_artifacts_page(
            request.test_result_id, request.pagination
        )
