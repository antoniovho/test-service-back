# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from test_service_server.apis.viewer_integration_api_base import BaseViewerIntegrationApi
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
from test_service_server.models.drift_event_list_response import DriftEventListResponse
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.sort_order import SortOrder
from test_service_server.models.viewer_operation import ViewerOperation
from test_service_server.models.viewer_operation_list_response import ViewerOperationListResponse
from test_service_server.models.viewer_operation_request import ViewerOperationRequest
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse
from test_service_server.models.viewer_type import ViewerType
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/v1/projects/{projectKey}/viewer/publications",
    responses={
        202: {"model": ViewerOperation, "description": "Publication accepted"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="Publish canonical data to the external viewer",
    response_model_by_alias=True,
)
async def publish_viewer_projection(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewer_operation_request: Annotated[ViewerOperationRequest, Field(description="External viewer that receives the project projection.")] = Body(..., description="External viewer that receives the project projection.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerOperation:
    """Publishes the current ACTIVE version of every test case, precondition, test set, and test plan in the project to the configured external viewer. """
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().publish_viewer_projection(projectKey, viewer_operation_request)


@router.post(
    "/v1/projects/{projectKey}/viewer/drift-checks",
    responses={
        202: {"model": ViewerOperation, "description": "Drift check accepted"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="Detect changes made in the external viewer",
    response_model_by_alias=True,
)
async def check_viewer_drift(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewer_operation_request: Annotated[ViewerOperationRequest, Field(description="External viewer whose project projection is checked for drift.")] = Body(..., description="External viewer whose project projection is checked for drift.")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerOperation:
    """Checks the external viewer for drift across every ACTIVE test case, precondition, test set, and test plan version in the project, without importing remote data into the domain. """
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().check_viewer_drift(projectKey, viewer_operation_request)


@router.get(
    "/v1/projects/{projectKey}/viewer/sync-records",
    responses={
        200: {"model": ViewerSyncRecordListResponse, "description": "Sync records"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List outbound synchronization records for a project",
    response_model_by_alias=True,
)
async def list_project_viewer_sync_records(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")] = Query('createdAt', description="Field used to sort the result set.", alias="sortBy", examples=["createdAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerSyncRecordListResponse:
    """Returns a paginated list of canonical-to-viewer synchronization records for one project."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_project_viewer_sync_records(projectKey, viewer_type, offset, limit, sort_by, order)


@router.get(
    "/v1/projects/{projectKey}/viewer/drift-events",
    responses={
        200: {"model": DriftEventListResponse, "description": "Drift events"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List detected viewer drift events for a project",
    response_model_by_alias=True,
)
async def list_project_viewer_drift_events(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")] = Query('detectedAt', description="Field used to sort the result set.", alias="sortBy", examples=["detectedAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> DriftEventListResponse:
    """Returns a paginated list of detected viewer changes and notification states for one project."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_project_viewer_drift_events(projectKey, viewer_type, offset, limit, sort_by, order)


@router.get(
    "/v1/projects/{projectKey}/viewer/operations",
    responses={
        200: {"model": ViewerOperationListResponse, "description": "Viewer operations for the project"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List asynchronous Viewer operations for a project",
    response_model_by_alias=True,
)
async def list_project_viewer_operations(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort asynchronous Viewer operations.")] = Query('createdAt', description="Field used to sort asynchronous Viewer operations.", alias="sortBy", examples=["createdAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerOperationListResponse:
    """Returns a paginated list of asynchronous Viewer operations within a specific project."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_project_viewer_operations(projectKey, viewer_type, offset, limit, sort_by, order)


@router.get(
    "/v1/projects/{projectKey}/viewer/operations/{viewerOperationId}",
    responses={
        200: {"model": ViewerOperation, "description": "Viewer operation"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="Get an asynchronous Viewer operation",
    response_model_by_alias=True,
)
async def get_project_viewer_operation(
    projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")] = Path(..., description="Stable key of the project in the Project Catalog.", min_length=2, max_length=20)
,
    viewerOperationId: UUID = Path(..., description="")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerOperation:
    """Retrieves the details of a specific asynchronous Viewer operation within a project."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().get_project_viewer_operation(projectKey, viewerOperationId)


@router.get(
    "/v1/viewer/sync-records",
    responses={
        200: {"model": ViewerSyncRecordListResponse, "description": "Sync records"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List outbound synchronization records",
    response_model_by_alias=True,
)
async def list_viewer_sync_records(
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")] = Query('createdAt', description="Field used to sort the result set.", alias="sortBy", examples=["createdAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerSyncRecordListResponse:
    """Returns a paginated list of canonical-to-viewer synchronization records."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_viewer_sync_records(viewer_type, offset, limit, sort_by, order)


@router.get(
    "/v1/viewer/drift-events",
    responses={
        200: {"model": DriftEventListResponse, "description": "Drift events"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        404: {"model": ErrorDetails, "description": "The requested resource was not found."},
        409: {"model": ErrorDetails, "description": "The operation conflicts with the current state of the resource."},
        422: {"model": ErrorDetails, "description": "The request is syntactically valid but violates a domain rule."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List detected viewer drift events",
    response_model_by_alias=True,
)
async def list_viewer_drift_events(
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")] = Query('detectedAt', description="Field used to sort the result set.", alias="sortBy", examples=["detectedAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> DriftEventListResponse:
    """Returns a paginated list of detected viewer changes and notification states."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_viewer_drift_events(viewer_type, offset, limit, sort_by, order)


@router.get(
    "/v1/viewer/operations",
    responses={
        200: {"model": ViewerOperationListResponse, "description": "Viewer operations"},
        400: {"model": ErrorDetails, "description": "The request is invalid."},
        401: {"model": ErrorDetails, "description": "Authentication is required or failed."},
        403: {"model": ErrorDetails, "description": "The authenticated principal is not allowed to perform the operation."},
        500: {"model": ErrorDetails, "description": "An unexpected server error occurred."},
        503: {"model": ErrorDetails, "description": "The service is temporarily unavailable."},
    },
    tags=["Viewer Integration"],
    summary="List asynchronous Viewer operations",
    response_model_by_alias=True,
)
async def list_viewer_operations(
    viewer_type: Annotated[Optional[ViewerType], Field(description="Optional external viewer integration used to filter the result set.")] = Query(None, description="Optional external viewer integration used to filter the result set.", alias="viewerType", examples=["XRAY"])
,
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort asynchronous Viewer operations.")] = Query('createdAt', description="Field used to sort asynchronous Viewer operations.", alias="sortBy", examples=["createdAt"])
,
    order: Annotated[Optional[SortOrder], Field(description="Sort direction.")] = Query('ASC', description="Sort direction.", alias="order")
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerOperationListResponse:
    """Returns a paginated list of asynchronous Viewer operations."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_viewer_operations(viewer_type, offset, limit, sort_by, order)
