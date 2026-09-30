from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.execution.environment import Environment, SecretReference
from test_service.domain.ports.input.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCase,
)
from test_service.infrastructure.adapters.input.rest.execution.environments.environment_mapper import (  # noqa: E501
    EnvironmentMapper,
)
from test_service.infrastructure.adapters.input.rest.execution.environments.environments_rest_controller import (  # noqa: E501
    EnvironmentsRestController,
)
from test_service.infrastructure.adapters.input.rest.execution.execution_controller import (
    ExecutionController,
)


def _environment() -> Environment:
    return Environment(
        identifier=uuid4(),
        environment_key="staging-eu",
        name="Staging Europe",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        configuration={"api_token": SecretReference("vault", "staging")},
    )


def _request() -> CreateEnvironmentRequest:
    return CreateEnvironmentRequest(
        environmentKey="staging-eu",
        name="Staging Europe",
        configuration={"api_token": {"provider": "vault", "referenceKey": "staging"}},
    )


def _controller(environment: Environment) -> EnvironmentsRestController:
    controller = EnvironmentsRestController.__new__(EnvironmentsRestController)
    controller.__dict__.update(
        _create=SimpleNamespace(execute=AsyncMock(return_value=environment)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=environment)),
        _activate=SimpleNamespace(execute=AsyncMock(return_value=environment)),
        _deactivate=SimpleNamespace(execute=AsyncMock(return_value=environment)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((environment,), 1))),
    )
    return controller


class TestEnvironmentRest:
    def test_when_mapping_request_expect_secret_reference_and_api_response(self):
        environment = _environment()

        command = EnvironmentMapper.to_create_command(
            _request(), "author@example.test", datetime(2026, 1, 1, tzinfo=UTC)
        )
        response = EnvironmentMapper.to_api(environment)

        assert command.configuration["api_token"] == SecretReference("vault", "staging")
        assert response.configuration["api_token"]["referenceKey"] == "staging"

    def test_when_mapping_list_query_expect_allowed_sort_field(self):
        query = EnvironmentMapper.to_list_query(0, 10, "environmentKey", ApiSortOrder.DESC)

        assert query.pagination.sort_by == "environment_key"
        assert query.pagination.order.value == "DESC"

    def test_when_mapping_empty_configuration_expect_none_preserved(self):
        request = CreateEnvironmentRequest(environmentKey="staging-eu", name="Staging Europe")

        command = EnvironmentMapper.to_create_command(
            request, "author@example.test", datetime(2026, 1, 1, tzinfo=UTC)
        )
        response = EnvironmentMapper.to_api(
            Environment(
                identifier=uuid4(),
                environment_key="staging-eu",
                name="Staging Europe",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                created_by="author@example.test",
            )
        )

        assert command.configuration is None
        assert response.configuration is None

    def test_when_constructed_expect_all_environment_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(5)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.environments."
            "environments_rest_controller.get_injector",
            lambda: injector,
        )

        controller = EnvironmentsRestController()

        assert controller._list == 4
        assert injector.inject.call_args_list == [
            ((CreateEnvironmentUseCase,),),
            ((GetEnvironmentUseCase,),),
            ((ActivateEnvironmentUseCase,),),
            ((DeactivateEnvironmentUseCase,),),
            ((ListEnvironmentsUseCase,),),
        ]

    async def test_when_environment_endpoints_are_called_expect_api_responses(self, monkeypatch):
        environment = _environment()
        controller = _controller(environment)
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.environments."
            "environments_rest_controller.get_current_identity",
            lambda: "author@example.test",
        )

        created = await controller.create(_request())
        found = await controller.get(environment.identifier)
        activated = await controller.activate(environment.identifier, ActionRequest(reason="ready"))
        deactivated = await controller.deactivate(environment.identifier, None)
        listed = await controller.list(0, 10, "name", ApiSortOrder.ASC)

        assert created.id == environment.identifier
        assert found.environment_key == environment.environment_key
        assert activated.status == "ACTIVE"
        assert deactivated.status == "ACTIVE"
        assert listed.pagination.total == 1

    async def test_when_execution_environment_endpoints_are_called_expect_delegation(self):
        feature = MagicMock()
        for method in ("create", "get", "activate", "deactivate", "list"):
            setattr(feature, method, AsyncMock(return_value=method))
        controller = ExecutionController.__new__(ExecutionController)
        controller._environments = feature
        identifier = uuid4()

        assert await controller.create_environment(_request()) == "create"
        assert await controller.get_environment(identifier) == "get"
        assert await controller.activate_environment(identifier, None) == "activate"
        assert await controller.deactivate_environment(identifier, None) == "deactivate"
        assert await controller.list_environments(0, 10, "name", ApiSortOrder.ASC) == "list"

    def test_when_execution_controller_is_constructed_expect_feature_controllers(self, monkeypatch):
        environment_feature = MagicMock()
        execution_feature = MagicMock()
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.execution_controller."
            "EnvironmentsRestController",
            lambda: environment_feature,
        )
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.execution.execution_controller."
            "ExecutionsRestController",
            lambda: execution_feature,
        )

        controller = ExecutionController()

        assert controller._environments is environment_feature
        assert controller._executions is execution_feature
