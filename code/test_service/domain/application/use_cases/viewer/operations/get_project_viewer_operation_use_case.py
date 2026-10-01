"""Use case implementation: get a project-scoped Viewer operation."""

from uuid import UUID

from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.viewer.records import ViewerOperation
from test_service.domain.ports.input.use_cases.viewer.operations.get_project_viewer_operation_use_case import (  # noqa: E501
    GetProjectViewerOperationUseCase,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)


class GetProjectViewerOperationUseCaseImpl(GetProjectViewerOperationUseCase):
    """Get one Viewer operation while enforcing its project scope."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: tuple[str, UUID]) -> ViewerOperation:
        project_key, operation_id = request
        await self._project_resolver.resolve(project_key)
        operation = await self._viewer_repository.get_operation(operation_id)
        if operation is None or operation.project_key != project_key:
            raise EntityNotFoundException("viewer operation", str(operation_id), project_key)
        return operation
