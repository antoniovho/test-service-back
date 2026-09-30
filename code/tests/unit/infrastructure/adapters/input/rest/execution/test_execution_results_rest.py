from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import (
    ActionResult,
    ArtifactType,
    ResultStatus,
    StorageType,
    TestResult,
    TestResultArtifact,
)
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
from test_service.infrastructure.adapters.input.rest.execution.executions.execution_results_rest_controller import (  # noqa: E501
    ExecutionResultsRestController,
)


def _result():
    return TestResult(
        uuid4(), uuid4(), uuid4(), ResultStatus.PASSED, datetime(2026, 1, 1, tzinfo=UTC)
    )


class TestExecutionResultsRest:
    def test_when_constructed_expect_result_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(4)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.executions."
            "execution_results_rest_controller.get_injector",
            lambda: injector,
        )

        controller = ExecutionResultsRestController()

        assert controller._list_artifacts == 3
        assert injector.inject.call_args_list == [
            ((ListExecutionResultsUseCase,),),
            ((GetExecutionResultUseCase,),),
            ((ListExecutionResultActionsUseCase,),),
            ((ListExecutionResultArtifactsUseCase,),),
        ]

    def test_when_mapping_queries_expect_project_scope_and_sort_fields(self):
        result = _result()

        result_query = ExecutionResultsMapper.to_list_results_query(
            "IAG", result.execution_id, 0, 10, "durationMs", ApiSortOrder.DESC
        )
        action_query = ExecutionResultsMapper.to_list_actions_query(
            "IAG", result.execution_id, result.identifier, 0, 10, "status", ApiSortOrder.ASC
        )
        artifact_query = ExecutionResultsMapper.to_list_artifacts_query(
            "IAG", result.execution_id, result.identifier, 0, 10, "sizeBytes", ApiSortOrder.ASC
        )

        assert result_query.project_key == "IAG"
        assert result_query.pagination.sort_by == "duration_ms"
        assert action_query.pagination.sort_by == "status"
        assert artifact_query.pagination.sort_by == "size_bytes"

    def test_when_mapping_domain_results_expect_api_responses(self):
        result = _result()
        action = ActionResult(
            uuid4(),
            result.identifier,
            "login",
            "HTTP",
            ResultStatus.PASSED,
            datetime(2026, 1, 1, tzinfo=UTC),
            expected={"code": 200},
        )
        artifact = TestResultArtifact(
            uuid4(),
            result.identifier,
            ArtifactType.LOG,
            StorageType.DB,
            datetime(2026, 1, 1, tzinfo=UTC),
        )
        pagination = ExecutionResultsMapper.to_list_results_query(
            "IAG", result.execution_id, 0, 10, None, None
        ).pagination

        result_response = ExecutionResultsMapper.to_test_result_list_response(
            Page((result,), 1), pagination
        )
        action_response = ExecutionResultsMapper.to_action_result_list_response(
            Page((action,), 1), pagination
        )
        artifact_response = ExecutionResultsMapper.to_artifact_list_response(
            Page((artifact,), 1), pagination
        )

        assert result_response.data[0].execution_id == result.execution_id
        assert action_response.data[0].expected == {"code": 200}
        assert artifact_response.data[0].artifact_type == "LOG"

    async def test_when_controller_endpoints_are_called_expect_mapped_responses(self):
        result = _result()
        controller = ExecutionResultsRestController.__new__(ExecutionResultsRestController)
        controller.__dict__.update(
            _list_results=SimpleNamespace(execute=AsyncMock(return_value=Page((result,), 1))),
            _get_result=SimpleNamespace(execute=AsyncMock(return_value=result)),
            _list_actions=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
            _list_artifacts=SimpleNamespace(execute=AsyncMock(return_value=Page((), 0))),
        )

        listed = await controller.list_results("IAG", result.execution_id, 0, 10, None, None)
        found = await controller.get_result("IAG", result.execution_id, result.identifier)
        actions = await controller.list_actions(
            "IAG", result.execution_id, result.identifier, 0, 10, None, None
        )
        artifacts = await controller.list_artifacts(
            "IAG", result.execution_id, result.identifier, 0, 10, None, None
        )

        assert listed.pagination.total == 1
        assert found.id == result.identifier
        assert actions.data == []
        assert artifacts.data == []
