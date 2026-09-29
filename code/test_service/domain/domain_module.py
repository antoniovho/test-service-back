"""Domain IoC module — binds use case ports to their implementations."""

from opyoid import Module  # type: ignore

from test_service.domain.application.services.precondition_references import (
    PreconditionReferenceResolver,
)
from test_service.domain.application.services.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCaseImpl,
)
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
from test_service.domain.application.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.get_test_set_use_case import (  # noqa: E501
    GetTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCaseImpl,
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
from test_service.domain.ports.input.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCase,
)
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
from test_service.domain.ports.input.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.get_test_set_use_case import (
    GetTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCase,
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


class ProjectsModule(Module):
    """Binds Project Catalog use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(ListProjectsUseCase, to_class=ListProjectsUseCaseImpl)
        self.bind(CreateProjectUseCase, to_class=CreateProjectUseCaseImpl)
        self.bind(GetProjectUseCase, to_class=GetProjectUseCaseImpl)
        self.bind(DeleteProjectUseCase, to_class=DeleteProjectUseCaseImpl)


class TestCasesModule(Module):
    """Binds Test Case use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(PreconditionReferenceResolver)
        self.bind(CreateTestCaseUseCase, to_class=CreateTestCaseUseCaseImpl)
        self.bind(CreateTestCaseVersionUseCase, to_class=CreateTestCaseVersionUseCaseImpl)
        self.bind(ActivateTestCaseUseCase, to_class=ActivateTestCaseUseCaseImpl)
        self.bind(DeprecateTestCaseUseCase, to_class=DeprecateTestCaseUseCaseImpl)
        self.bind(GetTestCaseUseCase, to_class=GetTestCaseUseCaseImpl)
        self.bind(ListTestCasesUseCase, to_class=ListTestCasesUseCaseImpl)
        self.bind(ListTestCaseVersionsUseCase, to_class=ListTestCaseVersionsUseCaseImpl)


class PreconditionsModule(Module):
    """Binds Precondition use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(CreatePreconditionUseCase, to_class=CreatePreconditionUseCaseImpl)
        self.bind(CreatePreconditionVersionUseCase, to_class=CreatePreconditionVersionUseCaseImpl)
        self.bind(ActivatePreconditionUseCase, to_class=ActivatePreconditionUseCaseImpl)
        self.bind(DeprecatePreconditionUseCase, to_class=DeprecatePreconditionUseCaseImpl)
        self.bind(GetPreconditionUseCase, to_class=GetPreconditionUseCaseImpl)
        self.bind(ListPreconditionsUseCase, to_class=ListPreconditionsUseCaseImpl)
        self.bind(ListPreconditionVersionsUseCase, to_class=ListPreconditionVersionsUseCaseImpl)


class TestSetsModule(Module):
    """Binds Test Set composition use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(TestCaseSnapshotResolver)
        self.bind(CreateTestSetUseCase, to_class=CreateTestSetUseCaseImpl)
        self.bind(CreateTestSetVersionUseCase, to_class=CreateTestSetVersionUseCaseImpl)
        self.bind(ActivateTestSetUseCase, to_class=ActivateTestSetUseCaseImpl)
        self.bind(DeprecateTestSetUseCase, to_class=DeprecateTestSetUseCaseImpl)
        self.bind(GetTestSetUseCase, to_class=GetTestSetUseCaseImpl)
        self.bind(ListTestSetsUseCase, to_class=ListTestSetsUseCaseImpl)
        self.bind(ListTestSetVersionsUseCase, to_class=ListTestSetVersionsUseCaseImpl)


class DomainModule(Module):
    """Domain modules available in the runnable application composition."""

    def configure(self) -> None:
        self.install(ProjectsModule)
        self.install(TestCasesModule)
        self.install(PreconditionsModule)
        self.install(TestSetsModule)
