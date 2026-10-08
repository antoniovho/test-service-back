from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import Page, PaginationParams, SortOrder
from test_service.domain.model.execution.execution import Execution, TriggerType
from test_service.infrastructure.adapters.output.execution.executions.execution_persistence_adapter import (  # noqa: E501
    ExecutionPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.mappers.execution_persistence_mapper import (  # noqa: E501
    ExecutionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories.execution_repository import (  # noqa: E501
    ExecutionRepository,
)


def _execution() -> Execution:
    return Execution(
        identifier=uuid4(),
        project_key="IAG",
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        trigger_type=TriggerType.API,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
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

    async def find_by_id(self, identifier):
        return self.dto

    async def claim_next_created(self):
        return self.dto

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
        found = await adapter.find_execution(execution.identifier)
        claimed = await adapter.claim_next_created()
        page = await adapter.find_page("IAG", PaginationParams())

        assert ExecutionPersistenceMapper.to_domain(dto) == execution
        assert saved == execution
        assert found == execution
        assert claimed == execution
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
        repository = ExecutionRepository(_SessionProvider(session))

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

    async def test_when_no_created_execution_exists_expect_no_claim(self):
        claim_result = MagicMock()
        claim_result.scalar_one_or_none.return_value = None
        session = MagicMock()
        session.execute = AsyncMock(return_value=claim_result)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        repository = ExecutionRepository(_SessionProvider(session))

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
        repository = ExecutionRepository(_SessionProvider(session))

        claimed = await repository.claim_next_created()

        assert claimed is execution
        assert execution.status == "RUNNING"
        assert execution.started_at.tzinfo is UTC
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(execution)
