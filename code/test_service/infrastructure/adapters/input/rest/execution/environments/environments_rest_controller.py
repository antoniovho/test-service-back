"""Feature controller for Environment execution operations."""

from datetime import UTC, datetime
from uuid import UUID

from test_service_server.models.action_request import ActionRequest
from test_service_server.models.create_environment_request import CreateEnvironmentRequest
from test_service_server.models.environment import Environment as ApiEnvironment
from test_service_server.models.environment_list_response import EnvironmentListResponse

from test_service.bootstrap.container import get_injector
from test_service.domain.ports.input.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCase,
)
from test_service.infrastructure.adapters.input.rest.execution.environments.environment_mapper import (  # noqa: E501
    EnvironmentMapper,
)
from test_service.infrastructure.adapters.input.rest.security.identity_context import (
    get_current_identity,
)


class EnvironmentsRestController:
    """Adapt Environment use cases to the Execution REST contract."""

    def __init__(self) -> None:
        injector = get_injector()
        self._create = injector.inject(CreateEnvironmentUseCase)
        self._get = injector.inject(GetEnvironmentUseCase)
        self._activate = injector.inject(ActivateEnvironmentUseCase)
        self._deactivate = injector.inject(DeactivateEnvironmentUseCase)
        self._list = injector.inject(ListEnvironmentsUseCase)

    async def create(self, request: CreateEnvironmentRequest) -> ApiEnvironment:
        command = EnvironmentMapper.to_create_command(
            request, get_current_identity(), datetime.now(UTC)
        )
        environment = await self._create.execute(command)
        return EnvironmentMapper.to_api(environment)

    async def get(self, environment_id: UUID) -> ApiEnvironment:
        query = EnvironmentMapper.to_get_query(environment_id)
        environment = await self._get.execute(query)
        return EnvironmentMapper.to_api(environment)

    async def activate(self, environment_id: UUID, request: ActionRequest | None) -> ApiEnvironment:
        return EnvironmentMapper.to_api(
            await self._activate.execute(
                EnvironmentMapper.to_activate_command(
                    environment_id, request.reason if request else None
                )
            )
        )

    async def deactivate(
        self, environment_id: UUID, request: ActionRequest | None
    ) -> ApiEnvironment:
        return EnvironmentMapper.to_api(
            await self._deactivate.execute(
                EnvironmentMapper.to_deactivate_command(
                    environment_id, request.reason if request else None
                )
            )
        )

    async def list(
        self, offset: int | None, limit: int | None, sort_by: str | None, order
    ) -> EnvironmentListResponse:
        query = EnvironmentMapper.to_list_query(offset, limit, sort_by, order)
        environments = await self._list.execute(query)
        return EnvironmentMapper.to_list_response(environments, query.pagination)
