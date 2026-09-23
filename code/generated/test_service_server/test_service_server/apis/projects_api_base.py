# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr, field_validator
from typing import Any, Optional
from typing_extensions import Annotated
from test_service_server.models.create_project_request import CreateProjectRequest
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.project import Project
from test_service_server.models.project_list_response import ProjectListResponse
from test_service_server.models.sort_order import SortOrder
from test_service_server.security_api import get_token_bearerAuth

class BaseProjectsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseProjectsApi.subclasses = BaseProjectsApi.subclasses + (cls,)
    async def list_projects(
        self,
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> ProjectListResponse:
        """Returns a paginated list of active projects registered in the local Project Catalog."""
        ...


    async def create_project(
        self,
        create_project_request: CreateProjectRequest,
    ) -> Project:
        """Registers a Jira project after a read-only validation that the exact key exists and is active in Jira."""
        ...


    async def get_project(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
    ) -> Project:
        """Returns a project by its stable project key, including logically deleted projects when explicitly authorized."""
        ...


    async def delete_project(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
    ) -> None:
        """Marks the project as DELETED without deleting tests, sets, plans, executions, results, or artifacts."""
        ...
