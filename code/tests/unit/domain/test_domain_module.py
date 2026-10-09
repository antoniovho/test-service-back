from opyoid import Injector, InstanceBinding

from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.application.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.create_project_use_case import (
    CreateProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.get_project_use_case import (
    GetProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCaseImpl,
)
from test_service.domain.domain_module import DomainModule, ExecutionsModule, TestCasesModule
from test_service.domain.ports.input.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.projects.create_project_use_case import (
    CreateProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCase,
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
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.projects.project_persistence_port import (
    ProjectPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (  # noqa: E501
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
from test_service.domain.ports.output.secrets.secret_resolver_port import SecretResolverPort
from test_service.domain.ports.output.viewer.viewer_drift_detector_port import (
    ViewerDriftDetectorPort,
)
from test_service.domain.ports.output.viewer.viewer_publisher_port import ViewerPublisherPort


class _FakeProjectRepository:
    async def save(self, project):
        return project

    async def find_by_key(self, key):
        return None

    async def find_page(self, pagination):
        raise NotImplementedError


class _FakeProjectValidation:
    async def validate(self, project_key):
        return None


class _FakeTestCaseRepository:
    async def save(self, test_case):
        return test_case

    async def find_by_id(self, identifier):
        return None

    async def find_page(self, project_key, pagination, status=None):
        raise NotImplementedError

    async def find_versions(self, project_key, test_key, pagination, status=None):
        raise NotImplementedError


class _FakePreconditionRepository:
    async def find_by_id(self, identifier):
        return None


class _FakeTestSetRepository:
    async def save(self, snapshot):
        return snapshot

    async def find_by_id(self, identifier):
        return None

    async def find_latest_version(self, project_key, set_key):
        return None

    async def find_page(self, project_key, pagination, status=None):
        raise NotImplementedError

    async def find_versions(self, project_key, set_key, pagination, status=None):
        raise NotImplementedError


class _FakeTestPlanRepository:
    async def save(self, snapshot):
        return snapshot

    async def find_by_id(self, identifier):
        return None

    async def find_latest_version(self, project_key, plan_key):
        return None

    async def find_page(self, project_key, pagination, status=None):
        raise NotImplementedError

    async def find_versions(self, project_key, plan_key, pagination, status=None):
        raise NotImplementedError


class _FakeEnvironmentRepository:
    async def save(self, environment):
        return environment

    async def find_by_id(self, identifier):
        return None

    async def find_by_key(self, environment_key):
        return None

    async def find_page(self, pagination):
        raise NotImplementedError


class _FakeExecutionRepository:
    async def save_execution(self, execution):
        return execution

    async def find_execution(self, identifier):
        return None

    async def find_page(self, project_key, pagination):
        raise NotImplementedError


class _FakeExecutionResultsRepository:
    async def find_result(self, identifier):
        return None

    async def find_results_page(self, execution_id, pagination):
        raise NotImplementedError

    async def find_actions_page(self, test_result_id, pagination):
        raise NotImplementedError

    async def find_artifacts_page(self, test_result_id, pagination):
        raise NotImplementedError


class _FakeExecutionCancellation:
    def register(self, execution_id):
        return None

    def unregister(self, execution_id):
        return None

    def request_cancellation(self, execution_id):
        return None


class _FakeRunner:
    @property
    def version(self):
        return "test"

    def supports(self, action_types):
        return True

    async def execute(self, test_case, cancellation):
        raise NotImplementedError


class _FakeSecretResolver:
    async def resolve(self, reference):
        raise NotImplementedError


class _FakeViewerRepository:
    async def save_sync_record(self, record):
        return record

    async def save_drift_event(self, event):
        return event

    async def find_sync_records_page(self, pagination, viewer_type=None):
        raise NotImplementedError

    async def find_sync_records_page_by_project(self, project_key, pagination, viewer_type=None):
        raise NotImplementedError

    async def find_drift_events_page(self, pagination, viewer_type=None):
        raise NotImplementedError

    async def find_drift_events_page_by_project(self, project_key, pagination, viewer_type=None):
        raise NotImplementedError


class _FakeViewerPublisher:
    async def publish(self, record):
        return None


class _FakeViewerDriftDetector:
    async def check_drift(self, record):
        return None


class TestDomainModule:
    def test_when_injecting_project_use_cases_expect_bound_implementations(self):
        injector = Injector(
            [DomainModule],
            bindings=[
                InstanceBinding(ProjectPersistencePort, _FakeProjectRepository()),
                InstanceBinding(ProjectValidationPort, _FakeProjectValidation()),
                InstanceBinding(TestCasePersistencePort, _FakeTestCaseRepository()),
                InstanceBinding(PreconditionPersistencePort, _FakePreconditionRepository()),
                InstanceBinding(TestSetPersistencePort, _FakeTestSetRepository()),
                InstanceBinding(TestPlanPersistencePort, _FakeTestPlanRepository()),
                InstanceBinding(EnvironmentPersistencePort, _FakeEnvironmentRepository()),
                InstanceBinding(ExecutionPersistencePort, _FakeExecutionRepository()),
                InstanceBinding(ExecutionResultsPersistencePort, _FakeExecutionResultsRepository()),
                InstanceBinding(ExecutionCancellationPort, _FakeExecutionCancellation()),
                InstanceBinding(RunnerPort, _FakeRunner()),
                InstanceBinding(SecretResolverPort, _FakeSecretResolver()),
                InstanceBinding(ViewerPersistencePort, _FakeViewerRepository()),
                InstanceBinding(ViewerPublisherPort, _FakeViewerPublisher()),
                InstanceBinding(ViewerDriftDetectorPort, _FakeViewerDriftDetector()),
            ],
        )

        assert isinstance(injector.inject(ListProjectsUseCase), ListProjectsUseCaseImpl)
        assert isinstance(injector.inject(CreateProjectUseCase), CreateProjectUseCaseImpl)
        assert isinstance(injector.inject(GetProjectUseCase), GetProjectUseCaseImpl)
        assert isinstance(injector.inject(DeleteProjectUseCase), DeleteProjectUseCaseImpl)

    def test_when_injecting_test_case_use_cases_expect_bound_implementations(self):
        injector = Injector(
            [TestCasesModule],
            bindings=[
                InstanceBinding(TestCasePersistencePort, _FakeTestCaseRepository()),
                InstanceBinding(PreconditionPersistencePort, _FakePreconditionRepository()),
                InstanceBinding(ProjectResolver, ProjectResolver(_FakeProjectRepository())),
            ],
        )

        assert isinstance(injector.inject(CreateTestCaseUseCase), CreateTestCaseUseCaseImpl)
        assert isinstance(
            injector.inject(CreateTestCaseVersionUseCase), CreateTestCaseVersionUseCaseImpl
        )
        assert isinstance(injector.inject(ActivateTestCaseUseCase), ActivateTestCaseUseCaseImpl)
        assert isinstance(injector.inject(DeprecateTestCaseUseCase), DeprecateTestCaseUseCaseImpl)
        assert isinstance(injector.inject(GetTestCaseUseCase), GetTestCaseUseCaseImpl)
        assert isinstance(injector.inject(ListTestCasesUseCase), ListTestCasesUseCaseImpl)
        assert isinstance(
            injector.inject(ListTestCaseVersionsUseCase), ListTestCaseVersionsUseCaseImpl
        )

    def test_when_injecting_execution_use_cases_expect_bound_implementations(self):
        injector = Injector(
            [ExecutionsModule],
            bindings=[
                InstanceBinding(ProjectPersistencePort, _FakeProjectRepository()),
                InstanceBinding(ProjectResolver, ProjectResolver(_FakeProjectRepository())),
                InstanceBinding(TestPlanPersistencePort, _FakeTestPlanRepository()),
                InstanceBinding(EnvironmentPersistencePort, _FakeEnvironmentRepository()),
                InstanceBinding(ExecutionPersistencePort, _FakeExecutionRepository()),
                InstanceBinding(ExecutionResultsPersistencePort, _FakeExecutionResultsRepository()),
                InstanceBinding(TestCasePersistencePort, _FakeTestCaseRepository()),
                InstanceBinding(PreconditionPersistencePort, _FakePreconditionRepository()),
                InstanceBinding(TestSetPersistencePort, _FakeTestSetRepository()),
                InstanceBinding(ExecutionCancellationPort, _FakeExecutionCancellation()),
                InstanceBinding(RunnerPort, _FakeRunner()),
                InstanceBinding(SecretResolverPort, _FakeSecretResolver()),
            ],
        )

        assert isinstance(injector.inject(ScheduleExecutionUseCase), ScheduleExecutionUseCaseImpl)
        assert isinstance(injector.inject(GetExecutionUseCase), GetExecutionUseCaseImpl)
        assert isinstance(injector.inject(ListExecutionsUseCase), ListExecutionsUseCaseImpl)
        assert isinstance(
            injector.inject(ProcessNextExecutionUseCase), ProcessNextExecutionUseCaseImpl
        )
        assert isinstance(injector.inject(CancelExecutionUseCase), CancelExecutionUseCaseImpl)
        assert isinstance(
            injector.inject(ListExecutionResultsUseCase), ListExecutionResultsUseCaseImpl
        )
        assert isinstance(injector.inject(GetExecutionResultUseCase), GetExecutionResultUseCaseImpl)
        assert isinstance(
            injector.inject(ListExecutionResultActionsUseCase),
            ListExecutionResultActionsUseCaseImpl,
        )
        assert isinstance(
            injector.inject(ListExecutionResultArtifactsUseCase),
            ListExecutionResultArtifactsUseCaseImpl,
        )
