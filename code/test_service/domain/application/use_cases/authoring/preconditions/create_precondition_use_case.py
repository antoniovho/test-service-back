"""Use case implementation: create Precondition."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import CreatePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.precondition_already_exists_exception import (
    PreconditionAlreadyExistsException,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class CreatePreconditionUseCaseImpl(CreatePreconditionUseCase):
    """Creates the first draft snapshot of a Precondition."""

    def __init__(self, precondition_repository: PreconditionPersistencePort) -> None:
        self._precondition_repository = precondition_repository

    async def execute(self, request: CreatePreconditionCommand) -> Precondition:
        """Create and persist version one of a Precondition."""
        latest_version = await self._precondition_repository.find_latest_version(
            request.project_key, request.precondition_key
        )
        if latest_version is not None:
            raise PreconditionAlreadyExistsException(request.project_key, request.precondition_key)
        return await self._precondition_repository.save(
            Precondition(
                identifier=uuid4(),
                project_key=request.project_key,
                precondition_key=request.precondition_key,
                version=1,
                name=request.name,
                description=request.description,
                validation_definition=request.validation_definition,
                created_at=request.requested_at,
                created_by=request.requested_by,
                metadata=request.metadata,
            )
        )
