"""Use case implementation: list projects."""

from test_service.domain.application.queries.projects import ListProjectsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCase,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class ListProjectsUseCaseImpl(ListProjectsUseCase):
    """Lists Project Catalog entries."""

    def __init__(self, project_repository: ProjectPersistencePort) -> None:
        self._project_repository = project_repository

    async def execute(self, request: ListProjectsQuery) -> Page[Project]:
        """Return a page of projects matching the requested pagination."""
        return await self._project_repository.find_page(request.pagination)
