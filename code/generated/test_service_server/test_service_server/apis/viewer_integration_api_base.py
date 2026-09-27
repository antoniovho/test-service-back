# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr, field_validator
from typing import Optional
from typing_extensions import Annotated
from test_service_server.models.drift_event_list_response import DriftEventListResponse
from test_service_server.models.error_details import ErrorDetails
from test_service_server.models.sort_order import SortOrder
from test_service_server.models.viewer_sync_record_list_response import ViewerSyncRecordListResponse
from test_service_server.security_api import get_token_bearerAuth

class BaseViewerIntegrationApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseViewerIntegrationApi.subclasses = BaseViewerIntegrationApi.subclasses + (cls,)
    async def publish_viewer_projection(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
    ) -> ViewerSyncRecordListResponse:
        """Publishes the current ACTIVE version of every test case, precondition, test set, and test plan in the project to the configured external viewer. """
        ...


    async def check_viewer_drift(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
    ) -> DriftEventListResponse:
        """Checks the external viewer for drift across every ACTIVE test case, precondition, test set, and test plan version in the project, without importing remote data into the domain. """
        ...


    async def list_project_viewer_sync_records(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> ViewerSyncRecordListResponse:
        """Returns a paginated list of canonical-to-viewer synchronization records for one project."""
        ...


    async def list_project_viewer_drift_events(
        self,
        projectKey: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project in the Project Catalog.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> DriftEventListResponse:
        """Returns a paginated list of detected viewer changes and notification states for one project."""
        ...


    async def list_viewer_sync_records(
        self,
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> ViewerSyncRecordListResponse:
        """Returns a paginated list of canonical-to-viewer synchronization records."""
        ...


    async def list_viewer_drift_events(
        self,
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> DriftEventListResponse:
        """Returns a paginated list of detected viewer changes and notification states."""
        ...
