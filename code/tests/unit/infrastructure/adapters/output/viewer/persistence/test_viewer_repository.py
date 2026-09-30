from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import PaginationParams, SortOrder
from test_service.domain.model.viewer.records import ViewerType
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
    ViewerSyncRecordDTO,
)
from test_service.infrastructure.adapters.output.viewer.persistence.repositories.viewer_repository import (  # noqa: E501
    ViewerRepository,
)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


def _sync_dto() -> ViewerSyncRecordDTO:
    return ViewerSyncRecordDTO(
        id=uuid4(),
        project_key="IAG",
        entity_type="TEST_CASE",
        entity_key="LOGIN",
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


class TestViewerRepository:
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
        repository = ViewerRepository(_SessionProvider(session))

        persisted = await repository.save_sync_record(record)

        assert persisted is record
        assert record.id == current.id
        assert record.created_at == current.created_at

    async def test_when_saving_new_sync_and_drift_expect_persisted_dtos(self) -> None:
        record = _sync_dto()
        event = _drift_dto(record)
        session = MagicMock()
        session.scalar = AsyncMock(return_value=None)
        session.merge = AsyncMock(side_effect=[record, event])
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ViewerRepository(_SessionProvider(session))

        saved_record = await repository.save_sync_record(record)
        saved_event = await repository.save_drift_event(event)

        assert saved_record is record
        assert saved_event is event

    async def test_when_listing_sync_records_expect_global_and_project_pages(self) -> None:
        record = _sync_dto()
        total = MagicMock()
        total.scalar_one.return_value = 1
        page = MagicMock()
        page.scalars.return_value.all.return_value = [record]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total, page, total, page])
        repository = ViewerRepository(_SessionProvider(session))
        pagination = PaginationParams(order=SortOrder.DESC)

        global_page = await repository.find_sync_records_page(pagination, ViewerType.XRAY)
        project_page = await repository.find_sync_records_page_by_project(
            "IAG", pagination, ViewerType.XRAY
        )

        assert global_page.items == (record,)
        assert project_page.total == 1

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
        repository = ViewerRepository(_SessionProvider(session))
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
        repository = ViewerRepository(_SessionProvider(MagicMock()))
        page_request = repository.find_sync_records_page(PaginationParams(sort_by="unsafe"))

        with pytest.raises(ValueError, match="unsupported viewer sort field: unsafe"):
            await page_request
