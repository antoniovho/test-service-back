"""Input port: list viewer sync records for one project."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListProjectViewerSyncRecordsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListProjectViewerSyncRecordsUseCase(
    AsyncUseCase[ListProjectViewerSyncRecordsQuery, Page[ViewerSyncRecord]], Protocol
):
    """Input port for listing Viewer synchronization records owned by one project."""
