"""Use case implementation: activate Precondition."""

from test_service.domain.application.commands.authoring import ActivatePreconditionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class ActivatePreconditionUseCaseImpl(ActivatePreconditionUseCase):
    """Activates one draft Precondition snapshot."""

    def __init__(self, precondition_repository: PreconditionPersistencePort) -> None:
        self._precondition_repository = precondition_repository

    async def execute(self, request: ActivatePreconditionCommand) -> Precondition:
        precondition = await self._precondition_repository.find_by_id(request.identifier)
        if precondition is None:
            raise EntityNotFoundException("precondition", str(request.identifier))
        return await self._precondition_repository.save(precondition.activate())
