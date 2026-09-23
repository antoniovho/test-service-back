# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BaseCompositionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseCompositionApi.subclasses = BaseCompositionApi.subclasses + (cls,)
    async def list_test_sets(
        self,
        project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")],
        status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> TestSetListResponse:
        """Returns a paginated list of versioned test set snapshots."""
        ...


    async def create_test_set(
        self,
        create_test_set_request: CreateTestSetRequest,
    ) -> TestSet:
        """Creates an immutable test set snapshot referencing exact test case versions."""
        ...


    async def get_test_set(
        self,
        testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")],
    ) -> TestSet:
        """Returns an immutable test set version by UUID."""
        ...


    async def create_test_set_version(
        self,
        testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")],
        create_test_set_request: CreateTestSetRequest,
    ) -> TestSet:
        """Creates a new immutable draft version of a test set."""
        ...


    async def activate_test_set(
        self,
        testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")],
        action_request: Optional[ActionRequest],
    ) -> TestSet:
        """Marks a test set version as active for new compositions."""
        ...


    async def deprecate_test_set(
        self,
        testSetId: Annotated[UUID, Field(description="UUID of the immutable test set version.")],
        action_request: Optional[ActionRequest],
    ) -> TestSet:
        """Marks a test set version as deprecated."""
        ...


    async def list_test_plans(
        self,
        project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")],
        status: Annotated[Optional[StrictStr], Field(description="Filter versions by lifecycle status. When omitted, all statuses are returned.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
        sort_by: Annotated[Optional[StrictStr], Field(description="Field used to sort the result set.")],
        order: Annotated[Optional[SortOrder], Field(description="Sort direction.")],
    ) -> TestPlanListResponse:
        """Returns a paginated list of versioned test plan snapshots."""
        ...


    async def create_test_plan(
        self,
        create_test_plan_request: CreateTestPlanRequest,
    ) -> TestPlan:
        """Creates an immutable test plan snapshot with sets, tests, and exclusions."""
        ...


    async def get_test_plan(
        self,
        testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")],
    ) -> TestPlan:
        """Returns an immutable test plan version by UUID."""
        ...


    async def create_test_plan_version(
        self,
        testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")],
        create_test_plan_request: CreateTestPlanRequest,
    ) -> TestPlan:
        """Creates a new immutable draft version of a test plan."""
        ...


    async def activate_test_plan(
        self,
        testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")],
        action_request: Optional[ActionRequest],
    ) -> TestPlan:
        """Marks a test plan version as active for execution."""
        ...


    async def deprecate_test_plan(
        self,
        testPlanId: Annotated[UUID, Field(description="UUID of the immutable test plan version.")],
        action_request: Optional[ActionRequest],
    ) -> TestPlan:
        """Marks a test plan version as deprecated."""
        ...
