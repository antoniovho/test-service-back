"""Mapping between Viewer REST models and domain requests."""

from test_service_server.models.drift_event import DriftEvent as ApiDriftEvent
from test_service_server.models.drift_event_list_response import DriftEventListResponse
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.project_reference import ProjectReference
from test_service_server.models.viewer_operation import ViewerOperation as ApiViewerOperation
from test_service_server.models.viewer_operation_list_response import ViewerOperationListResponse
from test_service_server.models.viewer_operation_request import ViewerOperationRequest
from test_service_server.models.viewer_sync_record import ViewerSyncRecord as ApiViewerSyncRecord
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse
from test_service_server.models.viewer_type import ViewerType as ApiViewerType

from test_service.domain.application.commands.viewer import (
    CheckViewerDriftCommand,
    PublishViewerProjectionCommand,
)
from test_service.domain.application.queries.viewer import (
    ListProjectViewerDriftEventsQuery,
    ListProjectViewerOperationsQuery,
    ListProjectViewerSyncRecordsQuery,
    ListViewerDriftEventsQuery,
    ListViewerOperationsQuery,
    ListViewerSyncRecordsQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.viewer.records import (
    DriftEvent,
    ViewerOperation,
    ViewerSyncRecord,
    ViewerType,
)


class ViewerMapper:
    @staticmethod
    def to_publish_command(
        project_key: str, request: ViewerOperationRequest
    ) -> PublishViewerProjectionCommand:
        return PublishViewerProjectionCommand(project_key, ViewerType(request.viewer_type.value))

    @staticmethod
    def to_check_drift_command(
        project_key: str, request: ViewerOperationRequest
    ) -> CheckViewerDriftCommand:
        return CheckViewerDriftCommand(project_key, ViewerType(request.viewer_type.value))

    @staticmethod
    def to_viewer_type(viewer_type: ApiViewerType | None) -> ViewerType | None:
        return ViewerType(viewer_type.value) if viewer_type is not None else None

    @staticmethod
    def to_pagination(offset, limit, sort_by, order) -> PaginationParams:
        sort_fields = {
            "createdAt": "created_at",
            "lastSyncedAt": "last_synced_at",
            "lastCheckedAt": "last_checked_at",
            "syncStatus": "sync_status",
            "entityKey": "entity_key",
            "detectedAt": "detected_at",
            "driftType": "drift_type",
            "notificationStatus": "notification_status",
            "startedAt": "started_at",
            "finishedAt": "finished_at",
            "status": "status",
        }
        return PaginationParams(
            offset=offset or 0,
            limit=limit or 20,
            sort_by=sort_fields.get(sort_by or "createdAt", "created_at"),
            order=SortOrder(order.value) if order else SortOrder.ASC,
        )

    @staticmethod
    def to_list_sync_records_query(
        pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListViewerSyncRecordsQuery:
        return ListViewerSyncRecordsQuery(pagination, ViewerMapper.to_viewer_type(viewer_type))

    @staticmethod
    def to_list_project_sync_records_query(
        project_key: str, pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListProjectViewerSyncRecordsQuery:
        return ListProjectViewerSyncRecordsQuery(
            project_key, pagination, ViewerMapper.to_viewer_type(viewer_type)
        )

    @staticmethod
    def to_list_operations_query(
        pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListViewerOperationsQuery:
        return ListViewerOperationsQuery(pagination, ViewerMapper.to_viewer_type(viewer_type))

    @staticmethod
    def to_list_project_operations_query(
        project_key: str, pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListProjectViewerOperationsQuery:
        return ListProjectViewerOperationsQuery(
            project_key, pagination, ViewerMapper.to_viewer_type(viewer_type)
        )

    @staticmethod
    def to_list_drift_events_query(
        pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListViewerDriftEventsQuery:
        return ListViewerDriftEventsQuery(pagination, ViewerMapper.to_viewer_type(viewer_type))

    @staticmethod
    def to_list_project_drift_events_query(
        project_key: str, pagination: PaginationParams, viewer_type: ApiViewerType | None
    ) -> ListProjectViewerDriftEventsQuery:
        return ListProjectViewerDriftEventsQuery(
            project_key, pagination, ViewerMapper.to_viewer_type(viewer_type)
        )

    @staticmethod
    def sync_record_to_api(record: ViewerSyncRecord, project_name: str) -> ApiViewerSyncRecord:
        return ApiViewerSyncRecord(
            id=record.identifier,
            project=ProjectReference(key=record.project_key, name=project_name),
            entityType=record.entity_type.value,
            entityKey=record.entity_key,
            projectedVersionId=record.projected_version_id,
            viewerType=ApiViewerType(record.viewer_type.value),
            externalEntityKey=record.external_entity_key,
            externalEntityId=record.external_entity_id,
            syncStatus=record.sync_status.value,
            lastSyncedAt=record.last_synced_at,
            lastCheckedAt=record.last_checked_at,
            createdAt=record.created_at,
        )

    @staticmethod
    def drift_event_to_api(event: DriftEvent, project_name: str) -> ApiDriftEvent:
        return ApiDriftEvent(
            id=event.identifier,
            project=ProjectReference(key=event.project_key, name=project_name),
            syncRecordId=event.sync_record_id,
            projectedVersionId=event.projected_version_id,
            detectedAt=event.detected_at,
            driftType=event.drift_type.value,
            notificationStatus=event.notification_status.value,
            details=dict(event.details) if event.details else None,
            createdAt=event.detected_at,
        )

    @staticmethod
    def operation_to_api(operation: ViewerOperation, project_name: str) -> ApiViewerOperation:
        return ApiViewerOperation(
            id=operation.identifier,
            project=ProjectReference(key=operation.project_key, name=project_name),
            viewerType=ApiViewerType(operation.viewer_type.value),
            operationType=operation.operation_type.value,
            status=operation.status.value,
            createdAt=operation.created_at,
            startedAt=operation.started_at,
            finishedAt=operation.finished_at,
            totalItems=operation.total_items,
            succeededItems=operation.succeeded_items,
            failedItems=operation.failed_items,
            error=operation.error,
        )

    @staticmethod
    def sync_response(
        page: Page[ViewerSyncRecord], pagination: PaginationParams, project_names: dict[str, str]
    ) -> ViewerSyncRecordListResponse:
        return ViewerSyncRecordListResponse(
            data=[
                ViewerMapper.sync_record_to_api(item, project_names[item.project_key])
                for item in page.items
            ],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )

    @staticmethod
    def drift_response(
        page: Page[DriftEvent], pagination: PaginationParams, project_names: dict[str, str]
    ) -> DriftEventListResponse:
        return DriftEventListResponse(
            data=[
                ViewerMapper.drift_event_to_api(item, project_names[item.project_key])
                for item in page.items
            ],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )

    @staticmethod
    def operation_response(
        page: Page[ViewerOperation], pagination: PaginationParams, project_names: dict[str, str]
    ) -> ViewerOperationListResponse:
        return ViewerOperationListResponse(
            data=[
                ViewerMapper.operation_to_api(item, project_names[item.project_key])
                for item in page.items
            ],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )

    @staticmethod
    def sync_records_response(
        records: tuple[ViewerSyncRecord, ...],
        project_names: dict[str, str],
    ) -> ViewerSyncRecordListResponse:
        return ViewerMapper.sync_response(
            Page(records, len(records)),
            PaginationParams(limit=max(1, len(records))),
            project_names,
        )

    @staticmethod
    def drift_events_response(
        events: tuple[DriftEvent, ...], project_names: dict[str, str]
    ) -> DriftEventListResponse:
        return ViewerMapper.drift_response(
            Page(events, len(events)),
            PaginationParams(limit=max(1, len(events))),
            project_names,
        )
