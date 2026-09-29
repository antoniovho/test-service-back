"""Use case implementation: create Precondition version."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import CreatePreconditionVersionCommand
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class CreatePreconditionVersionUseCaseImpl(CreatePreconditionVersionUseCase):
    """Creates a new draft snapshot from an existing Precondition snapshot."""

    def __init__(self, precondition_repository: PreconditionPersistencePort) -> None:
        self._precondition_repository = precondition_repository

    async def execute(self, request: CreatePreconditionVersionCommand) -> Precondition:
        """Create and persist the next immutable Precondition version."""
        source = await self._precondition_repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Precondition", str(request.source_id), f"project '{request.project_key}'"
            )
        latest_version = await self._precondition_repository.find_latest_version(
            source.project_key, source.precondition_key
        )
        return await self._precondition_repository.save(
            Precondition(
                identifier=uuid4(),
                project_key=source.project_key,
                precondition_key=source.precondition_key,
                version=(latest_version or source.version) + 1,
                name=request.name,
                description=request.description,
                validation_definition=request.validation_definition,
                created_at=request.requested_at,
                created_by=request.requested_by,
                metadata=request.metadata,
            )
        )
