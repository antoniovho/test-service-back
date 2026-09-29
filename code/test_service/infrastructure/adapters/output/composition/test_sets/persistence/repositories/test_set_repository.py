"""SQLAlchemy repository for Test Set DTOs."""

from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.composition.test_sets.persistence.dtos.test_set_dto import (  # noqa: E501
    TestSetDTO,
)


class TestSetRepository:
    """Persist and retrieve Test Set DTOs without exposing domain objects."""

    _SORT_COLUMNS = {"version": TestSetDTO.version, "created_at": TestSetDTO.created_at}

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save(self, test_set: TestSetDTO) -> TestSetDTO:
        """Insert or update one Test Set snapshot."""
        async with self._session_provider.session() as session:
            persisted = await session.merge(test_set)
            await session.commit()
            await session.refresh(persisted, attribute_names=["item_links"])
            return persisted

    async def find_by_id(self, identifier: UUID) -> TestSetDTO | None:
        """Find one Test Set snapshot by UUID."""
        async with self._session_provider.session() as session:
            return await self._find_by_id(session, identifier)

    async def find_latest_version(self, project_key: str, set_key: str) -> int | None:
        """Return the maximum version number for one logical Test Set."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(func.max(TestSetDTO.version)).where(
                    TestSetDTO.project_key == project_key, TestSetDTO.set_key == set_key
                )
            )
            return result.scalar_one()

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> Page[TestSetDTO]:
        """Return a project-scoped page of Test Set snapshots."""
        conditions = [TestSetDTO.project_key == project_key]
        if status is not None:
            conditions.append(TestSetDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def find_versions(
        self,
        project_key: str,
        set_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> Page[TestSetDTO]:
        """Return a page of snapshots for one logical Test Set."""
        conditions = [TestSetDTO.project_key == project_key, TestSetDTO.set_key == set_key]
        if status is not None:
            conditions.append(TestSetDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def _find_by_id(self, session, identifier: UUID) -> TestSetDTO | None:
        result = await session.execute(
            select(TestSetDTO)
            .options(selectinload(TestSetDTO.item_links))
            .where(TestSetDTO.id == identifier)
        )
        return result.scalar_one_or_none()

    async def _find_page(self, conditions, pagination: PaginationParams) -> Page[TestSetDTO]:
        sort_column = self._SORT_COLUMNS.get(pagination.sort_by or "created_at")
        if sort_column is None:
            raise ValueError(f"unsupported test set sort field: {pagination.sort_by}")
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        async with self._session_provider.session() as session:
            total = (
                await session.execute(
                    select(func.count()).select_from(TestSetDTO).where(*conditions)
                )
            ).scalar_one()
            result = await session.execute(
                select(TestSetDTO)
                .options(selectinload(TestSetDTO.item_links))
                .where(*conditions)
                .order_by(order_by, asc(TestSetDTO.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(result.scalars().all()), total=total)
