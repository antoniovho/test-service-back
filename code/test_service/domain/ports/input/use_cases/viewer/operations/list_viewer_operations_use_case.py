"""Input port for listing asynchronous Viewer operations."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListViewerOperationsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListViewerOperationsUseCase(
    AsyncUseCase[ListViewerOperationsQuery, Page[ViewerOperation]], Protocol
):
    """List asynchronous Viewer operations across all projects."""
