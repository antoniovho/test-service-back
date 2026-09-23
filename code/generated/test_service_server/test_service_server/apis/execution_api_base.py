# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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

class BaseExecutionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseExecutionApi.subclasses = BaseExecutionApi.subclasses + (cls,)
    async def list_environments(
        self,
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> EnvironmentListResponse:
        """Returns a paginated list of configured execution environments without secret values."""
        ...


    async def create_environment(
        self,
        create_environment_request: CreateEnvironmentRequest,
    ) -> Environment:
        """Creates execution environment metadata without persisting resolved secrets."""
        ...


    async def get_environment(
        self,
        environmentId: Annotated[UUID, Field(description="UUID of the environment.")],
    ) -> Environment:
        """Returns environment metadata without resolving or exposing secret values."""
        ...


    async def activate_environment(
        self,
        environmentId: Annotated[UUID, Field(description="UUID of the environment.")],
    ) -> Environment:
        """Marks an environment as available for new executions."""
        ...


    async def deactivate_environment(
        self,
        environmentId: Annotated[UUID, Field(description="UUID of the environment.")],
    ) -> Environment:
        """Marks an environment as unavailable for new executions without deleting its history."""
        ...


    async def list_executions(
        self,
        project_key: Annotated[str, Field(min_length=2, strict=True, max_length=20, description="Stable key of the project that owns the requested resources.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> ExecutionListResponse:
        """Returns a paginated list of historical and active plan executions."""
        ...


    async def create_execution(
        self,
        create_execution_request: CreateExecutionRequest,
    ) -> Execution:
        """Accepts a plan execution request and schedules it for asynchronous processing."""
        ...


    async def get_execution(
        self,
        executionId: UUID,
    ) -> Execution:
        """Returns the status, timing, and immutable references of an execution."""
        ...


    async def cancel_execution(
        self,
        executionId: UUID,
    ) -> Execution:
        """Requests cancellation of an execution that has not reached a terminal state."""
        ...


    async def list_execution_results(
        self,
        executionId: UUID,
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> TestResultListResponse:
        """Returns a paginated list of test results recorded for an execution."""
        ...


    async def get_execution_result(
        self,
        executionId: Annotated[UUID, Field(description="UUID of the execution.")],
        testResultId: Annotated[UUID, Field(description="UUID of the test result.")],
    ) -> TestResult:
        """Returns one immutable test result belonging to an execution."""
        ...


    async def list_execution_result_actions(
        self,
        executionId: Annotated[UUID, Field(description="UUID of the execution.")],
        testResultId: Annotated[UUID, Field(description="UUID of the test result.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> ActionResultListResponse:
        """Returns the action results recorded for an execution result."""
        ...


    async def list_execution_result_artifacts(
        self,
        executionId: Annotated[UUID, Field(description="UUID of the execution.")],
        testResultId: Annotated[UUID, Field(description="UUID of the test result.")],
        offset: Annotated[Optional[Annotated[int, Field(strict=True, ge=0)]], Field(description="Number of records to skip before returning results.")],
        limit: Annotated[Optional[Annotated[int, Field(le=100, strict=True, ge=1)]], Field(description="Maximum number of records returned in one page.")],
    ) -> TestResultArtifactListResponse:
        """Returns metadata for technical evidence attached to an execution result."""
        ...
