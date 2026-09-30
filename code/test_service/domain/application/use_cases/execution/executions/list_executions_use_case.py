"""Use case implementation: list executions."""

from test_service.domain.application.queries.execution import ListExecutionsQuery
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)


class ListExecutionsUseCaseImpl(ListExecutionsUseCase):
    """Lists executions for an existing project."""

    def __init__(
        self,
        execution_repository: ExecutionPersistencePort,
        project_resolver: ProjectResolver,
    ) -> None:
        self._execution_repository = execution_repository
        self._project_resolver = project_resolver

    async def execute(self, request: ListExecutionsQuery) -> Page[Execution]:
        """Return the requested page after validating project existence."""
        await self._project_resolver.resolve(request.project_key)
        return await self._execution_repository.find_page(request.project_key, request.pagination)
