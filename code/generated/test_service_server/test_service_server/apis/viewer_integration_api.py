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
from pydantic import Field
from typing import Optional
from typing_extensions import Annotated
from test_service_server.models.drift_event import DriftEvent
from test_service_server.models.drift_event_list_response import DriftEventListResponse
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.viewer_sync_record import ViewerSyncRecord
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse
from test_service_server.security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = test_service_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/v1/viewer/publications",
    responses={
        202: {"model": ViewerSyncRecord, "description": "Publication accepted"},
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
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerSyncRecord:
    """Publishes the canonical local projection to the configured external viewer."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().publish_viewer_projection()


@router.post(
    "/v1/viewer/drift-checks",
    responses={
        202: {"model": DriftEvent, "description": "Drift check accepted"},
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
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> DriftEvent:
    """Checks the external viewer for drift without importing remote data into the domain."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().check_viewer_drift()


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
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ViewerSyncRecordListResponse:
    """Returns a paginated list of canonical-to-viewer synchronization records."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_viewer_sync_records(offset, limit)


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
    offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")] = Query(0, description="Number of records to skip before returning results.", alias="offset", ge=0)
,
    limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")] = Query(20, description="Maximum number of records returned in one page.", alias="limit", ge=1, le=100)
,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> DriftEventListResponse:
    """Returns a paginated list of detected viewer changes and notification states."""
    if not BaseViewerIntegrationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseViewerIntegrationApi.subclasses[0]().list_viewer_drift_events(offset, limit)
