"""Execution Environment aggregate."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from test_service.domain.commons.immutable import freeze_mapping
from test_service.domain.model.exceptions.domain_exception import (
    BusinessRuleViolationException,
    ValidationException,
)

_SECRET_KEY_MARKERS = ("password", "secret", "token", "apikey", "api_key", "credential")


class EnvironmentStatus(StrEnum):
    """Availability state of an execution environment.

    Attributes:
        ACTIVE: Environment is available for new executions.
        INACTIVE: Environment is temporarily unavailable.
        DEPRECATED: Environment is retained only for history.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class SecretReference:
    """Pointer to a secret value resolved outside the domain by a SecretResolverPort.

    Storing a SecretReference instead of a resolved value keeps runbook-prohibited
    secret material out of Environment.configuration and out of persistence.

    Args:
        provider: Identifier of the secret store that owns the value, e.g. ``vault``.
        reference_key: Stable lookup key for the secret within the provider.

    Raises:
        ValidationException: If the provider or reference key is empty.
    """

    provider: str
    reference_key: str

    def __post_init__(self) -> None:
        """Validate SecretReference fields.

        Raises:
            ValidationException: If the provider or reference key is empty.
        """
        if not self.provider or not self.reference_key:
            raise ValidationException(
                "secret reference requires a provider and a reference key",
                "INVALID_SECRET_REFERENCE",
            )


ConfigurationValue = str | int | float | bool | SecretReference


@dataclass(frozen=True, slots=True)
class Environment:
    """Execution target that stores configuration without resolved secrets.

    Args:
        identifier: UUID of the environment.
        environment_key: Stable global environment key.
        name: Human-readable environment name.
        created_at: Creation timestamp.
        created_by: Identity that created the environment.
        description: Optional environment purpose.
        configuration: Safe unresolved configuration values. Keys that look like
            secrets (password, token, credential, ...) must use a SecretReference
            instead of a raw value.
        status: Environment availability state.

    Raises:
        ValidationException: If a secret-like configuration key holds a raw value.
    """

    identifier: UUID
    environment_key: str
    name: str
    created_at: datetime
    created_by: str
    description: str | None = None
    configuration: Mapping[str, ConfigurationValue] | None = None
    status: EnvironmentStatus = EnvironmentStatus.ACTIVE

    def __post_init__(self) -> None:
        """Validate the secrets policy and freeze the mutable configuration mapping.

        Raises:
            ValidationException: If a secret-like configuration key holds a raw value.
        """
        if self.configuration is not None:
            for key, value in self.configuration.items():
                is_secret_like_key = any(marker in key.lower() for marker in _SECRET_KEY_MARKERS)
                if is_secret_like_key and not isinstance(value, SecretReference):
                    raise ValidationException(
                        f"configuration key '{key}' looks like a secret and must use a "
                        "SecretReference instead of a raw value",
                        "RESOLVED_SECRET_NOT_ALLOWED",
                    )
        object.__setattr__(self, "configuration", freeze_mapping(self.configuration))

    def activate(self) -> "Environment":
        """Return an active environment.

        Returns:
            A new active environment.

        Raises:
            BusinessRuleViolationException: If the environment is deprecated.
        """
        if self.status is EnvironmentStatus.DEPRECATED:
            raise BusinessRuleViolationException(
                "deprecated environments cannot be activated",
                "INVALID_ENVIRONMENT_TRANSITION",
            )
        return replace(self, status=EnvironmentStatus.ACTIVE)

    def deactivate(self) -> "Environment":
        """Return an inactive environment.

        Returns:
            A new inactive environment.

        Raises:
            BusinessRuleViolationException: If the environment is deprecated.
        """
        if self.status is EnvironmentStatus.DEPRECATED:
            raise BusinessRuleViolationException(
                "deprecated environments cannot be deactivated",
                "INVALID_ENVIRONMENT_TRANSITION",
            )
        return replace(self, status=EnvironmentStatus.INACTIVE)
