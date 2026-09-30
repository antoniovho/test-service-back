"""Generated Execution API controller delegation boundary."""

from uuid import UUID

from test_service_server.apis.execution_api_base import BaseExecutionApi
from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.create_execution_request import CreateExecutionRequest

from test_service.infrastructure.adapters.input.rest.execution.environments.environments_rest_controller import (  # noqa: E501
    EnvironmentsRestController,
)
from test_service.infrastructure.adapters.input.rest.execution.executions.executions_rest_controller import (  # noqa: E501
    ExecutionsRestController,
)


class ExecutionController(BaseExecutionApi):
    """Delegate implemented Execution endpoints to their feature controllers."""

    def __init__(self) -> None:
        self._environments = EnvironmentsRestController()
        self._executions = ExecutionsRestController()

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
