# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BaseAuthoringApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthoringApi.subclasses = BaseAuthoringApi.subclasses + (cls,)
    async def list_test_cases(
        self,
        project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")],
        status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> TestCaseListResponse:
        """Returns a paginated list of immutable test case versions."""
        ...


    async def create_test_case(
        self,
        create_test_case_request: CreateTestCaseRequest,
    ) -> TestCase:
        """Creates a new immutable test case version in draft status."""
        ...


    async def get_test_case(
        self,
        testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")],
    ) -> TestCase:
        """Returns the complete definition and metadata of a test case version."""
        ...


    async def list_test_case_versions(
        self,
        testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> TestCaseVersionListResponse:
        """Returns all immutable versions associated with a test case key."""
        ...


    async def create_test_case_version(
        self,
        testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")],
        create_test_case_request: CreateTestCaseRequest,
    ) -> TestCase:
        """Creates a new version without modifying any existing test case version."""
        ...


    async def activate_test_case(
        self,
        testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")],
        action_request: Optional[ActionRequest],
    ) -> TestCase:
        """Activates a draft test case version for future compositions and executions."""
        ...


    async def deprecate_test_case(
        self,
        testCaseId: Annotated[UUID, Field(description="UUID of the test case version.")],
        action_request: Optional[ActionRequest],
    ) -> TestCase:
        """Deprecates a test case version so it cannot be selected for new compositions."""
        ...


    async def list_preconditions(
        self,
        status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> PreconditionListResponse:
        """Returns a paginated list of versioned preconditions."""
        ...


    async def create_precondition(
        self,
        create_precondition_request: CreatePreconditionRequest,
    ) -> Precondition:
        """Creates a new immutable precondition version in draft status."""
        ...


    async def get_precondition(
        self,
        preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")],
    ) -> Precondition:
        """Returns an immutable precondition version by UUID."""
        ...


    async def list_precondition_versions(
        self,
        preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> PreconditionListResponse:
        """Returns all immutable versions associated with a precondition key."""
        ...


    async def create_precondition_version(
        self,
        preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")],
        create_precondition_request: CreatePreconditionRequest,
    ) -> Precondition:
        """Creates a new immutable version for the selected precondition key."""
        ...


    async def activate_precondition(
        self,
        preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")],
    ) -> Precondition:
        """Activates a draft precondition version for future test executions."""
        ...


    async def deprecate_precondition(
        self,
        preconditionId: Annotated[UUID, Field(description="UUID of the precondition version.")],
        action_request: Optional[ActionRequest],
    ) -> Precondition:
        """Marks an immutable precondition version as deprecated."""
        ...
