"""Queries for Viewer integration use cases."""

from dataclasses import dataclass

from test_service.domain.commons.pagination import PaginationParams
from test_service.domain.model.viewer.records import ViewerType


@dataclass(frozen=True, slots=True)
class ListViewerSyncRecordsQuery:
    """Request to list Viewer synchronization records across all projects.

    Args:
        pagination: Page and ordering parameters.
        viewer_type: Optional external Viewer filter.
    """

    pagination: PaginationParams
    viewer_type: ViewerType | None = None


@dataclass(frozen=True, slots=True)
class ListProjectViewerSyncRecordsQuery:
    """Request to list Viewer synchronization records for one project.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        viewer_type: Optional external Viewer filter.
    """

    project_key: str
    pagination: PaginationParams
    viewer_type: ViewerType | None = None


@dataclass(frozen=True, slots=True)
class ListViewerDriftEventsQuery:
    """Request to list Viewer drift events across all projects.

    Args:
        pagination: Page and ordering parameters.
        viewer_type: Optional external Viewer filter.
    """

    pagination: PaginationParams
    viewer_type: ViewerType | None = None


@dataclass(frozen=True, slots=True)
class ListProjectViewerDriftEventsQuery:
    """Request to list Viewer drift events for one project.

    Args:
        project_key: Owning project key.
        pagination: Page and ordering parameters.
        viewer_type: Optional external Viewer filter.
    """

    project_key: str
    pagination: PaginationParams
    viewer_type: ViewerType | None = None


@dataclass(frozen=True, slots=True)
class ListViewerOperationsQuery:
    """Request to list asynchronous Viewer operations across all projects."""

    pagination: PaginationParams
    viewer_type: ViewerType | None = None


@dataclass(frozen=True, slots=True)
class ListProjectViewerOperationsQuery:
    """Request to list asynchronous Viewer operations for one project."""

    project_key: str
    pagination: PaginationParams
    viewer_type: ViewerType | None = None
