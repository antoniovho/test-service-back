"""Use case implementation: list Viewer synchronization records."""

from test_service.domain.application.queries.viewer import ListViewerSyncRecordsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_cases.viewer.list_viewer_sync_records_use_case import (
    ListViewerSyncRecordsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListViewerSyncRecordsUseCaseImpl(ListViewerSyncRecordsUseCase):
    """List synchronization records across all projects."""

    def __init__(self, viewer_repository: ViewerPersistencePort) -> None:
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListViewerSyncRecordsQuery) -> Page[ViewerSyncRecord]:
        return await self._viewer_repository.find_sync_records_page(
            request.pagination, request.viewer_type
        )
