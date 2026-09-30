"""Use case implementation: get project."""

from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)


class GetProjectUseCaseImpl(GetProjectUseCase):
    """Retrieves one Project Catalog entry by key."""

    def __init__(self, project_resolver: ProjectResolver) -> None:
        self._project_resolver = project_resolver

    async def execute(self, request: GetProjectQuery) -> Project:
        """Return the project matching the requested key.

        Raises:
            EntityNotFoundException: If no project has the requested key.
        """
        return await self._project_resolver.resolve(request.key)
