"""Secret resolution backed by namespaced environment variables of this process."""

import os
import re
from collections.abc import Mapping

from test_service.domain.model.exceptions.secret_resolution_exception import (
    SecretResolutionException,
)
from test_service.domain.model.execution.environment import SecretReference
from test_service.domain.ports.output.secrets.secret_resolver_port import SecretResolverPort

PROVIDER = "env"
DEFAULT_PREFIX = "TEST_SERVICE_SECRET_"
_REFERENCE_KEY = re.compile(r"[A-Z][A-Z0-9_]*")


class EnvironmentSecretResolver(SecretResolverPort):
    """Resolve ``env`` references only from variables carrying a dedicated prefix.

    The prefix keeps the service's own credentials, such as database or integration
    secrets, out of reach of an Environment that references a key by name.
    """

    def __init__(
        self, prefix: str = DEFAULT_PREFIX, environ: Mapping[str, str] | None = None
    ) -> None:
        self._prefix = prefix
        self._environ = environ

    async def resolve_secret(self, reference: SecretReference) -> str:
        """Return the value of ``<prefix><reference_key>`` from the environment.

        Raises:
            SecretResolutionException: If the provider is not ``env``, the key is malformed
                or the variable is missing or empty. The message never echoes the reference.
        """
        if reference.provider != PROVIDER:
            raise SecretResolutionException("secret provider is not supported")
        if _REFERENCE_KEY.fullmatch(reference.reference_key) is None:
            raise SecretResolutionException("secret reference key has an invalid format")
        environ = os.environ if self._environ is None else self._environ
        value = environ.get(f"{self._prefix}{reference.reference_key}")
        if not value:
            raise SecretResolutionException("secret is not available")
        return value
