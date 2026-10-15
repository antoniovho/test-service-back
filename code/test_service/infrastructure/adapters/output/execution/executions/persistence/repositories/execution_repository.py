"""SQLAlchemy repository for Execution DTOs."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import asc, desc, func, select, update

from test_service.config import ExecutionSettings
from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.dtos.test_plan_dto import (  # noqa: E501
    TestPlanDTO,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_dto import (  # noqa: E501
    ExecutionDTO,
)


class ExecutionRepository:
    """Persist and retrieve Execution DTOs without exposing domain objects."""

    _SORT_COLUMNS = {
        "created_at": ExecutionDTO.created_at,
        "started_at": ExecutionDTO.started_at,
        "finished_at": ExecutionDTO.finished_at,
        "duration_ms": ExecutionDTO.duration_ms,
        "status": ExecutionDTO.status,
    }

    def __init__(
        self, session_provider: PostgresSessionProvider, settings: ExecutionSettings
    ) -> None:
        self._session_provider = session_provider
        self._settings = settings

    async def save(self, execution: ExecutionDTO) -> ExecutionDTO:
        """Insert or update an Execution DTO and return its stored state."""
        async with self._session_provider.session() as session:
            persisted_execution = await session.merge(execution)
            await session.commit()
            await session.refresh(persisted_execution)
            return persisted_execution

    async def transition(
        self, execution: ExecutionDTO, expected_statuses: tuple[str, ...]
    ) -> ExecutionDTO | None:
        """Update terminal fields only while the row remains in an expected state."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                update(ExecutionDTO)
                .where(
                    (ExecutionDTO.id == execution.id) & (ExecutionDTO.status.in_(expected_statuses))
                )
                .values(
                    status=execution.status,
                    finished_at=execution.finished_at,
                    duration_ms=execution.duration_ms,
                )
                .returning(ExecutionDTO)
            )
            transitioned = result.scalar_one_or_none()
            if transitioned is not None:
                await session.commit()
                return transitioned
            return await session.get(ExecutionDTO, execution.id)

    async def find_by_id(self, identifier: UUID) -> ExecutionDTO | None:
        """Find an Execution DTO by UUID."""
        async with self._session_provider.session() as session:
            return await session.get(ExecutionDTO, identifier)

    async def claim_next_created(self) -> ExecutionDTO | None:
        """Claim one queued execution with a cross-process row lock."""
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(ExecutionDTO)
                .where(ExecutionDTO.status == "CREATED")
                .order_by(asc(ExecutionDTO.created_at))
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            execution = result.scalar_one_or_none()
            if execution is None:
                return None
            execution.status = "RUNNING"
            execution.started_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(execution)
            return execution

    async def mark_stale_running_as_error(self) -> int:
        """Mark expired RUNNING leases as ERROR without re-running their work."""
        recovered_at = datetime.now(UTC)
        stale_before = recovered_at - timedelta(seconds=self._settings.recovery_timeout_seconds)
        async with self._session_provider.session() as session:
            result = await session.execute(
                select(ExecutionDTO, TestPlanDTO)
                .join(TestPlanDTO, TestPlanDTO.id == ExecutionDTO.test_plan_id)
                .where(
                    (ExecutionDTO.status == "RUNNING") & (ExecutionDTO.started_at < stale_before)
                )
                .with_for_update(of=ExecutionDTO, skip_locked=True)
            )
            executions = tuple(
                (execution, started_at)
                for execution, test_plan in result.all()
                if (started_at := execution.started_at) is not None
                and started_at
                < recovered_at
                - timedelta(
                    seconds=max(
                        self._settings.recovery_timeout_seconds,
                        test_plan.timeout_seconds,
                    )
                )
            )
            for execution, started_at in executions:
                execution.status = "ERROR"
                execution.finished_at = recovered_at
                execution.duration_ms = int((recovered_at - started_at).total_seconds() * 1000)
            if executions:
                await session.commit()
            return len(executions)

    async def find_page(self, project_key: str, pagination: PaginationParams) -> Page[ExecutionDTO]:
        """Return a deterministically ordered page for one project."""
        sort_column = self._get_sort_column(pagination.sort_by)
        order_by = desc(sort_column) if pagination.order is SortOrder.DESC else asc(sort_column)
        filter_by_project = ExecutionDTO.project_key == project_key

        async with self._session_provider.session() as session:
            total_result = await session.execute(
                select(func.count()).select_from(ExecutionDTO).where(filter_by_project)
            )
            page_result = await session.execute(
                select(ExecutionDTO)
                .where(filter_by_project)
                .order_by(order_by, asc(ExecutionDTO.id))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            return Page(items=tuple(page_result.scalars().all()), total=total_result.scalar_one())

    def _get_sort_column(self, sort_by: str | None):
        sort_name = sort_by or "created_at"
        try:
            return self._SORT_COLUMNS[sort_name]
        except KeyError as error:
            raise ValueError(f"unsupported execution sort field: {sort_name}") from error
