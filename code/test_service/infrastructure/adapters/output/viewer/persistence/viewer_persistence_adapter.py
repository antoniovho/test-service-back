"""Viewer synchronization persistence adapter."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from test_service.domain.application.queries.pagination import Page, PaginationParams
from test_service.domain.model.viewer.execution_results import (
    ViewerResultPublication,
    ViewerResultPublicationStatus,
)
from test_service.domain.model.viewer.records import (
    DriftEvent,
    ViewerEntityType,
    ViewerOperation,
    ViewerOperationItem,
    ViewerSyncRecord,
    ViewerType,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)
from test_service.domain.ports.output.persistence.viewer.viewer_result_persistence_port import (
    ViewerResultPersistencePort,
)
from test_service.infrastructure.adapters.output.viewer.persistence.mappers.viewer_persistence_mapper import (  # noqa: E501
    ViewerPersistenceMapper,
)
from test_service.infrastructure.adapters.output.viewer.persistence.repositories.viewer_repository import (  # noqa: E501
    ViewerRepository,
)


class ViewerPersistenceAdapter(ViewerPersistencePort, ViewerResultPersistencePort):
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

    async def get_sync_record(self, sync_record_id: UUID) -> ViewerSyncRecord | None:
        record = await self._repository.get_sync_record(sync_record_id)
        return ViewerPersistenceMapper.sync_record_to_domain(record) if record is not None else None

    async def save_operation_item(self, item: ViewerOperationItem) -> ViewerOperationItem:
        return ViewerPersistenceMapper.operation_item_to_domain(
            await self._repository.save_operation_item(
                ViewerPersistenceMapper.operation_item_to_dto(item)
            )
        )

    async def find_operation_items_page(
        self, project_key: str, operation_id: UUID, pagination: PaginationParams
    ) -> Page[ViewerOperationItem]:
        page = await self._repository.find_operation_items_page(
            project_key, operation_id, pagination
        )
        return Page(
            tuple(ViewerPersistenceMapper.operation_item_to_domain(item) for item in page.items),
            page.total,
        )

    async def find_sync_record(
        self,
        project_key: str,
        entity_type: ViewerEntityType,
        entity_key: str,
        entity_version: int,
        viewer_type: ViewerType,
    ) -> ViewerSyncRecord | None:
        record = await self._repository.find_sync_record(
            project_key, entity_type, entity_key, entity_version, viewer_type
        )
        return ViewerPersistenceMapper.sync_record_to_domain(record) if record is not None else None

    async def save_drift_event(self, event: DriftEvent) -> DriftEvent:
        return ViewerPersistenceMapper.drift_event_to_domain(
            await self._repository.save_drift_event(
                ViewerPersistenceMapper.drift_event_to_dto(event)
            )
        )

    async def enqueue_result_publication(
        self, execution, viewer_type: ViewerType
    ) -> ViewerResultPublication:
        now = datetime.now(UTC)
        publication = ViewerResultPublication(
            identifier=uuid4(),
            project_key=execution.project_key,
            execution_id=execution.identifier,
            viewer_type=viewer_type,
            status=ViewerResultPublicationStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        return ViewerPersistenceMapper.result_publication_to_domain(
            await self._repository.enqueue_result_publication(
                ViewerPersistenceMapper.result_publication_to_dto(publication)
            )
        )

    async def claim_next_result_publication(self) -> ViewerResultPublication | None:
        publication = await self._repository.claim_next_result_publication()
        return (
            ViewerPersistenceMapper.result_publication_to_domain(publication)
            if publication is not None
            else None
        )

    async def save_result_publication(
        self, publication: ViewerResultPublication
    ) -> ViewerResultPublication:
        return ViewerPersistenceMapper.result_publication_to_domain(
            await self._repository.save_result_publication(
                ViewerPersistenceMapper.result_publication_to_dto(publication)
            )
        )

    async def find_result_publication(
        self, execution_id: UUID, viewer_type: ViewerType
    ) -> ViewerResultPublication | None:
        publication = await self._repository.find_result_publication(
            execution_id, viewer_type.value
        )
        return (
            ViewerPersistenceMapper.result_publication_to_domain(publication)
            if publication is not None
            else None
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
