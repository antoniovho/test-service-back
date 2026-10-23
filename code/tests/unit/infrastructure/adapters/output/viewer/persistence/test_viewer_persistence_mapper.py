from datetime import UTC, datetime
from uuid import uuid4

from test_service.domain.model.viewer.execution_results import (
    ViewerResultPublication,
    ViewerResultPublicationStatus,
)
from test_service.domain.model.viewer.records import (
    DriftEvent,
    DriftType,
    NotificationStatus,
    SyncStatus,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationItem,
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
        entity_version=1,
        projected_version_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        external_entity_key="LOGIN",
        external_entity_id="external-1",
        projection_hash="a" * 64,
        error="XrayTransportError: request failed",
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


def _operation_item(sync_record: ViewerSyncRecord) -> ViewerOperationItem:
    return ViewerOperationItem(
        identifier=uuid4(),
        operation_id=uuid4(),
        sync_record_id=sync_record.identifier,
        project_key=sync_record.project_key,
        entity_type=sync_record.entity_type,
        entity_key=sync_record.entity_key,
        entity_version=sync_record.entity_version,
        projected_version_id=sync_record.projected_version_id,
        viewer_type=sync_record.viewer_type,
        external_entity_key=sync_record.external_entity_key,
        external_entity_id=sync_record.external_entity_id,
        sync_status=sync_record.sync_status,
        error="XrayTransportError: request failed",
        created_at=sync_record.created_at,
    )


def _result_publication() -> ViewerResultPublication:
    return ViewerResultPublication(
        identifier=uuid4(),
        project_key="IAG",
        execution_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        status=ViewerResultPublicationStatus.RETRY_WAIT,
        attempts=2,
        next_attempt_at=datetime(2026, 1, 5, tzinfo=UTC),
        started_at=datetime(2026, 1, 4, tzinfo=UTC),
        finished_at=None,
        external_execution_id="10001",
        external_execution_key="IAG-1",
        error="Xray request timed out",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 4, tzinfo=UTC),
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

    def test_when_mapping_operation_item_expect_persistence_round_trip(self) -> None:
        item = _operation_item(_sync_record())

        restored = ViewerPersistenceMapper.operation_item_to_domain(
            ViewerPersistenceMapper.operation_item_to_dto(item)
        )

        assert restored == item

    def test_when_mapping_result_publication_expect_persistence_round_trip(self) -> None:
        publication = _result_publication()

        restored = ViewerPersistenceMapper.result_publication_to_domain(
            ViewerPersistenceMapper.result_publication_to_dto(publication)
        )

        assert restored == publication
