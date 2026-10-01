"""Input ports for asynchronous Viewer operation queries."""

from typing import Protocol
from uuid import UUID

from test_service.domain.application.queries.viewer import (
    ListProjectViewerOperationsQuery,
    ListViewerOperationsQuery,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListViewerOperationsUseCase(
    AsyncUseCase[ListViewerOperationsQuery, Page[ViewerOperation]], Protocol
):
    """List asynchronous Viewer operations across all projects."""


class ListProjectViewerOperationsUseCase(
    AsyncUseCase[ListProjectViewerOperationsQuery, Page[ViewerOperation]], Protocol
):
    """List asynchronous Viewer operations for one project."""


class GetProjectViewerOperationUseCase(AsyncUseCase[tuple[str, UUID], ViewerOperation], Protocol):
    """Get one asynchronous Viewer operation within its project scope."""
