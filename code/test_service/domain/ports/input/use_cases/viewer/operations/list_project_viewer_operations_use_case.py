"""Input port for listing project Viewer operations."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListProjectViewerOperationsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListProjectViewerOperationsUseCase(
    AsyncUseCase[ListProjectViewerOperationsQuery, Page[ViewerOperation]], Protocol
):
    """List asynchronous Viewer operations for one project."""
