"""Mapping between Viewer domain values and persistence DTOs."""

from test_service.domain.model.viewer.records import DriftEvent, ViewerOperation, ViewerSyncRecord
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
    ViewerOperationDTO,
    ViewerSyncRecordDTO,
)


class ViewerPersistenceMapper:
    @staticmethod
    def sync_record_to_dto(record: ViewerSyncRecord) -> ViewerSyncRecordDTO:
        return ViewerSyncRecordDTO(
            id=record.identifier,
            project_key=record.project_key,
            entity_type=record.entity_type.value,
            entity_key=record.entity_key,
            projected_version_id=record.projected_version_id,
            viewer_type=record.viewer_type.value,
            external_entity_key=record.external_entity_key,
            external_entity_id=record.external_entity_id,
            sync_status=record.sync_status.value,
            operation_id=record.operation_id,
            last_synced_at=record.last_synced_at,
            last_checked_at=record.last_checked_at,
            created_at=record.created_at,
        )

    @staticmethod
    def sync_record_to_domain(record: ViewerSyncRecordDTO) -> ViewerSyncRecord:
        from test_service.domain.model.viewer.records import (
            SyncStatus,
            ViewerEntityType,
            ViewerType,
        )

        return ViewerSyncRecord(
            identifier=record.id,
            project_key=record.project_key,
            entity_type=ViewerEntityType(record.entity_type),
            entity_key=record.entity_key,
            projected_version_id=record.projected_version_id,
            viewer_type=ViewerType(record.viewer_type),
            external_entity_key=record.external_entity_key,
            external_entity_id=record.external_entity_id,
            sync_status=SyncStatus(record.sync_status),
            operation_id=record.operation_id,
            last_synced_at=record.last_synced_at,
            last_checked_at=record.last_checked_at,
            created_at=record.created_at,
        )

    @staticmethod
    def operation_to_dto(operation: ViewerOperation) -> ViewerOperationDTO:
        return ViewerOperationDTO(
            id=operation.identifier,
            project_key=operation.project_key,
            viewer_type=operation.viewer_type.value,
            operation_type=operation.operation_type.value,
            status=operation.status.value,
            created_at=operation.created_at,
            started_at=operation.started_at,
            finished_at=operation.finished_at,
            total_items=operation.total_items,
            succeeded_items=operation.succeeded_items,
            failed_items=operation.failed_items,
            error=operation.error,
        )

    @staticmethod
    def operation_to_domain(operation: ViewerOperationDTO) -> ViewerOperation:
        from test_service.domain.model.viewer.records import (
            ViewerOperationStatus,
            ViewerOperationType,
            ViewerType,
        )

        return ViewerOperation(
            identifier=operation.id,
            project_key=operation.project_key,
            viewer_type=ViewerType(operation.viewer_type),
            operation_type=ViewerOperationType(operation.operation_type),
            status=ViewerOperationStatus(operation.status),
            created_at=operation.created_at,
            started_at=operation.started_at,
            finished_at=operation.finished_at,
            total_items=operation.total_items,
            succeeded_items=operation.succeeded_items,
            failed_items=operation.failed_items,
            error=operation.error,
        )

    @staticmethod
    def drift_event_to_dto(event: DriftEvent) -> DriftEventDTO:
        return DriftEventDTO(
            id=event.identifier,
            project_key=event.project_key,
            sync_record_id=event.sync_record_id,
            projected_version_id=event.projected_version_id,
            detected_at=event.detected_at,
            drift_type=event.drift_type.value,
            notification_status=event.notification_status.value,
            details=dict(event.details) if event.details is not None else None,
            created_at=event.detected_at,
        )

    @staticmethod
    def drift_event_to_domain(event: DriftEventDTO) -> DriftEvent:
        from test_service.domain.model.viewer.records import DriftType, NotificationStatus

        return DriftEvent(
            identifier=event.id,
            project_key=event.project_key,
            sync_record_id=event.sync_record_id,
            projected_version_id=event.projected_version_id,
            detected_at=event.detected_at,
            drift_type=DriftType(event.drift_type),
            notification_status=NotificationStatus(event.notification_status),
            details=event.details,
        )
