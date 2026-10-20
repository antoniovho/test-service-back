"""Input port for listing immutable Viewer operation outcomes."""

from typing import Protocol

from test_service.domain.application.queries.pagination import Page
from test_service.domain.application.queries.viewer import ListProjectViewerOperationItemsQuery
from test_service.domain.model.viewer.records import ViewerOperationItem
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListProjectViewerOperationItemsUseCase(
    AsyncUseCase[ListProjectViewerOperationItemsQuery, Page[ViewerOperationItem]], Protocol
):
    """List the per-entity historical outcomes of a project Viewer operation."""
