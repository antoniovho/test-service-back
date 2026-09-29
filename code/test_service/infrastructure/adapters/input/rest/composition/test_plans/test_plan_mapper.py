"""Mapping between the Composition REST contract and Test Plan domain types."""

from datetime import datetime
from uuid import UUID

from test_service_server.models.create_test_plan_request import CreateTestPlanRequest
from test_service_server.models.project_reference import ProjectReference
from test_service_server.models.test_plan import TestPlan as ApiTestPlan
from test_service_server.models.test_plan_list_response import TestPlanListResponse
from test_service_server.models.test_plan_version_list_response import TestPlanVersionListResponse

from test_service.domain.application.commands.composition import (
    ActivateTestPlanCommand,
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    DeprecateTestPlanCommand,
)
from test_service.domain.application.queries.composition import (
    ListTestPlansQuery,
    ListTestPlanVersionsQuery,
    TestPlanQuery,
)
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.composition.test_plan import ExecutionMode, TestPlan
from test_service.domain.model.lifecycle import VersionStatus
from test_service.infrastructure.adapters.input.rest.versioned_resource_mapper import (
    VersionedResourceMapper,
)


class TestPlanMapper:
    @staticmethod
    def _fields(request: CreateTestPlanRequest, identity: str, requested_at: datetime) -> dict:
        return {
            "name": request.name,
            "description": request.description,
            "execution_mode": ExecutionMode(request.execution_mode),
            "max_parallelism": request.max_parallelism,
            "timeout_seconds": request.timeout_seconds,
            "test_set_ids": tuple(request.test_set_ids or ()),
            "test_case_ids": tuple(request.test_case_ids or ()),
            "exclusions": tuple(request.exclusions or ()),
            "requested_by": identity,
            "requested_at": requested_at,
        }

    @staticmethod
    def to_create_command(
        project_key: str, request: CreateTestPlanRequest, identity: str, requested_at: datetime
    ) -> CreateTestPlanCommand:
        fields = TestPlanMapper._fields(request, identity, requested_at)
        fields.update(project_key=project_key, plan_key=request.plan_key)
        return CreateTestPlanCommand(**fields)

    @staticmethod
    def to_create_version_command(
        project_key: str,
        source_id: UUID,
        request: CreateTestPlanRequest,
        identity: str,
        requested_at: datetime,
    ) -> CreateTestPlanVersionCommand:
        fields = TestPlanMapper._fields(request, identity, requested_at)
        fields.update(source_id=source_id, project_key=project_key, plan_key=request.plan_key)
        return CreateTestPlanVersionCommand(**fields)

    @staticmethod
    def to_pagination(
        offset: int | None, limit: int | None, sort_by: str | None, order
    ) -> PaginationParams:
        return VersionedResourceMapper.to_pagination(offset, limit, sort_by, order)

    @staticmethod
    def to_status(value: str | None) -> VersionStatus | None:
        return VersionedResourceMapper.to_status(value)

    @staticmethod
    def to_get_query(project_key: str, identifier: UUID) -> TestPlanQuery:
        return TestPlanQuery(project_key=project_key, identifier=identifier)

    @staticmethod
    def to_activate_command(
        project_key: str, identifier: UUID, reason: str | None
    ) -> ActivateTestPlanCommand:
        return ActivateTestPlanCommand(
            project_key=project_key, identifier=identifier, reason=reason
        )

    @staticmethod
    def to_deprecate_command(
        project_key: str, identifier: UUID, reason: str | None
    ) -> DeprecateTestPlanCommand:
        return DeprecateTestPlanCommand(
            project_key=project_key, identifier=identifier, reason=reason
        )

    @staticmethod
    def to_list_query(
        project_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> ListTestPlansQuery:
        return ListTestPlansQuery(project_key=project_key, pagination=pagination, status=status)

    @staticmethod
    def to_versions_query(
        project_key: str, plan_key: str, pagination: PaginationParams, status: VersionStatus | None
    ) -> ListTestPlanVersionsQuery:
        return ListTestPlanVersionsQuery(
            project_key=project_key,
            plan_key=plan_key,
            pagination=pagination,
            status=status,
        )

    @staticmethod
    def to_api(test_plan: TestPlan, project_name: str) -> ApiTestPlan:
        return ApiTestPlan(
            id=test_plan.identifier,
            project=ProjectReference(key=test_plan.project_key, name=project_name),
            planKey=test_plan.plan_key,
            version=test_plan.version,
            name=test_plan.name,
            description=test_plan.description,
            status=test_plan.status.value,
            executionMode=test_plan.execution_mode.value,
            maxParallelism=test_plan.max_parallelism,
            timeoutSeconds=test_plan.timeout_seconds,
            testSetIds=list(test_plan.test_set_ids),
            testCaseIds=list(test_plan.test_case_ids),
            exclusions=list(test_plan.exclusions),
            createdAt=test_plan.created_at,
            createdBy=test_plan.created_by,
        )

    @staticmethod
    def to_list_response(
        page: Page[TestPlan], project_name: str, pagination: PaginationParams
    ) -> TestPlanListResponse:
        return VersionedResourceMapper.to_response(
            TestPlanListResponse, page, project_name, pagination, TestPlanMapper.to_api
        )

    @staticmethod
    def to_version_list_response(
        page: Page[TestPlan], project_name: str, pagination: PaginationParams
    ) -> TestPlanVersionListResponse:
        return VersionedResourceMapper.to_response(
            TestPlanVersionListResponse, page, project_name, pagination, TestPlanMapper.to_api
        )
