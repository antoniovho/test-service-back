"""Use case implementation: get project."""

from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class GetProjectUseCaseImpl(GetProjectUseCase):
    """Retrieves one Project Catalog entry by key."""

    def __init__(self, project_repository: ProjectPersistencePort) -> None:
        self._project_repository = project_repository

    async def execute(self, request: GetProjectQuery) -> Project:
        """Return the project matching the requested key.

        Raises:
            EntityNotFoundException: If no project has the requested key.
        """
        project = await self._project_repository.find_by_key(request.key)
        if project is None:
            raise EntityNotFoundException("project", request.key)
        return project
