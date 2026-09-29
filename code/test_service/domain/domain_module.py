"""Domain IoC module — binds use case ports to their implementations."""

from opyoid import Module  # type: ignore

from test_service.domain.application.services.precondition_references import (
    PreconditionReferenceResolver,
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


class DomainModule(Module):
    """Domain modules available in the runnable application composition."""

    def configure(self) -> None:
        self.install(ProjectsModule)
        self.install(TestCasesModule)
