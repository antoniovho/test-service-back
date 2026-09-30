import pytest
from opyoid import Injector

from test_service.domain.application.use_cases.projects.create_project_use_case import (
    CreateProjectUseCaseImpl,
)
from test_service.domain.domain_module import DomainModule
from test_service.domain.ports.input.use_cases.projects.create_project_use_case import (
    CreateProjectUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.infrastructure.adapters.output.execution.environments.environment_persistence_adapter import (  # noqa: E501
    EnvironmentPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.projects.persistence.project_persistence_adapter import (  # noqa: E501
    ProjectPersistenceAdapter,
)
from test_service.infrastructure.infrastructure_module import InfrastructureModule


@pytest.fixture
def postgres_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "test_db")
    monkeypatch.setenv("DATABASE_USER", "test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_password")


class TestInfrastructureModule:
    def test_when_domain_and_infrastructure_are_installed_expect_projects_resolve(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        use_case = injector.inject(CreateProjectUseCase)
        persistence_port = injector.inject(ProjectPersistencePort)

        assert isinstance(use_case, CreateProjectUseCaseImpl)
        assert isinstance(persistence_port, ProjectPersistenceAdapter)

    def test_when_infrastructure_is_installed_expect_environment_port_resolves(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        persistence_port = injector.inject(EnvironmentPersistencePort)

        assert isinstance(persistence_port, EnvironmentPersistenceAdapter)
