"""Use case implementation: get environment."""

from test_service.domain.application.queries.execution import EnvironmentQuery
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)


class GetEnvironmentUseCaseImpl(GetEnvironmentUseCase):
    """Retrieves an execution environment by UUID."""

    def __init__(self, environment_repository: EnvironmentPersistencePort) -> None:
        self._environment_repository = environment_repository

    async def execute(self, request: EnvironmentQuery) -> Environment:
        """Return the environment matching the requested identifier."""
        environment = await self._environment_repository.find_by_id(request.identifier)
        if environment is None:
            raise EntityNotFoundException("environment", str(request.identifier))
        return environment
