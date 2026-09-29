"""Projects domain persistence adapter."""

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.projects.project import Project
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.infrastructure.adapters.output.projects.persistence.mappers.project_persistence_mapper import (  # noqa: E501
    ProjectPersistenceMapper,
)
from test_service.infrastructure.adapters.output.projects.persistence.repositories.project_repository import (  # noqa: E501
    ProjectRepository,
)


class ProjectPersistenceAdapter(ProjectPersistencePort):
    """Adapt Projects domain objects to persistence DTO operations."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    async def save(self, project: Project) -> Project:
        """Persist a Project aggregate."""
        persisted_project = await self._repository.save(ProjectPersistenceMapper.to_dto(project))
        return ProjectPersistenceMapper.to_domain(persisted_project)

    async def find_by_key(self, key: str) -> Project | None:
        """Find a Project aggregate by its stable key."""
        project = await self._repository.find_by_key(key)
        return ProjectPersistenceMapper.to_domain(project) if project is not None else None

    async def find_page(self, pagination: PaginationParams) -> Page[Project]:
        """Find a page of Project aggregates."""
        page = await self._repository.find_page(pagination)
        return Page(
            items=tuple(ProjectPersistenceMapper.to_domain(project) for project in page.items),
            total=page.total,
        )
