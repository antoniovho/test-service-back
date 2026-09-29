"""Use case implementation: create Test Set."""

from uuid import uuid4

from test_service.domain.application.commands.composition import CreateTestSetCommand
from test_service.domain.application.services.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.exceptions.test_set_already_exists_exception import (
    TestSetAlreadyExistsException,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCase,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)


class CreateTestSetUseCaseImpl(CreateTestSetUseCase):
    """Creates the first draft snapshot of a Test Set."""

    def __init__(
        self,
        test_set_repository: TestSetPersistencePort,
        test_case_snapshot_resolver: TestCaseSnapshotResolver,
    ) -> None:
        self._test_set_repository = test_set_repository
        self._test_case_snapshot_resolver = test_case_snapshot_resolver

    async def execute(self, request: CreateTestSetCommand) -> TestSet:
        """Create and persist version one of a Test Set."""
        latest_version = await self._test_set_repository.find_latest_version(
            request.project_key, request.set_key
        )
        if latest_version is not None:
            raise TestSetAlreadyExistsException(request.project_key, request.set_key)
        items = await self._test_case_snapshot_resolver.resolve(request.project_key, request.items)
        test_set = TestSet(
            identifier=uuid4(),
            project_key=request.project_key,
            set_key=request.set_key,
            version=1,
            name=request.name,
            items=items,
            description=request.description,
            created_at=request.requested_at,
            created_by=request.requested_by,
        )
        return await self._test_set_repository.save(test_set)
