from types import MappingProxyType

import pytest

from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.tavern.compilers.tavern_compiler import (
    TavernCompiler,
)


class TestTavernCompiler:
    def test_when_compiling_expect_service_variables_rendered_and_tavern_variables_preserved(
        self,
    ) -> None:
        action = CompiledAction(
            identifier="get-order",
            action_type="HTTP",
            position=0,
            configuration={
                "method": "GET",
                "url": "{{baseUrl}}/orders/{orderId}",
                "headers": {"X-Tenant": "{{tenant}}", "X-Order": "{orderId}"},
                "query": {"source": "{{source}}", "id": "{orderId}"},
                "expectedStatus": 200,
                "expectedJson": {"id": "{orderId}", "tenant": "{{tenant}}"},
            },
        )

        document = TavernCompiler().compile(
            (action,),
            {"baseUrl": "https://api.example.test", "tenant": "acme", "source": "web"},
        )

        stage = document["stages"][0]
        assert stage == {
            "name": "get-order",
            "request": {
                "method": "GET",
                "url": "https://api.example.test/orders/{orderId}",
                "headers": {"X-Tenant": "acme", "X-Order": "{orderId}"},
                "params": {"source": "web", "id": "{orderId}"},
            },
            "response": {
                "status_code": 200,
                "json": {"id": "{orderId}", "tenant": "acme"},
            },
        }

    def test_when_service_variable_is_undefined_expect_placeholder_preserved(self) -> None:
        action = CompiledAction(
            identifier="get-health",
            action_type="HTTP",
            position=0,
            configuration={"url": "{{baseUrl}}/health", "method": "GET"},
        )

        document = TavernCompiler().compile((action,), {})

        assert document["stages"][0]["request"]["url"] == "{{baseUrl}}/health"

    def test_when_configuration_is_immutable_expect_service_variables_rendered(self) -> None:
        action = CompiledAction(
            "get-order",
            "HTTP",
            0,
            MappingProxyType({"url": "{{baseUrl}}/orders", "headers": {"X-Tenant": "{{t}}"}}),
        )

        document = TavernCompiler().compile((action,), {"baseUrl": "https://api.test", "t": "acme"})

        assert document["stages"][0]["request"] == {
            "url": "https://api.test/orders",
            "headers": {"X-Tenant": "acme"},
        }

    def test_when_variable_value_contains_tavern_placeholder_expect_value_made_literal(
        self,
    ) -> None:
        action = CompiledAction(
            "get-order", "HTTP", 0, {"url": "https://api.test", "headers": {"X-Id": "{{id}}"}}
        )

        document = TavernCompiler().compile((action,), {"id": "{tavern.env_vars.SECRET}"})

        assert document["stages"][0]["request"]["headers"] == {"X-Id": "{{tavern.env_vars.SECRET}}"}

    @pytest.mark.parametrize(
        ("configuration", "construct"),
        [
            ({"url": "https://api.test", "json": {"$ext": {"function": "os:system"}}}, "$ext"),
            ({"url": "https://api.test", "save": {"$ext": {"function": "os:system"}}}, "$ext"),
            ({"url": "https://api.test", "headers": {"X": "{tavern.env_vars.SECRET}"}}, "tavern"),
            ({"url": "https://api.test?k={tavern.env_vars.SECRET}"}, "tavern"),
            ({"url": "https://api.test", "headers": {"X": "{id.__class__}"}}, "__class__"),
        ],
        ids=["ext-in-json", "ext-in-save", "tavern-in-header", "tavern-in-url", "dunder"],
    )
    def test_when_configuration_uses_reserved_construct_expect_value_error(
        self, configuration, construct
    ) -> None:
        action = CompiledAction("get-order", "HTTP", 0, configuration)

        with pytest.raises(ValueError, match="get-order") as exc:
            TavernCompiler().compile((action,), {})

        assert construct in str(exc.value)

    def test_when_configuration_is_not_an_object_expect_value_error(self) -> None:
        action = CompiledAction("get-order", "HTTP", 0, "not-a-mapping")

        with pytest.raises(ValueError, match="must be an object"):
            TavernCompiler().compile((action,), {})
