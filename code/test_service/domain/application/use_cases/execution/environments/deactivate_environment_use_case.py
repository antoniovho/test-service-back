"""Use case implementation: deactivate environment."""

from test_service.domain.application.commands.execution import DeactivateEnvironmentCommand
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)


class DeactivateEnvironmentUseCaseImpl(DeactivateEnvironmentUseCase):
    """Marks an existing environment as inactive."""

    def __init__(self, environment_repository: EnvironmentPersistencePort) -> None:
        self._environment_repository = environment_repository

    async def execute(self, request: DeactivateEnvironmentCommand) -> Environment:
        """Persist the environment's inactive state."""
        environment = await self._environment_repository.find_by_id(request.identifier)
        if environment is None:
            raise EntityNotFoundException("environment", str(request.identifier))
        return await self._environment_repository.save(environment.deactivate())
