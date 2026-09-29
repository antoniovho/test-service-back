"""Use case implementation: create project."""

from test_service.domain.application.commands.projects import CreateProjectCommand
from test_service.domain.model.exceptions.project_already_exists_exception import (
    ProjectAlreadyExistsException,
)
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.create_project_use_case import (
    CreateProjectUseCase,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class CreateProjectUseCaseImpl(CreateProjectUseCase):
    """Registers a new Project Catalog entry."""

    def __init__(self, project_repository: ProjectPersistencePort) -> None:
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
