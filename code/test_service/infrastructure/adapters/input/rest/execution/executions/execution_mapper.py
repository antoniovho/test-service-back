"""Mapping between generated Execution REST models and domain types."""

from datetime import datetime
from uuid import UUID

from test_service_server.models.create_execution_request import CreateExecutionRequest
from test_service_server.models.execution import Execution as ApiExecution
from test_service_server.models.execution_list_response import ExecutionListResponse
from test_service_server.models.pagination import Pagination as ApiPagination
from test_service_server.models.project_reference import ProjectReference
from test_service_server.models.sort_order import SortOrder as ApiSortOrder

from test_service.domain.application.commands.execution import (
    CancelExecutionCommand,
    ScheduleExecutionCommand,
)
from test_service.domain.application.queries.execution import ExecutionQuery, ListExecutionsQuery
from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.commons.pagination import SortOrder as DomainSortOrder
from test_service.domain.model.execution.execution import Execution, TriggerType


class ExecutionMapper:
    """Translate between the Execution REST contract and execution domain types."""

    @staticmethod
    def to_schedule_command(
        project_key: str, request: CreateExecutionRequest, requested_at: datetime
    ) -> ScheduleExecutionCommand:
        return ScheduleExecutionCommand(
            project_key=project_key,
            test_plan_id=request.test_plan_id,
            environment_id=request.environment_id,
            trigger_type=TriggerType(request.trigger_type),
            requested_at=requested_at,
            triggered_by=request.triggered_by,
        )

    @staticmethod
    def to_get_query(project_key: str, identifier: UUID) -> ExecutionQuery:
        return ExecutionQuery(project_key=project_key, identifier=identifier)

    @staticmethod
    def to_cancel_command(project_key: str, identifier: UUID) -> CancelExecutionCommand:
        return CancelExecutionCommand(project_key=project_key, identifier=identifier)

    @staticmethod
    def to_list_query(
        project_key: str,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order: ApiSortOrder | None,
    ) -> ListExecutionsQuery:
        sort_fields = {
            "createdAt": "created_at",
            "startedAt": "started_at",
            "finishedAt": "finished_at",
            "durationMs": "duration_ms",
            "status": "status",
        }
        return ListExecutionsQuery(
            project_key=project_key,
            pagination=PaginationParams(
                offset=offset if offset is not None else 0,
                limit=limit if limit is not None else 20,
                sort_by=sort_fields.get(sort_by or "createdAt", "created_at"),
                order=DomainSortOrder(order.value) if order is not None else DomainSortOrder.ASC,
            ),
        )

    @staticmethod
    def to_api(execution: Execution, project_name: str) -> ApiExecution:
        return ApiExecution(
            id=execution.identifier,
            project=ProjectReference(key=execution.project_key, name=project_name),
            testPlanId=execution.test_plan_id,
            environmentId=execution.environment_id,
            triggerType=execution.trigger_type.value,
            triggeredBy=execution.triggered_by,
            status=execution.status.value,
            runnerVersion=execution.runner_version,
            startedAt=execution.started_at,
            finishedAt=execution.finished_at,
            durationMs=execution.duration_ms,
            createdAt=execution.created_at,
        )

    @staticmethod
    def to_list_response(
        page: Page[Execution], project_name: str, pagination: PaginationParams
    ) -> ExecutionListResponse:
        return ExecutionListResponse(
            data=[ExecutionMapper.to_api(execution, project_name) for execution in page.items],
            pagination=ApiPagination(
                offset=pagination.offset, limit=pagination.limit, total=page.total
            ),
        )
