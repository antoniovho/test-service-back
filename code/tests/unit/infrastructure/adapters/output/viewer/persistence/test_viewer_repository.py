from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from test_service.config import ViewerSettings
from test_service.domain.application.queries.pagination import PaginationParams, SortOrder
from test_service.domain.model.viewer.records import ViewerEntityType, ViewerType
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_dto import (  # noqa: E501
    ExecutionDTO,
)
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
    ViewerOperationDTO,
    ViewerOperationItemDTO,
    ViewerResultPublicationDTO,
    ViewerSyncRecordDTO,
)
from test_service.infrastructure.adapters.output.viewer.persistence.repositories import (
    viewer_repository,
)
from test_service.infrastructure.adapters.output.viewer.persistence.repositories.viewer_repository import (  # noqa: E501
    ViewerRepository,
)

_FIXED_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


class _SessionProvider(PostgresSessionProvider):
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        yield cast(AsyncSession, self._session)


def _sync_dto() -> ViewerSyncRecordDTO:
    return ViewerSyncRecordDTO(
        id=uuid4(),
        project_key="IAG",
        entity_type="TEST_CASE",
        entity_key="LOGIN",
        entity_version=1,
        projected_version_id=uuid4(),
        viewer_type="XRAY",
        external_entity_key="LOGIN",
        external_entity_id=None,
        sync_status="SYNCED",
        last_synced_at=None,
        last_checked_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _drift_dto(sync_dto: ViewerSyncRecordDTO) -> DriftEventDTO:
    return DriftEventDTO(
        id=uuid4(),
        project_key="IAG",
        sync_record_id=sync_dto.id,
        projected_version_id=sync_dto.projected_version_id,
        detected_at=datetime(2026, 1, 2, tzinfo=UTC),
        drift_type="MISSING",
        notification_status="PENDING",
        details=None,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


def _operation_dto() -> ViewerOperationDTO:
    return ViewerOperationDTO(
        id=uuid4(),
        project_key="IAG",
        viewer_type="XRAY",
        operation_type="DRIFT_CHECK",
        status="PENDING",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        started_at=None,
        finished_at=None,
        total_items=None,
        succeeded_items=None,
        failed_items=None,
        error=None,
    )


def _operation_item_dto(sync_record: ViewerSyncRecordDTO) -> ViewerOperationItemDTO:
    return ViewerOperationItemDTO(
        id=uuid4(),
        operation_id=uuid4(),
        sync_record_id=sync_record.id,
        project_key=sync_record.project_key,
        entity_type=sync_record.entity_type,
        entity_key=sync_record.entity_key,
        entity_version=sync_record.entity_version,
        projected_version_id=sync_record.projected_version_id,
        viewer_type=sync_record.viewer_type,
        external_entity_key=sync_record.external_entity_key,
        external_entity_id=sync_record.external_entity_id,
        sync_status=sync_record.sync_status,
        error=None,
        created_at=sync_record.created_at,
    )


def _execution_dto(status: str = "RUNNING") -> ExecutionDTO:
    return ExecutionDTO(
        id=uuid4(),
        project_key="IAG",
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        test_case_ids=[],
        environment_snapshot={},
        trigger_type="MANUAL",
        triggered_by="tester@example.test",
        status=status,
        runner_identifier="tavern",
        runner_version="2.0",
        started_at=_FIXED_NOW,
        finished_at=_FIXED_NOW + timedelta(seconds=1),
        duration_ms=1_000,
        created_at=_FIXED_NOW,
    )


def _result_publication_dto(execution_id=None) -> ViewerResultPublicationDTO:
    return ViewerResultPublicationDTO(
        id=uuid4(),
        project_key="IAG",
        execution_id=execution_id or uuid4(),
        viewer_type="XRAY",
        status="PENDING",
        attempts=0,
        next_attempt_at=_FIXED_NOW,
        started_at=None,
        finished_at=None,
        external_execution_id=None,
        external_execution_key=None,
        error=None,
        created_at=_FIXED_NOW,
        updated_at=_FIXED_NOW,
    )


class TestViewerRepository:
    @pytest.fixture
    def settings(self) -> ViewerSettings:
        return ViewerSettings(operation_recovery_timeout_seconds=60)

    async def test_when_saving_and_getting_operation_expect_persisted_dto(self) -> None:
        operation = _operation_dto()
        session = MagicMock()
        session.merge = AsyncMock(return_value=operation)
        session.get = AsyncMock(return_value=operation)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        saved = await repository.save_operation(operation)
        loaded = await repository.get_operation(operation.id)

        assert saved is operation
        assert loaded is operation
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(operation)

    async def test_when_saving_sync_record_expect_existing_identity_retained(self) -> None:
        record = _sync_dto()
        current = _sync_dto()
        scalar_result = MagicMock()
        scalar_result.return_value = current
        session = MagicMock()
        session.scalar = AsyncMock(return_value=current)
        session.merge = AsyncMock(return_value=record)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        persisted = await repository.save_sync_record(record)

        assert persisted is record
        assert record.id == current.id
        assert record.created_at == current.created_at

    async def test_when_claiming_operation_expect_configured_stale_timeout_used(
        self, settings: ViewerSettings, monkeypatch
    ) -> None:
        operation = _operation_dto()
        result = MagicMock()
        result.scalar_one_or_none.return_value = operation
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), settings)
        monkeypatch.setattr(
            viewer_repository, "datetime", SimpleNamespace(now=lambda _: _FIXED_NOW)
        )

        await repository.claim_next_operation()

        statement = session.execute.await_args.args[0]
        threshold = next(
            value for value in statement.compile().params.values() if isinstance(value, datetime)
        )
        assert threshold == _FIXED_NOW - timedelta(seconds=60)
        assert operation.status == "RUNNING"

    async def test_when_no_operation_is_available_expect_claim_returns_none(self) -> None:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        operation = await repository.claim_next_operation()

        assert operation is None
        session.commit.assert_not_awaited()

    async def test_when_saving_new_sync_and_drift_expect_persisted_dtos(self) -> None:
        record = _sync_dto()
        event = _drift_dto(record)
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)
        session.merge = AsyncMock(side_effect=[record, event])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        saved_record = await repository.save_sync_record(record)
        saved_event = await repository.save_drift_event(event)

        assert saved_record is record
        assert saved_event is event

    async def test_when_loading_and_finding_sync_record_expect_persisted_dto(self) -> None:
        record = _sync_dto()
        session = MagicMock()
        session.get = AsyncMock(return_value=record)
        session.scalar = AsyncMock(return_value=record)
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        loaded = await repository.get_sync_record(record.id)
        found = await repository.find_sync_record(
            record.project_key,
            ViewerEntityType(record.entity_type),
            record.entity_key,
            record.entity_version,
            ViewerType(record.viewer_type),
        )

        assert loaded is record
        assert found is record
        session.get.assert_awaited_once_with(ViewerSyncRecordDTO, record.id)
        session.scalar.assert_awaited_once()

    async def test_when_saving_operation_item_expect_persisted_dto(self) -> None:
        item = _operation_item_dto(_sync_dto())
        session = MagicMock()
        session.merge = AsyncMock(return_value=item)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        saved = await repository.save_operation_item(item)

        assert saved is item
        session.merge.assert_awaited_once_with(item)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(item)

    async def test_when_listing_operations_expect_global_and_project_pages(self) -> None:
        operation = _operation_dto()
        total = MagicMock()
        total.scalar_one.return_value = 1
        page = MagicMock()
        page.scalars.return_value.all.return_value = [operation]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total, page, total, page])
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())
        pagination = PaginationParams(order=SortOrder.DESC)

        global_page = await repository.find_operations_page(pagination)
        project_page = await repository.find_operations_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert global_page.items == (operation,)
        assert project_page.total == 1

    async def test_when_listing_sync_records_expect_global_and_project_pages(self) -> None:
        record = _sync_dto()
        total = MagicMock()
        total.scalar_one.return_value = 1
        page = MagicMock()
        page.scalars.return_value.all.return_value = [record]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total, page, total, page])
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())
        pagination = PaginationParams(order=SortOrder.DESC)

        global_page = await repository.find_sync_records_page(pagination, ViewerType.XRAY)
        project_page = await repository.find_sync_records_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert global_page.items == (record,)
        assert project_page.total == 1

    async def test_when_listing_operation_items_expect_filtered_page(self) -> None:
        item = _operation_item_dto(_sync_dto())
        total = MagicMock()
        total.scalar_one.return_value = 1
        page = MagicMock()
        page.scalars.return_value.all.return_value = [item]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total, page])
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        result = await repository.find_operation_items_page(
            item.project_key, item.operation_id, PaginationParams()
        )

        assert result.items == (item,)
        assert result.total == 1

    async def test_when_listing_drift_events_expect_unfiltered_and_viewer_filtered_pages(
        self,
    ) -> None:
        record = _sync_dto()
        event = _drift_dto(record)
        total = MagicMock()
        total.scalar_one.return_value = 1
        page = MagicMock()
        page.scalars.return_value.all.return_value = [event]
        session = MagicMock()
        session.execute = AsyncMock(
            side_effect=[total, page, total, page, total, page, total, page]
        )
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())
        pagination = PaginationParams()

        global_page = await repository.find_drift_events_page(pagination)
        filtered_page = await repository.find_drift_events_page(pagination, ViewerType.XRAY)
        project_page = await repository.find_drift_events_page_by_project("IAG", pagination)
        project_filtered_page = await repository.find_drift_events_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert global_page.items == (event,)
        assert filtered_page.total == 1
        assert project_page.items == (event,)
        assert project_filtered_page.total == 1

    async def test_when_sort_field_is_unsupported_expect_value_error(self) -> None:
        repository = ViewerRepository(_SessionProvider(MagicMock()), ViewerSettings())
        page_request = repository.find_sync_records_page(PaginationParams(sort_by="unsafe"))

        with pytest.raises(ValueError, match="unsupported viewer sort field: unsafe"):
            await page_request

    async def test_when_enqueueing_result_publication_expect_idempotent_record_persisted(
        self,
    ) -> None:
        publication = _result_publication_dto()
        session = MagicMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock(return_value=publication)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        persisted = await repository.enqueue_result_publication(publication)

        assert persisted is publication
        session.execute.assert_awaited_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(publication)

    async def test_when_result_publication_is_not_persisted_expect_error(self) -> None:
        publication = _result_publication_dto()
        session = MagicMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock(return_value=None)
        session.commit = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        with pytest.raises(RuntimeError, match="result publication was not persisted"):
            await repository.enqueue_result_publication(publication)

        session.commit.assert_not_awaited()

    async def test_when_transitioning_execution_expect_terminal_state_and_publication_committed(
        self,
    ) -> None:
        execution = _execution_dto(status="FAILED")
        publication = _result_publication_dto(execution.id)
        result = MagicMock()
        result.scalar_one_or_none.return_value = execution
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        transitioned = await repository.transition_execution_and_enqueue_result_publication(
            execution, ("RUNNING",), publication
        )

        assert transitioned is execution
        assert session.execute.await_count == 2
        session.commit.assert_awaited_once()

    async def test_when_execution_does_not_transition_expect_current_state_without_publication(
        self,
    ) -> None:
        execution = _execution_dto(status="FAILED")
        current_execution = _execution_dto(status="SUCCEEDED")
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.get = AsyncMock(return_value=current_execution)
        session.commit = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        transitioned = await repository.transition_execution_and_enqueue_result_publication(
            execution, ("RUNNING",), _result_publication_dto(execution.id)
        )

        assert transitioned is current_execution
        session.execute.assert_awaited_once()
        session.get.assert_awaited_once_with(ExecutionDTO, execution.id)
        session.commit.assert_not_awaited()

    async def test_when_claiming_due_result_publication_expect_running_state(
        self, settings: ViewerSettings, monkeypatch
    ) -> None:
        publication = _result_publication_dto()
        result = MagicMock()
        result.scalar_one_or_none.return_value = publication
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), settings)
        monkeypatch.setattr(
            viewer_repository, "datetime", SimpleNamespace(now=lambda _: _FIXED_NOW)
        )

        claimed = await repository.claim_next_result_publication()

        assert claimed is publication
        assert publication.status == "RUNNING"
        assert publication.attempts == 1
        assert publication.started_at == _FIXED_NOW
        assert publication.next_attempt_at is None
        assert publication.updated_at == _FIXED_NOW
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(publication)

    async def test_when_no_result_publication_is_due_expect_none(self) -> None:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        publication = await repository.claim_next_result_publication()

        assert publication is None
        session.commit.assert_not_awaited()

    async def test_when_saving_and_finding_result_publication_expect_persisted_dto(self) -> None:
        publication = _result_publication_dto()
        session = MagicMock()
        session.merge = AsyncMock(return_value=publication)
        session.scalar = AsyncMock(return_value=publication)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session), ViewerSettings())

        saved = await repository.save_result_publication(publication)
        found = await repository.find_result_publication(
            publication.execution_id, publication.viewer_type
        )

        assert saved is publication
        assert found is publication
        session.merge.assert_awaited_once_with(publication)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(publication)
