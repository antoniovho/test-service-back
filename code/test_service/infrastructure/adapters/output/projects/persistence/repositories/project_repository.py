"""SQLAlchemy repository for Project DTOs."""

from sqlalchemy import asc, desc, func, select

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)

from ..dtos.project_dto import ProjectDTO


class ProjectRepository:
    """Persist and retrieve Project DTOs without exposing domain objects."""

    _SORT_COLUMNS = {
        "key": ProjectDTO.key,
        "name": ProjectDTO.name,
        "created_at": ProjectDTO.created_at,
        "status": ProjectDTO.status,
    }

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save(self, project: ProjectDTO) -> ProjectDTO:
        """Insert or update a Project DTO and return its stored state."""
        async with self._session_provider.session() as session:
            persisted_project = await session.merge(project)
            await session.commit()
            await session.refresh(persisted_project)
            return persisted_project

    async def find_by_key(self, key: str) -> ProjectDTO | None:
        """Find a Project DTO by its stable key."""
        async with self._session_provider.session() as session:
            return await session.get(ProjectDTO, key)

    async def find_page(self, pagination: PaginationParams) -> Page[ProjectDTO]:
        """Return a deterministically ordered page of Project DTOs."""
        sort_column = self._get_sort_column(pagination.sort_by)
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)

        async with self._session_provider.session() as session:
            total_result = await session.execute(select(func.count()).select_from(ProjectDTO))
            page_result = await session.execute(
                select(ProjectDTO)
                .order_by(order_by, asc(ProjectDTO.key))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(page_result.scalars().all()), total=total_result.scalar_one())

    def _get_sort_column(self, sort_by: str | None):
        sort_name = sort_by or "created_at"
        try:
            return self._SORT_COLUMNS[sort_name]
        except KeyError as error:
            raise ValueError(f"unsupported project sort field: {sort_name}") from error
