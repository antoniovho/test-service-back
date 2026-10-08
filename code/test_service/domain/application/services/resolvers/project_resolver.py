"""Resolution of existing Project Catalog entries."""

from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.project_already_deleted_exception import (
    ProjectAlreadyDeletedException,
)
from test_service.domain.model.projects.project import Project, ProjectStatus
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)


class ProjectResolver:
    """Resolve projects while enforcing their existence."""

    def __init__(self, project_repository: ProjectPersistencePort) -> None:
        self._project_repository = project_repository

    async def resolve(self, project_key: str) -> Project:
        """Return the project identified by ``project_key``.

        Raises:
            EntityNotFoundException: If no project exists for the key.
        """
        project = await self._project_repository.find_by_key(project_key)
        if project is None:
            raise EntityNotFoundException("project", project_key)
        return project

    async def resolve_active(self, project_key: str) -> Project:
        """Return an active project suitable for creating new resources.

        Raises:
            EntityNotFoundException: If no project exists for the key.
            ProjectAlreadyDeletedException: If the project is logically deleted.
        """
        project = await self.resolve(project_key)
        if project.status is ProjectStatus.DELETED:
            raise ProjectAlreadyDeletedException("project is already deleted")
        return project
