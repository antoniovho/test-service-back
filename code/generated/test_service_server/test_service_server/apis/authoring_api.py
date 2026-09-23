# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from test_service_server.apis.authoring_api_base import BaseAuthoringApi
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
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_precondition_request import CreatePreconditionRequest
from test_service_server.models.create_test_case_request import CreateTestCaseRequest
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.precondition import Precondition
from test_service_server.models.precondition_list_response import PreconditionListResponse
from test_service_server.models.sort_order import SortOrder
from test_service_server.models.test_case import TestCase
from test_service_server.models.test_case_list_response import TestCaseListResponse
from test_service_server.models.test_case_version_list_response import TestCaseVersionListResponse
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/test-cases",
    responses={
        200: {"model": TestCaseListResponse, "description": "Paginated test cases"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="List test case versions",
    response_model_by_alias=True,
)
async def list_test_cases(
    project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")] = Query(..., description="Stable key of the project that owns the requested resources.", alias="projectKey", min_length=2, max_length=20)
,
    status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")] = Query(None, description="Filter versions by lifecycle status. When omitted, all statuses are returned.", alias="status")
,
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
) -> TestCaseListResponse:
    """Returns a paginated list of immutable test case versions."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().list_test_cases(project_key, status, offset, limit, sort_by, order)


@router.post(
    "/v1/test-cases",
    responses={
        201: {"model": TestCase, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Create a test case version",
    response_model_by_alias=True,
)
async def create_test_case(
    create_test_case_request: CreateTestCaseRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCase:
    """Creates a new immutable test case version in draft status."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().create_test_case(create_test_case_request)


@router.get(
    "/v1/test-cases/{testCaseId}",
    responses={
        200: {"model": TestCase, "description": "Test case"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Get a test case version",
    response_model_by_alias=True,
)
async def get_test_case(
    testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")] = Path(..., description="UUID of the test case version.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCase:
    """Returns the complete definition and metadata of a test case version."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().get_test_case(testCaseId)


@router.get(
    "/v1/test-cases/{testCaseId}/versions",
    responses={
        200: {"model": TestCaseVersionListResponse, "description": "Versions"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="List versions of a test case key",
    response_model_by_alias=True,
)
async def list_test_case_versions(
    testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")] = Path(..., description="UUID of the test case version.")
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCaseVersionListResponse:
    """Returns all immutable versions associated with a test case key."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().list_test_case_versions(testCaseId, offset, limit)


@router.post(
    "/v1/test-cases/{testCaseId}/versions",
    responses={
        201: {"model": TestCase, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Create a new immutable test case version",
    response_model_by_alias=True,
)
async def create_test_case_version(
    testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")] = Path(..., description="UUID of the test case version.")
,
    create_test_case_request: CreateTestCaseRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCase:
    """Creates a new version without modifying any existing test case version."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().create_test_case_version(testCaseId, create_test_case_request)


@router.post(
    "/v1/test-cases/{testCaseId}/activations",
    responses={
        200: {"model": TestCase, "description": "Activated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Activate a test case version",
    response_model_by_alias=True,
)
async def activate_test_case(
    testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")] = Path(..., description="UUID of the test case version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCase:
    """Activates a draft test case version for future compositions and executions."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().activate_test_case(testCaseId, action_request)


@router.post(
    "/v1/test-cases/{testCaseId}/deprecations",
    responses={
        200: {"model": TestCase, "description": "Deprecated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Deprecate a test case version",
    response_model_by_alias=True,
)
async def deprecate_test_case(
    testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")] = Path(..., description="UUID of the test case version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestCase:
    """Deprecates a test case version so it cannot be selected for new compositions."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().deprecate_test_case(testCaseId, action_request)


@router.get(
    "/v1/preconditions",
    responses={
        200: {"model": PreconditionListResponse, "description": "Preconditions"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="List preconditions",
    response_model_by_alias=True,
)
async def list_preconditions(
    status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")] = Query(None, description="Filter versions by lifecycle status. When omitted, all statuses are returned.", alias="status")
,
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
) -> PreconditionListResponse:
    """Returns a paginated list of versioned preconditions."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().list_preconditions(status, offset, limit, sort_by, order)


@router.post(
    "/v1/preconditions",
    responses={
        201: {"model": Precondition, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Create a precondition version",
    response_model_by_alias=True,
)
async def create_precondition(
    create_precondition_request: CreatePreconditionRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Precondition:
    """Creates a new immutable precondition version in draft status."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().create_precondition(create_precondition_request)


@router.get(
    "/v1/preconditions/{preconditionId}",
    responses={
        200: {"model": Precondition, "description": "Precondition"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Get a precondition version",
    response_model_by_alias=True,
)
async def get_precondition(
    preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")] = Path(..., description="UUID of the precondition version.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Precondition:
    """Returns an immutable precondition version by UUID."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().get_precondition(preconditionId)


@router.get(
    "/v1/preconditions/{preconditionId}/versions",
    responses={
        200: {"model": PreconditionListResponse, "description": "Precondition versions"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="List versions of a precondition",
    response_model_by_alias=True,
)
async def list_precondition_versions(
    preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")] = Path(..., description="UUID of the precondition version.")
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> PreconditionListResponse:
    """Returns all immutable versions associated with a precondition key."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().list_precondition_versions(preconditionId, offset, limit)


@router.post(
    "/v1/preconditions/{preconditionId}/versions",
    responses={
        201: {"model": Precondition, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Create a precondition version",
    response_model_by_alias=True,
)
async def create_precondition_version(
    preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")] = Path(..., description="UUID of the precondition version.")
,
    create_precondition_request: CreatePreconditionRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Precondition:
    """Creates a new immutable version for the selected precondition key."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().create_precondition_version(preconditionId, create_precondition_request)


@router.post(
    "/v1/preconditions/{preconditionId}/activations",
    responses={
        200: {"model": Precondition, "description": "Activated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Activate a precondition version",
    response_model_by_alias=True,
)
async def activate_precondition(
    preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")] = Path(..., description="UUID of the precondition version.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Precondition:
    """Activates a draft precondition version for future test executions."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().activate_precondition(preconditionId)


@router.post(
    "/v1/preconditions/{preconditionId}/deprecations",
    responses={
        200: {"model": Precondition, "description": "Deprecated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Authoring"],
    summary="Deprecate a precondition version",
    response_model_by_alias=True,
)
async def deprecate_precondition(
    preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")] = Path(..., description="UUID of the precondition version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Precondition:
    """Marks an immutable precondition version as deprecated."""
    if not BaseAuthoringApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthoringApi.subclasses[0]().deprecate_precondition(preconditionId, action_request)
