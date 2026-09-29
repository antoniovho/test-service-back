from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_plan_request import CreateTestPlanRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.ports.input.use_cases.composition.test_plans.activate_test_plan_use_case import (  # noqa: E501
    ActivateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_use_case import (  # noqa: E501
    CreateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_version_use_case import (  # noqa: E501
    CreateTestPlanVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.deprecate_test_plan_use_case import (  # noqa: E501
    DeprecateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.get_test_plan_use_case import (  # noqa: E501
    GetTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plan_versions_use_case import (  # noqa: E501
    ListTestPlanVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plans_use_case import (  # noqa: E501
    ListTestPlansUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plans_rest_controller import (  # noqa: E501
    TestPlansRestController,
)


def _test_plan() -> TestPlan:
    return TestPlan(
        uuid4(),
        "IAG",
        "checkout-nightly",
        1,
        "Checkout nightly",
        ExecutionMode.SEQUENTIAL,
        900,
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
        test_case_ids=(uuid4(),),
    )


def _request() -> CreateTestPlanRequest:
    return CreateTestPlanRequest(
        planKey="checkout-nightly",
        name="Checkout nightly",
        executionMode="SEQUENTIAL",
        timeoutSeconds=900,
    )


def _controller(test_plan: TestPlan) -> TestPlansRestController:
    controller = TestPlansRestController.__new__(TestPlansRestController)
    controller.__dict__.update(
        _create=SimpleNamespace(execute=AsyncMock(return_value=test_plan)),
        _create_version=SimpleNamespace(execute=AsyncMock(return_value=test_plan)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=test_plan)),
        _activate=SimpleNamespace(execute=AsyncMock(return_value=test_plan)),
        _deprecate=SimpleNamespace(execute=AsyncMock(return_value=test_plan)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((test_plan,), 1))),
        _list_versions=SimpleNamespace(execute=AsyncMock(return_value=Page((test_plan,), 1))),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(name="AI Gateway"))
        ),
    )
    return controller


class TestTestPlansRestController:
    def test_when_constructed_expect_all_required_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(8)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.composition.test_plans."
            "test_plans_rest_controller.get_injector",
            lambda: injector,
        )

        controller = TestPlansRestController()

        assert controller._create == 0
        assert controller._get_project == 7
        assert injector.inject.call_args_list == [
            ((CreateTestPlanUseCase,),),
            ((CreateTestPlanVersionUseCase,),),
            ((GetTestPlanUseCase,),),
            ((ActivateTestPlanUseCase,),),
            ((DeprecateTestPlanUseCase,),),
            ((ListTestPlansUseCase,),),
            ((ListTestPlanVersionsUseCase,),),
            ((GetProjectUseCase,),),
        ]

    async def test_when_test_plan_commands_are_requested_expect_api_test_plans(self, monkeypatch):
        test_plan = _test_plan()
        controller = _controller(test_plan)
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.composition.test_plans."
            "test_plans_rest_controller.get_current_identity",
            lambda: "author@example.test",
        )

        created = await controller.create("IAG", _request())
        found = await controller.get("IAG", test_plan.identifier)
        version = await controller.create_version("IAG", test_plan.identifier, _request())
        activated = await controller.activate(
            "IAG", test_plan.identifier, ActionRequest(reason="approved")
        )
        deprecated = await controller.deprecate("IAG", test_plan.identifier, None)

        assert created.id == test_plan.identifier
        assert found.project.name == "AI Gateway"
        assert version.plan_key == test_plan.plan_key
        assert activated.status == "DRAFT"
        assert deprecated.test_case_ids == list(test_plan.test_case_ids)

    async def test_when_test_plans_are_listed_expect_api_pagination(self):
        test_plan = _test_plan()
        controller = _controller(test_plan)

        listed = await controller.list("IAG", "DRAFT", 0, 10, "version", ApiSortOrder.ASC)
        versions = await controller.list_versions(
            "IAG", "checkout-nightly", None, None, None, "createdAt", ApiSortOrder.DESC
        )

        assert listed.pagination.total == 1
        assert listed.data[0].id == test_plan.identifier
        assert versions.pagination.offset == 0
        assert versions.data[0].plan_key == "checkout-nightly"
