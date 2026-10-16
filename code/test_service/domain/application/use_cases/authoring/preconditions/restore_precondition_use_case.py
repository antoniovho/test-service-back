"""Use case implementation: restore a historical Precondition."""

from uuid import uuid4

from test_service.domain.application.commands.authoring import RestorePreconditionCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.input.use_cases.authoring.preconditions.restore_precondition_use_case import (  # noqa: E501
    RestorePreconditionUseCase,
)
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)


class RestorePreconditionUseCaseImpl(RestorePreconditionUseCase):
    """Clone a deprecated Precondition snapshot into the next draft version."""

    def __init__(
        self, repository: PreconditionPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._repository = repository
        self._project_resolver = project_resolver

    async def execute(self, request: RestorePreconditionCommand) -> Precondition:
        await self._project_resolver.resolve_active(request.project_key)
        source = await self._repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Precondition", str(request.source_id), f"project '{request.project_key}'"
            )
        if source.status is not VersionStatus.DEPRECATED:
            raise InvalidLifecycleTransitionException(
                f"only deprecated precondition snapshot '{source.identifier}' can be restored"
            )
        latest = await self._repository.find_latest_version(
            source.project_key, source.precondition_key
        )
        return await self._repository.save(
            Precondition(
                identifier=uuid4(),
                project_key=source.project_key,
                precondition_key=source.precondition_key,
                version=(latest or source.version) + 1,
                name=source.name,
                description=source.description,
                validation_definition=source.validation_definition,
                created_at=request.requested_at,
                created_by=request.requested_by,
                metadata=dict(source.metadata) if source.metadata is not None else None,
            )
        )
