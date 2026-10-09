"""Contract for turning a SecretReference into its value outside the domain."""

from typing import Protocol

from test_service.domain.model.execution.environment import SecretReference


class SecretResolverPort(Protocol):
    """Resolve secret references held by an Environment configuration."""

    async def resolve_secret(self, reference: SecretReference) -> str:
        """Return the secret value addressed by a reference.

        Raises:
            SecretResolutionException: If the reference cannot be resolved. The
                failure must never include the secret value.
        """
        ...
