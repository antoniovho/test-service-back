"""Input port: list viewer sync records across all projects."""

from typing import Protocol

from test_service.domain.application.queries.viewer import ListViewerSyncRecordsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_case import AsyncUseCase


class ListViewerSyncRecordsUseCase(
    AsyncUseCase[ListViewerSyncRecordsQuery, Page[ViewerSyncRecord]], Protocol
):
    """Input port for listing Viewer synchronization records across every project."""
