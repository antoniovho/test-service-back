# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from test_service_server.apis.execution_api_base import BaseExecutionApi
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
from pydantic import Field
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from test_service_server.models.action_result_list_response import ActionResultListResponse
from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.create_execution_request import CreateExecutionRequest
from test_service_server.models.environment import Environment
from test_service_server.models.environment_list_response import EnvironmentListResponse
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.execution import Execution
from test_service_server.models.execution_list_response import ExecutionListResponse
from test_service_server.models.test_result import TestResult
from test_service_server.models.test_result_artifact_list_response import TestResultArtifactListResponse
from test_service_server.models.test_result_list_response import TestResultListResponse
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/v1/environments",
    responses={
        200: {"model": EnvironmentListResponse, "description": "Environments"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="List execution environments",
    response_model_by_alias=True,
)
async def list_environments(
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> EnvironmentListResponse:
    """Returns a paginated list of configured execution environments without secret values."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().list_environments(offset, limit)


@router.post(
    "/v1/environments",
    responses={
        201: {"model": Environment, "description": "Created"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Create an environment metadata resource",
    response_model_by_alias=True,
)
async def create_environment(
    create_environment_request: CreateEnvironmentRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Environment:
    """Creates execution environment metadata without persisting resolved secrets."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().create_environment(create_environment_request)


@router.get(
    "/v1/environments/{environmentId}",
    responses={
        200: {"model": Environment, "description": "Environment"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Get an environment",
    response_model_by_alias=True,
)
async def get_environment(
    environmentId: Annotated[UUID, Field(description="UUID of the environment.")] = Path(..., description="UUID of the environment.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Environment:
    """Returns environment metadata without resolving or exposing secret values."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().get_environment(environmentId)


@router.post(
    "/v1/environments/{environmentId}/activations",
    responses={
        200: {"model": Environment, "description": "Activated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Activate an environment",
    response_model_by_alias=True,
)
async def activate_environment(
    environmentId: Annotated[UUID, Field(description="UUID of the environment.")] = Path(..., description="UUID of the environment.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Environment:
    """Marks an environment as available for new executions."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().activate_environment(environmentId)


@router.post(
    "/v1/environments/{environmentId}/deactivations",
    responses={
        200: {"model": Environment, "description": "Deactivated"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Deactivate an environment",
    response_model_by_alias=True,
)
async def deactivate_environment(
    environmentId: Annotated[UUID, Field(description="UUID of the environment.")] = Path(..., description="UUID of the environment.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Environment:
    """Marks an environment as unavailable for new executions without deleting its history."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().deactivate_environment(environmentId)


@router.get(
    "/v1/executions",
    responses={
        200: {"model": ExecutionListResponse, "description": "Executions"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="List executions",
    response_model_by_alias=True,
)
async def list_executions(
    project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")] = Query(..., description="Stable key of the project that owns the requested resources.", alias="projectKey", min_length=2, max_length=20)
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ExecutionListResponse:
    """Returns a paginated list of historical and active plan executions."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().list_executions(project_key, offset, limit)


@router.post(
    "/v1/executions",
    responses={
        202: {"model": Execution, "description": "Execution accepted"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Create and schedule a plan execution",
    response_model_by_alias=True,
)
async def create_execution(
    create_execution_request: CreateExecutionRequest = Body(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Execution:
    """Accepts a plan execution request and schedules it for asynchronous processing."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().create_execution(create_execution_request)


@router.get(
    "/v1/executions/{executionId}",
    responses={
        200: {"model": Execution, "description": "Execution"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Get an execution",
    response_model_by_alias=True,
)
async def get_execution(
    executionId: UUID = Path(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Execution:
    """Returns the status, timing, and immutable references of an execution."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().get_execution(executionId)


@router.post(
    "/v1/executions/{executionId}/cancellations",
    responses={
        200: {"model": Execution, "description": "Cancelled"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Cancel an execution",
    response_model_by_alias=True,
)
async def cancel_execution(
    executionId: UUID = Path(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Execution:
    """Requests cancellation of an execution that has not reached a terminal state."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().cancel_execution(executionId)


@router.get(
    "/v1/executions/{executionId}/results",
    responses={
        200: {"model": TestResultListResponse, "description": "Results"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="List results for an execution",
    response_model_by_alias=True,
)
async def list_execution_results(
    executionId: UUID = Path(..., description="")
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestResultListResponse:
    """Returns a paginated list of test results recorded for an execution."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().list_execution_results(executionId, offset, limit)


@router.get(
    "/v1/executions/{executionId}/results/{testResultId}",
    responses={
        200: {"model": TestResult, "description": "Test result"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="Get an execution result",
    response_model_by_alias=True,
)
async def get_execution_result(
    executionId: Annotated[UUID, Field(description="UUID of the execution.")] = Path(..., description="UUID of the execution.")
,
    testResultId: Annotated[UUID, Field(description="UUID of the test result.")] = Path(..., description="UUID of the test result.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestResult:
    """Returns one immutable test result belonging to an execution."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().get_execution_result(executionId, testResultId)


@router.get(
    "/v1/executions/{executionId}/results/{testResultId}/actions",
    responses={
        200: {"model": ActionResultListResponse, "description": "Action results"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="List execution result actions",
    response_model_by_alias=True,
)
async def list_execution_result_actions(
    executionId: Annotated[UUID, Field(description="UUID of the execution.")] = Path(..., description="UUID of the execution.")
,
    testResultId: Annotated[UUID, Field(description="UUID of the test result.")] = Path(..., description="UUID of the test result.")
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ActionResultListResponse:
    """Returns the action results recorded for an execution result."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().list_execution_result_actions(executionId, testResultId, offset, limit)


@router.get(
    "/v1/executions/{executionId}/results/{testResultId}/artifacts",
    responses={
        200: {"model": TestResultArtifactListResponse, "description": "Result artifacts"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Execution"],
    summary="List execution result artifacts",
    response_model_by_alias=True,
)
async def list_execution_result_artifacts(
    executionId: Annotated[UUID, Field(description="UUID of the execution.")] = Path(..., description="UUID of the execution.")
,
    testResultId: Annotated[UUID, Field(description="UUID of the test result.")] = Path(..., description="UUID of the test result.")
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> TestResultArtifactListResponse:
    """Returns metadata for technical evidence attached to an execution result."""
    if not BaseExecutionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseExecutionApi.subclasses[0]().list_execution_result_artifacts(executionId, testResultId, offset, limit)
