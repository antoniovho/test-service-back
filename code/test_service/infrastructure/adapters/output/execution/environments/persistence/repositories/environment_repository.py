"""SQLAlchemy repository for Environment DTOs."""

from sqlalchemy import asc, desc, func, select

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.dtos.environment_dto import (  # noqa: E501
    EnvironmentDTO,
)


class EnvironmentRepository:
    """Persist and retrieve Environment DTOs without exposing domain objects."""

    _SORT_COLUMNS = {
        "environment_key": EnvironmentDTO.environment_key,
        "name": EnvironmentDTO.name,
        "created_at": EnvironmentDTO.created_at,
        "status": EnvironmentDTO.status,
    }

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save(self, environment: EnvironmentDTO) -> EnvironmentDTO:
        """Insert or update an Environment DTO and return its stored state."""
        async with self._session_provider.session() as session:
            persisted_environment = await session.merge(environment)
            await session.commit()
            await session.refresh(persisted_environment)
            return persisted_environment

    async def find_by_id(self, identifier) -> EnvironmentDTO | None:
        """Find an Environment DTO by UUID."""
        async with self._session_provider.session() as session:
            return await session.get(EnvironmentDTO, identifier)

    async def find_by_key(self, environment_key: str) -> EnvironmentDTO | None:
        """Find an Environment DTO by its stable global business key."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(EnvironmentDTO).where(EnvironmentDTO.environment_key == environment_key)
            )
            return result.scalar_one_or_none()

    async def find_page(self, pagination: PaginationParams) -> Page[EnvironmentDTO]:
        """Return a deterministically ordered page of Environment DTOs."""
        sort_column = self._get_sort_column(pagination.sort_by)
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)

        async with self._session_provider.session() as session:
            total_result = await session.execute(select(func.count()).select_from(EnvironmentDTO))
            page_result = await session.execute(
                select(EnvironmentDTO)
                .order_by(order_by, asc(EnvironmentDTO.environment_key))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(page_result.scalars().all()), total=total_result.scalar_one())

    def _get_sort_column(self, sort_by: str | None):
        sort_name = sort_by or "name"
        try:
            return self._SORT_COLUMNS[sort_name]
        except KeyError as error:
            raise ValueError(f"unsupported environment sort field: {sort_name}") from error
