"""Compilation from runner-neutral HTTP actions to Tavern documents."""

from collections.abc import Mapping

from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    render_service_variables,
)


class TavernCompiler:
    """Compile consecutive HTTP actions into one Tavern multi-stage test."""

    def compile(
        self, actions: tuple[CompiledAction, ...], variables: Mapping[str, str]
    ) -> dict[str, object]:
        """Produce one ordered Tavern document from HTTP runner actions."""
        return {
            "test_name": "Test Service execution block",
            "stages": [self._compile_stage(action, variables) for action in actions],
        }

    @staticmethod
    def _compile_stage(action: CompiledAction, variables: Mapping[str, str]) -> dict[str, object]:
        """Compile one neutral HTTP action into a named Tavern stage."""
        configuration = render_service_variables(action.configuration, variables)
        if not isinstance(configuration, dict):
            raise ValueError("HTTP action configuration must be an object")
        request = {
            key: configuration[key]
            for key in ("url", "method", "headers", "params", "json")
            if key in configuration
        }
        if "query" in configuration:
            request["params"] = configuration["query"]
        response: dict[str, object] = {"status_code": configuration.get("expectedStatus", 200)}
        if "expectedJson" in configuration:
            response["json"] = configuration["expectedJson"]
        if "save" in configuration:
            response["save"] = configuration["save"]
        return {"name": action.identifier, "request": request, "response": response}
