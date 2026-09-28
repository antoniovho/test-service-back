"""Mapping between the generated Projects REST models and domain Project Catalog types."""

from datetime import datetime

from test_service_server.models.create_project_request import CreateProjectRequest
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.project import Project as ApiProject
from test_service_server.models.project_list_response import ProjectListResponse
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.application.commands.projects import (
    CreateProjectCommand,
    DeleteProjectCommand,
)
from test_service.domain.application.queries.projects import GetProjectQuery, ListProjectsQuery
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.commons.pagination import SortOrder as DomainSortOrder
from test_service.domain.model.projects.project import Project


class ProjectMapper:
    """Translates between the Projects REST contract and the domain layer."""

    @staticmethod
    def to_pagination_params(
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> PaginationParams:
        """Build validated domain pagination parameters from REST query parameters."""
        kwargs: dict[str, object] = {}
        if offset is not None:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        if sort_by is not None:
            kwargs["sort_by"] = sort_by
        if order is not None:
            kwargs["order"] = DomainSortOrder(order.value)
        return PaginationParams(**kwargs)

    @staticmethod
    def to_list_query(pagination: PaginationParams) -> ListProjectsQuery:
        """Build the query used to list Project Catalog entries."""
        return ListProjectsQuery(pagination=pagination)

    @staticmethod
    def to_get_query(project_key: str) -> GetProjectQuery:
        """Build the query used to retrieve one project by key."""
        return GetProjectQuery(key=project_key)

    @staticmethod
    def to_create_command(
        request: CreateProjectRequest, requested_by: str, requested_at: datetime
    ) -> CreateProjectCommand:
        """Build the command used to register a project."""
        return CreateProjectCommand(
            key=request.key,
            name=request.name,
            requested_by=requested_by,
            requested_at=requested_at,
        )

    @staticmethod
    def to_delete_command(
        project_key: str, requested_by: str, requested_at: datetime
    ) -> DeleteProjectCommand:
        """Build the command used to logically delete a project."""
        return DeleteProjectCommand(
            key=project_key,
            requested_by=requested_by,
            requested_at=requested_at,
        )

    @staticmethod
    def domain_to_api(project: Project) -> ApiProject:
        """Map a domain project to its REST representation."""
        return ApiProject(
            key=project.key,
            name=project.name,
            status=project.status.value,
            createdAt=project.created_at,
            createdBy=project.created_by,
            deletedAt=project.deleted_at,
            deletedBy=project.deleted_by,
        )

    @staticmethod
    def domain_page_to_list_response(
        page: Page[Project], pagination: PaginationParams
    ) -> ProjectListResponse:
        """Map a domain page of projects to the paginated REST response."""
        return ProjectListResponse(
            data=[ProjectMapper.domain_to_api(project) for project in page.items],
            pagination=ApiPagination(
                offset=pagination.offset,
                limit=pagination.limit,
                total=page.total,
            ),
        )
