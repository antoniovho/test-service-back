from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

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

    async def recover_stale_running(self):
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
        recovered = await adapter.recover_stale_running()
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

        recovered = await repository.recover_stale_running()

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

        recovered = await repository.recover_stale_running()

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

        recovered = await repository.recover_stale_running()

        assert recovered == 0
        assert execution.status == "RUNNING"
        session.commit.assert_not_awaited()
