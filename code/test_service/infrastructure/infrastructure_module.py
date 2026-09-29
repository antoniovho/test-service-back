"""Infrastructure dependency-injection module."""

from opyoid import Module  # type: ignore

from test_service.config import PostgresDatabaseSettings
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_database_configuration import (  # noqa: E501
    PostgresDatabaseConfiguration,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)

from .adapters.output.projects.persistence.project_persistence_adapter import (
    ProjectPersistenceAdapter,
)
from .adapters.output.projects.persistence.repositories.project_repository import ProjectRepository


class DatabaseModule(Module):
    """Bind shared database infrastructure and the Projects persistence adapter."""

    def configure(self) -> None:
        self.bind(PostgresDatabaseSettings, to_instance=PostgresDatabaseSettings())
        self.bind(PostgresDatabaseConfiguration)
        self.bind(PostgresSessionProvider)


class ProjectModule(Module):
    def configure(self) -> None:
        self.bind(ProjectRepository)
        self.bind(ProjectPersistencePort, to_class=ProjectPersistenceAdapter)


class InfrastructureModule(Module):
    """Master module for outbound infrastructure adapters."""

    def configure(self) -> None:
        self.install(DatabaseModule)
        self.install(ProjectModule)
