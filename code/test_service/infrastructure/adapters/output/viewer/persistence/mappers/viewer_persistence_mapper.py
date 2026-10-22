"""Mapping between Viewer domain values and persistence DTOs."""

from test_service.domain.model.viewer.execution_results import (
    ViewerResultPublication,
    ViewerResultPublicationStatus,
)
from test_service.domain.model.viewer.records import (
    DriftEvent,
    ViewerOperation,
    ViewerOperationItem,
    ViewerSyncRecord,
)
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
    ViewerOperationDTO,
    ViewerOperationItemDTO,
    ViewerResultPublicationDTO,
    ViewerSyncRecordDTO,
)


class ViewerPersistenceMapper:
    @staticmethod
    def result_publication_to_dto(
        publication: ViewerResultPublication,
    ) -> ViewerResultPublicationDTO:
        return ViewerResultPublicationDTO(
            id=publication.identifier,
            project_key=publication.project_key,
            execution_id=publication.execution_id,
            viewer_type=publication.viewer_type.value,
            status=publication.status.value,
            attempts=publication.attempts,
            next_attempt_at=publication.next_attempt_at,
            started_at=publication.started_at,
            finished_at=publication.finished_at,
            external_execution_id=publication.external_execution_id,
            external_execution_key=publication.external_execution_key,
            error=publication.error,
            created_at=publication.created_at,
            updated_at=publication.updated_at,
        )

    @staticmethod
    def result_publication_to_domain(
        publication: ViewerResultPublicationDTO,
    ) -> ViewerResultPublication:
        from test_service.domain.model.viewer.records import ViewerType

        return ViewerResultPublication(
            identifier=publication.id,
            project_key=publication.project_key,
            execution_id=publication.execution_id,
            viewer_type=ViewerType(publication.viewer_type),
            status=ViewerResultPublicationStatus(publication.status),
            attempts=publication.attempts,
            next_attempt_at=publication.next_attempt_at,
            started_at=publication.started_at,
            finished_at=publication.finished_at,
            external_execution_id=publication.external_execution_id,
            external_execution_key=publication.external_execution_key,
            error=publication.error,
            created_at=publication.created_at,
            updated_at=publication.updated_at,
        )

    @staticmethod
    def operation_item_to_dto(item: ViewerOperationItem) -> ViewerOperationItemDTO:
        return ViewerOperationItemDTO(
            id=item.identifier,
            operation_id=item.operation_id,
            sync_record_id=item.sync_record_id,
            project_key=item.project_key,
            entity_type=item.entity_type.value,
            entity_key=item.entity_key,
            entity_version=item.entity_version,
            projected_version_id=item.projected_version_id,
            viewer_type=item.viewer_type.value,
            external_entity_key=item.external_entity_key,
            external_entity_id=item.external_entity_id,
            sync_status=item.sync_status.value,
            error=item.error,
            created_at=item.created_at,
        )

    @staticmethod
    def operation_item_to_domain(item: ViewerOperationItemDTO) -> ViewerOperationItem:
        from test_service.domain.model.viewer.records import (
            SyncStatus,
            ViewerEntityType,
            ViewerType,
        )

        return ViewerOperationItem(
            identifier=item.id,
            operation_id=item.operation_id,
            sync_record_id=item.sync_record_id,
            project_key=item.project_key,
            entity_type=ViewerEntityType(item.entity_type),
            entity_key=item.entity_key,
            entity_version=item.entity_version,
            projected_version_id=item.projected_version_id,
            viewer_type=ViewerType(item.viewer_type),
            external_entity_key=item.external_entity_key,
            external_entity_id=item.external_entity_id,
            sync_status=SyncStatus(item.sync_status),
            error=item.error,
            created_at=item.created_at,
        )

    @staticmethod
    def sync_record_to_dto(record: ViewerSyncRecord) -> ViewerSyncRecordDTO:
        return ViewerSyncRecordDTO(
            id=record.identifier,
            project_key=record.project_key,
            entity_type=record.entity_type.value,
            entity_key=record.entity_key,
            entity_version=record.entity_version,
            projected_version_id=record.projected_version_id,
            viewer_type=record.viewer_type.value,
            external_entity_key=record.external_entity_key,
            external_entity_id=record.external_entity_id,
            projection_hash=record.projection_hash,
            error=record.error,
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
            entity_version=record.entity_version,
            projected_version_id=record.projected_version_id,
            viewer_type=ViewerType(record.viewer_type),
            external_entity_key=record.external_entity_key,
            external_entity_id=record.external_entity_id,
            projection_hash=record.projection_hash,
            error=record.error,
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
