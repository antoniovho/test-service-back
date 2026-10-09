"""Resolution of Environment configuration into runner variables."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from test_service.domain.model.execution.environment import SecretReference
from test_service.domain.ports.output.secrets.secret_resolver_port import SecretResolverPort


@dataclass(frozen=True, slots=True)
class ExecutionVariables:
    """Variables an execution exposes to its runner.

    Args:
        values: Variable name to text value, with secrets already resolved.
        secrets: Resolved secret values that must never be persisted or exposed.
    """

    values: Mapping[str, str]
    secrets: frozenset[str]


class ExecutionVariablesResolver:
    """Turn the Environment snapshot of an execution into runner variables."""

    def __init__(self, secret_resolver: SecretResolverPort) -> None:
        self._secret_resolver = secret_resolver

    async def resolve(self, configuration: Mapping[str, object] | None) -> ExecutionVariables:
        """Resolve scalar configuration values and secret references.

        Args:
            configuration: Safe unresolved Environment snapshot of the execution.

        Returns:
            Text variables for the runner and the secret values among them. Values that
            are neither scalars nor secret references are not exposed as variables.

        Raises:
            SecretResolutionException: If a secret reference cannot be resolved.
        """
        values: dict[str, str] = {}
        secrets: set[str] = set()
        for name, value in (configuration or {}).items():
            if isinstance(value, SecretReference):
                resolved = await self._secret_resolver.resolve(value)
                values[name] = resolved
                secrets.add(resolved)
            elif isinstance(value, bool):
                values[name] = "true" if value else "false"
            elif isinstance(value, str | int | float):
                values[name] = str(value)
        return ExecutionVariables(MappingProxyType(values), frozenset(secrets))
