"""Compilation from runner-neutral HTTP actions to Tavern documents."""

from collections.abc import Mapping
from typing import Any, cast

from jsonschema import Draft202012Validator

from test_service.domain.ports.output.runners.runner_dtos import CompiledAction
from test_service.infrastructure.adapters.output.runners.tavern.tavern_safety import (
    find_unsafe_tavern_construct,
)
from test_service.infrastructure.adapters.output.runners.tavern.variable_renderer import (
    escape_tavern_literal_braces,
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
        configuration = render_service_variables(
            action.configuration, variables, escape_braces=True
        )
        if not isinstance(configuration, dict):
            raise ValueError("HTTP action configuration must be an object")
        unsafe = find_unsafe_tavern_construct(configuration)
        if unsafe is not None:
            raise ValueError(f"HTTP action '{action.identifier}' uses {unsafe}")
        configuration = escape_tavern_literal_braces(configuration)
        if not isinstance(configuration, dict):
            raise ValueError("HTTP action configuration must be an object")
        return {
            "name": action.identifier,
            "request": TavernCompiler._compile_request(configuration),
            "response": TavernCompiler._compile_response(configuration),
        }

    @staticmethod
    def _compile_request(configuration: dict[str, object]) -> dict[str, object]:
        """Compile Tavern request arguments from one HTTP configuration."""
        request = {
            key: configuration[key]
            for key in ("url", "method", "headers", "params", "json")
            if key in configuration
        }
        if "query" in configuration:
            request["params"] = configuration["query"]
        return request

    @staticmethod
    def _compile_response(configuration: dict[str, object]) -> dict[str, object]:
        """Compile response checks and capture behavior for one HTTP action."""
        response: dict[str, object] = {"status_code": configuration.get("expectedStatus", 200)}
        response_validators = TavernCompiler._compile_response_validators(configuration)
        if response_validators:
            response["verify_response_with"] = (
                response_validators[0] if len(response_validators) == 1 else response_validators
            )
        for source_key, target_key in (
            ("expectedJson", "json"),
            ("expectedHeaders", "headers"),
            ("save", "save"),
        ):
            if source_key in configuration:
                response[target_key] = configuration[source_key]
        if "capture" in configuration:
            response["save"] = {"json": configuration["capture"]}
        return response

    @staticmethod
    def _compile_response_validators(
        configuration: dict[str, object],
    ) -> list[dict[str, object]]:
        """Compile fixed verifier hooks for the response assertions present."""
        response_validators: list[dict[str, object]] = []
        if "expectedJsonSchema" in configuration:
            expected_json_schema = configuration["expectedJsonSchema"]
            if not isinstance(expected_json_schema, Mapping):
                raise ValueError("expectedJsonSchema must be an object")
            schema = cast(Mapping[str, Any], expected_json_schema)
            Draft202012Validator.check_schema(schema)
            response_validators.append(
                TavernCompiler._response_validator("validate_json_schema", {"schema": schema})
            )
        if "expectedText" in configuration:
            response_validators.append(
                TavernCompiler._response_validator(
                    "validate_response_text",
                    {"expected_text": configuration["expectedText"]},
                )
            )
        if "expectedTextContains" in configuration:
            expected_text = configuration["expectedTextContains"]
            expected_texts = [expected_text] if isinstance(expected_text, str) else expected_text
            response_validators.append(
                TavernCompiler._response_validator(
                    "validate_response_contains_text", {"expected_texts": expected_texts}
                )
            )
        if "forbiddenText" in configuration:
            response_validators.append(
                TavernCompiler._response_validator(
                    "validate_response_excludes_text",
                    {"forbidden_texts": configuration["forbiddenText"]},
                )
            )
        if "expectedHeaderNames" in configuration:
            response_validators.append(
                TavernCompiler._response_validator(
                    "validate_response_header_names",
                    {"expected_header_names": configuration["expectedHeaderNames"]},
                )
            )
        return response_validators

    @staticmethod
    def _response_validator(name: str, extra_kwargs: dict[str, object]) -> dict[str, object]:
        """Return a verifier hook constrained to a fixed project-owned function."""
        return {
            "function": (
                "test_service.infrastructure.adapters.output.runners.tavern."
                f"json_schema_validator:{name}"
            ),
            "extra_kwargs": extra_kwargs,
        }
