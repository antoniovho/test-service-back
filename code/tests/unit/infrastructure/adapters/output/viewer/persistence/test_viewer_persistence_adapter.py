from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from test_service.domain.application.queries.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import ExecutionStatus
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
from test_service.infrastructure.adapters.output.viewer.persistence.viewer_persistence_adapter import (  # noqa: E501
    ViewerPersistenceAdapter,
)
from tests.mothers.execution_mother import an_execution


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
        sync_status=SyncStatus.SYNCED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _drift_event(record: ViewerSyncRecord) -> DriftEvent:
    return DriftEvent(
        identifier=uuid4(),
        project_key=record.project_key,
        sync_record_id=record.identifier,
        projected_version_id=record.projected_version_id,
        detected_at=datetime(2026, 1, 2, tzinfo=UTC),
        drift_type=DriftType.MISSING,
        notification_status=NotificationStatus.PENDING,
    )


def _operation() -> ViewerOperation:
    return ViewerOperation(
        identifier=uuid4(),
        project_key="IAG",
        viewer_type=ViewerType.XRAY,
        operation_type=ViewerOperationType.PUBLICATION,
        status=ViewerOperationStatus.PENDING,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _operation_item(record: ViewerSyncRecord) -> ViewerOperationItem:
    return ViewerOperationItem(
        identifier=uuid4(),
        operation_id=uuid4(),
        sync_record_id=record.identifier,
        project_key=record.project_key,
        entity_type=record.entity_type,
        entity_key=record.entity_key,
        entity_version=record.entity_version,
        projected_version_id=record.projected_version_id,
        viewer_type=record.viewer_type,
        external_entity_key=record.external_entity_key,
        external_entity_id=record.external_entity_id,
        sync_status=record.sync_status,
        error=None,
        created_at=record.created_at,
    )


def _result_publication() -> ViewerResultPublication:
    return ViewerResultPublication(
        identifier=uuid4(),
        project_key="IAG",
        execution_id=uuid4(),
        viewer_type=ViewerType.XRAY,
        status=ViewerResultPublicationStatus.PENDING,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestViewerPersistenceAdapter:
    async def test_when_completing_execution_expect_transition_and_outbox_saved_together(
        self,
    ) -> None:
        execution = (
            an_execution(created_at=datetime(2026, 1, 1, tzinfo=UTC))
            .start(datetime(2026, 1, 1, 1, tzinfo=UTC))
            .complete(ExecutionStatus.FAILED, datetime(2026, 1, 1, 2, tzinfo=UTC))
        )
        from test_service.infrastructure.adapters.output.execution.executions.persistence.mappers.execution_persistence_mapper import (  # noqa: E501
            ExecutionPersistenceMapper,
        )

        execution_dto = ExecutionPersistenceMapper.to_dto(execution)
        repository = SimpleNamespace(
            transition_execution_and_enqueue_result_publication=AsyncMock(
                return_value=execution_dto
            )
        )
        adapter = ViewerPersistenceAdapter(repository)

        completed = await adapter.transition_execution_and_enqueue_result_publication(
            execution, (ExecutionStatus.RUNNING,), ViewerType.XRAY
        )

        assert completed == execution
        stored_execution, expected_statuses, publication = (
            repository.transition_execution_and_enqueue_result_publication.await_args.args
        )
        assert stored_execution.id == execution.identifier
        assert expected_statuses == (ExecutionStatus.RUNNING.value,)
        assert publication.execution_id == execution.identifier
        assert publication.viewer_type == ViewerType.XRAY.value

    async def test_when_saving_and_loading_operations_expect_domain_values_restored(self) -> None:
        operation = _operation()
        repository = SimpleNamespace(
            save_operation=AsyncMock(),
            get_operation=AsyncMock(),
            claim_next_operation=AsyncMock(),
        )
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        operation_dto = ViewerPersistenceMapper.operation_to_dto(operation)
        repository.save_operation.return_value = operation_dto
        repository.get_operation.return_value = operation_dto
        repository.claim_next_operation.return_value = operation_dto
        adapter = ViewerPersistenceAdapter(repository)

        saved = await adapter.save_operation(operation)
        loaded = await adapter.get_operation(operation.identifier)
        claimed = await adapter.claim_next_operation()

        assert saved == operation
        assert loaded == operation
        assert claimed == operation

    async def test_when_operations_are_absent_expect_none(self) -> None:
        repository = SimpleNamespace(
            get_operation=AsyncMock(return_value=None),
            claim_next_operation=AsyncMock(return_value=None),
        )
        adapter = ViewerPersistenceAdapter(repository)

        loaded = await adapter.get_operation(uuid4())
        claimed = await adapter.claim_next_operation()

        assert loaded is None
        assert claimed is None

    async def test_when_listing_operations_expect_filtered_pages_mapped_to_domain(self) -> None:
        operation = _operation()
        repository = SimpleNamespace(
            find_operations_page=AsyncMock(),
            find_operations_page_by_project=AsyncMock(),
        )
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        operation_page = Page((ViewerPersistenceMapper.operation_to_dto(operation),), 1)
        repository.find_operations_page.return_value = operation_page
        repository.find_operations_page_by_project.return_value = operation_page
        adapter = ViewerPersistenceAdapter(repository)
        pagination = PaginationParams()

        global_page = await adapter.find_operations_page(pagination, ViewerType.XRAY)
        project_page = await adapter.find_operations_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert global_page.items == (operation,)
        assert project_page.items == (operation,)

    async def test_when_saving_records_expect_domain_values_restored(self) -> None:
        record = _sync_record()
        event = _drift_event(record)
        repository = SimpleNamespace(save_sync_record=AsyncMock(), save_drift_event=AsyncMock())
        repository.save_sync_record.side_effect = lambda dto: dto
        repository.save_drift_event.side_effect = lambda dto: dto
        adapter = ViewerPersistenceAdapter(repository)

        saved_record = await adapter.save_sync_record(record)
        saved_event = await adapter.save_drift_event(event)

        assert saved_record == record
        assert saved_event == event

    async def test_when_loading_and_finding_records_expect_domain_values_restored(self) -> None:
        record = _sync_record()
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        record_dto = ViewerPersistenceMapper.sync_record_to_dto(record)
        repository = SimpleNamespace(
            get_sync_record=AsyncMock(return_value=record_dto),
            find_sync_record=AsyncMock(return_value=record_dto),
        )
        adapter = ViewerPersistenceAdapter(repository)

        loaded = await adapter.get_sync_record(record.identifier)
        found = await adapter.find_sync_record(
            record.project_key,
            record.entity_type,
            record.entity_key,
            record.entity_version,
            record.viewer_type,
        )

        assert loaded == record
        assert found == record

    async def test_when_sync_records_are_absent_expect_none(self) -> None:
        repository = SimpleNamespace(
            get_sync_record=AsyncMock(return_value=None),
            find_sync_record=AsyncMock(return_value=None),
        )
        adapter = ViewerPersistenceAdapter(repository)

        loaded = await adapter.get_sync_record(uuid4())
        found = await adapter.find_sync_record(
            "IAG", ViewerEntityType.TEST_CASE, "LOGIN", 1, ViewerType.XRAY
        )

        assert loaded is None
        assert found is None

    async def test_when_saving_and_listing_operation_items_expect_domain_values_restored(
        self,
    ) -> None:
        record = _sync_record()
        item = _operation_item(record)
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        item_dto = ViewerPersistenceMapper.operation_item_to_dto(item)
        repository = SimpleNamespace(
            save_operation_item=AsyncMock(return_value=item_dto),
            find_operation_items_page=AsyncMock(return_value=Page((item_dto,), 1)),
        )
        adapter = ViewerPersistenceAdapter(repository)

        saved = await adapter.save_operation_item(item)
        page = await adapter.find_operation_items_page(
            item.project_key, item.operation_id, PaginationParams()
        )

        assert saved == item
        assert page.items == (item,)
        assert page.total == 1

    async def test_when_listing_records_expect_filtered_pages_mapped_to_domain(self) -> None:
        record = _sync_record()
        event = _drift_event(record)
        repository = SimpleNamespace(
            find_sync_records_page=AsyncMock(),
            find_sync_records_page_by_project=AsyncMock(),
            find_drift_events_page=AsyncMock(),
            find_drift_events_page_by_project=AsyncMock(),
        )
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        repository.find_sync_records_page.return_value = Page(
            (ViewerPersistenceMapper.sync_record_to_dto(record),), 1
        )
        repository.find_sync_records_page_by_project.return_value = Page(
            (ViewerPersistenceMapper.sync_record_to_dto(record),), 1
        )
        repository.find_drift_events_page.return_value = Page(
            (ViewerPersistenceMapper.drift_event_to_dto(event),), 1
        )
        repository.find_drift_events_page_by_project.return_value = Page(
            (ViewerPersistenceMapper.drift_event_to_dto(event),), 1
        )
        adapter = ViewerPersistenceAdapter(repository)
        pagination = PaginationParams()

        sync_page = await adapter.find_sync_records_page(pagination, ViewerType.XRAY)
        project_sync_page = await adapter.find_sync_records_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )
        drift_page = await adapter.find_drift_events_page(pagination, ViewerType.XRAY)
        project_drift_page = await adapter.find_drift_events_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert sync_page.items == (record,)
        assert project_sync_page.items == (record,)
        assert drift_page.items == (event,)
        assert project_drift_page.items == (event,)

    async def test_when_enqueueing_result_publication_expect_pending_domain_value(self) -> None:
        execution = an_execution(created_at=datetime(2026, 1, 1, tzinfo=UTC))
        repository = SimpleNamespace(enqueue_result_publication=AsyncMock())
        repository.enqueue_result_publication.side_effect = lambda publication: publication
        adapter = ViewerPersistenceAdapter(repository)

        publication = await adapter.enqueue_result_publication(execution, ViewerType.XRAY)

        assert publication.project_key == execution.project_key
        assert publication.execution_id == execution.identifier
        assert publication.viewer_type is ViewerType.XRAY
        assert publication.status is ViewerResultPublicationStatus.PENDING

    async def test_when_claiming_result_publication_expect_domain_value_restored(self) -> None:
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        publication = _result_publication()
        repository = SimpleNamespace(
            claim_next_result_publication=AsyncMock(
                return_value=ViewerPersistenceMapper.result_publication_to_dto(publication)
            )
        )
        adapter = ViewerPersistenceAdapter(repository)

        claimed = await adapter.claim_next_result_publication()

        assert claimed == publication

    async def test_when_no_result_publication_is_available_expect_none(self) -> None:
        repository = SimpleNamespace(claim_next_result_publication=AsyncMock(return_value=None))
        adapter = ViewerPersistenceAdapter(repository)

        claimed = await adapter.claim_next_result_publication()

        assert claimed is None

    async def test_when_saving_result_publication_expect_domain_value_restored(self) -> None:
        publication = _result_publication()
        repository = SimpleNamespace(save_result_publication=AsyncMock())
        repository.save_result_publication.side_effect = lambda dto: dto
        adapter = ViewerPersistenceAdapter(repository)

        saved = await adapter.save_result_publication(publication)

        assert saved == publication

    async def test_when_result_publication_is_found_expect_domain_value_restored(self) -> None:
        from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
            ViewerPersistenceMapper,
        )

        publication = _result_publication()
        repository = SimpleNamespace(
            find_result_publication=AsyncMock(
                return_value=ViewerPersistenceMapper.result_publication_to_dto(publication)
            )
        )
        adapter = ViewerPersistenceAdapter(repository)

        found = await adapter.find_result_publication(
            publication.execution_id, publication.viewer_type
        )

        assert found == publication

    async def test_when_result_publication_is_not_found_expect_none(self) -> None:
        repository = SimpleNamespace(find_result_publication=AsyncMock(return_value=None))
        adapter = ViewerPersistenceAdapter(repository)

        found = await adapter.find_result_publication(uuid4(), ViewerType.XRAY)

        assert found is None
