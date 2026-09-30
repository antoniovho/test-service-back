"""Use case implementation: activate environment."""

from test_service.domain.application.commands.execution import ActivateEnvironmentCommand
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)


class ActivateEnvironmentUseCaseImpl(ActivateEnvironmentUseCase):
    """Marks an existing environment as active."""

    def __init__(self, environment_repository: EnvironmentPersistencePort) -> None:
        self._environment_repository = environment_repository

    async def execute(self, request: ActivateEnvironmentCommand) -> Environment:
        """Persist the environment's active state."""
        environment = await self._environment_repository.find_by_id(request.identifier)
        if environment is None:
            raise EntityNotFoundException("environment", str(request.identifier))
        return await self._environment_repository.save(environment.activate())
