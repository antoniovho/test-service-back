"""SQLAlchemy repository for Test Plan DTOs."""

from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.dtos.test_plan_dto import (  # noqa: E501
    TestPlanDTO,
)


class TestPlanRepository:
    """Persist and retrieve Test Plan DTOs without exposing domain objects."""

    _SORT_COLUMNS = {"version": TestPlanDTO.version, "created_at": TestPlanDTO.created_at}
    _LOAD_OPTIONS = (
        selectinload(TestPlanDTO.test_set_links),
        selectinload(TestPlanDTO.test_case_links),
        selectinload(TestPlanDTO.exclusion_links),
    )

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save(self, test_plan: TestPlanDTO) -> TestPlanDTO:
        """Insert or update one Test Plan snapshot."""
        async with self._session_provider.session() as session:
            persisted = await session.merge(test_plan)
            await session.commit()
            await session.refresh(
                persisted,
                attribute_names=["test_set_links", "test_case_links", "exclusion_links"],
            )
            return persisted

    async def find_by_id(self, identifier: UUID) -> TestPlanDTO | None:
        """Find one Test Plan snapshot by UUID."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(TestPlanDTO).options(*self._LOAD_OPTIONS).where(TestPlanDTO.id == identifier)
            )
            return result.scalar_one_or_none()

    async def find_latest_version(self, project_key: str, plan_key: str) -> int | None:
        """Return the maximum version number for one logical Test Plan."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(func.max(TestPlanDTO.version)).where(
                    TestPlanDTO.project_key == project_key, TestPlanDTO.plan_key == plan_key
                )
            )
            return result.scalar_one()

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> Page[TestPlanDTO]:
        """Return a project-scoped page of Test Plan snapshots."""
        conditions = [TestPlanDTO.project_key == project_key]
        if status is not None:
            conditions.append(TestPlanDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def find_versions(
        self,
        project_key: str,
        plan_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> Page[TestPlanDTO]:
        """Return a page of snapshots for one logical Test Plan."""
        conditions = [TestPlanDTO.project_key == project_key, TestPlanDTO.plan_key == plan_key]
        if status is not None:
            conditions.append(TestPlanDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def _find_page(self, conditions, pagination: PaginationParams) -> Page[TestPlanDTO]:
        sort_column = self._SORT_COLUMNS.get(pagination.sort_by or "created_at")
        if sort_column is None:
            raise ValueError(f"unsupported test plan sort field: {pagination.sort_by}")
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        async with self._session_provider.session() as session:
            total = (
                await session.execute(
                    select(func.count()).select_from(TestPlanDTO).where(*conditions)
                )
            ).scalar_one()
            result = await session.execute(
                select(TestPlanDTO)
                .options(*self._LOAD_OPTIONS)
                .where(*conditions)
                .order_by(order_by, asc(TestPlanDTO.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(result.scalars().all()), total=total)
