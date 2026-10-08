"""Use case implementation: create Test Set version."""

from uuid import uuid4

from test_service.domain.application.commands.composition import CreateTestSetVersionCommand
from test_service.domain.application.services.resolvers.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.entity_not_found_exception import EntityNotFoundException
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class CreateTestSetVersionUseCaseImpl(CreateTestSetVersionUseCase):
    """Creates a new draft snapshot from an existing Test Set snapshot."""

    def __init__(
        self,
        test_set_repository: TestSetPersistencePort,
        test_case_snapshot_resolver: TestCaseSnapshotResolver,
    ) -> None:
        self._test_set_repository = test_set_repository
        self._test_case_snapshot_resolver = test_case_snapshot_resolver

    async def execute(self, request: CreateTestSetVersionCommand) -> TestSet:
        """Create and persist the next immutable Test Set version."""
        source = await self._test_set_repository.find_by_id(request.source_id)
        if source is None or source.project_key != request.project_key:
            raise EntityNotFoundException(
                "Test set", str(request.source_id), f"project '{request.project_key}'"
            )
        latest_version = await self._test_set_repository.find_latest_version(
            source.project_key, source.set_key
        )
        items = await self._test_case_snapshot_resolver.resolve(source.project_key, request.items)
        test_set = TestSet(
            identifier=uuid4(),
            project_key=source.project_key,
            set_key=source.set_key,
            version=(latest_version or source.version) + 1,
            name=request.name,
            items=items,
            description=request.description,
            created_at=request.requested_at,
            created_by=request.requested_by,
        )
        return await self._test_set_repository.save(test_set)
