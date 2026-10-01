"""Inbound REST adapter for Viewer operations."""

from test_service_server.apis.viewer_integration_api_base import BaseViewerIntegrationApi
from test_service_server.models.drift_event_list_response import DriftEventListResponse
from test_service_server.models.sort_order import SortOrder as ApiSortOrder
from test_service_server.models.viewer_operation import ViewerOperation
from test_service_server.models.viewer_operation_list_response import ViewerOperationListResponse
from test_service_server.models.viewer_operation_request import ViewerOperationRequest
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse
from test_service_server.models.viewer_type import ViewerType as ApiViewerType

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.check_viewer_drift_use_case import (
    CheckViewerDriftUseCase,
)
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
from test_service.domain.ports.input.use_cases.viewer.publish_viewer_projection_use_case import (  # noqa: E501
    PublishViewerProjectionUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.viewer_operation_use_cases import (
    GetProjectViewerOperationUseCase,
    ListProjectViewerOperationsUseCase,
    ListViewerOperationsUseCase,
)
from test_service.infrastructure.adapters.input.rest.viewer.viewer_mapper import ViewerMapper


class ViewerIntegrationController(BaseViewerIntegrationApi):
    def __init__(self) -> None:
        injector = get_injector()
        self._publish = injector.inject(PublishViewerProjectionUseCase)
        self._get_project = injector.inject(GetProjectUseCase)
        self._check_drift = injector.inject(CheckViewerDriftUseCase)
        self._list_sync = injector.inject(ListViewerSyncRecordsUseCase)
        self._list_project_sync = injector.inject(ListProjectViewerSyncRecordsUseCase)
        self._list_drift = injector.inject(ListViewerDriftEventsUseCase)
        self._list_project_drift = injector.inject(ListProjectViewerDriftEventsUseCase)
        self._list_operations = injector.inject(ListViewerOperationsUseCase)
        self._list_project_operations = injector.inject(ListProjectViewerOperationsUseCase)
        self._get_operation = injector.inject(GetProjectViewerOperationUseCase)

    async def publish_viewer_projection(
        self,
        projectKey: str,  # NOSONAR
        viewer_operation_request: ViewerOperationRequest,
    ) -> ViewerOperation:  # NOSONAR
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        command = ViewerMapper.to_publish_command(projectKey, viewer_operation_request)
        operation = await self._publish.execute(command)
        return ViewerMapper.operation_to_api(operation, project.name)

    async def check_viewer_drift(
        self,
        projectKey: str,  # NOSONAR
        viewer_operation_request: ViewerOperationRequest,
    ) -> ViewerOperation:
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        command = ViewerMapper.to_check_drift_command(projectKey, viewer_operation_request)
        operation = await self._check_drift.execute(command)
        return ViewerMapper.operation_to_api(operation, project.name)

    async def list_viewer_operations(
        self,
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ViewerOperationListResponse:
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_operations.execute(
            ViewerMapper.to_list_operations_query(pagination, viewer_type)
        )
        return ViewerMapper.operation_response(
            page, pagination, await self._project_names(page.items)
        )

    async def list_project_viewer_operations(
        self,
        projectKey: str,  # NOSONAR
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ViewerOperationListResponse:  # NOSONAR
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        page = await self._list_project_operations.execute(
            ViewerMapper.to_list_project_operations_query(projectKey, pagination, viewer_type)
        )
        return ViewerMapper.operation_response(page, pagination, {project.key: project.name})

    async def get_project_viewer_operation(
        self,
        projectKey: str,  # NOSONAR
        viewerOperationId,  # NOSONAR
    ) -> ViewerOperation:  # NOSONAR
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        operation = await self._get_operation.execute((projectKey, viewerOperationId))
        return ViewerMapper.operation_to_api(operation, project.name)

    async def list_viewer_sync_records(
        self,
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ViewerSyncRecordListResponse:
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        query = ViewerMapper.to_list_sync_records_query(pagination, viewer_type)
        page_viewer_sync_records = await self._list_sync.execute(query)
        return ViewerMapper.sync_response(
            page_viewer_sync_records,
            pagination,
            await self._project_names(page_viewer_sync_records.items),
        )

    async def list_project_viewer_sync_records(
        self,
        projectKey: str,  # NOSONAR
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ViewerSyncRecordListResponse:  # NOSONAR
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        query = ViewerMapper.to_list_project_sync_records_query(projectKey, pagination, viewer_type)
        page_project_viewer_sync_records = await self._list_project_sync.execute(query)
        return ViewerMapper.sync_response(
            page_project_viewer_sync_records, pagination, {project.key: project.name}
        )

    async def list_viewer_drift_events(
        self,
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> DriftEventListResponse:
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        query = ViewerMapper.to_list_drift_events_query(pagination, viewer_type)
        page_drift_events = await self._list_drift.execute(query)
        return ViewerMapper.drift_response(
            page_drift_events,
            pagination,
            await self._project_names(page_drift_events.items),
        )

    async def list_project_viewer_drift_events(
        self,
        projectKey: str,  # NOSONAR
        viewer_type: ApiViewerType | None,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> DriftEventListResponse:  # NOSONAR
        project = await self._get_project.execute(GetProjectQuery(projectKey))
        pagination = ViewerMapper.to_pagination(offset, limit, sort_by, order)
        query = ViewerMapper.to_list_project_drift_events_query(projectKey, pagination, viewer_type)
        page_project_drift_events = await self._list_project_drift.execute(query)
        return ViewerMapper.drift_response(
            page_project_drift_events, pagination, {project.key: project.name}
        )

    async def _project_names(self, records) -> dict[str, str]:
        return {
            project_key: (await self._get_project.execute(GetProjectQuery(project_key))).name
            for project_key in {record.project_key for record in records}
        }
