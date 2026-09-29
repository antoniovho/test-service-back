"""Precondition persistence adapter used to resolve Test Case references."""

from uuid import UUID

from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.mappers.precondition_persistence_mapper import (  # noqa: E501
    PreconditionPersistenceMapper,
)
from test_service.infrastructure.adapters.output.authoring.preconditions.persistence.repositories.precondition_repository import (  # noqa: E501
    PreconditionRepository,
)


class PreconditionPersistenceAdapter(PreconditionPersistencePort):
    """Adapt lookup DTO operations to the Precondition domain port."""

    def __init__(self, repository: PreconditionRepository) -> None:
        self._repository = repository

    async def find_by_id(self, identifier: UUID) -> Precondition | None:
        precondition = await self._repository.find_by_id(identifier)
        return (
            PreconditionPersistenceMapper.to_domain(precondition)
            if precondition is not None
            else None
        )
