"""Generated Execution API controller delegation boundary."""

from uuid import UUID

from test_service_server.apis.execution_api_base import BaseExecutionApi
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.create_execution_request import CreateExecutionRequest

from test_service.infrastructure.adapters.input.rest.execution.environments.environments_rest_controller import (  # noqa: E501
    EnvironmentsRestController,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.execution_results_rest_controller import (  # noqa: E501
    ExecutionResultsRestController,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.executions_rest_controller import (  # noqa: E501
    ExecutionsRestController,
)


class ExecutionController(BaseExecutionApi):
    """Delegate implemented Execution endpoints to their feature controllers."""

    def __init__(self) -> None:
        self._environments = EnvironmentsRestController()
        self._executions = ExecutionsRestController()
        self._execution_results = ExecutionResultsRestController()

    async def list_environments(self, offset, limit, sort_by, order):
        return await self._environments.list(offset, limit, sort_by, order)

    async def create_environment(self, create_environment_request: CreateEnvironmentRequest):
        return await self._environments.create(create_environment_request)

    async def get_environment(self, environmentId: UUID):  # NOSONAR
        return await self._environments.get(environmentId)

    async def activate_environment(
        self, environment_id: UUID, action_request: ActionRequest | None
    ):  # NOSONAR
        return await self._environments.activate(environment_id, action_request)

    async def deactivate_environment(
        self, environment_id: UUID, action_request: ActionRequest | None
    ):  # NOSONAR
        return await self._environments.deactivate(environment_id, action_request)

    async def list_executions(self, project_key, offset, limit, sort_by, order):
        return await self._executions.list(project_key, offset, limit, sort_by, order)

    async def create_execution(self, project_key, create_execution_request: CreateExecutionRequest):
        return await self._executions.create(project_key, create_execution_request)

    async def get_execution(self, project_key, execution_id: UUID):
        return await self._executions.get(project_key, execution_id)

    async def cancel_execution(self, project_key, execution_id: UUID):
        return await self._executions.cancel(project_key, execution_id)

    async def list_execution_results(
        self, project_key, execution_id: UUID, offset, limit, sort_by, order
    ):
        return await self._execution_results.list_results(
            project_key, execution_id, offset, limit, sort_by, order
        )

    async def get_execution_result(self, project_key, execution_id: UUID, test_result_id: UUID):
        return await self._execution_results.get_result(project_key, execution_id, test_result_id)

    async def list_execution_result_actions(
        self, project_key, execution_id: UUID, test_result_id: UUID, offset, limit, sort_by, order
    ):
        return await self._execution_results.list_actions(
            project_key, execution_id, test_result_id, offset, limit, sort_by, order
        )

    async def list_execution_result_artifacts(
        self, project_key, execution_id: UUID, test_result_id: UUID, offset, limit, sort_by, order
    ):
        return await self._execution_results.list_artifacts(
            project_key, execution_id, test_result_id, offset, limit, sort_by, order
        )
