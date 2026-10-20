"""Use case implementation: list immutable Viewer operation outcomes."""

from test_service.domain.application.queries.pagination import Page
from test_service.domain.application.queries.viewer import ListProjectViewerOperationItemsQuery
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.viewer.records import ViewerOperationItem
from test_service.domain.ports.input.use_cases.viewer.operations.list_project_viewer_operation_items_use_case import (  # noqa: E501
    ListProjectViewerOperationItemsUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class ListProjectViewerOperationItemsUseCaseImpl(ListProjectViewerOperationItemsUseCase):
    """List operation history while enforcing ownership by the requested project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(
        self, request: ListProjectViewerOperationItemsQuery
    ) -> Page[ViewerOperationItem]:
        await self._project_resolver.resolve(request.project_key)
        operation = await self._viewer_repository.get_operation(request.operation_id)
        if operation is None or operation.project_key != request.project_key:
            raise EntityNotFoundException(
                "viewer operation", str(request.operation_id), request.project_key
            )
        return await self._viewer_repository.find_operation_items_page(
            request.project_key, request.operation_id, request.pagination
        )
