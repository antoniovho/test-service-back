from opyoid import Injector, InstanceBinding

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
from test_service.domain.domain_module import DomainModule
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
from test_service.domain.ports.output.repositories import ProjectRepositoryPort


class _FakeProjectRepository:
    async def save(self, project):
        return project

    async def find_by_key(self, key):
        return None

    async def find_page(self, pagination):
        raise NotImplementedError


class TestDomainModule:
    def test_when_injecting_project_use_cases_expect_bound_implementations(self):
        injector = Injector(
            [DomainModule],
            bindings=[InstanceBinding(ProjectRepositoryPort, _FakeProjectRepository())],
        )

        assert isinstance(injector.inject(ListProjectsUseCase), ListProjectsUseCaseImpl)
        assert isinstance(injector.inject(CreateProjectUseCase), CreateProjectUseCaseImpl)
        assert isinstance(injector.inject(GetProjectUseCase), GetProjectUseCaseImpl)
        assert isinstance(injector.inject(DeleteProjectUseCase), DeleteProjectUseCaseImpl)
