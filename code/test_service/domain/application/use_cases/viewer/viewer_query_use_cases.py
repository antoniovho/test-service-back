"""Use case implementations for Viewer synchronization queries."""

from uuid import UUID

from test_service.domain.application.queries.viewer import (
    ListProjectViewerDriftEventsQuery,
    ListProjectViewerOperationsQuery,
    ListProjectViewerSyncRecordsQuery,
    ListViewerDriftEventsQuery,
    ListViewerOperationsQuery,
    ListViewerSyncRecordsQuery,
)
from test_service.domain.application.services.project_resolver import ProjectResolver
from test_service.domain.commons.pagination import Page
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.viewer.records import DriftEvent, ViewerOperation, ViewerSyncRecord
from test_service.domain.ports.input.use_cases.viewer.list_project_viewer_drift_events_use_case import (  # noqa: E501
    ListProjectViewerDriftEventsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.list_project_viewer_sync_records_use_case import (  # noqa: E501
    ListProjectViewerSyncRecordsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.list_viewer_drift_events_use_case import (  # noqa: E501
    ListViewerDriftEventsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.list_viewer_sync_records_use_case import (  # noqa: E501
    ListViewerSyncRecordsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.viewer_operation_use_cases import (
    GetProjectViewerOperationUseCase,
    ListProjectViewerOperationsUseCase,
    ListViewerOperationsUseCase,
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


class ListViewerDriftEventsUseCaseImpl(ListViewerDriftEventsUseCase):
    """List drift events across all projects."""

    def __init__(self, viewer_repository: ViewerPersistencePort) -> None:
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListViewerDriftEventsQuery) -> Page[DriftEvent]:
        return await self._viewer_repository.find_drift_events_page(
            request.pagination, request.viewer_type
        )


class ListProjectViewerDriftEventsUseCaseImpl(ListProjectViewerDriftEventsUseCase):
    """List drift events for one existing project."""

    def __init__(
        self, project_resolver: ProjectResolver, viewer_repository: ViewerPersistencePort
    ) -> None:
        self._project_resolver = project_resolver
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListProjectViewerDriftEventsQuery) -> Page[DriftEvent]:
        await self._project_resolver.resolve(request.project_key)
        return await self._viewer_repository.find_drift_events_page_by_project(
            request.project_key, request.pagination, request.viewer_type
        )


class ListViewerOperationsUseCaseImpl(ListViewerOperationsUseCase):
    """List asynchronous Viewer operations across all projects."""

    def __init__(self, viewer_repository: ViewerPersistencePort) -> None:
        self._viewer_repository = viewer_repository

    async def execute(self, request: ListViewerOperationsQuery) -> Page[ViewerOperation]:
        return await self._viewer_repository.find_operations_page(
            request.pagination, request.viewer_type
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
