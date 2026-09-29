from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from test_service_server.models.action_request import ActionRequest

from test_service.infrastructure.adapters.input.rest.composition.composition_controller import (
    CompositionController,
)
from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plans_rest_controller import (  # noqa: E501
    TestPlansRestController,
)


def _feature_controller() -> MagicMock:
    controller = MagicMock()
    for method in (
        "create",
        "get",
        "create_version",
        "activate",
        "deprecate",
        "list",
        "list_versions",
    ):
        setattr(controller, method, AsyncMock(return_value=method))
    return controller


class TestCompositionController:
    async def test_when_test_set_endpoints_are_called_expect_feature_delegation(self):
        test_sets = _feature_controller()
        controller = CompositionController.__new__(CompositionController)
        controller._test_sets = test_sets
        identifier = uuid4()
        request = MagicMock()

        assert await controller.create_test_set("IAG", request) == "create"
        assert await controller.get_test_set("IAG", identifier) == "get"
        assert (
            await controller.create_test_set_version("IAG", identifier, request) == "create_version"
        )
        assert await controller.activate_test_set("IAG", identifier, ActionRequest()) == "activate"
        assert await controller.deprecate_test_set("IAG", identifier, None) == "deprecate"
        assert await controller.list_test_sets("IAG", None, 0, 10, None, None) == "list"
        assert (
            await controller.list_test_set_versions("IAG", "checkout", None, 0, 10, None, None)
            == "list_versions"
        )

    async def test_when_test_plan_endpoints_are_called_expect_feature_delegation(self):
        test_plans = _feature_controller()
        controller = CompositionController.__new__(CompositionController)
        controller._test_plans = test_plans
        identifier = uuid4()
        request = MagicMock()

        assert await controller.create_test_plan("IAG", request) == "create"
        assert await controller.get_test_plan("IAG", identifier) == "get"
        assert (
            await controller.create_test_plan_version("IAG", identifier, request)
            == "create_version"
        )
        assert await controller.activate_test_plan("IAG", identifier, ActionRequest()) == "activate"
        assert await controller.deprecate_test_plan("IAG", identifier, None) == "deprecate"
        assert await controller.list_test_plans("IAG", None, 0, 10, None, None) == "list"
        assert (
            await controller.list_test_plan_versions("IAG", "release", None, 0, 10, None, None)
            == "list_versions"
        )

    async def test_when_test_plan_vertical_is_not_implemented_expect_explicit_error(self):
        controller = TestPlansRestController()

        with pytest.raises(NotImplementedError, match="not implemented"):
            await controller.list("IAG", None, 0, 10, None, None)
