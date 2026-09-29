"""SQLAlchemy repository for Precondition DTOs."""

from uuid import UUID

from sqlalchemy import asc, desc, func, select

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.dtos.precondition_dto import (  # noqa: E501
    PreconditionDTO,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)


class PreconditionRepository:
    """Retrieve Precondition DTOs required by Test Case authoring."""

    _SORT_COLUMNS = {"version": PreconditionDTO.version, "created_at": PreconditionDTO.created_at}

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def find_by_id(self, identifier: UUID) -> PreconditionDTO | None:
        """Find one Precondition snapshot by UUID."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(PreconditionDTO).where(PreconditionDTO.id == identifier)
            )
            return result.scalar_one_or_none()

    async def save(self, precondition: PreconditionDTO) -> PreconditionDTO:
        """Insert or update one Precondition snapshot."""
        async with self._session_provider.session() as session:
            persisted = await session.merge(precondition)
            await session.commit()
            await session.refresh(persisted)
            return persisted

    async def find_latest_version(self, project_key: str, precondition_key: str) -> int | None:
        """Return the maximum version number for one logical Precondition."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(func.max(PreconditionDTO.version)).where(
                    PreconditionDTO.project_key == project_key,
                    PreconditionDTO.precondition_key == precondition_key,
                )
            )
            return result.scalar_one()

    async def find_page(
        self, project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> Page[PreconditionDTO]:
        conditions = [PreconditionDTO.project_key == project_key]
        if status is not None:
            conditions.append(PreconditionDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def find_versions(
        self,
        project_key: str,
        precondition_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None,
    ) -> Page[PreconditionDTO]:
        conditions = [
            PreconditionDTO.project_key == project_key,
            PreconditionDTO.precondition_key == precondition_key,
        ]
        if status is not None:
            conditions.append(PreconditionDTO.status == status.value)
        return await self._find_page(conditions, pagination)

    async def _find_page(self, conditions, pagination: PaginationParams) -> Page[PreconditionDTO]:
        sort_column = self._SORT_COLUMNS.get(pagination.sort_by or "created_at")
        if sort_column is None:
            raise ValueError(f"unsupported precondition sort field: {pagination.sort_by}")
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        async with self._session_provider.session() as session:
            total = (
                await session.execute(
                    select(func.count()).select_from(PreconditionDTO).where(*conditions)
                )
            ).scalar_one()
            result = await session.execute(
                select(PreconditionDTO)
                .where(*conditions)
                .order_by(order_by, asc(PreconditionDTO.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(result.scalars().all()), total=total)
