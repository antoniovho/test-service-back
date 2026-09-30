"""Mapping between Viewer domain values and persistence DTOs."""

from test_service.domain.model.viewer.records import DriftEvent, ViewerSyncRecord
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
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
            last_synced_at=record.last_synced_at,
            last_checked_at=record.last_checked_at,
            created_at=record.created_at,
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
