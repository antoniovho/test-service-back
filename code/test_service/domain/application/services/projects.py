"""Application services implementing the Project Catalog use cases."""

from test_service.domain.application.commands.projects import (
    CreateProjectCommand,
    DeleteProjectCommand,
)
from test_service.domain.application.queries.projects import GetProjectQuery, ListProjectsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.exceptions.entity_not_found_exception import (
    EntityNotFoundException,
)
from test_service.domain.model.exceptions.project_already_exists_exception import (
    ProjectAlreadyExistsException,
)
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.output.repositories import ProjectRepositoryPort


class ListProjectsUseCaseImpl:
    """Lists Project Catalog entries."""

    def __init__(self, project_repository: ProjectRepositoryPort) -> None:
        self._project_repository = project_repository

    async def execute(self, request: ListProjectsQuery) -> Page[Project]:
        """Return a page of projects matching the requested pagination."""
        return await self._project_repository.find_page(request.pagination)


class CreateProjectUseCaseImpl:
    """Registers a new Project Catalog entry."""

    def __init__(self, project_repository: ProjectRepositoryPort) -> None:
        self._project_repository = project_repository

    async def execute(self, request: CreateProjectCommand) -> Project:
        """Register a project, rejecting keys already present in the catalog.

        Raises:
            ProjectAlreadyExistsException: If a project with the same key already exists.
        """
        existing = await self._project_repository.find_by_key(request.key)
        if existing is not None:
            raise ProjectAlreadyExistsException(f"project with key '{request.key}' already exists")
        project = Project(
            key=request.key,
            name=request.name,
            created_at=request.requested_at,
            created_by=request.requested_by,
        )
        return await self._project_repository.save(project)


class GetProjectUseCaseImpl:
    """Retrieves one Project Catalog entry by key."""

    def __init__(self, project_repository: ProjectRepositoryPort) -> None:
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


class DeleteProjectUseCaseImpl:
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
