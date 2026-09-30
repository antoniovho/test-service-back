"""SQLAlchemy repository for Viewer synchronization state."""

from sqlalchemy import asc, desc, func, select

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.viewer.records import ViewerType
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.viewer.persistence.dtos.viewer_dtos import (
    DriftEventDTO,
    ViewerSyncRecordDTO,
)


class ViewerRepository:
    _SYNC_SORT_COLUMNS = {
        "created_at": ViewerSyncRecordDTO.created_at,
        "last_synced_at": ViewerSyncRecordDTO.last_synced_at,
        "last_checked_at": ViewerSyncRecordDTO.last_checked_at,
        "sync_status": ViewerSyncRecordDTO.sync_status,
        "entity_key": ViewerSyncRecordDTO.entity_key,
    }
    _DRIFT_SORT_COLUMNS = {
        "created_at": DriftEventDTO.created_at,
        "detected_at": DriftEventDTO.detected_at,
        "drift_type": DriftEventDTO.drift_type,
        "notification_status": DriftEventDTO.notification_status,
    }

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save_sync_record(self, record: ViewerSyncRecordDTO) -> ViewerSyncRecordDTO:
        async with self._session_provider.session() as session:
            current = await session.scalar(
                select(ViewerSyncRecordDTO).where(
                    ViewerSyncRecordDTO.project_key == record.project_key,
                    ViewerSyncRecordDTO.entity_type == record.entity_type,
                    ViewerSyncRecordDTO.entity_key == record.entity_key,
                    ViewerSyncRecordDTO.viewer_type == record.viewer_type,
                )
            )
            if current is not None:
                record.id = current.id
                record.created_at = current.created_at
            persisted = await session.merge(record)
            await session.commit()
            await session.refresh(persisted)
            return persisted

    async def save_drift_event(self, event: DriftEventDTO) -> DriftEventDTO:
        async with self._session_provider.session() as session:
            persisted = await session.merge(event)
            await session.commit()
            await session.refresh(persisted)
            return persisted

    async def find_sync_records_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[ViewerSyncRecordDTO]:
        return await self._find_sync_records_page(pagination, viewer_type=viewer_type)

    async def find_sync_records_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerSyncRecordDTO]:
        return await self._find_sync_records_page(
            pagination, project_key=project_key, viewer_type=viewer_type
        )

    async def find_drift_events_page(
        self, pagination: PaginationParams, viewer_type: ViewerType | None = None
    ) -> Page[DriftEventDTO]:
        return await self._find_drift_events_page(pagination, viewer_type=viewer_type)

    async def find_drift_events_page_by_project(
        self,
        project_key: str,
        pagination: PaginationParams,
        viewer_type: ViewerType | None = None,
    ) -> Page[DriftEventDTO]:
        return await self._find_drift_events_page(
            pagination, project_key=project_key, viewer_type=viewer_type
        )

    async def _find_sync_records_page(
        self,
        pagination: PaginationParams,
        project_key: str | None = None,
        viewer_type: ViewerType | None = None,
    ) -> Page[ViewerSyncRecordDTO]:
        conditions = []
        if project_key is not None:
            conditions.append(ViewerSyncRecordDTO.project_key == project_key)
        if viewer_type is not None:
            conditions.append(ViewerSyncRecordDTO.viewer_type == viewer_type.value)
        return await self._find_page(
            ViewerSyncRecordDTO, pagination, self._SYNC_SORT_COLUMNS, conditions
        )

    async def _find_drift_events_page(
        self,
        pagination: PaginationParams,
        project_key: str | None = None,
        viewer_type: ViewerType | None = None,
    ) -> Page[DriftEventDTO]:
        conditions = []
        if project_key is not None:
            conditions.append(DriftEventDTO.project_key == project_key)
        if viewer_type is None:
            return await self._find_page(
                DriftEventDTO, pagination, self._DRIFT_SORT_COLUMNS, conditions
            )
        conditions.append(ViewerSyncRecordDTO.viewer_type == viewer_type.value)
        return await self._find_page(
            DriftEventDTO,
            pagination,
            self._DRIFT_SORT_COLUMNS,
            conditions,
            join_sync_record=True,
        )

    async def _find_page(
        self, dto_type, pagination, sort_columns, conditions, join_sync_record: bool = False
    ):
        try:
            sort_column = sort_columns[pagination.sort_by or "created_at"]
        except KeyError as error:
            raise ValueError(f"unsupported viewer sort field: {pagination.sort_by}") from error
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        statement = select(dto_type)
        count_statement = select(func.count()).select_from(dto_type)
        if join_sync_record:
            join_condition = DriftEventDTO.sync_record_id == ViewerSyncRecordDTO.id
            statement = statement.join(ViewerSyncRecordDTO, join_condition)
            count_statement = count_statement.join(ViewerSyncRecordDTO, join_condition)
        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(*conditions)
        async with self._session_provider.session() as session:
            total = (await session.execute(count_statement)).scalar_one()
            result = await session.execute(
                statement.order_by(order_by, asc(dto_type.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(result.scalars().all()), total=total)
