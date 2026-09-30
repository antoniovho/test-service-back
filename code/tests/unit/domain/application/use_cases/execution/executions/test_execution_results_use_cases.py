from datetime import UTC, datetime
from uuid import uuid4

import pytest

from test_service.domain.application.queries.execution import (
    ExecutionResultQuery,
    ListExecutionResultActionsQuery,
    ListExecutionResultArtifactsQuery,
    ListExecutionResultsQuery,
)
from test_service.domain.application.services.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.execution_result_access_resolver import (
    ExecutionResultAccessResolver,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCaseImpl,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.execution import (
    ActionResult,
    ArtifactType,
    Execution,
    ResultStatus,
    StorageType,
    TestResult,
    TestResultArtifact,
    TriggerType,
)


def _execution(project_key: str = "IAG") -> Execution:
    return Execution(
        identifier=uuid4(),
        project_key=project_key,
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        trigger_type=TriggerType.API,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _result(execution_id) -> TestResult:
    return TestResult(
        identifier=uuid4(),
        execution_id=execution_id,
        test_case_id=uuid4(),
        status=ResultStatus.PASSED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class _ExecutionRepository:
    def __init__(self, execution):
        self.execution = execution

    async def find_execution(self, identifier):
        return self.execution


class _ResultsRepository:
    def __init__(self, result):
        self.result = result

    async def find_result(self, identifier):
        return self.result

    async def find_results_page(self, execution_id, pagination):
        return Page((self.result,), 1)

    async def find_actions_page(self, test_result_id, pagination):
        return Page(
            (
                ActionResult(
                    uuid4(),
                    test_result_id,
                    "login",
                    "HTTP",
                    ResultStatus.PASSED,
                    datetime(2026, 1, 1, tzinfo=UTC),
                ),
            ),
            1,
        )

    async def find_artifacts_page(self, test_result_id, pagination):
        return Page(
            (
                TestResultArtifact(
                    uuid4(),
                    test_result_id,
                    ArtifactType.LOG,
                    StorageType.DB,
                    datetime(2026, 1, 1, tzinfo=UTC),
                ),
            ),
            1,
        )


def _execution_access(execution):
    return ExecutionAccessResolver(_ExecutionRepository(execution))


def _result_access(result):
    return ExecutionResultAccessResolver(_ResultsRepository(result))


class TestExecutionResultsUseCases:
    async def test_when_execution_belongs_to_project_expect_results_page(self):
        execution = _execution()
        result = _result(execution.identifier)
        use_case = ListExecutionResultsUseCaseImpl(
            _execution_access(execution), _ResultsRepository(result)
        )

        page = await use_case.execute(
            ListExecutionResultsQuery("IAG", execution.identifier, PaginationParams())
        )

        assert page.items == (result,)

    async def test_when_execution_is_foreign_expect_result_not_found(self):
        execution = _execution()
        result = _result(execution.identifier)
        use_case = GetExecutionResultUseCaseImpl(
            _execution_access(execution), _result_access(result)
        )
        query = ExecutionResultQuery("ZAR", execution.identifier, result.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_result_belongs_to_another_execution_expect_not_found(self):
        execution = _execution()
        result = _result(uuid4())
        use_case = GetExecutionResultUseCaseImpl(
            _execution_access(execution), _result_access(result)
        )
        query = ExecutionResultQuery("IAG", execution.identifier, result.identifier)

        with pytest.raises(EntityNotFoundException):
            await use_case.execute(query)

    async def test_when_result_belongs_to_execution_expect_retrieved(self):
        execution = _execution()
        result = _result(execution.identifier)
        use_case = GetExecutionResultUseCaseImpl(
            _execution_access(execution), _result_access(result)
        )

        retrieved = await use_case.execute(
            ExecutionResultQuery("IAG", execution.identifier, result.identifier)
        )

        assert retrieved == result

    async def test_when_result_belongs_to_execution_expect_action_page(self):
        execution = _execution()
        result = _result(execution.identifier)
        use_case = ListExecutionResultActionsUseCaseImpl(
            _execution_access(execution), _result_access(result), _ResultsRepository(result)
        )

        page = await use_case.execute(
            ListExecutionResultActionsQuery(
                "IAG", execution.identifier, result.identifier, PaginationParams()
            )
        )

        assert page.items[0].test_result_id == result.identifier

    async def test_when_result_belongs_to_execution_expect_artifact_page(self):
        execution = _execution()
        result = _result(execution.identifier)
        use_case = ListExecutionResultArtifactsUseCaseImpl(
            _execution_access(execution), _result_access(result), _ResultsRepository(result)
        )

        page = await use_case.execute(
            ListExecutionResultArtifactsQuery(
                "IAG", execution.identifier, result.identifier, PaginationParams()
            )
        )

        assert page.items[0].test_result_id == result.identifier
