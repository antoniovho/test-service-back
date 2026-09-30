from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.execution.execution import ArtifactType, ResultStatus, StorageType
from test_service.infrastructure.adapters.output.execution.executions.execution_results_persistence_adapter import (  # noqa: E501
    ExecutionResultsPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.dtos.execution_result_dtos import (  # noqa: E501
    ActionResultDTO,
    TestResultArtifactDTO,
    TestResultDTO,
)
from test_service.infrastructure.adapters.output.execution.executions.persistence.repositories.execution_results_repository import (  # noqa: E501
    ExecutionResultsRepository,
)


def _dtos():
    result = TestResultDTO(
        id=uuid4(),
        execution_id=uuid4(),
        test_case_id=uuid4(),
        status="PASSED",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    action = ActionResultDTO(
        id=uuid4(),
        test_result_id=result.id,
        action_id="login",
        action_type="HTTP",
        status="PASSED",
        expected={"code": 200},
        actual={"code": 200},
        output=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    artifact = TestResultArtifactDTO(
        id=uuid4(),
        test_result_id=result.id,
        action_result_id=action.id,
        artifact_type="LOG",
        storage_type="DB",
        storage_uri=None,
        content_hash=None,
        size_bytes=1,
        mime_type="text/plain",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    return result, action, artifact


class _Repository:
    def __init__(self, result, action, artifact):
        self.result, self.action, self.artifact = result, action, artifact

    async def find_result(self, identifier):
        return self.result

    async def find_results_page(self, identifier, pagination):
        return Page((self.result,), 1)

    async def find_actions_page(self, identifier, pagination):
        return Page((self.action,), 1)

    async def find_artifacts_page(self, identifier, pagination):
        return Page((self.artifact,), 1)


class _SessionProvider:
    def __init__(self, session):
        self._session = session

    @asynccontextmanager
    async def session(self):
        yield self._session


class TestExecutionResultsPersistence:
    async def test_when_mapping_adapter_results_expect_domain_pages(self):
        result, action, artifact = _dtos()
        adapter = ExecutionResultsPersistenceAdapter(_Repository(result, action, artifact))

        found = await adapter.find_result(result.id)
        results = await adapter.find_results_page(result.execution_id, PaginationParams())
        actions = await adapter.find_actions_page(result.id, PaginationParams())
        artifacts = await adapter.find_artifacts_page(result.id, PaginationParams())

        assert found.status is ResultStatus.PASSED
        assert results.items[0].test_case_id == result.test_case_id
        assert actions.items[0].expected["code"] == 200
        assert artifacts.items[0].artifact_type is ArtifactType.LOG
        assert artifacts.items[0].storage_type is StorageType.DB

    def test_when_sort_field_is_unknown_expect_value_error(self):
        with pytest.raises(ValueError, match="unsupported artifact sort field"):
            ExecutionResultsRepository._artifact_sort_column("unknown")

    async def test_when_repository_queries_expect_owned_pages(self):
        result, action, artifact = _dtos()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.side_effect = [[result], [action], [artifact]]
        session = MagicMock()
        session.get = AsyncMock(return_value=result)
        session.execute = AsyncMock(
            side_effect=[
                count_result,
                page_result,
                count_result,
                page_result,
                count_result,
                page_result,
            ]
        )
        repository = ExecutionResultsRepository(_SessionProvider(session))

        found = await repository.find_result(result.id)
        results = await repository.find_results_page(result.execution_id, PaginationParams())
        actions = await repository.find_actions_page(result.id, PaginationParams())
        artifacts = await repository.find_artifacts_page(result.id, PaginationParams())

        assert found is result
        assert results.items == (result,)
        assert actions.items == (action,)
        assert artifacts.items == (artifact,)
