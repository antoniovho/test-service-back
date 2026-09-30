"""Use case implementation: create environment."""

from uuid import uuid4

from test_service.domain.application.commands.execution import CreateEnvironmentCommand
from test_service.domain.model.exceptions.environment_already_exists_exception import (
    EnvironmentAlreadyExistsException,
)
from test_service.domain.model.execution.environment import Environment
from test_service.domain.ports.input.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCase,
)
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (  # noqa: E501
    EnvironmentPersistencePort,
)


class CreateEnvironmentUseCaseImpl(CreateEnvironmentUseCase):
    """Creates an execution environment with a globally unique business key."""

    def __init__(self, environment_repository: EnvironmentPersistencePort) -> None:
        self._environment_repository = environment_repository

    async def execute(self, request: CreateEnvironmentCommand) -> Environment:
        """Create and persist an active execution environment."""
        existing_environment = await self._environment_repository.find_by_key(
            request.environment_key
        )
        if existing_environment is not None:
            raise EnvironmentAlreadyExistsException(request.environment_key)
        return await self._environment_repository.save(
            Environment(
                identifier=uuid4(),
                environment_key=request.environment_key,
                name=request.name,
                created_at=request.requested_at,
                created_by=request.requested_by,
                description=request.description,
                configuration=request.configuration,
            )
        )
