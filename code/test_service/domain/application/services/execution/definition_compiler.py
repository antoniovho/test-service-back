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
        variables = {**definition.variables, **(environment_variables or {})}
        return CompiledTestCase(str(test_case_id), variables, actions)

    def _compile_action(self, identifier: str, action_type: str, position: int, configuration):
        """Validate one supported action and translate it to runner-ready work."""
        if action_type not in self._SUPPORTED_ACTIONS:
            raise InvalidDefinitionException(f"unsupported runner action type '{action_type}'")
        url = configuration.get("url")
        if not isinstance(url, str) or not url:
            raise InvalidDefinitionException(f"action '{identifier}' must define a non-empty url")
        if action_type == "HTTP":
            method = configuration.get("method", "GET")
            if not isinstance(method, str) or not method:
                raise InvalidDefinitionException(
                    f"HTTP action '{identifier}' has an invalid method"
                )
        return CompiledAction(identifier, action_type, position, configuration)
