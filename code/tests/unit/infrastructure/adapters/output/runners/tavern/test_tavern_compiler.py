from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.tavern.compilers.tavern_compiler import (
    TavernCompiler,
)
from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    render_service_variables,
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


def test_render_service_variables_recursively_preserves_tavern_placeholders() -> None:
    rendered = render_service_variables(
        {"urls": ["{{baseUrl}}/events/{eventId}"], "enabled": True},
        {"baseUrl": "https://api.example.test"},
    )

    assert rendered == {
        "urls": ["https://api.example.test/events/{eventId}"],
        "enabled": True,
    }
