from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import (
    PreconditionReference,
    Priority,
    TestCase,
    TestLevel,
    TestType,
)
from test_service.domain.model.exceptions.viewer_projection_integrity_exception import (
    ViewerProjectionIntegrityException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.viewer.managed_state import ViewerManagedState
from test_service.domain.model.viewer.projection import ViewerExternalIdentity, ViewerProjection
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
    async def test_when_published_snapshot_is_unavailable_expect_integrity_exception(self) -> None:
        record = _record()
        test_case_repository = AsyncMock()
        test_case_repository.find_by_id.return_value = None
        service = ViewerProjectionService(
            AsyncMock(),
            test_case_repository,
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
            AsyncMock(),
        )

        with pytest.raises(
            ViewerProjectionIntegrityException,
            match="published Viewer snapshot is unavailable",
        ):
            await service._projection_for_drift(record)

    async def test_when_publishing_expect_dependencies_steps_and_xray_identities_saved(
        self,
    ) -> None:
        precondition = Precondition(
            identifier=uuid4(),
            project_key="SHOP",
            precondition_key="authenticated-customer",
            version=1,
            name="Authenticated customer",
            description="A customer is signed in.",
            validation_definition=Definition({}, (Action("login", "HTTP", {"url": "/login"}),)),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
            status=VersionStatus.ACTIVE,
        )
        test_case = TestCase(
            identifier=uuid4(),
            project_key="SHOP",
            test_key="checkout",
            version=1,
            name="Checkout succeeds",
            summary="A customer completes checkout.",
            objective="The order is accepted.",
            test_type=TestType.AUTOMATED,
            test_level=TestLevel.FUNCTIONAL,
            priority=Priority.HIGH,
            definition=Definition({}, (Action("submit", "HTTP", {"method": "POST"}),)),
            timeout_seconds=60,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_by="author@example.test",
            preconditions=(
                PreconditionReference(precondition.identifier, precondition.precondition_key, 1),
            ),
            status=VersionStatus.ACTIVE,
        )
        operation = ViewerOperation(
            identifier=uuid4(),
            project_key="SHOP",
            viewer_type=ViewerType.XRAY,
            operation_type=ViewerOperationType.PUBLICATION,
            status=ViewerOperationStatus.RUNNING,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        repository = AsyncMock()
        repository.claim_next_operation.return_value = operation
        repository.find_sync_record.return_value = None
        repository.save_operation.side_effect = lambda value: value
        repository.save_sync_record.side_effect = lambda value: value
        publisher = AsyncMock()
        publisher.publish.side_effect = [
            ViewerExternalIdentity("10001", "SHOP-11"),
            ViewerExternalIdentity("10002", "SHOP-12"),
        ]
        precondition_repository = AsyncMock()
        precondition_repository.find_page.return_value = Page((precondition,), 1)
        test_case_repository = AsyncMock()
        test_case_repository.find_page.return_value = Page((test_case,), 1)
        test_set_repository = AsyncMock()
        test_set_repository.find_page.return_value = Page((), 0)
        test_plan_repository = AsyncMock()
        test_plan_repository.find_page.return_value = Page((), 0)
        service = ViewerProjectionService(
            AsyncMock(),
            test_case_repository,
            precondition_repository,
            test_set_repository,
            test_plan_repository,
            repository,
            publisher,
            AsyncMock(),
        )

        result = await service.process_next_operation()

        published = [call.args[0] for call in publisher.publish.await_args_list]
        saved_records = [
            call.args[0]
            for call in repository.save_sync_record.await_args_list
            if call.args[0].sync_status is SyncStatus.SYNCED
        ]
        assert result is not None
        assert result.status is ViewerOperationStatus.SUCCEEDED
        assert [projection.record.entity_type for projection in published] == [
            ViewerEntityType.PRECONDITION,
            ViewerEntityType.TEST_CASE,
        ]
        assert published[1].precondition_external_ids == ("10001",)
        assert published[1].steps[0].action == "submit: HTTP"
        assert published[1].steps[0].result == "The order is accepted."
        assert [record.external_entity_id for record in saved_records] == ["10001", "10002"]
        assert [record.projection_hash for record in saved_records] == [
            ViewerManagedState.from_projection(projection).projection_hash
            for projection in published
        ]

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
        service._projection_for_drift = AsyncMock(
            return_value=ViewerProjection(record=record, summary="Checkout")
        )

        result = await service.process_next_operation()

        assert result is not None
        assert result.status is ViewerOperationStatus.SUCCEEDED
        event = repository.save_drift_event.await_args.args[0]
        assert event.sync_record_id == record.identifier
        assert event.drift_type is DriftType.MODIFIED
        detector.check_drift.assert_awaited_once_with(
            ViewerProjection(record=record, summary="Checkout")
        )
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
        service._projection_for_drift = AsyncMock(
            return_value=ViewerProjection(record=record, summary="Checkout")
        )

        result = await service.process_next_operation()

        assert result is not None
        repository.save_drift_event.assert_not_awaited()
        saved_record = repository.save_sync_record.await_args.args[0]
        assert saved_record.sync_status is SyncStatus.SYNCED
