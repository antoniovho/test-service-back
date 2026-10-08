"""Use case implementation: delete project."""

from test_service.domain.application.commands.projects import DeleteProjectCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCase,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class DeleteProjectUseCaseImpl(DeleteProjectUseCase):
    """Logically deletes one Project Catalog entry."""

    def __init__(
        self, project_repository: ProjectPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._project_repository = project_repository
        self._project_resolver = project_resolver

    async def execute(self, request: DeleteProjectCommand) -> Project:
        """Mark the project matching the requested key as deleted.

        Raises:
            EntityNotFoundException: If no project has the requested key.
            ProjectAlreadyDeletedException: If the project is already deleted.
        """
        project = await self._project_resolver.resolve(request.key)
        deleted_project = project.delete(
            deleted_at=request.requested_at, deleted_by=request.requested_by
        )
        return await self._project_repository.save(deleted_project)
