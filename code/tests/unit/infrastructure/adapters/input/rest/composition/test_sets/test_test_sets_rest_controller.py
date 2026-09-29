from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_test_set_request import CreateTestSetRequest
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.commons.pagination import Page
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.ports.input.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.get_test_set_use_case import (
    GetTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.composition.test_sets.test_sets_rest_controller import (  # noqa: E501
    TestSetsRestController,
)


def _test_set() -> TestSet:
    return TestSet(
        uuid4(),
        "IAG",
        "checkout",
        1,
        "Checkout",
        (uuid4(),),
        datetime(2026, 1, 1, tzinfo=UTC),
        "author@example.test",
    )


def _request() -> CreateTestSetRequest:
    return CreateTestSetRequest(setKey="checkout", name="Checkout", items=[uuid4()])


def _controller(test_set: TestSet) -> TestSetsRestController:
    controller = TestSetsRestController.__new__(TestSetsRestController)
    controller.__dict__.update(
        _create=SimpleNamespace(execute=AsyncMock(return_value=test_set)),
        _create_version=SimpleNamespace(execute=AsyncMock(return_value=test_set)),
        _get=SimpleNamespace(execute=AsyncMock(return_value=test_set)),
        _activate=SimpleNamespace(execute=AsyncMock(return_value=test_set)),
        _deprecate=SimpleNamespace(execute=AsyncMock(return_value=test_set)),
        _list=SimpleNamespace(execute=AsyncMock(return_value=Page((test_set,), 1))),
        _list_versions=SimpleNamespace(execute=AsyncMock(return_value=Page((test_set,), 1))),
        _get_project=SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(name="AI Gateway"))
        ),
    )
    return controller


class TestTestSetsRestController:
    def test_when_constructed_expect_all_required_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(8)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.composition.test_sets."
            "test_sets_rest_controller.get_injector",
            lambda: injector,
        )

        controller = TestSetsRestController()

        assert controller._create == 0
        assert controller._get_project == 7
        assert injector.inject.call_args_list == [
            ((CreateTestSetUseCase,),),
            ((CreateTestSetVersionUseCase,),),
            ((GetTestSetUseCase,),),
            ((ActivateTestSetUseCase,),),
            ((DeprecateTestSetUseCase,),),
            ((ListTestSetsUseCase,),),
            ((ListTestSetVersionsUseCase,),),
            ((GetProjectUseCase,),),
        ]

    async def test_when_test_set_commands_are_requested_expect_api_test_sets(self, monkeypatch):
        test_set = _test_set()
        controller = _controller(test_set)
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.composition.test_sets."
            "test_sets_rest_controller.get_current_identity",
            lambda: "author@example.test",
        )

        created = await controller.create("IAG", _request())
        found = await controller.get("IAG", test_set.identifier)
        version = await controller.create_version("IAG", test_set.identifier, _request())
        activated = await controller.activate(
            "IAG", test_set.identifier, ActionRequest(reason="approved")
        )
        deprecated = await controller.deprecate("IAG", test_set.identifier, None)

        assert created.id == test_set.identifier
        assert found.project.name == "AI Gateway"
        assert version.set_key == "checkout"
        assert activated.status == "DRAFT"
        assert deprecated.items == list(test_set.items)

    async def test_when_test_sets_are_listed_expect_api_pagination(self):
        test_set = _test_set()
        controller = _controller(test_set)

        listed = await controller.list("IAG", "DRAFT", 0, 10, "version", ApiSortOrder.ASC)
        versions = await controller.list_versions(
            "IAG", "checkout", None, None, None, "createdAt", ApiSortOrder.DESC
        )

        assert listed.pagination.total == 1
        assert listed.data[0].id == test_set.identifier
        assert versions.pagination.offset == 0
        assert versions.data[0].set_key == "checkout"
