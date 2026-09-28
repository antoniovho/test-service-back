"""Use case implementation: delete project."""

from test_service.domain.application.commands.projects import DeleteProjectCommand
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCase,
)
from test_service.domain.ports.output.repositories import ProjectRepositoryPort


class DeleteProjectUseCaseImpl(DeleteProjectUseCase):
    """Logically deletes one Project Catalog entry."""

    def __init__(self, project_repository: ProjectRepositoryPort) -> None:
        self._project_repository = project_repository

    async def execute(self, request: DeleteProjectCommand) -> Project:
        """Mark the project matching the requested key as deleted.

        Raises:
            EntityNotFoundException: If no project has the requested key.
            ProjectAlreadyDeletedException: If the project is already deleted.
        """
        project = await self._project_repository.find_by_key(request.key)
        if project is None:
            raise EntityNotFoundException("project", request.key)
        deleted_project = project.delete(
            deleted_at=request.requested_at, deleted_by=request.requested_by
        )
        return await self._project_repository.save(deleted_project)
