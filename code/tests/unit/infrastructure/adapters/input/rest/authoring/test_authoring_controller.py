from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from test_service_server.models.action_request import ActionRequest

from test_service.infrastructure.adapters.input.rest.authoring.authoring_controller import (
    AuthoringController,
)


class TestAuthoringController:
    async def test_when_constructed_expect_test_case_feature_controller(self, monkeypatch):
        feature_controller = MagicMock()
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.authoring.authoring_controller.TestCasesRestController",
            lambda: feature_controller,
        )

        controller = AuthoringController()

        assert controller._test_cases is feature_controller

    async def test_when_endpoints_are_called_expect_delegation_to_feature_controller(self):
        feature_controller = MagicMock()
        for method in (
            "create",
            "get",
            "create_version",
            "activate",
            "deprecate",
            "list",
            "list_versions",
        ):
            setattr(feature_controller, method, AsyncMock(return_value=method))
        controller = AuthoringController.__new__(AuthoringController)
        controller._test_cases = feature_controller
        identifier = uuid4()
        request = MagicMock()

        assert await controller.create_test_case("IAG", request) == "create"
        assert await controller.get_test_case("IAG", identifier) == "get"
        assert (
            await controller.create_test_case_version("IAG", identifier, request)
            == "create_version"
        )
        assert await controller.activate_test_case("IAG", identifier, ActionRequest()) == "activate"
        assert await controller.deprecate_test_case("IAG", identifier, None) == "deprecate"
        assert await controller.list_test_cases("IAG", None, 0, 10, None, None) == "list"
        assert (
            await controller.list_test_case_versions("IAG", "IAG-1", None, 0, 10, None, None)
            == "list_versions"
        )
