"""Feature controller for immutable execution result operations."""

from uuid import UUID

from test_service_server.models.action_result_list_response import ActionResultListResponse
from test_service_server.models.test_result import TestResult as ApiTestResult
from test_service_server.models.test_result_artifact_list_response import (
    TestResultArtifactListResponse,
)
from test_service_server.models.test_result_list_response import TestResultListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCase,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.execution_results_mapper import (  # noqa: E501
    ExecutionResultsMapper,
)


class ExecutionResultsRestController:
    """Adapt immutable result use cases to the Execution REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._list_results = injector.inject(ListExecutionResultsUseCase)
        self._get_result = injector.inject(GetExecutionResultUseCase)
        self._list_actions = injector.inject(ListExecutionResultActionsUseCase)
        self._list_artifacts = injector.inject(ListExecutionResultArtifactsUseCase)

    async def list_results(
        self, project_key: str, execution_id: UUID, offset, limit, sort_by, order
    ) -> TestResultListResponse:
        query = ExecutionResultsMapper.to_list_results_query(
            project_key, execution_id, offset, limit, sort_by, order
        )
        results = await self._list_results.execute(query)
        return ExecutionResultsMapper.to_test_result_list_response(results, query.pagination)

    async def get_result(
        self, project_key: str, execution_id: UUID, test_result_id: UUID
    ) -> ApiTestResult:
        query = ExecutionResultsMapper.to_get_result_query(
            project_key, execution_id, test_result_id
        )
        result = await self._get_result.execute(query)
        return ExecutionResultsMapper.to_test_result_api(result)

    async def list_actions(
        self,
        project_key: str,
        execution_id: UUID,
        test_result_id: UUID,
        offset,
        limit,
        sort_by,
        order,
    ) -> ActionResultListResponse:
        query = ExecutionResultsMapper.to_list_actions_query(
            project_key, execution_id, test_result_id, offset, limit, sort_by, order
        )
        actions = await self._list_actions.execute(query)
        return ExecutionResultsMapper.to_action_result_list_response(actions, query.pagination)

    async def list_artifacts(
        self,
        project_key: str,
        execution_id: UUID,
        test_result_id: UUID,
        offset,
        limit,
        sort_by,
        order,
    ) -> TestResultArtifactListResponse:
        query = ExecutionResultsMapper.to_list_artifacts_query(
            project_key, execution_id, test_result_id, offset, limit, sort_by, order
        )
        artifacts = await self._list_artifacts.execute(query)
        return ExecutionResultsMapper.to_artifact_list_response(artifacts, query.pagination)
