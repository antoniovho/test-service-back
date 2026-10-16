"""Deterministic compiler from canonical Definitions to runner work."""
# ruff: noqa: E501

from collections.abc import Mapping
from uuid import UUID

from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.exceptions.invalid_definition_exception import (
    InvalidDefinitionException,
)
from test_service.domain.ports.output.runners.runner_dtos import (
    CompiledAction,
    CompiledTestCase,
)


class DefinitionCompiler:
    """Validate the V1 HTTP/SSE action vocabulary before scheduling work."""

    _SUPPORTED_ACTIONS = frozenset({"HTTP", "SSE"})
    _SUPPORTED_CONFIGURATION_KEYS = {
        "HTTP": frozenset(
            {
                "url",
                "method",
                "headers",
                "params",
                "query",
                "json",
                "expectedStatus",
                "expectedJson",
                "expectedText",
                "expectedTextContains",
                "forbiddenText",
                "save",
                "expectedHeaders",
                "expectedHeaderNames",
                "expectedJsonSchema",
                "maxResponseTimeMs",
                "capture",
            }
        ),
        "SSE": frozenset(
            {
                "url",
                "method",
                "headers",
                "params",
                "query",
                "json",
                "expectedEvent",
                "expectedData",
                "expectedDataJsonSchema",
                "expectedFinalDataJsonSchema",
                "expectedConcatenatedContent",
                "expectedContentType",
                "validateUsageTotals",
                "expectedDone",
                "maxEvents",
                "receiveTimeoutSeconds",
                "maxResponseTimeMs",
            }
        ),
    }

    def compile(
        self,
        test_case_id: UUID,
        definition: Definition,
        environment_variables: Mapping[str, str] | None = None,
    ) -> CompiledTestCase:
        """Produce stable work and reject unknown or malformed actions early.

        Args:
            test_case_id: Identifier of the snapshot being compiled.
            definition: Canonical definition to compile.
            environment_variables: Variables supplied by the execution Environment. They
                take precedence over a Definition variable with the same name, so choosing
                an Environment decides where and how the Definition runs.
        """
        actions = tuple(
            self._compile_action(
                action.identifier, action.action_type, position, action.configuration
            )
            for position, action in enumerate(definition.actions)
        )
        # Merge environment variables with definition variables, giving precedence to environment variables.
        variables = {**definition.variables, **(environment_variables or {})}
        return CompiledTestCase(str(test_case_id), variables, actions)

    def _compile_action(
        self,
        identifier: str,
        action_type: str,
        position: int,
        configuration: Mapping[str, object],
    ) -> CompiledAction:
        """Validate one supported action and translate it to runner-ready work."""
        self._validate_action_type(action_type)
        self._validate_configuration_keys(identifier, action_type, configuration)
        self._validate_action_configuration(identifier, action_type, configuration)
        return CompiledAction(identifier, action_type, position, configuration)

    @classmethod
    def _validate_action_type(cls, action_type: str) -> None:
        """Reject action types not implemented by an output runner."""
        if action_type not in cls._SUPPORTED_ACTIONS:
            raise InvalidDefinitionException(f"unsupported runner action type '{action_type}'")

    @classmethod
    def _validate_configuration_keys(
        cls, identifier: str, action_type: str, configuration: Mapping[str, object]
    ) -> None:
        """Reject configuration keys that the selected action runner ignores."""
        unsupported_keys = set(configuration) - cls._SUPPORTED_CONFIGURATION_KEYS[action_type]
        if unsupported_keys:
            raise InvalidDefinitionException(
                f"{action_type} action '{identifier}' has unsupported configuration keys "
                f"{sorted(unsupported_keys)}"
            )

    @classmethod
    def _validate_action_configuration(
        cls, identifier: str, action_type: str, configuration: Mapping[str, object]
    ) -> None:
        """Validate common URL and action-specific request/response options."""
        url = configuration.get("url")
        if not isinstance(url, str) or not url:
            raise InvalidDefinitionException(f"action '{identifier}' must define a non-empty url")
        if action_type == "HTTP":
            cls._validate_http_configuration(identifier, configuration)
            return
        cls._validate_sse_configuration(identifier, configuration)

    @classmethod
    def _validate_http_configuration(
        cls, identifier: str, configuration: Mapping[str, object]
    ) -> None:
        """Validate HTTP request methods and text assertion inputs."""
        method = configuration.get("method", "GET")
        if not isinstance(method, str) or not method:
            raise InvalidDefinitionException(f"HTTP action '{identifier}' has an invalid method")
        if "expectedTextContains" in configuration:
            cls._validate_text_values(
                identifier, "expectedTextContains", configuration["expectedTextContains"], 50, 16384
            )
        if "forbiddenText" in configuration:
            cls._validate_text_values(
                identifier, "forbiddenText", configuration["forbiddenText"], 50, 4096
            )

    @classmethod
    def _validate_text_values(
        cls,
        identifier: str,
        key: str,
        value: object,
        max_count: int,
        max_length: int,
    ) -> None:
        """Validate bounded, unique response text markers."""
        if key == "expectedTextContains" and isinstance(value, str):
            values = [value]
        elif isinstance(value, list | tuple):
            values = value
        else:
            values = []
        if (
            not values
            or len(values) > max_count
            or any(
                not isinstance(item, str) or not item or len(item) > max_length for item in values
            )
            or len(set(values)) != len(values)
        ):
            raise InvalidDefinitionException(
                f"HTTP action '{identifier}' {key} must contain unique non-empty strings"
            )

    @staticmethod
    def _validate_sse_configuration(identifier: str, configuration: Mapping[str, object]) -> None:
        """Validate the supported SSE request method."""
        method = configuration.get("method", "GET")
        if method not in {"GET", "POST"}:
            raise InvalidDefinitionException(
                f"SSE action '{identifier}' method must be GET or POST"
            )
