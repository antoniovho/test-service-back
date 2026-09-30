"""Viewer synchronization persistence contract."""

from typing import Protocol

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.viewer.records import DriftEvent, ViewerSyncRecord, ViewerType


class ViewerPersistencePort(Protocol):
    """Persistence contract for Viewer synchronization state."""

    async def save_sync_record(self, record: ViewerSyncRecord) -> ViewerSyncRecord:
        """Persist a synchronization record."""
        ...

    async def save_drift_event(self, event: DriftEvent) -> DriftEvent:
        """Persist a drift event."""
        ...

    async def find_sync_records_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[ViewerSyncRecord]:
        """Find synchronization records across all projects."""
        ...

    async def find_sync_records_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerSyncRecord]:
        """Find synchronization records owned by one project."""
        ...

    async def find_drift_events_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[DriftEvent]:
        """Find drift events across all projects."""
        ...

    async def find_drift_events_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[DriftEvent]:
        """Find drift events owned by one project."""
        ...
