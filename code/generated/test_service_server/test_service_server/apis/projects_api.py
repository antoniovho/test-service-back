# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from test_service_server.apis.projects_api_base import BaseProjectsApi
import test_service_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from test_service_server.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr, field_validator
from typing import Any, Optional
from typing_extensions import Annotated
from test_service_server.models.create_project_request import CreateProjectRequest
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.project import Project
from test_service_server.models.project_list_response import ProjectListResponse
from test_service_server.models.sort_order import SortOrder
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/projects",
    responses={
        200: {"model": ProjectListResponse, "description": "Active projects."},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Projects"],
    summary="List projects",
    response_model_by_alias=True,
)
async def list_projects(
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")] = Query('version', description="Field used to sort the result set.", alias="sortBy", examples=["version"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ProjectListResponse:
    """Returns a paginated list of active projects registered in the local Project Catalog."""
    if not BaseProjectsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseProjectsApi.subclasses[0]().list_projects(offset, limit, sort_by, order)


@router.post(
    "/v1/projects",
    responses={
        201: {"model": Project, "description": "Project registered."},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Projects"],
    summary="Register a project",
    response_model_by_alias=True,
)
async def create_project(
    create_project_request: CreateProjectRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Project:
    """Registers a Jira project after a read-only validation that the exact key exists and is active in Jira."""
    if not BaseProjectsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseProjectsApi.subclasses[0]().create_project(create_project_request)


@router.get(
    "/v1/projects/{projectKey}",
    responses={
        200: {"model": Project, "description": "Project."},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Projects"],
    summary="Get a project",
    response_model_by_alias=True,
)
async def get_project(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Project:
    """Returns a project by its stable project key, including logically deleted projects when explicitly authorized."""
    if not BaseProjectsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseProjectsApi.subclasses[0]().get_project(projectKey)


@router.delete(
    "/v1/projects/{projectKey}",
    responses={
        204: {"description": "Project logically deleted. No response body is returned."},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Projects"],
    summary="Logically delete a project",
    response_model_by_alias=True,
)
async def delete_project(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    """Marks the project as DELETED without deleting tests, sets, plans, executions, results, or artifacts."""
    if not BaseProjectsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseProjectsApi.subclasses[0]().delete_project(projectKey)
