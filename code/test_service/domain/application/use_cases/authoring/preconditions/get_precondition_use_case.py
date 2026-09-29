"""Use case implementation: get Precondition."""

from test_service.domain.application.queries.authoring import PreconditionQuery
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class GetPreconditionUseCaseImpl(GetPreconditionUseCase):
    """Retrieves one immutable Precondition snapshot."""

    def __init__(self, precondition_repository: PreconditionPersistencePort) -> None:
        self._precondition_repository = precondition_repository

    async def execute(self, request: PreconditionQuery) -> Precondition:
        precondition = await self._precondition_repository.find_by_id(request.identifier)
        if precondition is None or precondition.project_key != request.project_key:
            raise EntityNotFoundException(
                "Precondition", str(request.identifier), f"project '{request.project_key}'"
            )
        return precondition
