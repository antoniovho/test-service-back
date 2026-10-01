from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.viewer.records import (
    DriftEvent,
    DriftType,
    NotificationStatus,
    SyncStatus,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationStatus,
    ViewerOperationType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
    ViewerPersistenceMapper,
)


def _sync_record() -> ViewerSyncRecord:
    return ViewerSyncRecord(
        identifier=uuid4(),
        project_key="IAG",
        entity_type=ViewerEntityType.TEST_CASE,
        entity_key="LOGIN",
        projected_version_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        external_entity_key="LOGIN",
        external_entity_id="external-1",
        sync_status=SyncStatus.SYNCED,
        last_synced_at=datetime(2026, 1, 2, tzinfo=UTC),
        last_checked_at=datetime(2026, 1, 3, tzinfo=UTC),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _drift_event(sync_record: ViewerSyncRecord) -> DriftEvent:
    return DriftEvent(
        identifier=uuid4(),
        project_key=sync_record.project_key,
        sync_record_id=sync_record.identifier,
        projected_version_id=sync_record.projected_version_id,
        detected_at=datetime(2026, 1, 4, tzinfo=UTC),
        drift_type=DriftType.MODIFIED,
        notification_status=NotificationStatus.PENDING,
        details={"field": "name"},
    )


def _operation() -> ViewerOperation:
    return ViewerOperation(
        identifier=uuid4(),
        project_key="IAG",
        viewer_type=ViewerType.XRAY,
        operation_type=ViewerOperationType.PUBLICATION,
        status=ViewerOperationStatus.PARTIALLY_SUCCEEDED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        started_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 2, tzinfo=UTC),
        total_items=3,
        succeeded_items=2,
        failed_items=1,
        error="One projection could not be published.",
    )


class TestViewerPersistenceMapper:
    def test_when_mapping_sync_record_expect_persistence_round_trip(self) -> None:
        record = _sync_record()

        restored = ViewerPersistenceMapper.sync_record_to_domain(
            ViewerPersistenceMapper.sync_record_to_dto(record)
        )

        assert restored == record

    def test_when_mapping_drift_event_expect_persistence_round_trip(self) -> None:
        event = _drift_event(_sync_record())

        restored = ViewerPersistenceMapper.drift_event_to_domain(
            ViewerPersistenceMapper.drift_event_to_dto(event)
        )

        assert restored == event

    def test_when_mapping_operation_expect_persistence_round_trip(self) -> None:
        operation = _operation()

        restored = ViewerPersistenceMapper.operation_to_domain(
            ViewerPersistenceMapper.operation_to_dto(operation)
        )

        assert restored == operation
