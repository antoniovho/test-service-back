"""SQLAlchemy repository for immutable execution evidence DTOs."""
# ruff: noqa: E501

from uuid import UUID

from sqlalchemy import asc, desc, func, select

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_result_dtos import (  # noqa: E501
    ActionResultDTO,
    TestResultArtifactDTO,
    TestResultDTO,
)


class ExecutionResultsRepository:
    """Read immutable execution evidence without exposing domain objects."""

    _RESULT_SORT_COLUMNS = {
        "created_at": TestResultDTO.created_at,
        "started_at": TestResultDTO.started_at,
        "finished_at": TestResultDTO.finished_at,
        "duration_ms": TestResultDTO.duration_ms,
        "status": TestResultDTO.status,
    }
    _ACTION_SORT_COLUMNS = {
        "created_at": ActionResultDTO.created_at,
        "started_at": ActionResultDTO.started_at,
        "finished_at": ActionResultDTO.finished_at,
        "duration_ms": ActionResultDTO.duration_ms,
        "status": ActionResultDTO.status,
    }
    _ARTIFACT_SORT_COLUMNS = {
        "created_at": TestResultArtifactDTO.created_at,
        "artifact_type": TestResultArtifactDTO.artifact_type,
        "storage_type": TestResultArtifactDTO.storage_type,
        "size_bytes": TestResultArtifactDTO.size_bytes,
    }

    def __init__(self, session_provider: PostgresSessionProvider) -> None:
        self._session_provider = session_provider

    async def save_results(
        self,
        result: TestResultDTO,
        actions: tuple[ActionResultDTO, ...],
        artifacts: tuple[TestResultArtifactDTO, ...],
    ) -> None:
        """Persist one immutable result tree in a single database transaction."""
        async with self._session_provider.session() as session:
            session.add(result)
            session.add_all(actions)
            session.add_all(artifacts)
            await session.commit()

    async def find_result(self, identifier: UUID) -> TestResultDTO | None:
        """Find an immutable test result by UUID."""
        async with self._session_provider.session() as session:
            return await session.get(TestResultDTO, identifier)

    async def find_results_page(
        self, execution_id: UUID, pagination: PaginationParams
    ) -> Page[TestResultDTO]:
        """Return a deterministically ordered page of results for an execution."""
        return await self._find_page(
            TestResultDTO,
            TestResultDTO.execution_id == execution_id,
            self._result_sort_column(pagination.sort_by),
            pagination,
        )

    async def find_actions_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[ActionResultDTO]:
        """Return a deterministically ordered page of actions for a test result."""
        return await self._find_page(
            ActionResultDTO,
            ActionResultDTO.test_result_id == test_result_id,
            self._action_sort_column(pagination.sort_by),
            pagination,
        )

    async def find_artifacts_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[TestResultArtifactDTO]:
        """Return a deterministically ordered page of artifact metadata for a result."""
        return await self._find_page(
            TestResultArtifactDTO,
            TestResultArtifactDTO.test_result_id == test_result_id,
            self._artifact_sort_column(pagination.sort_by),
            pagination,
        )

    async def _find_page(self, dto_type, ownership_filter, sort_column, pagination):
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        async with self._session_provider.session() as session:
            total_result = await session.execute(
                select(func.count()).select_from(dto_type).where(ownership_filter)
            )
            page_result = await session.execute(
                select(dto_type)
                .where(ownership_filter)
                .order_by(order_by, asc(dto_type.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(page_result.scalars().all()), total=total_result.scalar_one())

    @staticmethod
    def _result_sort_column(sort_by: str | None):
        return ExecutionResultsRepository._get_sort_column(
            ExecutionResultsRepository._RESULT_SORT_COLUMNS, sort_by, "result"
        )

    @staticmethod
    def _action_sort_column(sort_by: str | None):
        return ExecutionResultsRepository._get_sort_column(
            ExecutionResultsRepository._ACTION_SORT_COLUMNS, sort_by, "action result"
        )

    @staticmethod
    def _artifact_sort_column(sort_by: str | None):
        return ExecutionResultsRepository._get_sort_column(
            ExecutionResultsRepository._ARTIFACT_SORT_COLUMNS, sort_by, "artifact"
        )

    @staticmethod
    def _get_sort_column(columns, sort_by: str | None, resource_name: str):
        sort_name = sort_by or "created_at"
        try:
            return columns[sort_name]
        except KeyError as error:
            raise ValueError(f"unsupported {resource_name} sort field: {sort_name}") from error
