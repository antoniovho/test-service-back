"""Mapping between Environment domain objects and SQLAlchemy DTOs."""

from typing import Any

from test_service.domain.model.execution.environment import (
    Environment,
    EnvironmentStatus,
    SecretReference,
)
from test_service.infrastructure.adapters.output.execution.environments.persistence.dtos.environment_dto import (  # noqa: E501
    EnvironmentDTO,
)


class EnvironmentPersistenceMapper:
    """Translate Environment data at the domain and persistence boundary."""

    @staticmethod
    def to_dto(environment: Environment) -> EnvironmentDTO:
        """Create a persistence DTO from an Environment aggregate."""
        return EnvironmentDTO(
            id=environment.identifier,
            environment_key=environment.environment_key,
            name=environment.name,
            description=environment.description,
            status=environment.status.value,
            configuration=EnvironmentPersistenceMapper._to_storage_configuration(
                environment.configuration
            ),
            created_at=environment.created_at,
            created_by=environment.created_by,
        )

    @staticmethod
    def to_domain(environment: EnvironmentDTO) -> Environment:
        """Create an Environment aggregate from a persistence DTO."""
        return Environment(
            identifier=environment.id,
            environment_key=environment.environment_key,
            name=environment.name,
            description=environment.description,
            status=EnvironmentStatus(environment.status),
            configuration=EnvironmentPersistenceMapper._to_domain_configuration(
                environment.configuration
            ),
            created_at=environment.created_at,
            created_by=environment.created_by,
        )

    @staticmethod
    def _to_storage_configuration(configuration) -> dict[str, Any]:
        return {
            key: (
                {"provider": value.provider, "referenceKey": value.reference_key}
                if isinstance(value, SecretReference)
                else value
            )
            for key, value in (configuration or {}).items()
        }

    @staticmethod
    def _to_domain_configuration(configuration: dict[str, Any]) -> dict[str, Any]:
        return {
            key: (
                SecretReference(value["provider"], value["referenceKey"])
                if isinstance(value, dict) and set(value) == {"provider", "referenceKey"}
                else value
            )
            for key, value in configuration.items()
        }
