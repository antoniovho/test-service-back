from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action import Action as ApiAction
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.definition import Definition as ApiDefinition
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.authoring.definition import Action, Definition
from test_service.domain.model.authoring.test_case import Priority, TestCase, TestLevel, TestType
from test_service.domain.ports.input.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_cases_rest_controller import (  # noqa: E501
    TestCasesRestController,
)


def _test_case() -> TestCase:
    return TestCase(
        identifier=uuid4(),
        project_key="IAG",
        test_key="IAG-1",
        version=1,
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        test_type=TestType.AUTOMATED,
        test_level=TestLevel.FUNCTIONAL,
        priority=Priority.HIGH,
        definition=Definition(
            schema_version="1.0",
            variables={},
            actions=(Action(identifier="request", action_type="HTTP_REQUEST", configuration={}),),
        ),
        timeout_seconds=30,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="author@example.test",
        metadata={},
    )


def _request() -> CreateTestCaseRequest:
    return CreateTestCaseRequest(
        testKey="IAG-1",
        name="Gateway test",
        summary="Checks the gateway",
        objective="Receive success",
        testType="AUTOMATED",
        testLevel="FUNCTIONAL",
        priority="HIGH",
        timeoutSeconds=30,
        definition=ApiDefinition(
            schemaVersion="1.0",
            variables={},
            actions=[ApiAction(id="request", type="HTTP_REQUEST", config={})],
        ),
    )


def _controller(test_case: TestCase) -> TestCasesRestController:
    controller = TestCasesRestController.__new__(TestCasesRestController)
    controller.__dict__.update(
        _create=SimpleNamespace(execute=AsyncMock(return_value=test_case)),
        _create_version=SimpleNamespace(execute=AsyncMock(return_value=test_case)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=test_case)),
        _activate=SimpleNamespace(execute=AsyncMock(return_value=test_case)),
        _deprecate=SimpleNamespace(execute=AsyncMock(return_value=test_case)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((test_case,), 1))),
        _list_versions=SimpleNamespace(execute=AsyncMock(return_value=Page((test_case,), 1))),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(name="AI Gateway"))
        ),
    )
    return controller


class TestTestCasesRestController:
    def test_when_constructed_expect_all_required_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(8)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_cases_rest_controller.get_injector",
            lambda: injector,
        )

        controller = TestCasesRestController()

        assert controller._create == 0
        assert controller._get_project == 7
        assert injector.inject.call_args_list == [
            ((CreateTestCaseUseCase,),),
            ((CreateTestCaseVersionUseCase,),),
            ((GetTestCaseUseCase,),),
            ((ActivateTestCaseUseCase,),),
            ((DeprecateTestCaseUseCase,),),
            ((ListTestCasesUseCase,),),
            ((ListTestCaseVersionsUseCase,),),
            ((GetProjectUseCase,),),
        ]

    async def test_when_test_case_commands_are_requested_expect_api_test_cases(self, monkeypatch):
        test_case = _test_case()
        controller = _controller(test_case)
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.authoring.test_cases.test_cases_rest_controller.get_current_identity",
            lambda: "author@example.test",
        )

        created = await controller.create("IAG", _request())
        found = await controller.get("IAG", test_case.identifier)
        version = await controller.create_version("IAG", test_case.identifier, _request())
        activated = await controller.activate(
            "IAG", test_case.identifier, ActionRequest(reason="approved")
        )
        deprecated = await controller.deprecate("IAG", test_case.identifier, None)

        assert created.id == test_case.identifier
        assert found.project.name == "AI Gateway"
        assert version.test_key == test_case.test_key
        assert activated.status == "DRAFT"
        assert deprecated.definition.actions[0].id == "request"

    async def test_when_test_cases_are_listed_expect_api_pagination(self):
        test_case = _test_case()
        controller = _controller(test_case)

        listed = await controller.list("IAG", "DRAFT", 0, 10, "version", ApiSortOrder.ASC)
        versions = await controller.list_versions(
            "IAG", "IAG-1", None, None, None, "createdAt", ApiSortOrder.DESC
        )

        assert listed.pagination.total == 1
        assert listed.data[0].id == test_case.identifier
        assert versions.pagination.offset == 0
        assert versions.data[0].test_key == "IAG-1"
