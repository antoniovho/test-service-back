"""Inbound REST adapter for the Projects API, implementing the generated base class."""

from datetime import UTC, datetime

from test_service_server.apis.projects_api_base import BaseProjectsApi
from test_service_server.models.create_project_request import CreateProjectRequest
from test_service_server.models.project import Project as ApiProject
from test_service_server.models.project_list_response import ProjectListResponse
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.bootstrap.container import get_injector
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
from test_service.infrastructure.adapters.input.rest.projects.project_mapper import (
    ProjectMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    get_current_identity,
)


class ProjectsController(BaseProjectsApi):
    """Adapts Project Catalog use cases to the generated Projects REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._list_projects_use_case = injector.inject(ListProjectsUseCase)
        self._create_project_use_case = injector.inject(CreateProjectUseCase)
        self._get_project_use_case = injector.inject(GetProjectUseCase)
        self._delete_project_use_case = injector.inject(DeleteProjectUseCase)

    async def list_projects(
        self,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ProjectListResponse:
        """Return a paginated list of active projects."""
        pagination = ProjectMapper.to_pagination_params(offset, limit, sort_by, order)
        query = ProjectMapper.to_list_query(pagination)
        page = await self._list_projects_use_case.execute(request=query)
        return ProjectMapper.domain_page_to_list_response(page, pagination)

    async def create_project(self, create_project_request: CreateProjectRequest) -> ApiProject:
        """Register a project after read-only validation against Jira."""
        command = ProjectMapper.to_create_command(
            create_project_request, get_current_identity(), datetime.now(UTC)
        )
        project = await self._create_project_use_case.execute(command)
        return ProjectMapper.domain_to_api(project)

    async def get_project(self, projectKey: str) -> ApiProject:  # NOSONAR
        """Return a project by its stable key."""
        project = await self._get_project_use_case.execute(ProjectMapper.to_get_query(projectKey))
        return ProjectMapper.domain_to_api(project)

    async def delete_project(self, projectKey: str) -> None:  # NOSONAR
        """Mark a project as logically deleted."""
        command = ProjectMapper.to_delete_command(
            projectKey, get_current_identity(), datetime.now(UTC)
        )
        await self._delete_project_use_case.execute(command)
