"""Use case implementation: list executions."""

from test_service.domain.application.queries.execution import ListExecutionsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.execution import Execution
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class ListExecutionsUseCaseImpl(ListExecutionsUseCase):
    """Lists executions for an existing project."""

    def __init__(
        self,
        execution_repository: ExecutionPersistencePort,
        project_repository: ProjectPersistencePort,
    ) -> None:
        self._execution_repository = execution_repository
        self._project_repository = project_repository

    async def execute(self, request: ListExecutionsQuery) -> Page[Execution]:
        """Return the requested page after validating project existence."""
        project = await self._project_repository.find_by_key(request.project_key)
        if project is None:
            raise EntityNotFoundException("project", request.project_key)
        return await self._execution_repository.find_page(request.project_key, request.pagination)
