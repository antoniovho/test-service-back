"""Projects persistence contract."""

from typing import Protocol

from test_service.domain.application.queries.pagination import Page, PaginationParams
from test_service.domain.model.projects.project import Project, ProjectStatus


class ProjectPersistencePort(Protocol):
    """Persistence contract for Project Catalog entries."""

    async def save(self, project: Project) -> Project:
        """Persist a project."""
        ...

    async def find_by_key(self, key: str) -> Project | None:
        """Find a project by its stable key."""
        ...

    async def find_page(
        self, pagination: PaginationParams, status: ProjectStatus | None = None
    ) -> Page[Project]:
        """Find a page of projects, optionally filtered by lifecycle status."""
        ...
