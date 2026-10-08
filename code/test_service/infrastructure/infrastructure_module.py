"""Infrastructure dependency-injection module."""

from opyoid import Module  # type: ignore

from test_service.config import JiraSettings, PostgresDatabaseSettings, ViewerSettings, XraySettings
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
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_plans.test_plan_persistence_port import (
    TestPlanPersistencePort,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)
from test_service.domain.ports.output.projects.project_validation_port import ProjectValidationPort
from test_service.domain.ports.output.runners.runner_port import RunnerPort
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_database_configuration import (  # noqa: E501
    PostgresDatabaseConfiguration,
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_session_provider import (  # noqa: E501
    PostgresSessionProvider,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.repositories.test_plan_repository import (  # noqa: E501
    TestPlanRepository,
)
from test_service.infrastructure.adapters.output.composition.test_plans.persistence.test_plan_persistence_adapter import (  # noqa: E501
    TestPlanPersistenceAdapter,
)

from .adapters.output.authoring.preconditions.persistence.precondition_persistence_adapter import (  # noqa: E501
    PreconditionPersistenceAdapter,
)
from .adapters.output.authoring.preconditions.persistence.repositories.precondition_repository import (  # noqa: E501
    PreconditionRepository,
)
from .adapters.output.authoring.test_cases.persistence.repositories.test_case_repository import (
    TestCaseRepository,
)
from .adapters.output.authoring.test_cases.persistence.test_case_persistence_adapter import (
    TestCasePersistenceAdapter,
)
from .adapters.output.composition.test_sets.persistence.repositories.test_set_repository import (
    TestSetRepository,
)
from .adapters.output.composition.test_sets.persistence.test_set_persistence_adapter import (
    TestSetPersistenceAdapter,
)
from .adapters.output.execution.environments.environment_persistence_adapter import (
    EnvironmentPersistenceAdapter,
)
from .adapters.output.execution.environments.persistence.repositories.environment_repository import (  # noqa: E501
    EnvironmentRepository,
)
from .adapters.output.execution.executions.cancellation.execution_cancellation_registry import (  # noqa: E501
    ExecutionCancellationRegistry,
)
from .adapters.output.execution.executions.execution_persistence_adapter import (
    ExecutionPersistenceAdapter,
)
from .adapters.output.execution.executions.execution_results_persistence_adapter import (  # noqa: E501
    ExecutionResultsPersistenceAdapter,
)
from .adapters.output.execution.executions.persistence.repositories.execution_repository import (  # noqa: E501
    ExecutionRepository,
)
from .adapters.output.execution.executions.persistence.repositories.execution_results_repository import (  # noqa: E501
    ExecutionResultsRepository,
)
from .adapters.output.projects.jira.jira_project_validation_adapter import (
    JiraProjectValidationAdapter,
)
from .adapters.output.projects.persistence.project_persistence_adapter import (
    ProjectPersistenceAdapter,
)
from .adapters.output.projects.persistence.repositories.project_repository import ProjectRepository
from .adapters.output.runners.tavern.tavern_runner_adapter import TavernRunnerAdapter
from .adapters.output.viewer.persistence.repositories.viewer_repository import ViewerRepository
from .adapters.output.viewer.persistence.viewer_persistence_adapter import ViewerPersistenceAdapter
from .adapters.output.viewer.xray_viewer_adapter import XrayViewerAdapter


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
        self.bind(JiraSettings, to_instance=JiraSettings())
        self.bind(ProjectValidationPort, to_class=JiraProjectValidationAdapter)


class AuthoringModule(Module):
    """Bind persistence adapters required by Test Case authoring."""

    def configure(self) -> None:
        self.bind(TestCaseRepository)
        self.bind(PreconditionRepository)
        self.bind(TestSetRepository)
        self.bind(TestPlanRepository)
        self.bind(TestCasePersistencePort, to_class=TestCasePersistenceAdapter)
        self.bind(PreconditionPersistencePort, to_class=PreconditionPersistenceAdapter)
        self.bind(TestSetPersistencePort, to_class=TestSetPersistenceAdapter)
        self.bind(TestPlanPersistencePort, to_class=TestPlanPersistenceAdapter)


class ExecutionModule(Module):
    """Bind persistence adapters required by execution resources."""

    def configure(self) -> None:
        self.bind(EnvironmentRepository)
        self.bind(ExecutionRepository)
        self.bind(ExecutionResultsRepository)
        self.bind(EnvironmentPersistencePort, to_class=EnvironmentPersistenceAdapter)
        self.bind(ExecutionPersistencePort, to_class=ExecutionPersistenceAdapter)
        self.bind(ExecutionResultsPersistencePort, to_class=ExecutionResultsPersistenceAdapter)
        self.bind(RunnerPort, to_class=TavernRunnerAdapter)
        cancellations = ExecutionCancellationRegistry()
        self.bind(ExecutionCancellationRegistry, to_instance=cancellations)
        self.bind(ExecutionCancellationPort, to_instance=cancellations)


class ViewerModule(Module):
    def configure(self) -> None:
        self.bind(ViewerRepository)
        self.bind(ViewerSettings, to_instance=ViewerSettings())
        self.bind(XraySettings, to_instance=XraySettings())
        self.bind(ViewerPublisherPort, to_class=XrayViewerAdapter)
        self.bind(ViewerDriftDetectorPort, to_class=XrayViewerAdapter)
        self.bind(ViewerPersistencePort, to_class=ViewerPersistenceAdapter)


class InfrastructureModule(Module):
    """Master module for outbound infrastructure adapters."""

    def configure(self) -> None:
        self.install(DatabaseModule)
        self.install(ProjectModule)
        self.install(AuthoringModule)
        self.install(ExecutionModule)
        self.install(ViewerModule)
