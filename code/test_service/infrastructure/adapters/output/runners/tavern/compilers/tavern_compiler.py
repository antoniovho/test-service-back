"""Compilation from runner-neutral HTTP actions to Tavern documents."""

import re
from collections.abc import Mapping

from test_service.domain.ports.output.runners.runner_dtos import CompiledAction


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
        configuration = _render(action.configuration, variables)
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


def _render(value: object, variables: Mapping[str, str]) -> object:
    """Resolve service-owned placeholders while preserving Tavern variables."""
    if isinstance(value, str):
        return _VARIABLE.sub(lambda match: variables.get(match.group(1), match.group(0)), value)
    if isinstance(value, list):
        return [_render(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: _render(item, variables) for key, item in value.items()}
    return value


_VARIABLE = re.compile(r"\{\{([A-Za-z_]\w*)\}\}")
