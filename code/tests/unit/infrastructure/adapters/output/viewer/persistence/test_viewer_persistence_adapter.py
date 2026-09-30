from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.viewer.records import (
    DriftEvent,
    DriftType,
    NotificationStatus,
    SyncStatus,
    ViewerEntityType,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.infrastructure.adapters.output.viewer.persistence.viewer_persistence_adapter import (  # noqa: E501
    ViewerPersistenceAdapter,
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


class TestViewerPersistenceAdapter:
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
