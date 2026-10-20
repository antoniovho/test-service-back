"""Viewer synchronization persistence contract."""

from typing import Protocol
from uuid import UUID

from test_service.domain.application.queries.pagination import Page, PaginationParams
from test_service.domain.model.viewer.records import (
    DriftEvent,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationItem,
    ViewerSyncRecord,
    ViewerType,
)


class ViewerPersistencePort(Protocol):
    """Persistence contract for Viewer synchronization state."""

    async def save_operation(self, operation: ViewerOperation) -> ViewerOperation:
        """Persist a Viewer operation state transition."""
        ...

    async def get_operation(self, operation_id: UUID) -> ViewerOperation | None:
        """Find one Viewer operation by its technical identifier."""
        ...

    async def claim_next_operation(self) -> ViewerOperation | None:
        """Atomically claim the oldest pending operation for processing."""
        ...

    async def find_operations_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[ViewerOperation]:
        """Find Viewer operations across all projects."""
        ...

    async def find_operations_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerOperation]:
        """Find Viewer operations owned by one project."""
        ...

    async def save_sync_record(self, record: ViewerSyncRecord) -> ViewerSyncRecord:
        """Persist a synchronization record."""
        ...

    async def get_sync_record(self, sync_record_id: UUID) -> ViewerSyncRecord | None:
        """Find the current synchronization state by its technical identifier."""
        ...

    async def save_operation_item(self, item: ViewerOperationItem) -> ViewerOperationItem:
        """Append an immutable per-entity outcome to a Viewer operation."""
        ...

    async def find_operation_items_page(
        self, project_key: str, operation_id: UUID, pagination: PaginationParams
    ) -> Page[ViewerOperationItem]:
        """Find the immutable per-entity outcomes of a project operation."""
        ...

    async def find_sync_record(
        self,
        project_key: str,
        entity_type: ViewerEntityType,
        entity_key: str,
        entity_version: int,
        viewer_type: ViewerType,
    ) -> ViewerSyncRecord | None:
        """Find the durable identity for one projected entity."""
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
