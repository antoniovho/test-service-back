"""Use case implementation: list project Viewer synchronization records."""

from test_service.domain.application.queries.viewer import ListProjectViewerSyncRecordsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerSyncRecord
from test_service.domain.ports.input.use_cases.viewer.sync_records.list_project_viewer_sync_records_use_case import (  # noqa: E501
    ListProjectViewerSyncRecordsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListProjectViewerSyncRecordsUseCaseImpl(ListProjectViewerSyncRecordsUseCase):
    """List synchronization records for one existing project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListProjectViewerSyncRecordsQuery) -> Page[ViewerSyncRecord]:
        await self._project_resolver.resolve(request.project_key)
        return await self._viewer_repository.find_sync_records_page_by_project(
            request.project_key, request.pagination, request.viewer_type
        )
