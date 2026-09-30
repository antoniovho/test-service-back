from opyoid import Injector, InstanceBinding

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
from test_service.domain.domain_module import DomainModule, TestCasesModule
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
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
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


class _FakeProjectRepository:
    async def save(self, project):
        return project

    async def find_by_key(self, key):
        return None

    async def find_page(self, pagination):
        raise NotImplementedError


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


class TestDomainModule:
    def test_when_injecting_project_use_cases_expect_bound_implementations(self):
        injector = Injector(
            [DomainModule],
            bindings=[
                InstanceBinding(ProjectPersistencePort, _FakeProjectRepository()),
                InstanceBinding(TestCasePersistencePort, _FakeTestCaseRepository()),
                InstanceBinding(PreconditionPersistencePort, _FakePreconditionRepository()),
                InstanceBinding(TestSetPersistencePort, _FakeTestSetRepository()),
                InstanceBinding(TestPlanPersistencePort, _FakeTestPlanRepository()),
                InstanceBinding(EnvironmentPersistencePort, _FakeEnvironmentRepository()),
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
