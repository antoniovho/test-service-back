"""Queries for Project Catalog use cases."""

from dataclasses import dataclass

from test_service.domain.application.queries.pagination import PaginationParams
from test_service.domain.model.projects.project import ProjectStatus


@dataclass(frozen=True, slots=True)
class GetProjectQuery:
    """Request to retrieve one project.

    Args:
        key: Stable project key.
    """

    key: str


@dataclass(frozen=True, slots=True)
class ListProjectsQuery:
    """Request to list projects.

    Args:
        pagination: Page and ordering parameters.
        status: Optional lifecycle status to filter by. When omitted, all states are returned.
    """

    pagination: PaginationParams
    status: ProjectStatus | None = None
