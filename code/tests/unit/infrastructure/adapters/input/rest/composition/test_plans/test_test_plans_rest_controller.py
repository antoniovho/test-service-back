import pytest

from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plans_rest_controller import (  # noqa: E501
    TestPlansRestController,
)


class TestTestPlansRestController:
    @pytest.mark.parametrize(
        "method_name",
        ("create", "get", "create_version", "activate", "deprecate", "list", "list_versions"),
    )
    async def test_when_test_plan_operation_is_requested_expect_not_implemented(self, method_name):
        controller = TestPlansRestController()

        operation = getattr(controller, method_name)

        with pytest.raises(
            NotImplementedError, match="Test Plan composition operations are not implemented yet"
        ):
            await operation()
