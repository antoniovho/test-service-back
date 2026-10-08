from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.create_execution_request import CreateExecutionRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.execution import Execution, TriggerType
from test_service.domain.ports.input.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.execution.execution_controller import (
    ExecutionController,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.execution_mapper import (  # noqa: E501
    ExecutionMapper,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.executions_rest_controller import (  # noqa: E501
    ExecutionsRestController,
)


def _execution() -> Execution:
    return Execution(
        identifier=uuid4(),
        project_key="IAG",
        test_plan_id=uuid4(),
        environment_id=uuid4(),
        trigger_type=TriggerType.API,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        runner_identifier="tavern",
        runner_version="2.4.1",
    )


def _request(execution: Execution) -> CreateExecutionRequest:
    return CreateExecutionRequest(
        testPlanId=execution.test_plan_id,
        environmentId=execution.environment_id,
        triggerType="API",
    )


def _controller(execution: Execution) -> ExecutionsRestController:
    controller = ExecutionsRestController.__new__(ExecutionsRestController)
    controller.__dict__.update(
        _schedule=SimpleNamespace(execute=AsyncMock(return_value=execution)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=execution)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((execution,), 1))),
        _cancel=SimpleNamespace(execute=AsyncMock(return_value=execution)),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(name="AI Gateway"))
        ),
    )
    return controller


class TestExecutionRest:
    def test_when_mapping_requests_expect_project_scoped_domain_values(self):
        execution = _execution()

        schedule = ExecutionMapper.to_schedule_command(
            "IAG", _request(execution), datetime(2026, 1, 1, tzinfo=UTC)
        )
        listed = ExecutionMapper.to_list_query("IAG", 0, 10, "durationMs", ApiSortOrder.DESC)

        assert schedule.project_key == "IAG"
        assert schedule.trigger_type is TriggerType.API
        assert ExecutionMapper.to_get_query("IAG", execution.identifier).project_key == "IAG"
        assert (
            ExecutionMapper.to_cancel_command("IAG", execution.identifier).identifier
            == execution.identifier
        )
        assert listed.pagination.sort_by == "duration_ms"

    def test_when_mapping_execution_expect_api_resource_and_page(self):
        execution = _execution()
        pagination = ExecutionMapper.to_list_query("IAG", 0, 10, None, None).pagination

        response = ExecutionMapper.to_api(execution, "AI Gateway")
        page = ExecutionMapper.to_list_response(Page((execution,), 1), "AI Gateway", pagination)

        assert response.project.name == "AI Gateway"
        assert response.status == "CREATED"
        assert response.runner_identifier == "tavern"
        assert response.runner_version == "2.4.1"
        assert page.pagination.total == 1

    def test_when_constructed_expect_execution_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(5)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.executions."
            "executions_rest_controller.get_injector",
            lambda: injector,
        )

        controller = ExecutionsRestController()

        assert controller._get_project == 4
        assert injector.inject.call_args_list == [
            ((ScheduleExecutionUseCase,),),
            ((GetExecutionUseCase,),),
            ((ListExecutionsUseCase,),),
            ((CancelExecutionUseCase,),),
            ((GetProjectUseCase,),),
        ]

    async def test_when_execution_endpoints_are_called_expect_api_responses(self):
        execution = _execution()
        controller = _controller(execution)

        created = await controller.create("IAG", _request(execution))
        found = await controller.get("IAG", execution.identifier)
        cancelled = await controller.cancel("IAG", execution.identifier)
        listed = await controller.list("IAG", 0, 10, "createdAt", ApiSortOrder.ASC)

        assert created.id == execution.identifier
        assert found.project.key == "IAG"
        assert cancelled.status == "CREATED"
        assert listed.data[0].test_plan_id == execution.test_plan_id

    async def test_when_execution_endpoints_are_called_expect_facade_delegation(self):
        feature = MagicMock()
        for method in ("create", "get", "cancel", "list"):
            setattr(feature, method, AsyncMock(return_value=method))
        controller = ExecutionController.__new__(ExecutionController)
        controller._executions = feature
        identifier = uuid4()

        assert await controller.create_execution("IAG", _request(_execution())) == "create"
        assert await controller.get_execution("IAG", identifier) == "get"
        assert await controller.cancel_execution("IAG", identifier) == "cancel"
        assert (
            await controller.list_executions("IAG", 0, 10, "createdAt", ApiSortOrder.ASC) == "list"
        )
