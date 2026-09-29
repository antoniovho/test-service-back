"""SQLAlchemy repository for Test Case DTOs."""

from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.test_cases.persistence.dtos.test_case_dto import (  # noqa: E501
    TestCaseDTO,
    TestCasePreconditionDTO,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)


class TestCaseRepository:
    """Persist and retrieve Test Case DTOs without exposing domain objects."""

    _SORT_COLUMNS = {"version": TestCaseDTO.version, "created_at": TestCaseDTO.created_at}

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save(self, test_case: TestCaseDTO) -> TestCaseDTO:
        """Insert or update one Test Case snapshot."""
        async with self._session_provider.session() as session:
            persisted = await session.merge(test_case)
            await session.commit()
            await session.refresh(persisted)
            return persisted

    async def find_by_id(self, identifier: UUID) -> TestCaseDTO | None:
        """Find one Test Case snapshot by UUID."""
        async with self._session_provider.session() as session:
            return await self._find_by_id(session, identifier)

    async def find_latest_version(self, project_key: str, test_key: str) -> int | None:
        """Return the maximum version number for one logical Test Case."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(func.max(TestCaseDTO.version)).where(
                    TestCaseDTO.project_key == project_key, TestCaseDTO.test_key == test_key
                )
            )
            return result.scalar_one()

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> Page[TestCaseDTO]:
        """Return a project-scoped page of Test Case snapshots."""
        conditions = [TestCaseDTO.project_key == project_key]
        if status is not None:
            conditions.append(TestCaseDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def find_versions(
        self,
        project_key: str,
        test_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> Page[TestCaseDTO]:
        """Return a page of snapshots for one logical Test Case."""
        conditions = [TestCaseDTO.project_key == project_key, TestCaseDTO.test_key == test_key]
        if status is not None:
            conditions.append(TestCaseDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def _find_by_id(self, session, identifier: UUID) -> TestCaseDTO | None:
        result = await session.execute(
            select(TestCaseDTO)
            .options(
                selectinload(TestCaseDTO.precondition_links).selectinload(
                    TestCasePreconditionDTO.precondition
                )
            )
            .where(TestCaseDTO.id == identifier)
        )
        return result.scalar_one_or_none()

    async def _find_page(self, conditions, pagination: PaginationParams) -> Page[TestCaseDTO]:
        sort_column = self._SORT_COLUMNS.get(pagination.sort_by or "created_at")
        if sort_column is None:
            raise ValueError(f"unsupported test case sort field: {pagination.sort_by}")
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        async with self._session_provider.session() as session:
            total = (
                await session.execute(
                    select(func.count()).select_from(TestCaseDTO).where(*conditions)
                )
            ).scalar_one()
            result = await session.execute(
                select(TestCaseDTO)
                .options(
                    selectinload(TestCaseDTO.precondition_links).selectinload(
                        TestCasePreconditionDTO.precondition
                    )
                )
                .where(*conditions)
                .order_by(order_by, asc(TestCaseDTO.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(result.scalars().all()), total=total)
