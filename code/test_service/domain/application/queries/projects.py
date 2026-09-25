"""Queries for Project Catalog use cases."""

from dataclasses import dataclass

from test_service.domain.commons.pagination import PaginationParams


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
    """

    pagination: PaginationParams
