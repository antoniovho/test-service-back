"""Use case implementation: list project Viewer operations."""

from test_service.domain.application.queries.viewer import ListProjectViewerOperationsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_cases.viewer.operations.list_project_viewer_operations_use_case import (  # noqa: E501
    ListProjectViewerOperationsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListProjectViewerOperationsUseCaseImpl(ListProjectViewerOperationsUseCase):
    """List asynchronous Viewer operations for one existing project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListProjectViewerOperationsQuery) -> Page[ViewerOperation]:
        await self._project_resolver.resolve(request.project_key)
        return await self._viewer_repository.find_operations_page_by_project(
            request.project_key, request.pagination, request.viewer_type
        )
