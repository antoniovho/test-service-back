from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from test_service.config import ExecutionSettings
from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.execution.execution import Execution, ExecutionStatus
from test_service.infrastructure.adapters.output.execution.executions.execution_persistence_adapter import (  # noqa: E501
    ExecutionPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.mappers.execution_persistence_mapper import (  # noqa: E501
    ExecutionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories import (  # noqa: E501
    execution_repository,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories.execution_repository import (  # noqa: E501
    ExecutionRepository,
)
from tests.mothers.execution_mother import an_execution

_FIXED_NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _execution() -> Execution:
    return an_execution(
        test_case_ids=(uuid4(),),
        environment_snapshot={"baseUrl": "https://staging.example.test"},
        runner_identifier="tavern",
        runner_version="2.4.1",
    )


class _Repository:
    def __init__(self, dto) -> None:
        self.dto = dto

    async def save(self, dto):
        return dto

    async def transition(self, dto, expected_statuses):
        return dto

    async def find_by_id(self, identifier):
        return self.dto

    async def claim_next_created(self):
        return self.dto

    async def mark_stale_running_as_error(self):
        return 0

    async def find_page(self, project_key, pagination):
        return Page((self.dto,), 1)


class _SessionProvider:
    def __init__(self, session: MagicMock) -> None:
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


class TestExecutionPersistence:
    async def test_when_mapping_and_adapting_expect_execution_round_trip(self):
        execution = _execution()
        dto = ExecutionPersistenceMapper.to_dto(execution)
        adapter = ExecutionPersistenceAdapter(_Repository(dto))

        saved = await adapter.save_execution(execution)
        running = execution.start(datetime(2026, 1, 1, tzinfo=UTC))
        completed = running.complete(
            ExecutionStatus.PASSED, datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC)
        )
        transitioned = await adapter.transition_execution(completed, (ExecutionStatus.RUNNING,))
        found = await adapter.find_execution(execution.identifier)
        claimed = await adapter.claim_next_created()
        recovered = await adapter.mark_stale_running_as_error()
        page = await adapter.find_page("IAG", PaginationParams())

        assert ExecutionPersistenceMapper.to_domain(dto) == execution
        assert saved == execution
        assert transitioned == completed
        assert found == execution
        assert claimed == execution
        assert recovered == 0
        assert page.items == (execution,)

    async def test_when_repository_operations_are_called_expect_persistence_results(self):
        dto = ExecutionPersistenceMapper.to_dto(_execution())
        total_result = MagicMock()
        total_result.scalar_one.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [dto]
        session = MagicMock()
        session.merge = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock(return_value=dto)
        session.execute = AsyncMock(side_effect=[total_result, page_result])
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        assert await repository.save(dto) is dto
        assert await repository.find_by_id(dto.id) is dto
        assert (
            await repository.find_page(
                "IAG", PaginationParams(sort_by="status", order=SortOrder.DESC)
            )
        ).items == (dto,)
        pagination = PaginationParams(sort_by="unsafe")

        with pytest.raises(ValueError, match="unsupported execution sort field"):
            await repository.find_page("IAG", pagination)

    @pytest.mark.parametrize(
        ("pagination", "expected_order"),
        (
            pytest.param(
                PaginationParams(offset=3, limit=7),
                "execution.created_at ASC, test_service_v1.execution.id ASC",
                id="default-created-at-ascending",
            ),
            pytest.param(
                PaginationParams(offset=5, limit=9, sort_by="status", order=SortOrder.DESC),
                "execution.status DESC, test_service_v1.execution.id ASC",
                id="status-descending",
            ),
        ),
    )
    async def test_when_page_is_requested_expect_project_scoped_deterministic_query(
        self, pagination, expected_order
    ):
        first_dto = ExecutionPersistenceMapper.to_dto(_execution())
        second_dto = ExecutionPersistenceMapper.to_dto(_execution())
        total_result = MagicMock()
        total_result.scalar_one.return_value = 12
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [first_dto, second_dto]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total_result, page_result])
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        page = await repository.find_page("IAG", pagination)

        count_statement, page_statement = (call.args[0] for call in session.execute.await_args_list)
        count_query = count_statement.compile()
        page_query = page_statement.compile()
        page_sql = str(page_query)
        assert page == Page((first_dto, second_dto), 12)
        assert "count(*)" in str(count_query).lower()
        assert "execution.project_key" in str(count_query)
        assert "execution.project_key" in page_sql
        assert f"ORDER BY test_service_v1.{expected_order}" in page_sql
        assert set(page_query.params.values()) >= {"IAG", pagination.offset, pagination.limit}

    async def test_when_page_is_requested_expect_count_and_rows_are_executed_separately(self):
        dto = ExecutionPersistenceMapper.to_dto(_execution())
        total_result = MagicMock()
        total_result.scalar_one.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [dto]
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[total_result, page_result])
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        page = await repository.find_page("IAG", PaginationParams())

        assert page == Page((dto,), 1)
        assert session.execute.await_count == 2

    async def test_when_execution_transition_matches_expected_status_expect_atomic_update(self):
        dto = ExecutionPersistenceMapper.to_dto(
            _execution().start(datetime(2026, 1, 1, tzinfo=UTC))
        )
        dto.status = "PASSED"
        result = MagicMock()
        result.scalar_one_or_none.return_value = dto
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        transitioned = await repository.transition(dto, ("RUNNING",))

        statement = session.execute.await_args.args[0]
        parameters = statement.compile().params.values()
        assert transitioned is dto
        assert "status IN" in str(statement)
        assert "RUNNING" in repr(parameters)
        assert "PASSED" in parameters
        session.commit.assert_awaited_once()

    async def test_when_execution_transition_loses_race_expect_current_state_preserved(self):
        dto = ExecutionPersistenceMapper.to_dto(
            _execution().start(datetime(2026, 1, 1, tzinfo=UTC))
        )
        dto.status = "CANCELLED"
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.get = AsyncMock(return_value=dto)
        session.commit = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        current = await repository.transition(dto, ("RUNNING",))

        assert current is dto
        session.commit.assert_not_awaited()
        session.get.assert_awaited_once()

    async def test_when_no_created_execution_exists_expect_no_claim(self):
        claim_result = MagicMock()
        claim_result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=claim_result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        claimed = await repository.claim_next_created()

        assert claimed is None
        session.commit.assert_not_awaited()
        session.refresh.assert_not_awaited()

    async def test_when_created_execution_exists_expect_claimed_running_execution(self):
        execution = MagicMock()
        claim_result = MagicMock()
        claim_result.scalar_one_or_none.return_value = execution
        session = MagicMock()
        session.execute = AsyncMock(return_value=claim_result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        claimed = await repository.claim_next_created()

        assert claimed is execution
        assert execution.status == "RUNNING"
        assert execution.started_at.tzinfo is UTC
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(execution)

    async def test_when_running_execution_is_stale_expect_marked_error_with_duration(
        self, monkeypatch
    ):
        started_at = _FIXED_NOW - timedelta(seconds=60)
        execution = MagicMock(status="RUNNING", started_at=started_at)
        test_plan = MagicMock(timeout_seconds=30)
        result = MagicMock()
        result.all.return_value = [(execution, test_plan)]
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ExecutionRepository(
            _SessionProvider(session), ExecutionSettings(recovery_timeout_seconds=30)
        )
        monkeypatch.setattr(
            execution_repository, "datetime", SimpleNamespace(now=lambda _: _FIXED_NOW)
        )

        recovered = await repository.mark_stale_running_as_error()

        statement = session.execute.await_args.args[0]
        threshold = next(
            value for value in statement.compile().params.values() if isinstance(value, datetime)
        )
        assert threshold == _FIXED_NOW - timedelta(seconds=30)
        assert recovered == 1
        assert execution.status == "ERROR"
        assert execution.finished_at >= started_at
        assert execution.duration_ms >= 60000
        session.commit.assert_awaited_once()

    async def test_when_no_running_execution_is_stale_expect_no_commit(self):
        result = MagicMock()
        result.all.return_value = []
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session), ExecutionSettings())

        recovered = await repository.mark_stale_running_as_error()

        assert recovered == 0
        session.commit.assert_not_awaited()

    async def test_when_running_execution_has_not_exceeded_plan_timeout_expect_not_recovered(
        self, monkeypatch
    ):
        started_at = _FIXED_NOW - timedelta(seconds=60)
        execution = MagicMock(status="RUNNING", started_at=started_at)
        test_plan = MagicMock(timeout_seconds=120)
        result = MagicMock()
        result.all.return_value = [(execution, test_plan)]
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ExecutionRepository(
            _SessionProvider(session), ExecutionSettings(recovery_timeout_seconds=30)
        )
        monkeypatch.setattr(
            execution_repository, "datetime", SimpleNamespace(now=lambda _: _FIXED_NOW)
        )

        recovered = await repository.mark_stale_running_as_error()

        assert recovered == 0
        assert execution.status == "RUNNING"
        session.commit.assert_not_awaited()

    async def test_when_recovery_boundaries_are_evaluated_expect_only_expired_rows_recovered(
        self, monkeypatch
    ):
        stale_execution = MagicMock(status="RUNNING", started_at=_FIXED_NOW - timedelta(seconds=31))
        exact_timeout_execution = MagicMock(
            status="RUNNING", started_at=_FIXED_NOW - timedelta(seconds=60)
        )
        missing_start_execution = MagicMock(status="RUNNING", started_at=None)
        no_plan_timeout = SimpleNamespace(timeout_seconds=0)
        sixty_second_timeout = SimpleNamespace(timeout_seconds=60)
        result = MagicMock()
        result.all.return_value = [
            (stale_execution, no_plan_timeout),
            (exact_timeout_execution, sixty_second_timeout),
            (missing_start_execution, no_plan_timeout),
        ]
        session = MagicMock()
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        repository = ExecutionRepository(
            _SessionProvider(session), ExecutionSettings(recovery_timeout_seconds=30)
        )
        monkeypatch.setattr(
            execution_repository, "datetime", SimpleNamespace(now=lambda _: _FIXED_NOW)
        )

        recovered = await repository.mark_stale_running_as_error()

        statement = session.execute.await_args.args[0]
        query = statement.compile(dialect=postgresql.dialect())
        assert recovered == 1
        assert stale_execution.status == "ERROR"
        assert stale_execution.finished_at == _FIXED_NOW
        assert stale_execution.duration_ms == 31000
        assert exact_timeout_execution.status == "RUNNING"
        assert missing_start_execution.status == "RUNNING"
        assert _FIXED_NOW - timedelta(seconds=30) in query.params.values()
        assert "execution.started_at <" in str(query)
        assert "FOR UPDATE OF execution SKIP LOCKED" in str(query)
        session.commit.assert_awaited_once()
