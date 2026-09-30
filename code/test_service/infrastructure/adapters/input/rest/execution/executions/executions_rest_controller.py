"""Feature controller for Test Plan execution operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.create_execution_request import CreateExecutionRequest
from test_service_server.models.execution import Execution as ApiExecution
from test_service_server.models.execution_list_response import ExecutionListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.application.queries.projects import GetProjectQuery
from test_service.domain.ports.input.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.execution_mapper import (  # noqa: E501
    ExecutionMapper,
)


class ExecutionsRestController:
    """Adapt execution use cases to the Execution REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._schedule = injector.inject(ScheduleExecutionUseCase)
        self._get = injector.inject(GetExecutionUseCase)
        self._list = injector.inject(ListExecutionsUseCase)
        self._cancel = injector.inject(CancelExecutionUseCase)
        self._get_project = injector.inject(GetProjectUseCase)

    async def create(self, project_key: str, request: CreateExecutionRequest) -> ApiExecution:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        execution = await self._schedule.execute(
            ExecutionMapper.to_schedule_command(project_key, request, datetime.now(UTC))
        )
        return ExecutionMapper.to_api(execution, project.name)

    async def get(self, project_key: str, execution_id: UUID) -> ApiExecution:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        execution = await self._get.execute(ExecutionMapper.to_get_query(project_key, execution_id))
        return ExecutionMapper.to_api(execution, project.name)

    async def cancel(self, project_key: str, execution_id: UUID) -> ApiExecution:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        execution = await self._cancel.execute(
            ExecutionMapper.to_cancel_command(project_key, execution_id)
        )
        return ExecutionMapper.to_api(execution, project.name)

    async def list(
        self,
        project_key: str,
        offset: int | None,
        limit: int | None,
        sort_by: str | None,
        order,
    ) -> ExecutionListResponse:
        project = await self._get_project.execute(GetProjectQuery(project_key))
        query = ExecutionMapper.to_list_query(project_key, offset, limit, sort_by, order)
        return ExecutionMapper.to_list_response(
            await self._list.execute(query), project.name, query.pagination
        )
