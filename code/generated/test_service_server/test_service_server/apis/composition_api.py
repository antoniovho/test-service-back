# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from test_service_server.apis.composition_api_base import BaseCompositionApi
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
from test_service_server.models.create_test_plan_request import CreateTestPlanRequest
from test_service_server.models.create_test_set_request import CreateTestSetRequest
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.sort_order import SortOrder
from test_service_server.models.test_plan import TestPlan
from test_service_server.models.test_plan_list_response import TestPlanListResponse
from test_service_server.models.test_set import TestSet
from test_service_server.models.test_set_list_response import TestSetListResponse
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/test-sets",
    responses={
        200: {"model": TestSetListResponse, "description": "Test sets"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="List test set snapshots",
    response_model_by_alias=True,
)
async def list_test_sets(
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
) -> TestSetListResponse:
    """Returns a paginated list of versioned test set snapshots."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().list_test_sets(project_key, status, offset, limit, sort_by, order)


@router.post(
    "/v1/test-sets",
    responses={
        201: {"model": TestSet, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Create a test set snapshot",
    response_model_by_alias=True,
)
async def create_test_set(
    create_test_set_request: CreateTestSetRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestSet:
    """Creates an immutable test set snapshot referencing exact test case versions."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().create_test_set(create_test_set_request)


@router.get(
    "/v1/test-sets/{testSetId}",
    responses={
        200: {"model": TestSet, "description": "Test set"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Get a test set version",
    response_model_by_alias=True,
)
async def get_test_set(
    testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")] = Path(..., description="UUID of the immutable test set version.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestSet:
    """Returns an immutable test set version by UUID."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().get_test_set(testSetId)


@router.post(
    "/v1/test-sets/{testSetId}/versions",
    responses={
        201: {"model": TestSet, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Create a test set version",
    response_model_by_alias=True,
)
async def create_test_set_version(
    testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")] = Path(..., description="UUID of the immutable test set version.")
,
    create_test_set_request: CreateTestSetRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestSet:
    """Creates a new immutable draft version of a test set."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().create_test_set_version(testSetId, create_test_set_request)


@router.post(
    "/v1/test-sets/{testSetId}/activations",
    responses={
        200: {"model": TestSet, "description": "Activated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Activate a test set version",
    response_model_by_alias=True,
)
async def activate_test_set(
    testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")] = Path(..., description="UUID of the immutable test set version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestSet:
    """Marks a test set version as active for new compositions."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().activate_test_set(testSetId, action_request)


@router.post(
    "/v1/test-sets/{testSetId}/deprecations",
    responses={
        200: {"model": TestSet, "description": "Deprecated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Deprecate a test set version",
    response_model_by_alias=True,
)
async def deprecate_test_set(
    testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")] = Path(..., description="UUID of the immutable test set version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestSet:
    """Marks a test set version as deprecated."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().deprecate_test_set(testSetId, action_request)


@router.get(
    "/v1/test-plans",
    responses={
        200: {"model": TestPlanListResponse, "description": "Test plans"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="List test plan snapshots",
    response_model_by_alias=True,
)
async def list_test_plans(
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
) -> TestPlanListResponse:
    """Returns a paginated list of versioned test plan snapshots."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().list_test_plans(project_key, status, offset, limit, sort_by, order)


@router.post(
    "/v1/test-plans",
    responses={
        201: {"model": TestPlan, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Create a test plan snapshot",
    response_model_by_alias=True,
)
async def create_test_plan(
    create_test_plan_request: CreateTestPlanRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestPlan:
    """Creates an immutable test plan snapshot with sets, tests, and exclusions."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().create_test_plan(create_test_plan_request)


@router.get(
    "/v1/test-plans/{testPlanId}",
    responses={
        200: {"model": TestPlan, "description": "Test plan"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Get a test plan version",
    response_model_by_alias=True,
)
async def get_test_plan(
    testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")] = Path(..., description="UUID of the immutable test plan version.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestPlan:
    """Returns an immutable test plan version by UUID."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().get_test_plan(testPlanId)


@router.post(
    "/v1/test-plans/{testPlanId}/versions",
    responses={
        201: {"model": TestPlan, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Create a test plan version",
    response_model_by_alias=True,
)
async def create_test_plan_version(
    testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")] = Path(..., description="UUID of the immutable test plan version.")
,
    create_test_plan_request: CreateTestPlanRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestPlan:
    """Creates a new immutable draft version of a test plan."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().create_test_plan_version(testPlanId, create_test_plan_request)


@router.post(
    "/v1/test-plans/{testPlanId}/activations",
    responses={
        200: {"model": TestPlan, "description": "Activated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Activate a test plan version",
    response_model_by_alias=True,
)
async def activate_test_plan(
    testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")] = Path(..., description="UUID of the immutable test plan version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestPlan:
    """Marks a test plan version as active for execution."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().activate_test_plan(testPlanId, action_request)


@router.post(
    "/v1/test-plans/{testPlanId}/deprecations",
    responses={
        200: {"model": TestPlan, "description": "Deprecated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Composition"],
    summary="Deprecate a test plan version",
    response_model_by_alias=True,
)
async def deprecate_test_plan(
    testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")] = Path(..., description="UUID of the immutable test plan version.")
,
    action_request: Optional[ActionRequest] = Body(None, description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestPlan:
    """Marks a test plan version as deprecated."""
    if not BaseCompositionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCompositionApi.subclasses[0]().deprecate_test_plan(testPlanId, action_request)
