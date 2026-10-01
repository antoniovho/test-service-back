"""Viewer synchronization persistence adapter."""

from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.viewer.records import (
    DriftEvent,
    ViewerOperation,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)
from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
    ViewerPersistenceMapper,
)
from test_service.infrastructure.adapters.output.viewer.persistence.repositories.viewer_repository import (  # noqa: E501
    ViewerRepository,
)


class ViewerPersistenceAdapter(ViewerPersistencePort):
    def __init__(self, repository: ViewerRepository) -> None:
        self._repository = repository

    async def save_operation(self, operation: ViewerOperation) -> ViewerOperation:
        return ViewerPersistenceMapper.operation_to_domain(
            await self._repository.save_operation(
                ViewerPersistenceMapper.operation_to_dto(operation)
            )
        )

    async def get_operation(self, operation_id: UUID) -> ViewerOperation | None:
        operation = await self._repository.get_operation(operation_id)
        return (
            ViewerPersistenceMapper.operation_to_domain(operation)
            if operation is not None
            else None
        )

    async def claim_next_operation(self) -> ViewerOperation | None:
        operation = await self._repository.claim_next_operation()
        return (
            ViewerPersistenceMapper.operation_to_domain(operation)
            if operation is not None
            else None
        )

    async def find_operations_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[ViewerOperation]:
        return self._operation_page(
            await self._repository.find_operations_page(pagination, viewer_type)
        )

    async def find_operations_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerOperation]:
        return self._operation_page(
            await self._repository.find_operations_page_by_project(
                project_key, pagination, viewer_type
            )
        )

    async def save_sync_record(self, record: ViewerSyncRecord) -> ViewerSyncRecord:
        return ViewerPersistenceMapper.sync_record_to_domain(
            await self._repository.save_sync_record(
                ViewerPersistenceMapper.sync_record_to_dto(record)
            )
        )

    async def save_drift_event(self, event: DriftEvent) -> DriftEvent:
        return ViewerPersistenceMapper.drift_event_to_domain(
            await self._repository.save_drift_event(
                ViewerPersistenceMapper.drift_event_to_dto(event)
            )
        )

    async def find_sync_records_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[ViewerSyncRecord]:
        return self._sync_page(
            await self._repository.find_sync_records_page(pagination, viewer_type)
        )

    async def find_sync_records_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerSyncRecord]:
        return self._sync_page(
            await self._repository.find_sync_records_page_by_project(
                project_key, pagination, viewer_type
            )
        )

    async def find_drift_events_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[DriftEvent]:
        return self._drift_page(
            await self._repository.find_drift_events_page(pagination, viewer_type)
        )

    async def find_drift_events_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[DriftEvent]:
        return self._drift_page(
            await self._repository.find_drift_events_page_by_project(
                project_key, pagination, viewer_type
            )
        )

    @staticmethod
    def _sync_page(page) -> Page[ViewerSyncRecord]:
        return Page(
            tuple(ViewerPersistenceMapper.sync_record_to_domain(item) for item in page.items),
            page.total,
        )

    @staticmethod
    def _operation_page(page) -> Page[ViewerOperation]:
        return Page(
            tuple(ViewerPersistenceMapper.operation_to_domain(item) for item in page.items),
            page.total,
        )

    @staticmethod
    def _drift_page(page) -> Page[DriftEvent]:
        return Page(
            tuple(ViewerPersistenceMapper.drift_event_to_domain(item) for item in page.items),
            page.total,
        )
