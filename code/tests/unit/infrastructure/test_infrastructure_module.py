import pytest
from opyoid import Injector

from test_service.domain.application.use_cases.projects.create_project_use_case import (
    CreateProjectUseCaseImpl,
)
from test_service.domain.domain_module import DomainModule
from test_service.domain.ports.input.use_cases.projects.create_project_use_case import (
    CreateProjectUseCase,
)
from test_service.domain.ports.output.executions.execution_cancellation_port import (
    ExecutionCancellationPort,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (  # noqa: E501
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort
from test_service.infrastructure.adapters.output.execution.environments.environment_persistence_adapter import (  # noqa: E501
    EnvironmentPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.executions.cancellation.execution_cancellation_registry import (  # noqa: E501
    ExecutionCancellationRegistry,
)
from test_service.infrastructure.adapters.output.execution.executions.execution_persistence_adapter import (  # noqa: E501
    ExecutionPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.execution.executions.execution_results_persistence_adapter import (  # noqa: E501
    ExecutionResultsPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.projects.persistence.project_persistence_adapter import (  # noqa: E501
    ProjectPersistenceAdapter,
)
from test_service.infrastructure.adapters.output.viewer.xray_viewer_adapter import XrayViewerAdapter
from test_service.infrastructure.infrastructure_module import InfrastructureModule


@pytest.fixture
def postgres_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("DATABASE_NAME", "test_db")
    monkeypatch.setenv("DATABASE_USER", "test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_password")
    monkeypatch.setenv("XRAY_CLIENT_ID", "test-client")
    monkeypatch.setenv("XRAY_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("XRAY_PROJECTION_URL", "https://xray.example.test/projections")
    monkeypatch.setenv("XRAY_DRIFT_CHECK_URL", "https://xray.example.test/drift")
    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example.test")
    monkeypatch.setenv("JIRA_USER_EMAIL", "test@example.test")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")


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

    def test_when_infrastructure_is_installed_expect_execution_port_resolves(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        persistence_port = injector.inject(ExecutionPersistencePort)

        assert isinstance(persistence_port, ExecutionPersistenceAdapter)

    def test_when_infrastructure_is_installed_expect_execution_results_port_resolves(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        persistence_port = injector.inject(ExecutionResultsPersistencePort)

        assert isinstance(persistence_port, ExecutionResultsPersistenceAdapter)

    def test_when_infrastructure_is_installed_expect_shared_cancellation_registry(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        cancellation_port = injector.inject(ExecutionCancellationPort)
        registry = injector.inject(ExecutionCancellationRegistry)

        assert cancellation_port is registry

    def test_when_infrastructure_is_installed_expect_xray_publisher_resolves(
        self,
        postgres_settings_env: None,
    ) -> None:
        injector = Injector([DomainModule, InfrastructureModule])

        publisher = injector.inject(ViewerPublisherPort)

        assert isinstance(publisher, XrayViewerAdapter)
