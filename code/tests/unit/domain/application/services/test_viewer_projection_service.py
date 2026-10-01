from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.viewer.records import (
    DriftObservation,
    DriftType,
    SyncStatus,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationStatus,
    ViewerOperationType,
    ViewerSyncRecord,
    ViewerType,
)


def _operation() -> ViewerOperation:
    return ViewerOperation(
        identifier=uuid4(),
        project_key="SHOP",
        viewer_type=ViewerType.XRAY,
        operation_type=ViewerOperationType.DRIFT_CHECK,
        status=ViewerOperationStatus.RUNNING,
        created_at=datetime.now(UTC),
    )


def _record(sync_status: SyncStatus = SyncStatus.SYNCED) -> ViewerSyncRecord:
    return ViewerSyncRecord(
        identifier=uuid4(),
        project_key="SHOP",
        entity_type=ViewerEntityType.TEST_CASE,
        entity_key="CHECKOUT",
        projected_version_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        external_entity_key="SHOP-101",
        sync_status=sync_status,
        created_at=datetime.now(UTC),
    )


class TestViewerProjectionService:
    async def test_when_detector_observes_drift_expect_event_and_drift_status_saved(self) -> None:
        operation = _operation()
        record = _record()
        repository = AsyncMock()
        repository.claim_next_operation.return_value = operation
        repository.find_sync_records_page_by_project.return_value = Page((record,), 1)
        repository.save_operation.side_effect = lambda value: value
        repository.save_sync_record.side_effect = lambda value: value
        detector = AsyncMock()
        detector.check_drift.return_value = DriftObservation(
            DriftType.MODIFIED, {"field": "summary"}
        )
        service = ViewerProjectionService(
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            repository,
            AsyncMock(),
            detector,
        )

        result = await service.process_next_operation()

        assert result is not None
        assert result.status is ViewerOperationStatus.SUCCEEDED
        event = repository.save_drift_event.await_args.args[0]
        assert event.sync_record_id == record.identifier
        assert event.drift_type is DriftType.MODIFIED
        saved_record = repository.save_sync_record.await_args.args[0]
        assert saved_record.sync_status is SyncStatus.DRIFT_DETECTED

    async def test_when_detector_observes_no_drift_expect_no_event_and_synced_status(self) -> None:
        operation = _operation()
        record = _record(SyncStatus.DRIFT_DETECTED)
        repository = AsyncMock()
        repository.claim_next_operation.return_value = operation
        repository.find_sync_records_page_by_project.return_value = Page((record,), 1)
        repository.save_operation.side_effect = lambda value: value
        repository.save_sync_record.side_effect = lambda value: value
        detector = AsyncMock()
        detector.check_drift.return_value = None
        service = ViewerProjectionService(
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            repository,
            AsyncMock(),
            detector,
        )

        result = await service.process_next_operation()

        assert result is not None
        repository.save_drift_event.assert_not_awaited()
        saved_record = repository.save_sync_record.await_args.args[0]
        assert saved_record.sync_status is SyncStatus.SYNCED
