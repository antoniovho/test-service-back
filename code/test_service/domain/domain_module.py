"""Domain IoC module — binds use case ports to their implementations."""

from opyoid import Module # type: ignore

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


class DomainModule(Module):
    """Master domain module. Installs all bounded-context sub-modules."""

    def configure(self) -> None:
        self.install(ProjectsModule)
