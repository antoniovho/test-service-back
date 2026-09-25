"""Queries for Viewer integration use cases."""

from dataclasses import dataclass

from test_service.domain.commons.pagination import PaginationParams


@dataclass(frozen=True, slots=True)
class ListViewerSyncRecordsQuery:
    """Request to list Viewer synchronization records across all projects.

    Args:
        pagination: Page and ordering parameters.
    """

    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListProjectViewerSyncRecordsQuery:
    """Request to list Viewer synchronization records for one project.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
    """

    project_key: str
    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListViewerDriftEventsQuery:
    """Request to list Viewer drift events across all projects.

    Args:
        pagination: Page and ordering parameters.
    """

    pagination: PaginationParams


@dataclass(frozen=True, slots=True)
class ListProjectViewerDriftEventsQuery:
    """Request to list Viewer drift events for one project.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
    """

    project_key: str
    pagination: PaginationParams
