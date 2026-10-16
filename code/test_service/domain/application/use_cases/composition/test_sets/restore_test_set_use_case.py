"""Use case implementation: restore a historical Test Set."""

from uuid import uuid4

from test_service.domain.application.commands.composition import RestoreTestSetCommand
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.model.exceptions.invalid_lifecycle_transition_exception import (
    InvalidLifecycleTransitionException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.input.use_cases.composition.test_sets.restore_test_set_use_case import (  # noqa: E501
    RestoreTestSetUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class RestoreTestSetUseCaseImpl(RestoreTestSetUseCase):
    """Clone a deprecated Test Set snapshot into the next draft version."""

    def __init__(
        self, repository: TestSetPersistencePort, project_resolver: ProjectResolver
    ) -> None:
        self._repository = repository
        self._project_resolver = project_resolver

    async def execute(self, request: RestoreTestSetCommand) -> TestSet:
        await self._project_resolver.resolve_active(request.project_key)
        source = await self._repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test set", str(request.source_id), f"project '{request.project_key}'"
            )
        if source.status is not VersionStatus.DEPRECATED:
            raise InvalidLifecycleTransitionException(
                "only deprecated test set snapshots can be restored"
            )
        latest = await self._repository.find_latest_version(source.project_key, source.set_key)
        return await self._repository.save(
            TestSet(
                identifier=uuid4(),
                project_key=source.project_key,
                set_key=source.set_key,
                version=(latest or source.version) + 1,
                name=source.name,
                items=source.items,
                created_at=request.requested_at,
                created_by=request.requested_by,
                description=source.description,
            )
        )
