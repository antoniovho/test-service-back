"""Use case implementation: restore project."""

from test_service.domain.application.commands.projects import RestoreProjectCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.input.use_cases.projects.restore_project_use_case import (
    RestoreProjectUseCase,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.domain.ports.output.projects.project_validation_port import ProjectValidationPort


class RestoreProjectUseCaseImpl(RestoreProjectUseCase):
    """Restores a deleted Project Catalog entry after validating Jira access."""

    def __init__(
        self,
        project_repository: ProjectPersistencePort,
        project_resolver: ProjectResolver,
        project_validation: ProjectValidationPort,
    ) -> None:
        self._project_repository = project_repository
        self._project_resolver = project_resolver
        self._project_validation = project_validation

    async def execute(self, request: RestoreProjectCommand) -> Project:
        """Restore a deleted project if its Jira project remains accessible."""
        project = await self._project_resolver.resolve(request.key)
        restored_project = project.restore()
        await self._project_validation.validate(restored_project.key)
        return await self._project_repository.save(restored_project)
