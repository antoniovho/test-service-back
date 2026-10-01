"""Use case implementation: list asynchronous Viewer operations."""

from test_service.domain.application.queries.viewer import ListViewerOperationsQuery
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_cases.viewer.operations.list_viewer_operations_use_case import (  # noqa: E501
    ListViewerOperationsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListViewerOperationsUseCaseImpl(ListViewerOperationsUseCase):
    """List asynchronous Viewer operations across all projects."""

    def __init__(self, viewer_repository: ViewerPersistencePort) -> None:
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListViewerOperationsQuery) -> Page[ViewerOperation]:
        return await self._viewer_repository.find_operations_page(
            request.pagination, request.viewer_type
        )
